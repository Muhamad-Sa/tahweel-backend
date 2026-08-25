from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from apps.inquiries.models import ContactInquiry
from apps.inquiries.serializers import ContactInquirySerializer


class ContactInquiryViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """POST-only public endpoint: anyone can submit an inquiry, nobody can read/list it via the API."""

    queryset = ContactInquiry.objects.all()
    serializer_class = ContactInquirySerializer
    permission_classes = [AllowAny]
