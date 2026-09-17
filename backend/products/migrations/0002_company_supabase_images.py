from django.db import migrations, models
import django.db.models.deletion


def assign_legacy_company(apps, schema_editor):
    Company = apps.get_model('users', 'Company')
    Category = apps.get_model('products', 'Category')
    Product = apps.get_model('products', 'Product')
    company = Company.objects.get(slug='legacy')
    Category.objects.filter(company__isnull=True).update(company=company)
    Product.objects.filter(company__isnull=True).update(company=company)


class Migration(migrations.Migration):
    dependencies = [('products', '0001_initial'), ('users', '0002_company_user_company')]

    operations = [
        migrations.AddField(
            model_name='category',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='categories', to='users.company'),
        ),
        migrations.AddField(
            model_name='product',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='users.company'),
        ),
        migrations.AddField(
            model_name='productimage',
            name='storage_path',
            field=models.CharField(blank=True, max_length=600, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='productimage',
            name='url',
            field=models.URLField(blank=True, max_length=1000, null=True),
        ),
        migrations.RunPython(assign_legacy_company, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='category',
            name='company',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='categories', to='users.company'),
        ),
        migrations.AlterField(
            model_name='product',
            name='company',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='users.company'),
        ),
        migrations.AlterField(
            model_name='product',
            name='code',
            field=models.CharField(max_length=50),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(fields=('company', 'code'), name='unique_product_code_per_company'),
        ),
    ]
