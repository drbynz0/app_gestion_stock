from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('users', '0002_company_user_company')]

    operations = [
        migrations.AddField(
            model_name='company',
            name='currency',
            field=models.CharField(default='MAD', max_length=3),
        ),
    ]
