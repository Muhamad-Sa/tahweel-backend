from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.products.models import Category, Product


class ProductAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="PPR Systems", display_order=1)
        self.other_category = Category.objects.create(name="UPVC Systems", display_order=2)
        self.active_product = Product.objects.create(
            name="PPR Pipe", category=self.category, active=True
        )
        self.inactive_product = Product.objects.create(
            name="Discontinued Pipe", category=self.category, active=False
        )

    def test_list_only_returns_active_products(self):
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, 200)
        names = [p["name"] for p in response.data["results"]]
        self.assertIn("PPR Pipe", names)
        self.assertNotIn("Discontinued Pipe", names)

    def test_detail_by_slug(self):
        response = self.client.get(f"/api/v1/products/{self.active_product.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "PPR Pipe")
        self.assertIn("specifications", response.data)
        self.assertIn("images", response.data)

    def test_filter_by_category_slug(self):
        response = self.client.get(f"/api/v1/products/?category={self.other_category.slug}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_search(self):
        response = self.client.get("/api/v1/products/?search=PPR")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_category_list_excludes_subcategories_and_includes_product_count(self):
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, 200)
        ppr = next(c for c in response.data["results"] if c["slug"] == self.category.slug)
        self.assertEqual(ppr["product_count"], 1)


class ProductSlugUniquenessTests(TestCase):
    def test_duplicate_names_get_unique_slugs(self):
        category = Category.objects.create(name="Sanitary Fixtures & Valves")
        p1 = Product.objects.create(name="Angle Valve", category=category)
        p2 = Product.objects.create(name="Angle Valve", category=category)
        self.assertNotEqual(p1.slug, p2.slug)


class WaterSupplyProductCommandTests(TestCase):
    def test_command_adds_flange_and_is_idempotent(self):
        call_command("add_water_supply_valves", verbosity=0)
        call_command("add_water_supply_valves", verbosity=0)

        water_supply = Category.objects.get(name="Water Supply")
        self.assertEqual(water_supply.products.count(), 6)
        flange = Product.objects.get(name="Flange")
        self.assertEqual(flange.category, water_supply)
        self.assertIn("no standalone datasheet", flange.long_description.lower())
