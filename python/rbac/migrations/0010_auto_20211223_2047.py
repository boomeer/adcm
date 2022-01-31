# Generated by Django 3.2.4 on 2021-12-23 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0009_upd_role_category'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='role',
            name='unique_role',
        ),
        migrations.AddConstraint(
            model_name='role',
            constraint=models.UniqueConstraint(fields=('name', 'built_in'), name='unique_name'),
        ),
        migrations.AddConstraint(
            model_name='role',
            constraint=models.UniqueConstraint(
                fields=('display_name', 'built_in'), name='unique_display_name'
            ),
        ),
        migrations.AlterField(
            model_name='policy',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]