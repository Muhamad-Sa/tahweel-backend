from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.products.filters import ProductFilter
from apps.products.models import Category, Product, Standard
from apps.products.serializers import (
    CategoryDetailSerializer,
    CategoryListSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    StandardSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    serializer_class = CategoryListSerializer
    filterset_fields = ["parent"]
    search_fields = ["name", "description"]
    ordering_fields = ["display_order", "name"]

    def get_queryset(self):
        qs = Category.objects.filter(active=True).annotate(
            product_count=Count("products", filter=Q(products__active=True))
        )
        if self.action == "list":
            qs = qs.filter(parent__isnull=True)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CategoryDetailSerializer
        return CategoryListSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    filterset_class = ProductFilter
    search_fields = ["name", "short_description", "long_description", "product_code"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        qs = Product.objects.filter(active=True).select_related("category").prefetch_related(
            "images", "specifications", "standards"
        )
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    @action(detail=True, methods=["get"], url_path="documents")
    def documents(self, request, slug=None):
        from apps.documents.serializers import DocumentListSerializer

        product = self.get_object()
        docs = product.documents.filter(active=True, public=True).select_related(
            "current_revision", "category"
        ).prefetch_related("standards")
        serializer = DocumentListSerializer(docs, many=True, context={"request": request})
        return Response(serializer.data)


class StandardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Standard.objects.all()
    serializer_class = StandardSerializer
    search_fields = ["code", "name"]
    pagination_class = None
