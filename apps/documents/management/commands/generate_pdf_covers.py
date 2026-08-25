import io

import pymupdf as fitz
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.documents.models import Document

COVER_MAX_DIM = 1000  # px, longest side


class Command(BaseCommand):
    help = "Render page 1 of each document's current-revision PDF into Document.cover_image."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Regenerate covers even for documents that already have one.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        qs = Document.objects.select_related("current_revision").exclude(current_revision__isnull=True)
        if not overwrite:
            qs = qs.filter(cover_image="")

        total = qs.count()
        if not total:
            self.stdout.write(self.style.WARNING("No documents need a cover image."))
            return

        made, failed = 0, 0
        for doc in qs:
            revision = doc.current_revision
            try:
                revision.file.open("rb")
                pdf_bytes = revision.file.read()
                revision.file.close()

                pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
                page = pdf.load_page(0)
                zoom = COVER_MAX_DIM / max(page.rect.width, page.rect.height)
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                png_bytes = pix.tobytes("png")
                pdf.close()

                doc.cover_image.save(
                    f"{doc.slug}.png", ContentFile(png_bytes), save=True
                )
                made += 1
                self.stdout.write(f"  covered: {doc.title}")
            except Exception as exc:  # noqa: BLE001 - report and continue seeding the rest
                failed += 1
                self.stdout.write(self.style.ERROR(f"  failed: {doc.title} ({exc})"))

        self.stdout.write(self.style.SUCCESS(f"Generated {made} cover image(s), {failed} failed, out of {total}."))
