# Generated by Django 3.2.15 on 2022-12-13 06:22

from django.db import migrations, models

import cm.models


class Migration(migrations.Migration):

    dependencies = [
        ('cm', '0100_subaction_allow_terminate'),
    ]

    operations = [
        migrations.AddField(
            model_name='clusterobject',
            name='before_upgrade',
            field=models.JSONField(default=cm.models.get_default_before_upgrade),
        ),
        migrations.AddField(
            model_name='host',
            name='before_upgrade',
            field=models.JSONField(default=cm.models.get_default_before_upgrade),
        ),
        migrations.AddField(
            model_name='servicecomponent',
            name='before_upgrade',
            field=models.JSONField(default=cm.models.get_default_before_upgrade),
        ),
    ]
