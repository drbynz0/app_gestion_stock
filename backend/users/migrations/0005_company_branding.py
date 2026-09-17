from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('users', '0004_platform_admin_role')]

    operations = [
        migrations.AddField(model_name='company', name='logo_uri', field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='company', name='primary_color', field=models.CharField(default='#00E599', max_length=9)),
    ]
