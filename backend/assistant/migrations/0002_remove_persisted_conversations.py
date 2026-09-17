from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('assistant', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='AssistantMessage'),
        migrations.DeleteModel(name='AssistantConversation'),
    ]