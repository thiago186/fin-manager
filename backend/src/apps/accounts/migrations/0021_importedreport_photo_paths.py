from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0020_populate_transaction_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="importedreport",
            name="photo_paths",
            field=models.JSONField(
                blank=True,
                help_text="List of stored image file paths for photo imports",
                null=True,
            ),
        ),
    ]
