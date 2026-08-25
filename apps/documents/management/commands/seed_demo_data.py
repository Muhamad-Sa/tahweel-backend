"""
Seed realistic demo content for the Tahweel catalogue.

Creates categories, standards, and products matching Tahweel's real product
lines, then attaches the ACTUAL supplied PDFs (catalogues, datasheets,
material submittals) as Document + DocumentRevision records -- the files are
copied from the source folders into MEDIA_ROOT via Django's File wrapper, so
file_size / mime_type / checksum reflect the real files, not fabricated data.

Where real Tahweel marketing copy was not supplied, descriptions/specs are
clearly-marked illustrative placeholder text. Standards referenced (e.g. DIN
8077/8078 for PPR pipe) are cited only as generic real-world industry
standards for the material class -- NOT asserted as verified Tahweel
certifications.

Usage:
    python manage.py seed_demo_data [--source-dir PATH] [--reset-files]
"""
import hashlib
import mimetypes
from datetime import date
from pathlib import Path

from django.core.files import File
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.documents.models import Document, DocumentRevision, DocumentType, Language, RevisionStatus
from apps.products.models import Category, Product, ProductSpecification, Standard

DEFAULT_SOURCE_DIR = Path("D:/Projects/Youssef")

ILLUSTRATIVE_NOTE = (
    " (Placeholder copy: real Tahweel marketing text was not supplied for this pass; "
    "content here is illustrative only and should be replaced with verified copy.)"
)


