from urllib.parse import quote

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.documents.models import Document, DocumentRevision, RevisionStatus


RELEASE_BASE_URL = (
    "https://github.com/Muhamad-Sa/tahweel-backend/releases/download/documents-v1"
)

# title, release asset filename, original filename, size in bytes, SHA-256
RELEASE_DOCUMENTS = [
    ("Tahweel Product Catalogue 2024", "Tahweel.-.Product.Catalogue.English.24.12.MC.1.pdf", "Tahweel - Product Catalogue English 24.12 MC (1).pdf", 65340239, "43d8674e7cec018d3b05fc91ecc63d7271cbf18a32a92942c45de33425d396c3"),
    ("PPR Pipes and Fittings Catalogue", "Tahweel.PPR.Pipes.and.Fittings.Catalogue.pdf", "Tahweel PPR Pipes and Fittings Catalogue.pdf", 31595168, "aa5a403cef4a33d6e755543e13808fad39b4f00fe4ba7f86014be69bc8da03d0"),
    ("Silent Pipe Systems Brochure", "Tahweel_Silent.Brochure-10-2025.MC.pdf", "Tahweel_Silent Brochure-10-2025 MC.pdf", 30219142, "da861f2b504f3cad4ad13848dc351008638ea16db282078dc9772ac6487b14d5"),
    ("UPVC Catalogue", "UPVC.Catalogue.3.3.26.pdf", "UPVC Catalogue 3.3.26.pdf", 10285207, "344f53136c409431b36a27a5e0c0bddee716a470cb8b180260598026303d26b1"),
    ("Floor Drain with Rubber 50/75mm Datasheet", "ABS.Floor.Drain.with.Rubber.5075.mm.pdf", "ABS Floor Drain with Rubber 5075 mm.pdf", 295180, "58227370dbfc66bffb039ad421bb05935ddcc41c57efe229804fc3d5acb70c78"),
    ("Angle Valve Datasheet", "Angle.Valve_Tahweel_Datasheet.pdf", "Angle Valve_Tahweel_Datasheet.pdf", 266270, "398d3aa23ac2398c06744618acb775cb43688ef5bcf0f97a17f0da6568f4dba4"),
    ("Back Water Valve Datasheet", "Back.water.valve.data.sheet.pdf", "Back water valve data sheet .pdf", 489192, "62d3c364bc97c96a4056e75f4128a0b4d8371001e4c4953f8e3ab59316630406"),
    ("Concealed Shower Mixer Datasheet", "Concealed.Shower.Mixer.Data.Sheet.pdf", "Concealed Shower Mixer Data Sheet.pdf", 2870842, "3b8e45157329344a7e1bb8d78f5f55ef846504da4754bd82adde57101f3bd22b"),
    ("Dual Flush Mechanical Concealed Cistern Datasheet", "Dual.Flush.Mechanical.Concealed.Cistern55.pdf", "Dual Flush Mechanical Concealed Cistern55.pdf", 293900, "a89aa819719efc8209383c153de2c07a0eecf690653bde0c67fee241e3825c41"),
    ("Flush Tank Datasheet", "Flush.tank.kessel.pdf", "Flush tank kessel .pdf", 1768697, "5c0caaa432f6010fb0203b4fa4aa7953e32efda06d956abebc462b0f504e8393"),
    ("Gully Trap Datasheet", "Gullytrap.Data.sheet.pdf", "Gullytrap Data sheet.pdf", 823900, "a47a4faffe24e949d98ff546d8812331e80937c0752926fb669df9cafe32b96a"),
    ("Inspection Chamber (Manhole) Datasheet", "Inspection.Chamber.Manhole.Tahweel.pdf", "Inspection Chamber ( Manhole ) Tahweel.pdf", 890661, "71e3d6fa15a9ba74e3b39351bc0d02bc767768c1bee0e8b9380558b8c8388d15"),
    ("Tahweel 714 Datasheet", "Tahweel.714.Data.Sheet.pdf", "Tahweel 714 Data Sheet.pdf", 698026, "df8de1c455cea70e7e94f0bda1589e09fe64e4828b72dd4096328c5a369f136d"),
    ("Flexible Connection Datasheet", "Tahweel.Flexible.Connection.Data.Sheet.pdf", "Tahweel Flexible Connection Data Sheet..pdf", 634639, "025e101cffd10f12eb4a047309e9c7f03672f5ba5df37bbfce392b0fd9bde101"),
    ("Shower Drain Datasheet", "Tahweel.Shower.drains.data.sheet.pdf", "Tahweel Shower drains data sheet.pdf", 1826674, "3d2e1f989f1cc27f51884685c15d114dd48548f9abcccb2404588b74a8236462"),
    ("Stainless Steel Cover Datasheet", "Tahweel.Stainless-steel.cover.pdf", "Tahweel Stainless-steel cover.pdf", 271345, "82bfbcd1561df90b2c237a9ee202f72a2de3a0778d569a0114841c6c1113f312"),
    ("Trench Drain Datasheet", "Tahweel.Trench.Drain.Data.sheet.pdf", "Tahweel Trench Drain Data sheet.pdf", 11218434, "6898506e81d1d331f3d1737c1bdfda79c3b746bdf9f506642d87aa6e2bf229dd"),
    ("PP Silent Pipes Material Submittal", "Tahweel.Integrated.Company.PP.Silent.Pipes.Material.Submittal-.B.Hotel.18-08-2026.pdf", "Tahweel Integrated Company PP Silent Pipes Material Submittal- B Hotel 18-08-2026.pdf", 66112354, "f57b51900ddd257e80deb56e74855c98d3d0c0dde264850540aa2a725a17b0dc"),
    ("PPR Material Submittal", "Tahweel.PPR.Material.Submittal.pdf", "Tahweel PPR Material Submittal.pdf", 49618987, "33070f437d3e37a9f7c70b0699a85aff81e4fac422a8c28edc391cc2021b0da4"),
    ("PVC Material Submittal", "Tahweel.PVC.Material.Submittal.pdf", "Tahweel PVC Material Submittal.pdf", 59372292, "59c13b5aa5e9377b1fff29a36eced5b8b65eea1d0b4ae7fe489752027e4d209f"),
    ("UPVC Material Submittal", "Tahweel.UPVC.Material.Sumbittal.1.pdf", "Tahweel UPVC Material Sumbittal (1).pdf", 60244387, "f406d20babe2a5cf09cbf4abeea92d5c93ff0bb3a0de65644933a87212fb6062"),
]


