import apps.documents.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0003_documentsection_document_section"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentrevision",
            name="file",
            field=models.FileField(blank=True, upload_to=apps.documents.models.document_upload_path),
        ),
        migrations.AddField(
            model_name="documentrevision",
            name="external_url",
            field=models.URLField(
                blank=True,
                help_text="Public URL for documents hosted outside Django storage, such as GitHub release assets.",
                max_length=1000,
            ),
        ),
    ]
