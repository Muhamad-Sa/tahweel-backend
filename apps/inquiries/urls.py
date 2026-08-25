from rest_framework.routers import DefaultRouter

from apps.inquiries.views import ContactInquiryViewSet

router = DefaultRouter()
router.register("contact", ContactInquiryViewSet, basename="contact")

urlpatterns = router.urls
