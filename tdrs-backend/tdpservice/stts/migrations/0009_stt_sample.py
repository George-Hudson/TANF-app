# Generated by Django 3.2.15 on 2023-01-18 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stts', '0008_auto_20230118_1623'),
    ]

    operations = [
        migrations.AddField(
            model_name='stt',
            name='sample',
            field=models.BooleanField(default=False, null=True),
        ),
    ]