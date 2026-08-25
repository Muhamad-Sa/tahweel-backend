from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """A product family, e.g. PPR Systems, Drainage Systems.

    Supports one level (or more, via self-FK) of subcategories.
    """

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Lucide icon name used by the frontend, e.g. 'droplets', 'pipe'.",
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="subcategories"
    )
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Standard(models.Model):
    """A referenced industry standard, e.g. DIN 8077, ISO 15874."""

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    long_description = models.TextField(blank=True)
    product_code = models.CharField(max_length=100, blank=True, db_index=True)
    featured_image = models.ImageField(upload_to="products/", blank=True, null=True)
    active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    application = models.CharField(
        max_length=255, blank=True, help_text="Typical use case, e.g. 'Hot & cold water supply lines'."
    )
    material = models.CharField(max_length=150, blank=True, help_text="e.g. PP-R, uPVC, ABS, Stainless Steel 304")
    country_of_origin = models.CharField(max_length=100, blank=True, default="Saudi Arabia")
    warranty_info = models.CharField(max_length=255, blank=True)
    standards = models.ManyToManyField(Standard, blank=True, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__display_order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["active"]),
            models.Index(fields=["category"]),
            models.Index(fields=["featured"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.product.name} image #{self.display_order}"


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specifications")
    group = models.CharField(
        max_length=100, blank=True, help_text="Section heading, e.g. 'Dimensions', 'Pressure Rating'."
    )
    name = models.CharField(max_length=150)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=30, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["group", "display_order", "id"]

    def __str__(self):
        return f"{self.name}: {self.value}{self.unit}"
