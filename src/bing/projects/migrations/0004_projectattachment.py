# Generated by Django 2.2 on 2019-04-29 07:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("projects", "0003_project_toetswijze")]

    operations = [
        migrations.CreateModel(
            name="ProjectAttachment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("io_type", models.URLField(blank=True, verbose_name="document type")),
                (
                    "eio_url",
                    models.URLField(
                        blank=True, verbose_name="enkelvoudig informatieobject URL"
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="projects.Project",
                    ),
                ),
            ],
            options={
                "verbose_name": "project attachment",
                "verbose_name_plural": "project attachments",
            },
        )
    ]
