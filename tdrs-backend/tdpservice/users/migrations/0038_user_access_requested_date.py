# Generated by Django 3.2.15 on 2023-04-28 20:52

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0037_auto_20230306_1434'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='access_requested_date',
            field=models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0)),
        ),
    ]