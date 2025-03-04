# Generated by Django 5.1.4 on 2025-01-18 19:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectapp', '0008_candidature_adresse_candidature_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employe',
            name='nb_massrouf',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='entretien',
            name='candidature',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectapp.candidature'),
        ),
    ]
