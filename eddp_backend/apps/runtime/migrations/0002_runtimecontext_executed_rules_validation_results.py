from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runtime", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="runtimecontext",
            old_name="resolved_rules",
            new_name="executed_rules",
        ),
        migrations.AddField(
            model_name="runtimecontext",
            name="validation_results",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
