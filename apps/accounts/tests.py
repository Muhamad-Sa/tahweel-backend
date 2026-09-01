from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase


class SiteAccessTests(APITestCase):
    access_url = "/api/v1/auth/site-access/"

    @override_settings(SITE_ACCESS_PASSCODE="test-passcode")
    def test_status_reports_that_access_is_required(self):
        response = self.client.get(self.access_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"required": True, "authenticated": False})

    @override_settings(SITE_ACCESS_PASSCODE="test-passcode")
    def test_incorrect_passcode_is_rejected(self):
        response = self.client.post(self.access_url, {"passcode": "wrong"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Incorrect passcode.")

    @override_settings(SITE_ACCESS_PASSCODE="test-passcode")
    def test_valid_token_unlocks_protected_api_routes(self):
        blocked = self.client.get("/api/v1/categories/")
        self.assertEqual(blocked.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(blocked.json()["code"], "site_access_required")

        unlock = self.client.post(self.access_url, {"passcode": "test-passcode"})
        token = unlock.data["token"]

        allowed = self.client.get("/api/v1/categories/", HTTP_X_SITE_ACCESS=token)
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)

        with override_settings(SITE_ACCESS_PASSCODE="a-new-passcode"):
            revoked = self.client.get("/api/v1/categories/", HTTP_X_SITE_ACCESS=token)
            self.assertEqual(revoked.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(SITE_ACCESS_PASSCODE="test-passcode")
    def test_non_object_request_body_is_rejected(self):
        response = self.client.post(self.access_url, ["test-passcode"], format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(SITE_ACCESS_PASSCODE="")
    def test_blank_configuration_disables_gate(self):
        response = self.client.get("/api/v1/categories/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
