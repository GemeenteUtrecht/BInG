# Generated by Django 2.2.1 on 2019-05-14 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("projects", "0004_projectattachment")]

    operations = [
        migrations.AddField(
            model_name="project",
            name="zaak",
            field=models.URLField(
                blank=True, editable=False, max_length=1000, verbose_name="zaak"
            ),
        )
    ]
