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
        ["Tahweel 714 Fitting"],
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

RENAMES = {
    "Tahweel 714 Fitting": "Tahweel 714 Adhesive",
}

RETIRE_IF_EMPTY = ["Drainage Systems", "Sanitary Fixtures & Valves"]

MISSING_PRODUCTS = {
    "Tahweel Glue & Adhesives": ["717 Adhesive"],
}


class Command(BaseCommand):
    help = "Reassign products into the curated catalogue taxonomy supplied by the client."

    def handle(self, *args, **options):
        for old_name, new_name in RENAMES.items():
            Product.objects.filter(name=old_name).update(name=new_name)

        for name, order, description, product_names in NEW_CATEGORIES:
            category, _ = Category.objects.update_or_create(
                name=name, defaults={"display_order": order, "description": description, "active": True}
            )
            moved = 0
            for pname in product_names:
                actual_name = RENAMES.get(pname, pname)
                updated = Product.objects.filter(name=actual_name).update(category=category)
                if updated:
                    moved += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  '{actual_name}' not found -- not moved into {name}"))

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

        self.stdout.write(self.style.SUCCESS("\nProducts not yet supplied:"))
        for section, products in MISSING_PRODUCTS.items():
            self.stdout.write(f"  {section}: {', '.join(products)}")
