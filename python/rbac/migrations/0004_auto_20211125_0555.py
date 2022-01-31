# Generated by Django 3.2 on 2021-11-25 05:55

import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('rbac', '0003_auto_20211122_1048'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                (
                    'group_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='auth.group',
                    ),
                ),
                ('description', models.CharField(max_length=255, null=True)),
            ],
            bases=('auth.group',),
            managers=[
                ('objects', django.contrib.auth.models.GroupManager()),
            ],
        ),
        migrations.AlterField(
            model_name='policy',
            name='group',
            field=models.ManyToManyField(blank=True, to='rbac.Group'),
        ),
        migrations.AlterField(
            model_name='policypermission',
            name='group',
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='rbac.group',
            ),
        ),
    ]