# Generated by Django 4.2.7 on 2023-12-29 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyecto', '0017_alter_historicalbonos_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipoperfil',
            name='esquema_bono',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
