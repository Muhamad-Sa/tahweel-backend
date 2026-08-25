from django.core.management.base import BaseCommand

from apps.products.models import Category, Product

# Sourced from the real "Tahweel Product Catalogue 2024" PDF (image-based /
# scanned, so it has no text layer -- verified by visually rendering pages
# 16-19: "PP-R Valves for Water Supply Solutions"). No separate standalone
# datasheet PDF exists yet for these -- the catalogue page is the only
# source, so specs below are limited to what that spread actually states.
PRODUCTS = [
    {
        "name": "Ball Valve",
        "short_description": "PP-R ball valve for cold and hot water supply, 20 mm to 110 mm.",
        "long_description": (
            "Withstands high water pressures up to 25 bar (PN25). Features premium-quality "
            "copper in compliance with European standards. Equipped with a stainless steel 304 "
            "handle and a distinctive plastic hand cover. Nickel-chrome plated brass ball, sealed "
            "with premium German gaskets. Also available in a compression-fitting 'Multi+' "
            "variant for multilayer pipe. Source: Tahweel Product Catalogue 2024, p.16-17."
        ),
        "material": "Brass (nickel-chrome plated), PP-R body",
        "application": "Cold and hot water supply, infrastructure networks, swimming pool systems",
        "warranty_info": "",
    },
    {
        "name": "Gate Valve",
        "short_description": "PP-R gate valve for water supply isolation.",
        "long_description": (
            "Featured in the PP-R Valves range of the Tahweel Product Catalogue 2024 (p.16), "
            "also available in a compression-fitting 'Multi+' variant for multilayer pipe. "
            "No standalone datasheet has been supplied yet -- detailed specifications beyond "
            "what appears on the catalogue page are not confirmed."
        ),
        "material": "Brass",
        "application": "Water supply isolation",
        "warranty_info": "",
    },
    {
        "name": "Stop Globe Valve",
        "short_description": "PP-R stop globe valve for water supply flow regulation.",
        "long_description": (
            "Featured in the PP-R Valves range of the Tahweel Product Catalogue 2024 (p.16), "
            "also available in a compression-fitting 'Multi+' variant for multilayer pipe. "
            "No standalone datasheet has been supplied yet -- detailed specifications beyond "
            "what appears on the catalogue page are not confirmed."
        ),
        "material": "Brass",
        "application": "Water supply flow regulation",
        "warranty_info": "",
    },
    {
        "name": "Quarter Turn Valve",
        "short_description": "Quick-turn concealed ball valve, 25-32 mm, in-wall installation.",
        "long_description": (
            "Nickel-chrome plated handle and cover, premium-quality copper core for the longest "
            "service life, German gasket for a tight seal, nickel-chrome plated ball for maximum "
            "flow efficiency. Quick quarter-turn operation for easy opening/closing; designed for "
            "premium bathrooms and kitchens. Source: Tahweel Product Catalogue 2024, p.18 "
            "('Quick-turn Concealed Ball Valve 25-32mm')."
        ),
        "material": "Brass core, nickel-chrome plated handle and cover",
        "application": "Concealed in-wall water supply shut-off",
        "warranty_info": "",
    },
    {
        "name": "Concealed Valve",
        "short_description": "Concealed chrome valve for in-wall installation, 20-40 mm.",
        "long_description": (
            "Engraved with a 'T' on the handle to guarantee product authenticity. High-quality "
            "German gaskets ensure a secure seal. Nickel-chrome plating for extended operational "
            "lifespan. Source: Tahweel Product Catalogue 2024, p.19 ('Concealed Chrome Valve')."
        ),
        "material": "Brass, nickel-chrome plated",
        "application": "Concealed in-wall water supply shut-off",
        "warranty_info": "",
    },
    {
        "name": "Flange",
        "short_description": "PP-R flange adaptor for bolted water-supply connections.",
        "long_description": (
            "Flanged PP-R connection component for joining a PP-R water-supply line to "
            "compatible flanged equipment or pipework. A product image has been supplied, "
            "but no standalone datasheet is available yet; dimensions, pressure ratings, "
            "and standards should be confirmed with Tahweel before specification."
        ),
        "material": "PP-R body with bolted flange ring",
        "application": "Flanged transitions in water-supply systems",
        "warranty_info": "",
    },
]


class Command(BaseCommand):
    help = "Add the Water Supply valve products found in the Tahweel Product Catalogue 2024 (pages 16-19)."

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            name="Water Supply", defaults={"display_order": 10}
        )
        for data in PRODUCTS:
            name = data["name"]
            defaults = {key: value for key, value in data.items() if key != "name"}
            product, created = Product.objects.update_or_create(
                name=name,
                defaults={**defaults, "category": category, "country_of_origin": "Saudi Arabia"},
            )
            self.stdout.write(f"{'Created' if created else 'Updated'}: {name}")

        self.stdout.write(
            self.style.WARNING(
                "\nNo standalone PDF was supplied for the water-supply valve products. "
                "Product records are published from the supplied catalogue information and images only."
            )
        )
        self.stdout.write(self.style.SUCCESS("Done."))
