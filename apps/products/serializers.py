from rest_framework import serializers

from apps.products.models import Category, Product, ProductImage, ProductSpecification, Standard


class StandardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Standard
        fields = ["id", "code", "name", "description"]


class CategoryListSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = [
            "id", "name", "slug", "description", "image", "icon",
            "parent", "display_order", "product_count",
        ]


class CategoryDetailSerializer(CategoryListSerializer):
    subcategories = CategoryListSerializer(many=True, read_only=True)

    class Meta(CategoryListSerializer.Meta):
        fields = CategoryListSerializer.Meta.fields + ["subcategories"]


class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "display_order"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "display_order"]


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ["id", "group", "name", "value", "unit", "display_order"]


class ProductListSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "short_description", "product_code",
            "featured_image", "category", "material", "featured", "active",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    standards = StandardSerializer(many=True, read_only=True)
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "short_description", "long_description",
            "product_code", "featured_image", "category", "material",
            "application", "country_of_origin", "warranty_info", "standards",
            "images", "specifications", "active", "featured",
            "document_count", "created_at", "updated_at",
        ]

    def get_document_count(self, obj):
        return obj.documents.filter(active=True, public=True).count()
