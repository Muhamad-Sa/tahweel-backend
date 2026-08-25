import logging

from django.conf import settings
from django.core.mail import EmailMessage

from apps.inquiries.models import ContactInquiry


logger = logging.getLogger(__name__)


def send_contact_inquiry_notification(inquiry: ContactInquiry) -> int:
    """Email a newly saved website inquiry to the configured recipient."""
    recipient = settings.CONTACT_NOTIFICATION_EMAIL.strip()
    if not recipient:
        logger.warning("Contact inquiry %s saved without an email recipient configured.", inquiry.pk)
        return 0

    body = "\n".join(
        [
            "A new message was submitted through the Tahweel website.",
            "",
            f"Name: {inquiry.name}",
            f"Email: {inquiry.email}",
            f"Phone: {inquiry.phone or '-'}",
            f"Company: {inquiry.company or '-'}",
            f"Position: {inquiry.position or '-'}",
            f"Country: {inquiry.country or '-'}",
            f"Inquiry type: {inquiry.get_inquiry_type_display()}",
            f"Project: {inquiry.project_name or '-'}",
            "",
            "Message:",
            inquiry.message,
        ]
    )

    email = EmailMessage(
        subject=f"[Tahweel Website] New {inquiry.get_inquiry_type_display()} inquiry",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        reply_to=[inquiry.email],
    )
    return email.send(fail_silently=False)
