# Generated by Django 3.2.3 on 2022-10-02 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyecto', '0012_auto_20221002_1649'),
    ]

    operations = [
        migrations.AddField(
            model_name='economicos',
            name='complete_dias',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicaleconomicos',
            name='complete_dias',
            field=models.BooleanField(default=False),
        ),
    ]