class Command(BaseCommand):
    help = "Seed demo categories/products/documents, attaching the real supplied Tahweel PDFs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir", default=str(DEFAULT_SOURCE_DIR),
            help="Folder containing Catalogues/, Data sheets/, Material submittal/ subfolders.",
        )
        parser.add_argument(
            "--reset-files", action="store_true",
            help="Re-copy PDFs and create new revisions even if a document already has one.",
        )

    def handle(self, *args, **options):
        self.source_dir = Path(options["source_dir"])
        self.reset_files = options["reset_files"]

        catalogues_dir = self.source_dir / "Catalogues"
        datasheets_dir = self.source_dir / "Data sheets"
        submittals_dir = self.source_dir / "Material submittal"

        for d in (catalogues_dir, datasheets_dir, submittals_dir):
            if not d.exists():
                self.stdout.write(self.style.WARNING(f"Source folder not found: {d} (skipping its files)"))

        with transaction.atomic():
            categories = self._seed_categories()
            standards = self._seed_standards()
            products = self._seed_products(categories, standards)

        self._seed_catalogues(catalogues_dir, categories)
        self._seed_datasheets(datasheets_dir, products, categories)
        self._seed_submittals(submittals_dir, categories, products)

        call_command("add_water_supply_valves")
        call_command("recategorize_products")
        call_command("setup_datasheet_sections")
        call_command("generate_pdf_covers")
        call_command("import_named_covers", source_dir=str(self.source_dir))

        self.stdout.write(self.style.SUCCESS("Seed complete."))

    # ------------------------------------------------------------------
    def _seed_categories(self):
        defs = [
            ("PPR Systems", "pipe", "Polypropylene Random Copolymer (PP-R) pressure pipe systems for hot & cold water supply."),
            ("PVC Systems", "pipe", "PVC pressure and drainage pipe systems."),
            ("UPVC Systems", "pipe", "Unplasticized PVC pipe systems for drainage and water supply."),
            ("Drainage Systems", "waves", "Floor drains, gully traps, inspection chambers, and below-ground drainage accessories."),
            ("Sanitary Fixtures & Valves", "droplets", "Valves, cisterns, mixers, and sanitary fittings for bathrooms and utility areas."),
            ("Silent Pipe Systems", "volume-x", "Acoustic-dampened PP soil & waste pipe systems for noise-sensitive buildings."),
        ]
        cats = {}
        for order, (name, icon, desc) in enumerate(defs):
            cat, _ = Category.objects.update_or_create(
                slug=self._slug(name),
                defaults=dict(name=name, icon=icon, description=desc + ILLUSTRATIVE_NOTE, display_order=order, active=True),
            )
            cats[name] = cat
        self.stdout.write(self.style.SUCCESS(f"Categories: {len(cats)}"))
        return cats

    def _seed_standards(self):
        defs = [
            ("DIN 8077", "PP-R Pipes - Dimensions", "General dimensional standard commonly referenced for PP-R pressure pipe (illustrative reference, not an asserted Tahweel certification)."),
            ("DIN 8078", "PP-R Pipes - General quality requirements", "General quality-requirements standard commonly referenced for PP-R pressure pipe (illustrative reference, not an asserted Tahweel certification)."),
            ("ISO 15874", "Plastics piping systems for hot and cold water - PP-R", "International standard for PP-R piping systems (illustrative reference)."),
            ("ASTM D1785", "PVC Pipe, Schedules 40, 80, and 120", "Common PVC pressure-pipe specification (illustrative reference)."),
            ("EN 1451", "Plastics piping systems for soil and waste discharge (low and high temperature) within the building structure - PP", "Common standard referenced for PP soil & waste (silent) pipe systems (illustrative reference)."),
        ]
        standards = {}
        for code, name, desc in defs:
            std, _ = Standard.objects.update_or_create(code=code, defaults=dict(name=name, description=desc))
            standards[code] = std
        self.stdout.write(self.style.SUCCESS(f"Standards: {len(standards)}"))
        return standards

    def _seed_products(self, cats, standards):
        # (name, category, code, material, application, specs[(group,name,value,unit)], standard codes)
        defs = [
            ("PPR Pipes and Fittings", "PPR Systems", "TAH-PPR", "PP-R (PN20)",
             "Hot & cold water supply lines",
             [("Dimensions", "Diameter range", "20-160", "mm"), ("Pressure", "Pressure rating", "PN20", ""), ("Temperature", "Max operating temp", "70", "\u00b0C")],
             ["DIN 8077", "DIN 8078", "ISO 15874"]),
            ("PVC Pipes and Fittings", "PVC Systems", "TAH-PVC", "PVC",
             "Cold water supply & general purpose piping",
             [("Dimensions", "Diameter range", "20-315", "mm"), ("Pressure", "Pressure rating", "PN10-PN16", "")],
             ["ASTM D1785"]),
            ("UPVC Pipes and Fittings", "UPVC Systems", "TAH-UPVC", "uPVC",
             "Drainage, waste & vent (DWV) and pressure water supply",
             [("Dimensions", "Diameter range", "32-400", "mm")],
             []),
            ("PP Silent Pipes", "Silent Pipe Systems", "TAH-SIL", "PP (mineral-reinforced)",
             "Acoustic soil & waste discharge in noise-sensitive buildings (hotels, hospitals, residential towers)",
             [("Acoustics", "Sound reduction", "< 14", "dB(A)"), ("Dimensions", "Diameter range", "32-200", "mm")],
             ["EN 1451"]),
            ("Floor Drain with Rubber 50/75mm", "Drainage Systems", "TAH-FD-5075", "ABS / Stainless Steel",
             "Floor-level water drainage in bathrooms and wet areas",
             [("Dimensions", "Outlet size", "50/75", "mm")],
             []),
            ("Angle Valve", "Sanitary Fixtures & Valves", "TAH-AV", "Brass / Chrome-plated",
             "Isolation valve for water supply to fixtures",
             [], []),
            ("Back Water Valve", "Drainage Systems", "TAH-BWV", "PVC/ABS",
             "Prevents backflow of wastewater into the building drainage system",
             [], []),
            ("Concealed Shower Mixer", "Sanitary Fixtures & Valves", "TAH-CSM", "Brass",
             "In-wall concealed hot/cold water mixing for showers",
             [], []),
            ("Dual Flush Mechanical Concealed Cistern", "Sanitary Fixtures & Valves", "TAH-DFC", "Polypropylene",
             "In-wall concealed cistern with dual-flush mechanism for water-efficient WC flushing",
             [], []),
            ("Flush Tank", "Sanitary Fixtures & Valves", "TAH-FT", "Polypropylene",
             "Exposed flush tank assembly",
             [], []),
            ("Gully Trap", "Drainage Systems", "TAH-GT", "PVC",
             "External below-ground wastewater collection point with trap seal",
             [], []),
            ("Inspection Chamber (Manhole)", "Drainage Systems", "TAH-IC", "PVC/PP",
             "Access point for inspection and maintenance of underground drainage runs",
             [], []),
            ("Tahweel 714 Fitting", "Sanitary Fixtures & Valves", "TAH-714", "PP-R",
             "Specialty fitting - see attached datasheet for exact application",
             [], []),
            ("Flexible Connection", "Drainage Systems", "TAH-FC", "Rubber/PVC",
             "Flexible coupling for connecting dissimilar pipe diameters/materials",
             [], []),
            ("Shower Drain", "Drainage Systems", "TAH-SD", "Stainless Steel 304",
             "Linear or point shower-floor water drainage",
             [], []),
            ("Stainless Steel Cover", "Drainage Systems", "TAH-SSC", "Stainless Steel 304",
             "Decorative/functional cover plate for floor drains",
             [], []),
            ("Trench Drain", "Drainage Systems", "TAH-TD", "Stainless Steel / PP",
             "Linear channel drainage for large-area surface water collection",
             [], []),
        ]
        products = {}
        for name, cat_name, code, material, application, specs, std_codes in defs:
            product, _ = Product.objects.update_or_create(
                slug=self._slug(name),
                defaults=dict(
                    category=cats[cat_name],
                    name=name,
                    product_code=code,
                    material=material,
                    application=application,
                    short_description=(f"{material} {name.lower()} for {application.lower()}." + ILLUSTRATIVE_NOTE)[:300],
                    long_description=(
                        f"The Tahweel {name} is engineered for reliable performance in {application.lower()}. "
                        "Manufactured in Saudi Arabia using German-derived extrusion/molding technology."
                    ) + ILLUSTRATIVE_NOTE,
                    country_of_origin="Saudi Arabia",
                    warranty_info="Contact Tahweel for warranty terms." + ILLUSTRATIVE_NOTE,
                    active=True,
                    featured=code in ("TAH-PPR", "TAH-SIL", "TAH-UPVC"),
                ),
            )
            for group, spec_name, value, unit in specs:
                ProductSpecification.objects.update_or_create(
                    product=product, name=spec_name, group=group, defaults=dict(value=value, unit=unit)
                )
            if std_codes:
                product.standards.set([standards[c] for c in std_codes if c in standards])
            products[name] = product
        self.stdout.write(self.style.SUCCESS(f"Products: {len(products)}"))
        return products

    # ------------------------------------------------------------------
    def _attach_revision(self, document, src_path: Path, issue_date=None, revision_label="Rev 01"):
        if not src_path.exists():
            self.stdout.write(self.style.WARNING(f"  Missing source file, skipping: {src_path}"))
            return

        if document.current_revision_id and not self.reset_files:
            return  # already seeded

        checksum = hashlib.sha256()
        with open(src_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                checksum.update(chunk)

        mime_type, _ = mimetypes.guess_type(src_path.name)

        with open(src_path, "rb") as fh:
            revision = DocumentRevision(
                document=document,
                revision=revision_label,
                status=RevisionStatus.CURRENT,
                issue_date=issue_date or date.today(),
                mime_type=mime_type or "application/pdf",
                checksum=checksum.hexdigest(),
            )
            revision.file.save(src_path.name, File(fh), save=False)
            revision.save()

        self.stdout.write(f"  + {document.title}: attached {src_path.name} ({revision.file_size} bytes)")

    def _make_document(self, title, document_type, category=None, product=None, language=Language.ENGLISH, description=""):
        doc, _ = Document.objects.update_or_create(
            slug=self._slug(title),
            defaults=dict(
                title=title,
                document_type=document_type,
                category=category,
                product=product,
                language=language,
                description=(description or f"{title}." ) + ILLUSTRATIVE_NOTE,
                active=True,
                public=True,
                featured=document_type == DocumentType.CATALOGUE,
            ),
        )
        return doc

    def _seed_catalogues(self, catalogues_dir: Path, cats):
        items = [
            ("Tahweel Product Catalogue 2024", "Tahweel - Product Catalogue English 24.12 MC (1).pdf", None),
            ("PPR Pipes and Fittings Catalogue", "Tahweel PPR Pipes and Fittings Catalogue.pdf", cats["PPR Systems"]),
            ("Silent Pipe Systems Brochure", "Tahweel_Silent Brochure-10-2025 MC.pdf", cats["Silent Pipe Systems"]),
            ("UPVC Catalogue", "UPVC Catalogue 3.3.26.pdf", cats["UPVC Systems"]),
        ]
        for title, filename, category in items:
            doc = self._make_document(title, DocumentType.CATALOGUE, category=category,
                                       description=f"Full product catalogue: {title}.")
            self._attach_revision(doc, catalogues_dir / filename, revision_label="Edition 2024")

    def _seed_datasheets(self, datasheets_dir: Path, products, cats):
        items = [
            ("Floor Drain with Rubber 50/75mm Datasheet", "ABS Floor Drain with Rubber 5075 mm.pdf", "Floor Drain with Rubber 50/75mm"),
            ("Angle Valve Datasheet", "Angle Valve_Tahweel_Datasheet.pdf", "Angle Valve"),
            ("Back Water Valve Datasheet", "Back water valve data sheet .pdf", "Back Water Valve"),
            ("Concealed Shower Mixer Datasheet", "Concealed Shower Mixer Data Sheet.pdf", "Concealed Shower Mixer"),
            ("Dual Flush Mechanical Concealed Cistern Datasheet", "Dual Flush Mechanical Concealed Cistern55.pdf", "Dual Flush Mechanical Concealed Cistern"),
            ("Flush Tank Datasheet", "Flush tank kessel .pdf", "Flush Tank"),
            ("Gully Trap Datasheet", "Gullytrap Data sheet.pdf", "Gully Trap"),
            ("Inspection Chamber (Manhole) Datasheet", "Inspection Chamber ( Manhole ) Tahweel.pdf", "Inspection Chamber (Manhole)"),
            ("Tahweel 714 Datasheet", "Tahweel 714 Data Sheet.pdf", "Tahweel 714 Fitting"),
            ("Flexible Connection Datasheet", "Tahweel Flexible Connection Data Sheet..pdf", "Flexible Connection"),
            ("Shower Drain Datasheet", "Tahweel Shower drains data sheet.pdf", "Shower Drain"),
            ("Stainless Steel Cover Datasheet", "Tahweel Stainless-steel cover.pdf", "Stainless Steel Cover"),
            ("Trench Drain Datasheet", "Tahweel Trench Drain Data sheet.pdf", "Trench Drain"),
        ]
        for title, filename, product_name in items:
            product = products.get(product_name)
            doc = self._make_document(
                title, DocumentType.DATASHEET,
                category=product.category if product else None,
                product=product,
                description=f"Technical datasheet for the {product_name}.",
            )
            self._attach_revision(doc, datasheets_dir / filename)

    def _seed_submittals(self, submittals_dir: Path, cats, products):
        items = [
            ("PP Silent Pipes Material Submittal", "Tahweel Integrated Company PP Silent Pipes Material Submittal- B Hotel 18-08-2026.pdf", cats["Silent Pipe Systems"], products.get("PP Silent Pipes")),
            ("PPR Material Submittal", "Tahweel PPR Material Submittal.pdf", cats["PPR Systems"], products.get("PPR Pipes and Fittings")),
            ("PVC Material Submittal", "Tahweel PVC Material Submittal.pdf", cats["PVC Systems"], products.get("PVC Pipes and Fittings")),
            ("UPVC Material Submittal", "Tahweel UPVC Material Sumbittal (1).pdf", cats["UPVC Systems"], products.get("UPVC Pipes and Fittings")),
        ]
        for title, filename, category, product in items:
            doc = self._make_document(
                title, DocumentType.MATERIAL_SUBMITTAL, category=category, product=product,
                description=f"Material submittal package: {title}.",
            )
            self._attach_revision(doc, submittals_dir / filename)

    @staticmethod
    def _slug(value: str) -> str:
        from django.utils.text import slugify

        return slugify(value)
