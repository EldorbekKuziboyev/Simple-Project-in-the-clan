# Generated by Django 5.1.6 on 2025-03-13 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0015_telegramuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='film_year_manufacture',
            field=models.DateField(blank=True, db_index=True, null=True, verbose_name='Film created year'),
        ),
        migrations.AlterField(
            model_name='movie',
            name='title',
            field=models.CharField(db_index=True, max_length=255, verbose_name='title'),
        ),
    ]
