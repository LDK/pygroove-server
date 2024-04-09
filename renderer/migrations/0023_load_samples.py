from django.db import migrations

def load_fixture(apps, schema_editor):
    from django.core.management import call_command
    call_command('loaddata', 'samples.json')
    call_command('loaddata', 'samples2.json')
    call_command('loaddata', 'samples3.json')

class Migration(migrations.Migration):

    dependencies = [
        ('renderer', '0022_remove_filter_q_filter_order'),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]
