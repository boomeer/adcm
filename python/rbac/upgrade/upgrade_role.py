# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.  You may obtain a
# copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Init or upgrade RBAC roles and permissions"""
from typing import List

import ruyaml

from django.contrib.contenttypes.models import ContentType

from adwp_base.errors import raise_AdwpEx as err

import cm.checker
from cm.models import ProductCategory
from rbac import log
from rbac.settings import api_settings
from rbac.models import Role, RoleMigration, Policy, Permission, re_apply_all_polices


def upgrade(data: dict):
    """Upgrade roles and user permissions"""
    new_roles = {}
    for role in data['roles']:
        new_roles[role['name']] = upgrade_role(role, data)

    for role in data['roles']:
        role_obj = new_roles[role['name']]
        role_obj.child.clear()
        if 'child' not in role:
            continue
        for child in role['child']:
            child_role = new_roles[child]
            role_obj.child.add(child_role)
        role_obj.save()
    re_apply_all_polices()


def find_role(name: str, roles: list):
    """search role in role list by name"""
    for role in roles:
        if role['name'] == name:
            return role
    return err('INVALID_ROLE_SPEC', f'child role "{name}" is absent')


def check_roles_child(data: dict):
    """Check if role child name are exist in specification file"""
    for role in data['roles']:
        if 'child' in role:
            for child in role['child']:
                find_role(child, data['roles'])


def get_role_permissions(role: dict, data: dict) -> List[Permission]:
    """Retrieve all role's permissions"""
    all_perm = []
    if 'apps' not in role:
        return []
    for app in role['apps']:
        for model in app['models']:
            try:
                ct = ContentType.objects.get(app_label=app['label'], model=model['name'])
            except ContentType.DoesNotExist:
                msg = 'no model "{}" in application "{}"'
                err('INVALID_ROLE_SPEC', msg.format(model['name'], app['label']))
            for code in model['codenames']:
                codename = f"{code}_{model['name']}"
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                except Permission.DoesNotExist:
                    perm = Permission(content_type=ct, codename=codename)
                    perm.save()
                if perm not in all_perm:
                    all_perm.append(perm)
    return all_perm


def upgrade_role(role: dict, data: dict) -> Role:
    """Upgrade single role"""
    perm_list = get_role_permissions(role, data['roles'])
    try:
        new_role = Role.objects.get(name=role['name'])
        new_role.permissions.clear()
    except Role.DoesNotExist:
        new_role = Role(name=role['name'])
        new_role.save()
    new_role.module_name = role['module_name']
    new_role.class_name = role['class_name']
    if 'init_params' in role:
        new_role.init_params = role['init_params']
    if 'description' in role:
        new_role.description = role['description']
    if 'display_name' in role:
        new_role.display_name = role['display_name']
    else:
        new_role.display_name = role['name']
    if 'parametrized_by' in role:
        new_role.parametrized_by_type = role['parametrized_by']
    if 'type' in role:
        new_role.type = role['type']
    for perm in perm_list:
        new_role.permissions.add(perm)
    for category_value in role.get('category', []):
        category = ProductCategory.objects.get(value=category_value)
        new_role.category.add(category)
    new_role.any_category = role.get('any_category', False)
    new_role.save()
    return new_role


def get_role_spec(data: str, schema: str) -> dict:
    """
    Read and parse roles specification from role_spec.yaml file.
    Specification file structure is checked against role_schema.yaml file.
    (see https://github.com/arenadata/yspec for details about schema syntaxis)
    """
    try:
        with open(data, encoding='utf_8') as fd:
            data = ruyaml.round_trip_load(fd)
    except FileNotFoundError:
        err('INVALID_ROLE_SPEC', f'Can not open role file "{data}"')
    except (ruyaml.parser.ParserError, ruyaml.scanner.ScannerError, NotImplementedError) as e:
        err('INVALID_ROLE_SPEC', f'YAML decode "{data}" error: {e}')

    with open(schema, encoding='utf_8') as fd:
        rules = ruyaml.round_trip_load(fd)

    try:
        cm.checker.check(data, rules)
    except cm.checker.FormatError as e:
        args = ''
        if e.errors:
            for ee in e.errors:
                if 'Input data for' in ee.message:
                    continue
                args += f'line {ee.line}: {ee}\n'
        err('INVALID_ROLE_SPEC', f'line {e.line} error: {e}', args)

    return data


def create_default_policy():
    policy_name = 'default'
    role = Role.objects.get(name='Base role')
    try:
        policy = Policy.objects.get(name=policy_name)
        policy.role = role
        policy.save()
    except Policy.DoesNotExist:
        Policy.objects.create(name=policy_name, role_id=role.id, built_in=True)


def init_roles():
    """
    Init or upgrade roles and permissions in DB
    To run upgrade call
    manage.py upgarderole
    """
    role_data = get_role_spec(api_settings.ROLE_SPEC, api_settings.ROLE_SCHEMA)
    check_roles_child(role_data)

    rm = RoleMigration.objects.last()
    if rm is None:
        rm = RoleMigration(version=0)
    if role_data['version'] > rm.version:
        upgrade(role_data)
        rm.version = role_data['version']
        rm.save()
        create_default_policy()
        msg = f'Roles are upgraded to version {rm.version}'
        log.info(msg)
    else:
        msg = f'Roles are already at version {rm.version}'
    return msg