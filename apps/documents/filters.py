import django_filters

from apps.documents.models import Document


class DocumentFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    section = django_filters.CharFilter(field_name="section__slug")
    product = django_filters.CharFilter(field_name="product__slug")
    document_type = django_filters.CharFilter(field_name="document_type")
    language = django_filters.CharFilter(field_name="language")
    standard = django_filters.CharFilter(field_name="standards__code")
    year = django_filters.NumberFilter(field_name="current_revision__issue_date", lookup_expr="year")
    featured = django_filters.BooleanFilter(field_name="featured")

    class Meta:
        model = Document
        fields = ["category", "section", "product", "document_type", "language", "standard", "year", "featured"]
