from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.documents.models import Document
from apps.products.models import Product


IMAGE_EXTENSIONS = (".jpeg", ".jpg", ".png")
PRODUCT_COVER_FALLBACKS = {
    "tahweel-714-fitting": "tahweel-714-datasheet.png",
}


class Command(BaseCommand):
    help = "Link seeded product/document records to bundled static cover images."

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        product_count = self._link_products(media_root / "products")
        document_count = self._link_documents(media_root / "documents" / "covers")
        self.stdout.write(
            self.style.SUCCESS(
                f"Linked {product_count} product image(s) and "
                f"{document_count} document cover(s)."
            )
        )

    @staticmethod
    def _find_image(folder: Path, slug: str):
        for extension in IMAGE_EXTENSIONS:
            candidate = folder / f"{slug}{extension}"
            if candidate.is_file():
                return candidate
        return None

    def _link_products(self, folder: Path):
        linked = 0
        for product in Product.objects.all():
            image = self._find_image(folder, product.slug)
            if image is not None:
                name = f"products/{image.name}"
            else:
                fallback_name = PRODUCT_COVER_FALLBACKS.get(product.slug)
                fallback = (
                    Path(settings.MEDIA_ROOT) / "documents" / "covers" / fallback_name
                    if fallback_name
                    else None
                )
                if fallback is None or not fallback.is_file():
                    continue
                name = f"documents/covers/{fallback.name}"
            if product.featured_image.name != name:
                product.featured_image.name = name
                product.save(update_fields=["featured_image", "updated_at"])
            linked += 1
        return linked

    def _link_documents(self, folder: Path):
        linked = 0
        for document in Document.objects.all():
            image = self._find_image(folder, document.slug)
            if image is None:
                continue
            name = f"documents/covers/{image.name}"
            if document.cover_image.name != name:
                document.cover_image.name = name
                document.save(update_fields=["cover_image", "updated_at"])
            linked += 1
        return linked
