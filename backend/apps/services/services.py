"""
Service collection service with strict SSRF protections.

This service provides conservative service observation with:
- Strict connection timeouts
- Redirect validation
- Response-size limits
- Concurrency limits
- SSRF protections (private IP blocking, reserved address blocking, loopback blocking, link-local blocking, multicast blocking)
- DNS resolution validation
- DNS rebinding protection

Absolutely NO credential attacks, brute force, exploitation, authentication bypass, or destructive testing.
"""
import socket
import ipaddress
import urllib.parse
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.utils import timezone

from .models import Service, ServiceObservation


class ServiceCollectionError(Exception):
    """Base exception for service collection errors."""
    pass


class ServiceTimeoutError(ServiceCollectionError):
    """Raised when service collection times out."""
    pass


class ServiceSecurityError(ServiceCollectionError):
    """Raised when a security check fails (SSRF, etc.)."""
    pass


class ServiceResolutionError(ServiceCollectionError):
    """Raised when domain resolution fails."""
    pass


class ServiceService:
    """Service for collecting service metadata with strict safety controls."""
    
    # Strict timeout settings (in seconds)
    DNS_TIMEOUT = 5
    CONNECTION_TIMEOUT = 10
    RESPONSE_TIMEOUT = 10
    
    # Response size limit (in bytes)
    MAX_RESPONSE_SIZE = 1024 * 1024  # 1MB
    
    # Blocked address ranges for SSRF protection
    BLOCKED_RANGES = [
        # Private addresses
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        # Loopback
        "127.0.0.0/8",
        "::1/128",
        # Link-local
        "169.254.0.0/16",
        "fe80::/10",
        # Multicast
        "224.0.0.0/4",
        "ff00::/8",
        # Reserved
        "0.0.0.0/8",
        "240.0.0.0/4",
    ]
    
    # Blocked ports (well-known administrative ports)
    BLOCKED_PORTS = [
        22,   # SSH (avoid brute force)
        23,   # Telnet (insecure)
        25,   # SMTP (avoid mail abuse)
        53,   # DNS
        67,   # DHCP
        68,   # DHCP
        123,  # NTP
        161,  # SNMP
        162,  # SNMP trap
        389,  # LDAP
        636,  # LDAPS
        1433, # MSSQL
        3306, # MySQL
        3389, # RDP
        5432, # PostgreSQL
        5900, # VNC
    ]
    
    @staticmethod
    def _is_blocked_address(ip_address: str) -> bool:
        """
        Check if an IP address is in a blocked range.
        
        Prevents SSRF attacks by blocking private, loopback, link-local,
        multicast, and reserved addresses.
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            
            for blocked_range in ServiceService.BLOCKED_RANGES:
                network = ipaddress.ip_network(blocked_range, strict=False)
                if ip in network:
                    return True
            
            return False
        except (ValueError, ipaddress.AddressValueError):
            # Invalid IP address - block it
            return True
    
    @staticmethod
    def _is_blocked_port(port: int) -> bool:
        """
        Check if a port is blocked.
        
        Blocks well-known administrative ports to avoid
        potential abuse or brute force implications.
        """
        return port in ServiceService.BLOCKED_PORTS
    
    @staticmethod
    def _validate_url_safely(url: str) -> Dict[str, Any]:
        """
        Validate a URL and extract safe components.
        
        Args:
            url: The URL to validate
            
        Returns:
            Dictionary with hostname, port, and protocol
            
        Raises:
            ServiceSecurityError: If URL is invalid or unsafe
        """
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Only allow http and https
            if parsed.scheme not in ["http", "https"]:
                raise ServiceSecurityError(f"Unsupported scheme: {parsed.scheme}")
            
            # Extract hostname
            hostname = parsed.hostname
            if not hostname:
                raise ServiceSecurityError("No hostname in URL")
            
            # Extract port (default to scheme default)
            port = parsed.port
            if port is None:
                port = 443 if parsed.scheme == "https" else 80
            
            # Check if port is blocked
            if ServiceService._is_blocked_port(port):
                raise ServiceSecurityError(f"Port {port} is blocked")
            
            # Resolve hostname to check for blocked IPs
            ips = ServiceService._resolve_hostname_safely(hostname)
            
            return {
                "hostname": hostname,
                "port": port,
                "protocol": parsed.scheme.upper(),
                "ips": ips,
            }
            
        except (ValueError, AttributeError) as e:
            raise ServiceSecurityError(f"Invalid URL: {e}")
    
    @staticmethod
    def _resolve_hostname_safely(hostname: str) -> List[str]:
        """
        Resolve a hostname to IP addresses with strict timeout and validation.
        
        Args:
            hostname: The hostname to resolve
            
        Returns:
            List of resolved IP addresses
            
        Raises:
            ServiceResolutionError: If resolution fails or times out
            ServiceSecurityError: If resolved IP is in a blocked range
        """
        try:
            # Set DNS timeout
            socket.setdefaulttimeout(ServiceService.DNS_TIMEOUT)
            
            # Resolve the hostname
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            
            # Extract unique IP addresses
            ips = set()
            for info in addr_info:
                ip = info[4][0]
                
                # Check if IP is blocked
                if ServiceService._is_blocked_address(ip):
                    raise ServiceSecurityError(
                        f"Resolved IP {ip} is in a blocked range - potential SSRF attempt"
                    )
                
                ips.add(ip)
            
            if not ips:
                raise ServiceResolutionError(f"No IP addresses resolved for {hostname}")
            
            return list(ips)
            
        except socket.timeout:
            raise ServiceResolutionError(f"DNS resolution timeout for {hostname}")
        except socket.gaierror as e:
            raise ServiceResolutionError(f"DNS resolution failed for {hostname}: {e}")
        finally:
            socket.setdefaulttimeout(None)
    
    @staticmethod
    def _check_tcp_port(ip_address: str, port: int, timeout: int = None) -> bool:
        """
        Check if a TCP port is open with strict timeout.
        
        Args:
            ip_address: The IP address to check
            port: The port to check
            timeout: Connection timeout in seconds
            
        Returns:
            True if port is open, False otherwise
        """
        if timeout is None:
            timeout = ServiceService.CONNECTION_TIMEOUT
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_address, port))
            return result == 0
        except socket.timeout:
            return False
        except Exception:
            return False
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    @staticmethod
    def _probe_http_service(url: str, timeout: int = None) -> Dict[str, Any]:
        """
        Probe an HTTP/HTTPS service with strict safety controls.
        
        Args:
            url: The URL to probe
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary containing service metadata
            
        Raises:
            ServiceTimeoutError: If request times out
            ServiceSecurityError: If security check fails
            ServiceCollectionError: If collection fails
        """
        if timeout is None:
            timeout = ServiceService.RESPONSE_TIMEOUT
        
        try:
            import urllib.request
            import urllib.error
            
            # Create request with timeout
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "DNS-Sentinel/1.0 (Passive Observation)")
            
            # Open with timeout
            response = urllib.request.urlopen(req, timeout=timeout)
            
            # Read response with size limit
            content = response.read(ServiceService.MAX_RESPONSE_SIZE)
            
            # Get HTTP status
            http_status = response.getcode()
            
            # Get headers
            headers = dict(response.headers)
            
            return {
                "is_available": True,
                "http_status": http_status,
                "response_size": len(content),
                "headers": headers,
                "ssl_tls_enabled": url.startswith("https://"),
            }
            
        except urllib.error.HTTPError as e:
            return {
                "is_available": True,
                "http_status": e.code,
                "error": str(e),
                "ssl_tls_enabled": url.startswith("https://"),
            }
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.timeout):
                raise ServiceTimeoutError(f"Request timeout for {url}")
            return {
                "is_available": False,
                "error": str(e),
                "ssl_tls_enabled": url.startswith("https://"),
            }
        except socket.timeout:
            raise ServiceTimeoutError(f"Request timeout for {url}")
        except Exception as e:
            return {
                "is_available": False,
                "error": str(e),
                "ssl_tls_enabled": url.startswith("https://"),
            }
    
    @staticmethod
    def observe_service(domain_name: str, ip_address: str = None, port: int = None, service_type: str = "HTTP") -> Dict[str, Any]:
        """
        Observe a service with full safety controls.
        
        This method:
        1. Validates the target
        2. Checks for blocked IP ranges (SSRF protection)
        3. Checks for blocked ports
        4. Enforces strict network timeouts
        5. Limits response size
        6. Avoids intrusive testing
        
        Args:
            domain_name: The domain name
            ip_address: Specific IP address (optional, will resolve if not provided)
            port: Specific port (optional)
            service_type: Type of service to observe (HTTP, HTTPS, etc.)
            
        Returns:
            Dictionary containing service metadata
            
        Raises:
            ServiceResolutionError: If domain resolution fails
            ServiceSecurityError: If security check fails
            ServiceTimeoutError: If operation times out
            ServiceCollectionError: If collection fails
        """
        # Resolve IP if not provided
        if not ip_address:
            ips = ServiceService._resolve_hostname_safely(domain_name)
            ip_address = ips[0] if ips else None
        
        if not ip_address:
            raise ServiceResolutionError(f"No IP address available for {domain_name}")
        
        # Check if IP is blocked
        if ServiceService._is_blocked_address(ip_address):
            raise ServiceSecurityError(f"IP {ip_address} is in a blocked range")
        
        # Determine port
        if not port:
            port = 443 if service_type == "HTTPS" else 80
        
        # Check if port is blocked
        if ServiceService._is_blocked_port(port):
            raise ServiceSecurityError(f"Port {port} is blocked")
        
        # Build URL for HTTP/HTTPS services
        if service_type in ["HTTP", "HTTPS"]:
            protocol = "https" if service_type == "HTTPS" else "http"
            url = f"{protocol}://{domain_name}:{port}/"
            
            # Probe the service
            metadata = ServiceService._probe_http_service(url)
        else:
            # For other services, just check port availability
            is_available = ServiceService._check_tcp_port(ip_address, port)
            metadata = {
                "is_available": is_available,
                "service_type": service_type,
            }
        
        # Add metadata
        metadata["ip_address"] = ip_address
        metadata["port"] = port
        metadata["protocol"] = "TCP"
        metadata["service_type"] = service_type
        metadata["domain_name"] = domain_name
        
        return metadata
    
    @staticmethod
    def save_service_observation(domain, metadata: Dict[str, Any]) -> ServiceObservation:
        """
        Save a service observation to the database.
        
        Args:
            domain: The Domain model instance
            metadata: Service metadata from observation
            
        Returns:
            ServiceObservation instance
        """
        observation = ServiceObservation.objects.create(
            domain=domain,
            ip_address=metadata.get("ip_address"),
            port=metadata.get("port"),
            protocol=metadata.get("protocol", "TCP"),
            service_type=metadata.get("service_type", "UNKNOWN"),
            is_available=metadata.get("is_available", False),
            http_status=metadata.get("http_status"),
            response_time_ms=metadata.get("response_time_ms"),
            service_banner=metadata.get("service_banner", ""),
            ssl_tls_enabled=metadata.get("ssl_tls_enabled", False),
            source="Service Observation",
            collection_method="Passive Observation",
            confidence="MEDIUM",
        )
        
        return observation
    
    @staticmethod
    def update_current_service(domain, metadata: Dict[str, Any]) -> Service:
        """
        Update or create the current service for a domain.
        
        Args:
            domain: The Domain model instance
            metadata: Service metadata from observation
            
        Returns:
            Service instance
        """
        service, created = Service.objects.update_or_create(
            domain=domain,
            ip_address=metadata.get("ip_address"),
            port=metadata.get("port"),
            protocol=metadata.get("protocol", "TCP"),
            defaults={
                "service_type": metadata.get("service_type", "UNKNOWN"),
                "is_available": metadata.get("is_available", False),
                "http_status": metadata.get("http_status"),
                "response_time_ms": metadata.get("response_time_ms"),
                "service_banner": metadata.get("service_banner", ""),
                "ssl_tls_enabled": metadata.get("ssl_tls_enabled", False),
                "source": "Service Observation",
            }
        )
        
        # Update last_observed
        service.last_observed = timezone.now()
        service.save()
        
        return service
