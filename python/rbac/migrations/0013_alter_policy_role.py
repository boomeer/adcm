# Generated by Django 3.2.4 on 2022-01-21 09:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0012_policy_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='policy',
            name='role',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to='rbac.role'
            ),
        ),
    ]