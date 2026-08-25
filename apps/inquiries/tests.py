from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.inquiries.models import ContactInquiry


class ContactInquiryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "name": "Jane Engineer",
            "email": "jane@example.com",
            "message": "We need pricing for PPR pipes for a 200-unit residential project.",
            "inquiry_type": "quotation",
        }

    def test_valid_submission_creates_inquiry(self):
        response = self.client.post("/api/v1/contact/", self.valid_payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactInquiry.objects.count(), 1)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="website@tahweel.com",
        CONTACT_NOTIFICATION_EMAIL="youssef.samier@tahweel.com",
    )
    def test_valid_submission_emails_youssef(self):
        response = self.client.post("/api/v1/contact/", self.valid_payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["youssef.samier@tahweel.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["jane@example.com"])
        self.assertIn("200-unit residential project", mail.outbox[0].body)

    def test_short_message_is_rejected(self):
        payload = {**self.valid_payload, "message": "too short"}
        response = self.client.post("/api/v1/contact/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.data)

    def test_invalid_email_is_rejected(self):
        payload = {**self.valid_payload, "email": "not-an-email"}
        response = self.client.post("/api/v1/contact/", payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_required_field_is_rejected(self):
        payload = {**self.valid_payload}
        del payload["name"]
        response = self.client.post("/api/v1/contact/", payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_list_is_not_publicly_exposed(self):
        self.client.post("/api/v1/contact/", self.valid_payload, format="json")
        response = self.client.get("/api/v1/contact/")
        self.assertIn(response.status_code, (404, 405))
