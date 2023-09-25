# Generated by Django 4.1.1 on 2023-09-10 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyecto', '0011_remove_datos_baja_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipoperfil',
            name='autorizacion',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='tipoperfil',
            name='empleados',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='tipoperfil',
            name='info_general',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='tipoperfil',
            name='solicitudes',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='tipoperfil',
            name='tablas_empleados',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='tipoperfil',
            name='usuario',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
