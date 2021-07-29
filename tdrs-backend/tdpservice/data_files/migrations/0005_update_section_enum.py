# Generated by Django 3.1.7 on 2021-04-22 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('reports','0005_update_section_enum')]
    dependencies = [
        ('data_files', '0004_auto_20210305_2040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='section',
            field=models.CharField(choices=[('Active Case Data', 'Active Case Data'), ('Closed Case Data', 'Closed Case Data'), ('Aggregate Data', 'Aggregate Data'), ('Stratum Data', 'Stratum Data')], max_length=32),
        ),
    ]
