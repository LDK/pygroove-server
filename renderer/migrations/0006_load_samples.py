from django.db import migrations

def load_fixture(apps, schema_editor):
    from django.core.management import call_command
    call_command('loaddata', 'samples.json')

class Migration(migrations.Migration):

    dependencies = [
        ('renderer', '0005_song_author'),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]
