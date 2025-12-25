# Generated manually for AI transaction classification feature

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_cashflowview_cashflowresult_cashflowgroup_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="need_review",
            field=models.BooleanField(
                default=False,
                help_text="Whether this transaction needs review after AI classification",
            ),
        ),
    ]