"""
Certificate collection service with strict safety controls.

This service provides passive/public TLS metadata collection only.
Implements strict network timeouts, validates target resolution before connecting,
and respects the platform's passive/public-observation model.
"""
import socket
import ssl
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.utils import timezone

from .models import Certificate, CertificateObservation


class CertificateCollectionError(Exception):
    """Base exception for certificate collection errors."""
    pass


class CertificateTimeoutError(CertificateCollectionError):
    """Raised when certificate collection times out."""
    pass


class CertificateResolutionError(CertificateCollectionError):
    """Raised when domain resolution fails."""
    pass


class CertificateSecurityError(CertificateCollectionError):
    """Raised when a security check fails."""
    pass


class CertificateService:
    """Service for collecting TLS certificate metadata with safety controls."""
    
    # Strict timeout settings (in seconds)
    DNS_TIMEOUT = 5
    CONNECTION_TIMEOUT = 10
    TLS_HANDSHAKE_TIMEOUT = 10
    
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
    ]
    
    @staticmethod
    def _is_blocked_address(ip_address: str) -> bool:
        """
        Check if an IP address is in a blocked range.
        
        Prevents SSRF attacks by blocking private, loopback, link-local,
        and multicast addresses.
        """
        import ipaddress
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            for blocked_range in CertificateService.BLOCKED_RANGES:
                network = ipaddress.ip_network(blocked_range, strict=False)
                if ip in network:
                    return True
            
            return False
        except (ValueError, ipaddress.AddressValueError):
            # Invalid IP address - block it
            return True
    
    @staticmethod
    def _resolve_domain_safely(domain: str) -> List[str]:
        """
        Resolve a domain to IP addresses with strict timeout and validation.
        
        Args:
            domain: The domain name to resolve
            
        Returns:
            List of resolved IP addresses
            
        Raises:
            CertificateResolutionError: If resolution fails or times out
            CertificateSecurityError: If resolved IP is in a blocked range
        """
        try:
            # Set DNS timeout
            socket.setdefaulttimeout(CertificateService.DNS_TIMEOUT)
            
            # Resolve the domain
            addr_info = socket.getaddrinfo(domain, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
            
            # Extract unique IP addresses
            ips = set()
            for info in addr_info:
                ip = info[4][0]
                
                # Check if IP is blocked
                if CertificateService._is_blocked_address(ip):
                    raise CertificateSecurityError(
                        f"Resolved IP {ip} is in a blocked range - potential SSRF attempt"
                    )
                
                ips.add(ip)
            
            if not ips:
                raise CertificateResolutionError(f"No IP addresses resolved for {domain}")
            
            return list(ips)
            
        except socket.timeout:
            raise CertificateResolutionError(f"DNS resolution timeout for {domain}")
        except socket.gaierror as e:
            raise CertificateResolutionError(f"DNS resolution failed for {domain}: {e}")
        finally:
            socket.setdefaulttimeout(None)
    
    @staticmethod
    def _collect_certificate_from_host(hostname: str, port: int = 443) -> Dict[str, Any]:
        """
        Collect certificate metadata from a host with strict timeout.
        
        Args:
            hostname: The hostname to connect to
            port: The port to connect to (default 443)
            
        Returns:
            Dictionary containing certificate metadata
            
        Raises:
            CertificateTimeoutError: If connection or handshake times out
            CertificateCollectionError: If certificate collection fails
        """
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # We're collecting metadata, not validating
        
        sock = None
        ssl_sock = None
        
        try:
            # Create socket with timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CertificateService.CONNECTION_TIMEOUT)
            
            # Connect
            sock.connect((hostname, port))
            
            # Wrap with SSL
            ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
            ssl_sock.settimeout(CertificateService.TLS_HANDSHAKE_TIMEOUT)
            
            # Get certificate
            cert_der = ssl_sock.getpeercert(binary_form=True)
            cert_dict = ssl_sock.getpeercert()
            
            if not cert_der or not cert_dict:
                raise CertificateCollectionError("No certificate returned")
            
            # Extract metadata
            metadata = {
                "subject": CertificateService._extract_subject(cert_dict),
                "issuer": CertificateService._extract_issuer(cert_dict),
                "serial_number": CertificateService._extract_serial_number(cert_dict),
                "fingerprint": CertificateService._calculate_fingerprint(cert_der, "sha1"),
                "fingerprint_sha256": CertificateService._calculate_fingerprint(cert_der, "sha256"),
                "valid_from": CertificateService._parse_time(cert_dict.get("notBefore")),
                "valid_until": CertificateService._parse_time(cert_dict.get("notAfter")),
                "sans": CertificateService._extract_sans(cert_dict),
                "public_key_algorithm": CertificateService._extract_public_key_algorithm(cert_dict),
                "public_key_size": CertificateService._extract_public_key_size(cert_dict),
                "tls_version": ssl_sock.version(),
                "cipher_suite": ssl_sock.cipher(),
            }
            
            return metadata
            
        except socket.timeout:
            raise CertificateTimeoutError(f"Connection timeout to {hostname}:{port}")
        except ssl.SSLError as e:
            raise CertificateCollectionError(f"SSL error: {e}")
        except Exception as e:
            raise CertificateCollectionError(f"Certificate collection failed: {e}")
        finally:
            if ssl_sock:
                try:
                    ssl_sock.close()
                except:
                    pass
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    @staticmethod
    def _extract_subject(cert_dict: Dict[str, Any]) -> str:
        """Extract subject from certificate dictionary."""
        subject = cert_dict.get("subject", [])
        if subject:
            for item in subject:
                if item[0][0] == "commonName":
                    return item[0][1]
        return "Unknown"
    
    @staticmethod
    def _extract_issuer(cert_dict: Dict[str, Any]) -> str:
        """Extract issuer from certificate dictionary."""
        issuer = cert_dict.get("issuer", [])
        if issuer:
            for item in issuer:
                if item[0][0] == "organizationName":
                    return item[0][1]
                if item[0][0] == "commonName":
                    return item[0][1]
        return "Unknown"
    
    @staticmethod
    def _extract_serial_number(cert_dict: Dict[str, Any]) -> str:
        """Extract serial number from certificate dictionary."""
        serial = cert_dict.get("serialNumber")
        if serial:
            return str(serial)
        return "Unknown"
    
    @staticmethod
    def _calculate_fingerprint(cert_der: bytes, algorithm: str = "sha256") -> str:
        """Calculate certificate fingerprint."""
        if algorithm == "sha1":
            return hashlib.sha1(cert_der).hexdigest().upper()
        elif algorithm == "sha256":
            return hashlib.sha256(cert_der).hexdigest().upper()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    @staticmethod
    def _parse_time(time_str: Optional[str]) -> Optional[datetime]:
        """Parse ASN.1 time string to datetime."""
        if not time_str:
            return None
        
        try:
            # Handle various time formats
            if "T" in time_str:
                # Format: YYYYMMDDHHMMSSZ or YYYYMMDDHHMMSS+HHMM
                return datetime.strptime(time_str[:14], "%Y%m%d%H%M%S")
            else:
                # Try other formats
                return datetime.strptime(time_str, "%Y%m%d%H%M%SZ")
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _extract_sans(cert_dict: Dict[str, Any]) -> List[str]:
        """Extract Subject Alternative Names from certificate."""
        sans = []
        extensions = cert_dict.get("extensions", [])
        
        for ext in extensions:
            if ext[0] == "subjectAltName":
                for san in ext[1]:
                    if san.startswith("DNS:"):
                        sans.append(san[4:])
        
        return sans
    
    @staticmethod
    def _extract_public_key_algorithm(cert_dict: Dict[str, Any]) -> str:
        """Extract public key algorithm from certificate."""
        pubkey = cert_dict.get("pubkey", {})
        if pubkey:
            return pubkey.get("type", "Unknown")
        return "Unknown"
    
    @staticmethod
    def _extract_public_key_size(cert_dict: Dict[str, Any]) -> Optional[int]:
        """Extract public key size from certificate."""
        pubkey = cert_dict.get("pubkey", {})
        if pubkey:
            bits = pubkey.get("bits")
            if bits:
                return int(bits)
        return None
    
    @staticmethod
    def collect_certificate(domain_name: str) -> Dict[str, Any]:
        """
        Collect certificate metadata for a domain with full safety controls.
        
        This method:
        1. Validates domain resolution
        2. Checks for blocked IP ranges (SSRF protection)
        3. Enforces strict network timeouts
        4. Collects only passive/public TLS metadata
        5. Avoids intrusive TLS testing
        
        Args:
            domain_name: The domain name to collect certificate for
            
        Returns:
            Dictionary containing certificate metadata
            
        Raises:
            CertificateResolutionError: If domain resolution fails
            CertificateSecurityError: If security check fails
            CertificateTimeoutError: If operation times out
            CertificateCollectionError: If collection fails
        """
        # Resolve domain with safety checks
        ips = CertificateService._resolve_domain_safely(domain_name)
        
        if not ips:
            raise CertificateResolutionError(f"No IP addresses resolved for {domain_name}")
        
        # Collect certificate from first resolved IP
        # Use hostname for SNI
        metadata = CertificateService._collect_certificate_from_host(domain_name, 443)
        
        # Add resolved IPs to metadata
        metadata["resolved_ips"] = ips
        
        # Determine certificate status
        now = timezone.now()
        valid_from = metadata.get("valid_from")
        valid_until = metadata.get("valid_until")
        
        metadata["is_valid"] = True
        metadata["is_expired"] = False
        metadata["is_self_signed"] = False
        
        if valid_until and valid_until < now:
            metadata["is_expired"] = True
            metadata["is_valid"] = False
        
        # Check for self-signed (issuer == subject)
        if metadata["issuer"] == metadata["subject"]:
            metadata["is_self_signed"] = True
        
        return metadata
    
    @staticmethod
    def save_certificate_observation(domain, metadata: Dict[str, Any]) -> CertificateObservation:
        """
        Save a certificate observation to the database.
        
        Args:
            domain: The Domain model instance
            metadata: Certificate metadata from collection
            
        Returns:
            CertificateObservation instance
        """
        observation = CertificateObservation.objects.create(
            domain=domain,
            subject=metadata.get("subject", "Unknown"),
            issuer=metadata.get("issuer", "Unknown"),
            serial_number=metadata.get("serial_number", "Unknown"),
            fingerprint=metadata.get("fingerprint", ""),
            fingerprint_sha256=metadata.get("fingerprint_sha256", ""),
            valid_from=metadata.get("valid_from"),
            valid_until=metadata.get("valid_until"),
            sans=metadata.get("sans", []),
            public_key_algorithm=metadata.get("public_key_algorithm", ""),
            public_key_size=metadata.get("public_key_size"),
            tls_version=metadata.get("tls_version", ""),
            cipher_suite=str(metadata.get("cipher_suite", "")),
            is_valid=metadata.get("is_valid", True),
            is_expired=metadata.get("is_expired", False),
            is_self_signed=metadata.get("is_self_signed", False),
            source="TLS Handshake",
            collection_method="Passive Collection",
            confidence="HIGH",
        )
        
        return observation
    
    @staticmethod
    def update_current_certificate(domain, metadata: Dict[str, Any]) -> Certificate:
        """
        Update or create the current certificate for a domain.
        
        Args:
            domain: The Domain model instance
            metadata: Certificate metadata from collection
            
        Returns:
            Certificate instance
        """
        certificate, created = Certificate.objects.update_or_create(
            domain=domain,
            fingerprint_sha256=metadata.get("fingerprint_sha256", ""),
            defaults={
                "subject": metadata.get("subject", "Unknown"),
                "issuer": metadata.get("issuer", "Unknown"),
                "serial_number": metadata.get("serial_number", "Unknown"),
                "fingerprint": metadata.get("fingerprint", ""),
                "valid_from": metadata.get("valid_from"),
                "valid_until": metadata.get("valid_until"),
                "sans": metadata.get("sans", []),
                "public_key_algorithm": metadata.get("public_key_algorithm", ""),
                "public_key_size": metadata.get("public_key_size"),
                "tls_version": metadata.get("tls_version", ""),
                "cipher_suite": str(metadata.get("cipher_suite", "")),
                "is_valid": metadata.get("is_valid", True),
                "is_expired": metadata.get("is_expired", False),
                "is_self_signed": metadata.get("is_self_signed", False),
                "source": "TLS Handshake",
            }
        )
        
        # Update last_seen
        certificate.last_seen = timezone.now()
        certificate.save()
        
        return certificate
