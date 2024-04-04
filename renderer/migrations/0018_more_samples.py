from django.db import migrations

def load_fixture(apps, schema_editor):
    from django.core.management import call_command
    call_command('loaddata', 'samples3.json')

class Migration(migrations.Migration):

    dependencies = [
        ('renderer', '0017_step_retrigger'),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]
