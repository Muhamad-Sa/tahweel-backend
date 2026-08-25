from rest_framework import serializers

from apps.documents.models import Document, DocumentRevision, DocumentSection
from apps.products.serializers import CategoryMiniSerializer, StandardSerializer


class DocumentSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentSection
        fields = ["id", "name", "slug", "display_order"]


class DocumentRevisionSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = DocumentRevision
        fields = [
            "id", "revision", "version", "file_url", "original_filename",
            "file_size", "file_size_display", "mime_type", "issue_date", "status",
        ]

    def get_file_url(self, obj):
        if obj.external_url:
            return obj.external_url
        request = self.context.get("request")
        if not obj.file:
            return None
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_file_size_display(self, obj):
        size = obj.file_size or 0
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class DocumentProductMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    featured_image = serializers.SerializerMethodField()

    def get_featured_image(self, obj):
        if not obj.featured_image:
            return None
        request = self.context.get("request")
        url = obj.featured_image.url
        return request.build_absolute_uri(url) if request else url


class DocumentListSerializer(serializers.ModelSerializer):
    current_revision = DocumentRevisionSerializer(read_only=True)
    category = CategoryMiniSerializer(read_only=True)
    section = DocumentSectionSerializer(read_only=True)
    product = DocumentProductMiniSerializer(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id", "title", "slug", "document_code", "document_type",
            "language", "category", "section", "product", "cover_image",
            "current_revision", "featured",
        ]

class DocumentDetailSerializer(DocumentListSerializer):
    standards = StandardSerializer(many=True, read_only=True)
    revisions = DocumentRevisionSerializer(many=True, read_only=True)
    description = serializers.CharField()

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + ["description", "standards", "revisions", "created_at", "updated_at"]
