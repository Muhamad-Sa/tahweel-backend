from django.core.management.base import BaseCommand

from apps.products.models import Category, Product

# (category name, display_order, description, [exact product names to move in])
NEW_CATEGORIES = [
    (
        "Water Supply",
        10,
        "Valves and fittings for potable water supply lines.",
        [
            "Ball Valve", "Gate Valve", "Stop Globe Valve",
            "Quarter Turn Valve", "Concealed Valve", "Flange",
        ],
    ),
    (
        "Indoor Drainage",
        20,
        "Floor drains and covers for internal drainage points.",
        ["Floor Drain with Rubber 50/75mm", "Stainless Steel Cover"],
    ),
    (
        "Outdoor Drainage Solutions",
        30,
        "Below-ground and site drainage: trench drains, gully traps, inspection chambers and back water valves.",
        ["Trench Drain", "Gully Trap", "Inspection Chamber (Manhole)", "Back Water Valve"],
    ),
    (
        "Tahweel Glue & Adhesives",
        40,
        "Solvent cements and adhesives for pipe jointing.",
        ["Tahweel 714 CPVC Cement", "Tahweel 717 PVC Cement"],
    ),
    (
        "Sanitary Ware & Accessories",
        50,
        "Valves, connectors, mixers, cisterns and shower drains for bathrooms and utility areas.",
        [
            "Angle Valve", "Flexible Connection", "Concealed Shower Mixer",
            "Dual Flush Mechanical Concealed Cistern", "Flush Tank", "Shower Drain",
        ],
    ),
]

ADHESIVE_PRODUCTS = [
    {
        "slug": "tahweel-714-fitting",
        "name": "Tahweel 714 CPVC Cement",
        "product_code": "TAH-714",
        "material": "CPVC solvent cement",
        "application": "Heavy-bodied orange cement for CPVC pipes and fittings up to 12 inches",
        "short_description": "Low-VOC, heavy-bodied orange CPVC solvent cement for joining CPVC pipes and fittings.",
        "long_description": "Tahweel 714 is a heavy-bodied orange CPVC solvent cement for CPVC pipe and fitting joints. The supplied product label references ASTM F493.",
        "country_of_origin": "United States",
    },
    {
        "slug": "tahweel-717-pvc-cement",
        "name": "Tahweel 717 PVC Cement",
        "product_code": "TAH-717",
        "material": "PVC solvent cement",
        "application": "Heavy-bodied gray cement for PVC pipes and fittings up to 12 inches",
        "short_description": "Low-VOC, heavy-bodied gray PVC solvent cement for joining PVC pipes and fittings.",
        "long_description": "Tahweel 717 is a heavy-bodied gray PVC solvent cement for PVC pipe and fitting joints. The supplied product label references ASTM D2564.",
        "country_of_origin": "United States",
    },
]

RETIRE_IF_EMPTY = ["Drainage Systems", "Sanitary Fixtures & Valves"]

class Command(BaseCommand):
    help = "Reassign products into the curated catalogue taxonomy supplied by the client."

    def handle(self, *args, **options):
        for name, order, description, product_names in NEW_CATEGORIES:
            category, _ = Category.objects.update_or_create(
                name=name, defaults={"display_order": order, "description": description, "active": True}
            )
            if name == "Tahweel Glue & Adhesives":
                for details in ADHESIVE_PRODUCTS:
                    slug = details["slug"]
                    Product.objects.update_or_create(
                        slug=slug,
                        defaults={**details, "category": category, "active": True},
                    )

            moved = 0
            for pname in product_names:
                updated = Product.objects.filter(name=pname).update(category=category)
                if updated:
                    moved += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  '{pname}' not found -- not moved into {name}"))

            # Also repoint that product's documents' category badge to match.
            for product in Product.objects.filter(category=category):
                product.documents.update(category=category)

            self.stdout.write(f"{name}: {moved}/{len(product_names)} product(s) assigned")

        for name in RETIRE_IF_EMPTY:
            try:
                cat = Category.objects.get(name=name)
            except Category.DoesNotExist:
                continue
            if not cat.products.exists():
                cat.active = False
                cat.save(update_fields=["active"])
                self.stdout.write(f"Retired empty category: {name}")
            else:
                self.stdout.write(self.style.WARNING(f"{name} still has products -- not retired"))

        self.stdout.write(self.style.SUCCESS("\nCatalogue categories and supplied products are up to date."))
