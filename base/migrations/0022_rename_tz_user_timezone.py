# Generated by Django 5.0.1 on 2024-02-10 07:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0021_alter_user_tz'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='tz',
            new_name='Timezone',
        ),
    ]