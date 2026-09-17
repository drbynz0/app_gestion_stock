from django.db import migrations, models
import django.db.models.deletion

def assign_company(apps, schema_editor):
    Company = apps.get_model('users', 'Company')
    Activity = apps.get_model('activities', 'Activity')
    company, _ = Company.objects.get_or_create(slug='legacy', defaults={'name': 'Entreprise existante'})
    Activity.objects.filter(company__isnull=True).update(company=company)

class Migration(migrations.Migration):
    dependencies = [('activities', '0001_initial'), ('users', '0002_company_user_company')]
    operations = [
        migrations.AddField(model_name='activity', name='company', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activities', to='users.company')),
        migrations.RunPython(assign_company, migrations.RunPython.noop),
        migrations.AlterField(model_name='activity', name='company', field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='activities', to='users.company')),
    ]
