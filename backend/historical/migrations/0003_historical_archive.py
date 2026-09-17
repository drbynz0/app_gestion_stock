from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('historical', '0002_historical_company')]
    operations = [
        migrations.AddField(model_name='historical', name='is_archived', field=models.BooleanField(db_index=True, default=False)),
        migrations.AddField(model_name='historical', name='archived_at', field=models.DateTimeField(blank=True, null=True)),
    ]
