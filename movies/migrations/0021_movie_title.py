# Generated by Django 5.1.6 on 2025-03-27 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0020_remove_movie_movie_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='title',
            field=models.CharField(blank=True, null=True),
        ),
    ]
