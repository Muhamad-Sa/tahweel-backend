from django.contrib import admin

from apps.products.models import Category, Product, ProductImage, ProductSpecification, Standard


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "display_order", "active", "product_count"]
    list_filter = ["active", "parent"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["display_order", "name"]

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "product_code", "material", "active", "featured", "document_count"]
    list_filter = ["active", "featured", "category", "material"]
    search_fields = ["name", "product_code", "short_description"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ["standards"]
    inlines = [ProductImageInline, ProductSpecificationInline]
    autocomplete_fields = ["category"]

    @admin.display(description="Documents")
    def document_count(self, obj):
        return obj.documents.count()


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]
