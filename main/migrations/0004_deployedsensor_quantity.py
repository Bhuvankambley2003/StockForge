# Generated by Django 5.1.6 on 2025-03-11 05:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_alter_inventoryitem_part_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployedsensor',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
