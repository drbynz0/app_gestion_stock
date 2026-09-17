from django.db import migrations, models


def promote_existing_superusers(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(is_superuser=True).update(user_type='PLATFORM_ADMIN')


class Migration(migrations.Migration):
    dependencies = [('users', '0003_company_currency')]

    operations = [
        migrations.AlterField(
            model_name='user', name='user_type',
            field=models.CharField(choices=[('SELLER', 'Vendeur'), ('ADMIN', 'Administrateur entreprise'), ('PLATFORM_ADMIN', 'Administrateur plateforme')], default='ADMIN', max_length=20),
        ),
        migrations.RunPython(promote_existing_superusers, migrations.RunPython.noop),
    ]
