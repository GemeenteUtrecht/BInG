# Generated by Django 2.2.4 on 2019-08-13 12:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Webhook",
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
                (
                    "key",
                    models.CharField(
                        choices=[("aanvraag-zaken", "aanvraag-zaken")],
                        max_length=50,
                        unique=True,
                        verbose_name="subscription key",
                    ),
                ),
                (
                    "_subscription",
                    models.URLField(
                        blank=True, editable=False, verbose_name="subscription URL"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        limit_choices_to={"auth_token__isnull": False},
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="webhook",
            constraint=models.UniqueConstraint(
                condition=models.Q(_negated=True, _subscription=""),
                fields=("_subscription",),
                name="unique_subscription",
            ),
        ),
    ]