class Command(BaseCommand):
    help = "Link seeded document revisions to the public GitHub release PDFs."

    @transaction.atomic
    def handle(self, *args, **options):
        linked = 0
        missing = []

        for title, asset_name, original_filename, size, checksum in RELEASE_DOCUMENTS:
            document = Document.objects.filter(slug=slugify(title)).first()
            if document is None:
                missing.append(title)
                continue

            external_url = f"{RELEASE_BASE_URL}/{quote(asset_name)}"
            revision = document.current_revision

            if revision is None:
                revision = DocumentRevision.objects.create(
                    document=document,
                    revision="Published",
                    external_url=external_url,
                    original_filename=original_filename,
                    file_size=size,
                    mime_type="application/pdf",
                    checksum=checksum,
                    status=RevisionStatus.CURRENT,
                )
            else:
                revision.external_url = external_url
                revision.original_filename = original_filename
                revision.file_size = size
                revision.mime_type = "application/pdf"
                revision.checksum = checksum
                revision.status = RevisionStatus.CURRENT
                revision.save()

            linked += 1

        if missing:
            self.stdout.write(self.style.WARNING(f"Missing document records: {', '.join(missing)}"))

        self.stdout.write(self.style.SUCCESS(f"Linked {linked} GitHub release document(s)."))
