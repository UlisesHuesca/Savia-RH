# Generated by Django 3.2.3 on 2022-09-13 19:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proyecto', '0002_subproyecto_proyecto'),
    ]

    operations = [
        migrations.AddField(
            model_name='tallas',
            name='ropa',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='proyecto.ropa'),
        ),
    ]
