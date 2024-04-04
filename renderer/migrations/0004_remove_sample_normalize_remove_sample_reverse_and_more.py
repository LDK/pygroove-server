# Generated by Django 5.0 on 2023-12-19 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('renderer', '0003_song_patternsequence_track_position_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sample',
            name='normalize',
        ),
        migrations.RemoveField(
            model_name='sample',
            name='reverse',
        ),
        migrations.RemoveField(
            model_name='sample',
            name='trim',
        ),
        migrations.AddField(
            model_name='sample',
            name='display',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
