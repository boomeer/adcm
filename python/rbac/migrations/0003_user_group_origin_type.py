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

# Generated by Django 3.2.13 on 2022-06-22 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0002_rm_default_policy'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='type',
            field=models.CharField(
                choices=[('local', 'local'), ('ldap', 'ldap')], default='local', max_length=16
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.CharField(
                choices=[('local', 'local'), ('ldap', 'ldap')], default='local', max_length=16
            ),
        ),
    ]
