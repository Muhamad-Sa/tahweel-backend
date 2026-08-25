from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.storage import storage_service
from apps.documents.filters import DocumentFilter
from apps.documents.models import Document, DocumentRevision, DocumentType
from apps.documents.serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentRevisionSerializer,
)


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """Public technical library: datasheets, catalogues, submittals, certificates, etc."""

    lookup_field = "slug"
    filterset_class = DocumentFilter
    search_fields = ["title", "document_code", "description"]
    ordering_fields = ["title", "created_at", "current_revision__issue_date"]

    def get_queryset(self):
        qs = Document.objects.filter(active=True, public=True).select_related(
            "current_revision", "category", "section", "product"
        ).prefetch_related("standards", "revisions")
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DocumentDetailSerializer
        return DocumentListSerializer


class CatalogueViewSet(DocumentViewSet):
    """Same as DocumentViewSet, pre-filtered to document_type=catalogue."""

    def get_queryset(self):
        return super().get_queryset().filter(document_type=DocumentType.CATALOGUE)


@api_view(["GET"])
def document_type_list(request):
    return Response([{"value": value, "label": label} for value, label in DocumentType.choices])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def presign_upload(request):
    """Staff-only stub/working endpoint for a future direct-to-R2 upload flow.

    Not called by the current frontend -- document uploads today go through
    Django Admin (DocumentRevision.file, handled by the active storage
    backend). Kept here so the presigned-upload path can be wired up later
    without touching models or serializers.
    """
    if not request.user.is_staff:
        return Response({"detail": "Staff access required."}, status=status.HTTP_403_FORBIDDEN)

    filename = request.data.get("filename")
    content_type = request.data.get("content_type", "application/pdf")
    if not filename:
        return Response({"detail": "filename is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        presigned = storage_service.build_presigned_upload_url("documents", filename, content_type)
    except NotImplementedError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_501_NOT_IMPLEMENTED)

    return Response(
        {
            "url": presigned.url,
            "fields": presigned.fields,
            "key": presigned.key,
            "expires_in": presigned.expires_in,
        }
    )
