# Generated by Django 4.2.7 on 2023-12-29 23:20

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import esquema.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('proyecto', '0018_tipoperfil_esquema_bono'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('slug', models.SlugField(blank=True, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subcategoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('esquema_categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='esquema.categoria')),
            ],
        ),
        migrations.CreateModel(
            name='Solicitud',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('folio', models.BigIntegerField(unique=True)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('bono', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='esquema.subcategoria')),
                ('solicitante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proyecto.perfil')),
            ],
        ),
        migrations.CreateModel(
            name='Requerimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('url', models.FileField(unique=True, upload_to='bonos/', validators=[esquema.models.validar_size, django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg'])])),
                ('solicitud', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='esquema.solicitud')),
            ],
        ),
        migrations.CreateModel(
            name='BonoSolicitado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('distrito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proyecto.distrito')),
                ('puesto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proyecto.puesto')),
                ('solicitud', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='esquema.solicitud')),
                ('trabajador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proyecto.perfil')),
            ],
        ),
        migrations.CreateModel(
            name='Bono',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('importe', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('distrito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proyecto.distrito')),
                ('esquema_subcategoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='esquema.subcategoria')),
                ('puesto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proyecto.puesto')),
            ],
        ),
    ]
