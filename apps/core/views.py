from django.db.models import Q
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from apps.documents.serializers import DocumentListSerializer
from apps.products.models import Product
from apps.products.serializers import ProductListSerializer


class GlobalSearchView(APIView):
    """Cross-model search across products, documents, and catalogues.

    GET /api/v1/search/?q=<term>
    Returns up to 8 results per bucket, grouped by type, for use in the
    header command-palette (Cmd/Ctrl+K) search overlay.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        if len(query) < 2:
            return Response({"query": query, "products": [], "documents": [], "catalogues": []})

        products = (
            Product.objects.filter(active=True)
            .filter(Q(name__icontains=query) | Q(short_description__icontains=query) | Q(product_code__icontains=query))
            .select_related("category")[:8]
        )
        documents = (
            Document.objects.filter(active=True, public=True)
            .exclude(document_type="catalogue")
            .filter(Q(title__icontains=query) | Q(document_code__icontains=query) | Q(description__icontains=query))
            .select_related("current_revision", "product", "category")[:8]
        )
        catalogues = (
            Document.objects.filter(active=True, public=True, document_type="catalogue")
            .filter(Q(title__icontains=query) | Q(description__icontains=query))
            .select_related("current_revision", "category")[:8]
        )

        return Response(
            {
                "query": query,
                "products": ProductListSerializer(products, many=True, context={"request": request}).data,
                "documents": DocumentListSerializer(documents, many=True, context={"request": request}).data,
                "catalogues": DocumentListSerializer(catalogues, many=True, context={"request": request}).data,
            }
        )
