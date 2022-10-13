# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Generated by Django 3.2.15 on 2022-09-28 04:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0005_rbac_group_unique_display_name_type_constraint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='display_name',
            field=models.CharField(default='', max_length=1000),
        ),
        migrations.AlterField(
            model_name='role',
            name='name',
            field=models.CharField(max_length=1000),
        ),
    ]
