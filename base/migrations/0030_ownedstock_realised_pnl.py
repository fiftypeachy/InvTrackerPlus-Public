# Generated by Django 5.0.1 on 2024-02-11 08:28

import base.models
import django.core.validators
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0029_rename_last_modified_stock_last_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownedstock',
            name='realised_pnl',
            field=base.models.PositiveDecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]