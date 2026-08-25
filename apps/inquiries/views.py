import logging

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from apps.inquiries.models import ContactInquiry
from apps.inquiries.notifications import send_contact_inquiry_notification
from apps.inquiries.serializers import ContactInquirySerializer


logger = logging.getLogger(__name__)


class ContactInquiryViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """POST-only public endpoint: anyone can submit an inquiry, nobody can read/list it via the API."""

    queryset = ContactInquiry.objects.all()
    serializer_class = ContactInquirySerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        inquiry = serializer.save()
        try:
            send_contact_inquiry_notification(inquiry)
        except Exception:
            # The inquiry remains safely stored in Neon even if the mail
            # provider is temporarily unavailable.
            logger.exception("Unable to email contact inquiry %s.", inquiry.pk)
