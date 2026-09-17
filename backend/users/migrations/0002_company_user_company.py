# Generated manually to safely migrate the existing single-company installation.
from django.db import migrations, models
import django.db.models.deletion


def create_legacy_company_and_assign_users(apps, schema_editor):
    Company = apps.get_model('users', 'Company')
    User = apps.get_model('users', 'User')
    company, _ = Company.objects.get_or_create(slug='legacy', defaults={'name': 'Entreprise existante'})
    User.objects.filter(company__isnull=True).update(company=company)


class Migration(migrations.Migration):
    dependencies = [('users', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160)),
                ('slug', models.SlugField(unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='users', to='users.company'),
        ),
        migrations.RunPython(create_legacy_company_and_assign_users, migrations.RunPython.noop),
    ]
