from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import users.models


def migrate_existing_admins(apps, schema_editor):
    User = apps.get_model('users', 'User')
    Company = apps.get_model('users', 'Company')
    
    # Convertir tout ancien PLATFORM_ADMIN en ADMIN
    User.objects.filter(user_type='PLATFORM_ADMIN').update(user_type='ADMIN')
    
    # Associer l'admin créateur à chaque entreprise existante
    for company in Company.objects.all():
        admin_user = User.objects.filter(company=company, user_type='ADMIN').order_by('date_joined').first()
        if admin_user:
            company.created_by = admin_user
            company.save(update_fields=['created_by'])
            admin_user.is_primary_admin = True
            admin_user.save(update_fields=['is_primary_admin'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_company_branding'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='company_username',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='company',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_companies',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='is_primary_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='two_factor_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='users',
                to='users.company',
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(
                choices=[('SELLER', 'Vendeur'), ('ADMIN', 'Administrateur')],
                default='ADMIN',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(
                error_messages={'unique': "Ce nom d'utilisateur est déjà utilisé."},
                max_length=150,
                unique=True,
                validators=[users.models.validate_username_format],
            ),
        ),
        migrations.CreateModel(
            name='VerificationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_type', models.CharField(choices=[('EMAIL', 'Email'), ('SMS', 'SMS'), ('2FA', '2FA')], max_length=10)),
                ('target', models.CharField(max_length=255)),
                ('code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='verification_codes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(migrate_existing_admins, migrations.RunPython.noop),
    ]
