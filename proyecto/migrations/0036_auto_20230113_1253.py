# Generated by Django 3.2.3 on 2023-01-13 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyecto', '0035_historicalvacaciones_dia_inhabil_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalbonos',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical bonos', 'verbose_name_plural': 'historical bonoss'},
        ),
        migrations.AlterModelOptions(
            name='historicalcosto',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical costo', 'verbose_name_plural': 'historical costos'},
        ),
        migrations.AlterModelOptions(
            name='historicaleconomicos',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical economicos', 'verbose_name_plural': 'historical economicoss'},
        ),
        migrations.AlterModelOptions(
            name='historicaluniformes',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical uniformes', 'verbose_name_plural': 'historical uniformess'},
        ),
        migrations.AlterModelOptions(
            name='historicalvacaciones',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical vacaciones', 'verbose_name_plural': 'historical vacacioness'},
        ),
        migrations.AlterField(
            model_name='historicalbonos',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalcosto',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicaleconomicos',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicaluniformes',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalvacaciones',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
    ]
