# Generated by Django 2.2.9 on 2020-03-03 10:30

import datetime
import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BInGConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organisatie_rsin', models.CharField(default='002220647', max_length=9, verbose_name='RSIN organisatie')),
                ('zaaktype_aanvraag', models.URLField(verbose_name='Zaaktype aanvraag')),
                ('zaaktype_vergadering', models.URLField(verbose_name='Zaaktype vergadering')),
                ('minimal_plan_duration', models.DurationField(default=datetime.timedelta(7), help_text='De minimale tijd die nodig is tussen het moment van indienen aanvraag en de eerst mogelijke vergadering.', verbose_name='minimal duration from aanvraag to vergadering')),
                ('aanvraag_process_key', models.CharField(blank=True, help_text='Na het indienen van een BInG-aanvraag wordt een instantie van een procesdefinitie met deze key opgestart.', max_length=100, verbose_name='aanvraag process key')),
            ],
            options={
                'verbose_name': 'BInG configuratie',
            },
        ),
        migrations.CreateModel(
            name='RequiredDocuments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('toetswijze', models.CharField(choices=[('versneld', 'versneld'), ('regulier', 'regulier'), ('onbekend', 'weet ik niet')], max_length=20, unique=True, verbose_name='toetswijze')),
                ('informatieobjecttypen', django.contrib.postgres.fields.ArrayField(base_field=models.URLField(max_length=1000, verbose_name='informatieobjecttype'), help_text='Documenttypen', size=None)),
            ],
            options={
                'verbose_name': 'verplichte documenten',
                'verbose_name_plural': 'verplichte documenten',
            },
        ),
    ]
