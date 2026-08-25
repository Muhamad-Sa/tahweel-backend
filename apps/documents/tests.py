from datetime import date

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.documents.models import Document, DocumentRevision, DocumentType, RevisionStatus
from apps.products.models import Category


def make_pdf(name="file.pdf", content=b"%PDF-1.4 test"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


class DocumentRevisionStatusTests(TestCase):
    """The most important model behaviour: exactly one 'current' revision per document."""

    def setUp(self):
        self.category = Category.objects.create(name="PPR Systems")
        self.document = Document.objects.create(
            title="Test Datasheet", document_type=DocumentType.DATASHEET, category=self.category
        )

    def test_first_current_revision_becomes_document_pointer(self):
        rev = DocumentRevision.objects.create(
            document=self.document, revision="Rev 01", status=RevisionStatus.CURRENT, file=make_pdf()
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.current_revision_id, rev.id)
        self.assertEqual(rev.version, 1)

    def test_new_current_revision_demotes_previous_to_archived(self):
        rev1 = DocumentRevision.objects.create(
            document=self.document, revision="Rev 01", status=RevisionStatus.CURRENT, file=make_pdf("a.pdf")
        )
        rev2 = DocumentRevision.objects.create(
            document=self.document, revision="Rev 02", status=RevisionStatus.CURRENT, file=make_pdf("b.pdf")
        )
        rev1.refresh_from_db()
        self.document.refresh_from_db()

        self.assertEqual(rev1.status, RevisionStatus.ARCHIVED)
        self.assertEqual(rev2.status, RevisionStatus.CURRENT)
        self.assertEqual(self.document.current_revision_id, rev2.id)
        self.assertEqual(rev2.version, 2)

    def test_only_one_current_revision_ever_exists(self):
        for i in range(5):
            DocumentRevision.objects.create(
                document=self.document, revision=f"Rev {i}", status=RevisionStatus.CURRENT, file=make_pdf(f"{i}.pdf")
            )
        current_count = DocumentRevision.objects.filter(document=self.document, status=RevisionStatus.CURRENT).count()
        self.assertEqual(current_count, 1)

    def test_draft_revision_does_not_become_current_pointer(self):
        DocumentRevision.objects.create(
            document=self.document, revision="Draft", status=RevisionStatus.DRAFT, file=make_pdf()
        )
        self.document.refresh_from_db()
        self.assertIsNone(self.document.current_revision_id)

    def test_file_size_is_populated_from_actual_file(self):
        content = b"%PDF-1.4" + b"x" * 100
        rev = DocumentRevision.objects.create(
            document=self.document, revision="Rev 01", status=RevisionStatus.CURRENT, file=make_pdf(content=content)
        )
        self.assertEqual(rev.file_size, len(content))

    def test_demoting_current_revision_clears_or_reassigns_document_pointer(self):
        rev1 = DocumentRevision.objects.create(
            document=self.document, revision="Rev 01", status=RevisionStatus.CURRENT, file=make_pdf("a.pdf")
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.current_revision_id, rev1.id)

        rev1.status = RevisionStatus.ARCHIVED
        rev1.save()
        self.document.refresh_from_db()
        self.assertIsNone(self.document.current_revision_id)


class DocumentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Drainage Systems")
        self.public_doc = Document.objects.create(
            title="Public Datasheet", document_type=DocumentType.DATASHEET,
            category=self.category, active=True, public=True,
        )
        self.hidden_doc = Document.objects.create(
            title="Hidden Datasheet", document_type=DocumentType.DATASHEET,
            category=self.category, active=True, public=False,
        )
        DocumentRevision.objects.create(
            document=self.public_doc, revision="Rev 01", status=RevisionStatus.CURRENT, file=make_pdf()
        )

    def test_list_only_returns_public_active_documents(self):
        response = self.client.get("/api/v1/documents/")
        self.assertEqual(response.status_code, 200)
        titles = [d["title"] for d in response.data["results"]]
        self.assertIn("Public Datasheet", titles)
        self.assertNotIn("Hidden Datasheet", titles)

    def test_detail_includes_current_revision_with_file_url_and_size(self):
        response = self.client.get(f"/api/v1/documents/{self.public_doc.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["current_revision"])
        self.assertGreater(response.data["current_revision"]["file_size"], 0)

    def test_filter_by_document_type(self):
        response = self.client.get("/api/v1/documents/?document_type=datasheet")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_catalogues_endpoint_only_returns_catalogue_type(self):
        Document.objects.create(
            title="A Catalogue", document_type=DocumentType.CATALOGUE, active=True, public=True
        )
        response = self.client.get("/api/v1/catalogues/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["document_type"], "catalogue")


class DocumentPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="PPR Systems")
        self.document = Document.objects.create(
            title="Doc", document_type=DocumentType.DATASHEET, category=self.category
        )

    def test_anonymous_can_read(self):
        response = self.client.get("/api/v1/documents/")
        self.assertEqual(response.status_code, 200)

    def test_anonymous_cannot_delete(self):
        response = self.client.delete(f"/api/v1/documents/{self.document.slug}/")
        self.assertIn(response.status_code, (401, 403, 405))

    def test_staff_write_permission_helper(self):
        from apps.core.permissions import IsStaffOrReadOnly

        class Req:
            method = "POST"

            class user:
                is_authenticated = True
                is_staff = False

        perm = IsStaffOrReadOnly()
        self.assertFalse(perm.has_permission(Req(), None))

        Req.user.is_staff = True
        self.assertTrue(perm.has_permission(Req(), None))
