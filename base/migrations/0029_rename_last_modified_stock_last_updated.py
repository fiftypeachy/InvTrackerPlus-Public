# Generated by Django 5.0.1 on 2024-02-10 16:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0028_stock_last_modified'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stock',
            old_name='last_modified',
            new_name='last_updated',
        ),
    ]
