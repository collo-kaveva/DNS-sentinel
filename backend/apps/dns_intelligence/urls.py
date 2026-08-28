from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"domains", views.DomainViewSet, basename="domain")
router.register(r"jobs", views.ScanJobViewSet, basename="job")

urlpatterns = router.urls
