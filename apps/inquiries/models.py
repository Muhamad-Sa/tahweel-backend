from django.db import models

from apps.products.models import Product


class InquiryType(models.TextChoices):
    GENERAL = "general", "General"
    SALES = "sales", "Sales"
    TECHNICAL_SUPPORT = "technical_support", "Technical Support"
    QUOTATION = "quotation", "Quotation"
    MATERIAL_SUBMITTAL = "material_submittal", "Material Submittal"
    DISTRIBUTOR = "distributor", "Distributor / Partnership"


class InquiryStatus(models.TextChoices):
    NEW = "new", "New"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"


class ContactInquiry(models.Model):
    name = models.CharField(max_length=150)
    company = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=150, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    country = models.CharField(max_length=100, blank=True)
    inquiry_type = models.CharField(max_length=30, choices=InquiryType.choices, default=InquiryType.GENERAL)
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="inquiries"
    )
    project_name = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=InquiryStatus.choices, default=InquiryStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "contact inquiries"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_inquiry_type_display()} ({self.created_at:%Y-%m-%d})"
