# Generated by Django 5.1.4 on 2025-01-14 12:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectapp', '0005_employe_sexe'),
    ]

    operations = [
        migrations.CreateModel(
            name='Candidature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_candidat', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('cv', models.FileField(upload_to='cvs/')),
                ('status', models.CharField(choices=[('reçue', 'Reçue'), ('en traitement', 'En traitement'), ('rejetée', 'Rejetée'), ('acceptée', 'Acceptée')], max_length=50)),
                ('date_candidature', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='OffreEmploi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('date_publication', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='absence',
            name='est_absent',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='Entretien',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('candidat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectapp.candidature')),
            ],
        ),
        migrations.CreateModel(
            name='Massrouf',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_demande', models.DateField()),
                ('montant', models.DecimalField(decimal_places=2, max_digits=10)),
                ('justification', models.TextField()),
                ('approuve', models.BooleanField(default=False)),
                ('employe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projectapp.employe')),
            ],
        ),
        migrations.CreateModel(
            name='Salaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('salaire_base', models.DecimalField(decimal_places=2, max_digits=10)),
                ('salaire_quot', models.DecimalField(decimal_places=2, max_digits=10)),
                ('primes', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('date_paiement', models.DateField()),
                ('salaire_total', models.DecimalField(decimal_places=2, editable=False, max_digits=10)),
                ('employe', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='projectapp.employe')),
            ],
        ),
    ]
