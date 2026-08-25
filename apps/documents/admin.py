from django.contrib import admin
from django.utils.html import format_html

from apps.documents.models import Document, DocumentRevision, DocumentSection


class DocumentRevisionInline(admin.TabularInline):
    model = DocumentRevision
    extra = 0
    fk_name = "document"
    fields = ["revision", "version", "file", "status", "issue_date", "file_size_display", "uploaded_by"]
    readonly_fields = ["version", "file_size_display"]

    @admin.display(description="Size")
    def file_size_display(self, obj):
        if not obj.file_size:
            return "-"
        size = obj.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@admin.register(DocumentSection)
class DocumentSectionAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "display_order"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title", "document_type", "category", "section", "product", "language",
        "active", "public", "featured", "current_revision_badge",
    ]
    list_filter = ["document_type", "language", "active", "public", "featured", "category", "section"]
    search_fields = ["title", "document_code", "description"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["standards"]
    autocomplete_fields = ["product", "category", "section"]
    inlines = [DocumentRevisionInline]

    @admin.display(description="Current revision")
    def current_revision_badge(self, obj):
        if not obj.current_revision:
            return format_html('<span style="color:#b91c1c;font-weight:600;">No current revision</span>')
        return format_html(
            '<span style="color:#166534;font-weight:600;">{} (v{})</span>',
            obj.current_revision.revision,
            obj.current_revision.version,
        )


@admin.register(DocumentRevision)
class DocumentRevisionAdmin(admin.ModelAdmin):
    list_display = ["document", "revision", "version", "status", "issue_date", "file_size_display", "uploaded_by"]
    list_filter = ["status"]
    search_fields = ["document__title", "revision", "original_filename"]
    autocomplete_fields = ["document"]
    readonly_fields = ["file_size", "mime_type", "original_filename"]

    @admin.display(description="Size")
    def file_size_display(self, obj):
        if not obj.file_size:
            return "-"
        size = obj.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
