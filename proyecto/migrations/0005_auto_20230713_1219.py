# Generated by Django 3.2.3 on 2023-07-13 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyecto', '0004_auto_20230713_1131'),
    ]

    operations = [
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='asunto10',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='asunto11',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='asunto12',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='asunto7',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='asunto8',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='asunto9',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='estado10',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='estado11',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='estado12',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='estado7',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='estado8',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trabajos_encomendados',
            name='estado9',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='solicitud_vacaciones',
            name='anexos',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]