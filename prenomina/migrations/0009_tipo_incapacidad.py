# Generated by Django 4.2.9 on 2024-05-10 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prenomina', '0008_castigos_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tipo_incapacidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
            ],
        ),
    ]
