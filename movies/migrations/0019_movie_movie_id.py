# Generated by Django 5.1.6 on 2025-03-25 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0018_remove_movie_title_translations_movie_title_en_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='movie_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
