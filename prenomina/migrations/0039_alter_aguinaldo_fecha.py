# Generated by Django 4.2.9 on 2024-06-25 21:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prenomina', '0038_aguinaldo_rename_contratoaguinaldo_tipoaguinaldo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aguinaldo',
            name='fecha',
            field=models.DateField(db_index=True, null=True),
        ),
    ]