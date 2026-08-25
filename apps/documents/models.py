from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.products.models import Category, Product, Standard


class DocumentType(models.TextChoices):
    DATASHEET = "datasheet", "Datasheet"
    CATALOGUE = "catalogue", "Catalogue"
    MATERIAL_SUBMITTAL = "material_submittal", "Material Submittal"
    CERTIFICATE = "certificate", "Certificate"
    TEST_REPORT = "test_report", "Test Report"
    INSTALLATION_GUIDE = "installation_guide", "Installation Guide"
    WARRANTY = "warranty", "Warranty"
    COMPANY_PROFILE = "company_profile", "Company Profile"
    TECHNICAL_MANUAL = "technical_manual", "Technical Manual"
    OTHER = "other", "Other"


class Language(models.TextChoices):
    ENGLISH = "en", "English"
    ARABIC = "ar", "Arabic"
    BILINGUAL = "en_ar", "English / Arabic"


class DocumentSection(models.Model):
    """A curated grouping used to organize datasheets on the Technical Library page.

    Distinct from Category (product family): a section is a document-browsing
    concept (e.g. "Water Supply", "Indoor Drainage") independent of how
    products are grouped for the catalogue.
    """

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Document(models.Model):
    """A logical document (e.g. 'Angle Valve Datasheet').

    The actual PDF binary lives on DocumentRevision -- a Document can have
    many revisions over time, with exactly one marked 'current'.
    """

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    document_code = models.CharField(max_length=100, blank=True, db_index=True)
    document_type = models.CharField(max_length=30, choices=DocumentType.choices, db_index=True)
    description = models.TextField(blank=True)
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Product family this document belongs to (used for filtering even when not tied to a single product, e.g. a catalogue).",
    )
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.ENGLISH)
    section = models.ForeignKey(
        DocumentSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Curated Technical Library grouping (datasheets only, e.g. 'Water Supply').",
    )
    standards = models.ManyToManyField(Standard, blank=True, related_name="documents")
    current_revision = models.ForeignKey(
        "documents.DocumentRevision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    cover_image = models.ImageField(upload_to="documents/covers/", blank=True, null=True)
    active = models.BooleanField(default=True, db_index=True)
    public = models.BooleanField(default=True, db_index=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-featured", "title"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["document_type"]),
            models.Index(fields=["active", "public"]),
            models.Index(fields=["product"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            i = 1
            while Document.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)


class RevisionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    CURRENT = "current", "Current"
    ARCHIVED = "archived", "Archived"


def document_upload_path(instance, filename):
    return f"documents/{instance.document_id or 'unassigned'}/{filename}"


class DocumentRevision(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="revisions")
    revision = models.CharField(max_length=30, help_text="Human label, e.g. 'Rev 04'.")
    version = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Auto-assigned on create (next integer for this document) -- leave blank.",
    )
    file = models.FileField(upload_to=document_upload_path)
    storage_key = models.CharField(max_length=500, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(default=0, help_text="Bytes")
    mime_type = models.CharField(max_length=100, blank=True)
    checksum = models.CharField(max_length=64, blank=True, help_text="SHA-256 hex digest")
    issue_date = models.DateField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_revisions"
    )
    status = models.CharField(max_length=20, choices=RevisionStatus.choices, default=RevisionStatus.CURRENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version"]
        indexes = [
            models.Index(fields=["document"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["document", "version"], name="unique_document_version"),
        ]

    def __str__(self):
        return f"{self.document.title} - {self.revision}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if self.file and not self.original_filename:
            self.original_filename = getattr(self.file, "name", "") .rsplit("/", 1)[-1]
        if self.file:
            try:
                self.file_size = self.file.size
            except (OSError, ValueError):
                pass

        if is_new and not self.version:
            last = DocumentRevision.objects.filter(document=self.document).order_by("-version").first()
            self.version = (last.version + 1) if last else 1

        promoting_to_current = self.status == RevisionStatus.CURRENT

        super().save(*args, **kwargs)

        if promoting_to_current:
            # Enforce: only one 'current' revision per document at a time.
            # Demote every other revision on this document to 'archived'.
            DocumentRevision.objects.filter(document=self.document, status=RevisionStatus.CURRENT).exclude(
                pk=self.pk
            ).update(status=RevisionStatus.ARCHIVED)

            if self.document.current_revision_id != self.pk:
                self.document.current_revision = self
                self.document.save(update_fields=["current_revision", "updated_at"])
        elif self.document.current_revision_id == self.pk:
            # This revision was demoted away from 'current' -- clear the
            # document's pointer so it doesn't reference a non-current revision.
            self.document.current_revision = (
                DocumentRevision.objects.filter(document=self.document, status=RevisionStatus.CURRENT)
                .order_by("-version")
                .first()
            )
            self.document.save(update_fields=["current_revision", "updated_at"])
