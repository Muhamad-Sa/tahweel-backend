from django.core.management.base import BaseCommand

from apps.documents.models import Document, DocumentSection, DocumentType

# (section name, display_order, [substrings matched case-insensitively against Document.title])
SECTIONS = [
    ("Water Supply", 10, [
        "ball valve", "gate valve", "stop globe valve", "quarter turn valve",
        "concealed valve", "flange",
    ]),
    ("Indoor Drainage", 20, [
        "abs floor drain", "floor drain", "stainless steel cover", "stainless-steel cover",
    ]),
    ("Outdoor Drainage Solutions", 30, [
        "trench drain", "gully trap", "inspection chamber", "back water valve",
    ]),
    ("Tahweel Glue & Adhesives", 40, [
        "714", "717",
    ]),
    ("Sanitary Ware & Accessories", 50, [
        "angle valve", "flexible connect", "concealed shower mixer", "shower mixer",
        "dual flush", "concealed dual flush", "flush tank", "shower drain",
    ]),
]


class Command(BaseCommand):
    help = (
        "Create the curated Technical Library sections for datasheets and assign "
        "existing Datasheet documents to them by title match."
    )

    def handle(self, *args, **options):
        datasheets = list(Document.objects.filter(document_type=DocumentType.DATASHEET))
        assigned_ids = set()

        for name, order, keywords in SECTIONS:
            section, _ = DocumentSection.objects.update_or_create(
                name=name, defaults={"display_order": order}
            )
            matched = 0
            for doc in datasheets:
                title_lower = doc.title.lower()
                if doc.id in assigned_ids:
                    continue
                if any(kw in title_lower for kw in keywords):
                    doc.section = section
                    doc.save(update_fields=["section"])
                    assigned_ids.add(doc.id)
                    matched += 1
            self.stdout.write(f"{name}: {matched} document(s) assigned")

        unmatched = [d.title for d in datasheets if d.id not in assigned_ids]
        if unmatched:
            self.stdout.write(self.style.WARNING(f"Unmatched datasheets (no section): {unmatched}"))

        missing = [
            "Ball Valve", "Gate Valve", "Stop Globe Valve", "Quarter Turn Valve",
            "Concealed Valve", "Flange", "717 (Glue & Adhesives)",
        ]
        self.stdout.write(
            self.style.WARNING(
                "No standalone datasheet PDF was supplied yet for: " + ", ".join(missing) +
                ". Product records may exist, but technical-library entries require real PDFs."
            )
        )
        self.stdout.write(self.style.SUCCESS("Done."))
