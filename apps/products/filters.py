import django_filters

from apps.products.models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    material = django_filters.CharFilter(field_name="material", lookup_expr="icontains")
    featured = django_filters.BooleanFilter(field_name="featured")

    class Meta:
        model = Product
        fields = ["category", "material", "featured"]
