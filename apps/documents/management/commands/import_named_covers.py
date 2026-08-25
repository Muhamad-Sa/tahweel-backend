from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.documents.models import Document
from apps.products.models import Product


# (source image, related product, related document)
DATASHEET_COVERS = [
    ("ABS Floor Drain.jpeg", "Floor Drain with Rubber 50/75mm", "Floor Drain with Rubber 50/75mm Datasheet"),
    ("Angle Valve.jpeg", "Angle Valve", "Angle Valve Datasheet"),
    ("Arabic Flush Tank.jpeg", "Dual Flush Mechanical Concealed Cistern", "Dual Flush Mechanical Concealed Cistern Datasheet"),
    ("Back Water Valve.jpeg", "Back Water Valve", "Back Water Valve Datasheet"),
    ("Flexible Connectors.jpeg", "Flexible Connection", "Flexible Connection Datasheet"),
    ("Flush Tank Kessel.jpeg", "Flush Tank", "Flush Tank Datasheet"),
    ("Gully Trap.jpeg", "Gully Trap", "Gully Trap Datasheet"),
    ("Inspection Chamber.jpeg", "Inspection Chamber (Manhole)", "Inspection Chamber (Manhole) Datasheet"),
    ("Shower drains.jpeg", "Shower Drain", "Shower Drain Datasheet"),
    ("Shower Mixer.jpeg", "Concealed Shower Mixer", "Concealed Shower Mixer Datasheet"),
    ("Stainless Steel cover.jpeg", "Stainless Steel Cover", "Stainless Steel Cover Datasheet"),
    ("Trench Drain Data sheet.jpeg", "Trench Drain", "Trench Drain Datasheet"),
    ("Ball Valve.jpeg", "Ball Valve", None),
    ("Concealed Valve.jpeg", "Concealed Valve", None),
    ("Flange.jpeg", "Flange", None),
    ("Gate Valve.jpeg", "Gate Valve", None),
    ("Quarter Turn.jpeg", "Quarter Turn Valve", None),
    ("Stop globe.jpeg", "Stop Globe Valve", None),
]

SUBMITTAL_COVERS = [
    ("PP Silent Material Submittal.jpeg", "PP Silent Pipes", "PP Silent Pipes Material Submittal"),
    ("PPR Material Submittal.jpeg", "PPR Pipes and Fittings", "PPR Material Submittal"),
    ("PVC Material Submittal.jpeg", "PVC Pipes and Fittings", "PVC Material Submittal"),
    ("UPVC Material Submittal.jpeg", "UPVC Pipes and Fittings", "UPVC Material Submittal"),
]


class Command(BaseCommand):
    help = "Import explicitly named source images as product and document covers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            default="D:/Projects/Youssef",
            help="Folder containing the Data sheets/ and Material submittal/ folders.",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"])
        groups = [
            (source_dir / "Data sheets", DATASHEET_COVERS),
            (source_dir / "Material submittal", SUBMITTAL_COVERS),
        ]

        imported = 0
        warnings = 0
        for folder, mappings in groups:
            for filename, product_name, document_title in mappings:
                source = folder / filename
                if not source.is_file():
                    warnings += 1
                    self.stdout.write(self.style.WARNING(f"Missing cover image: {source}"))
                    continue

                product = Product.objects.filter(name=product_name).first()
                if product:
                    self._replace_image(product.featured_image, source, f"{product.slug}{source.suffix.lower()}")
                    imported += 1
                    self.stdout.write(f"  product: {product.name} <- {filename}")
                else:
                    warnings += 1
                    self.stdout.write(self.style.WARNING(f"Product not found for {filename}: {product_name}"))

                if document_title:
                    document = Document.objects.filter(title=document_title).first()
                    if document:
                        self._replace_image(document.cover_image, source, f"{document.slug}{source.suffix.lower()}")
                        imported += 1
                        self.stdout.write(f"  document: {document.title} <- {filename}")
                    else:
                        warnings += 1
                        self.stdout.write(self.style.WARNING(f"Document not found for {filename}: {document_title}"))

        self.stdout.write(
            self.style.SUCCESS(f"Imported {imported} named cover assignment(s); {warnings} warning(s).")
        )

    @staticmethod
    def _replace_image(field, source: Path, destination_name: str):
        if field:
            field.delete(save=False)
        with source.open("rb") as image_file:
            field.save(destination_name, File(image_file), save=True)
