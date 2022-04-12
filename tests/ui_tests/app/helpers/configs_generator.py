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
# pylint: disable=too-many-branches,too-many-statements

"""UI tests for config page"""

import os
import tempfile

import allure
import pytest
import yaml
from adcm_pytest_plugin.utils import random_string

pytestmark = [pytest.mark.full()]


TYPES = ['string', 'password', 'integer', 'text', 'boolean', 'float', 'list', 'map', 'json', 'file', 'secrettext']

CONFIG_FILE = 'config.yaml'
DEFAULT_VALUE = {
    "string": "string",
    "text": "text",
    "password": "password",
    "integer": 4,
    "float": 4.1,
    "boolean": True,
    "json": {},
    "map": {"name": "Joe", "age": "24", "sex": "m"},
    "list": ['/dev/rdisk0s1', '/dev/rdisk0s2', '/dev/rdisk0s3'],
    "file": "./file.txt",
    "secrettext": "sec\nret\ntext",
}


class ListWithoutRepr(list):
    """Custom list without direct repr"""

    def __repr__(self):
        return f'<{self.__class__.__name__} instance at {id(self):#x}>'


# Generate config for usual fields


@allure.step('Generate expected result for config')
def generate_config_expected_result(config) -> dict:
    """Generate expected result for config"""
    expected_result = {
        'visible': not config['ui_options']['invisible'],
        'editable': not config['read_only'],
        "content": config['default'],
    }
    if config['required'] and not config['default']:
        expected_result['save'] = False
        expected_result['alerts'] = True
    else:
        expected_result['save'] = True
        expected_result['alerts'] = False
    if config['read_only'] or config['ui_options']['invisible']:
        expected_result['save'] = False
    if config['ui_options']['advanced'] and not config['ui_options']['invisible']:
        expected_result['visible_advanced'] = True
    else:
        expected_result['visible_advanced'] = False
    return expected_result


@allure.step('Generate ADCM config dictionaries for fields')
def generate_configs(
    field_type: str,
    invisible: bool = True,
    advanced: bool = True,
    default: bool = True,
    required: bool = True,
    read_only: bool = True,
) -> tuple:
    """Generate ADCM config dictionaries for fields"""

    with allure.step('Generate data set for configs without groups'):
        data = {
            'default': default,
            "required": required,
            "read_only": read_only,
            "ui_options": {"invisible": invisible, 'advanced': advanced},
        }
    config_dict = {"type": "cluster", "version": "1", "config": []}
    field_config = {'name': field_type, 'type': field_type, 'required': data['required']}
    if data['default']:
        field_config['default'] = DEFAULT_VALUE[field_type]
    if data['read_only']:
        field_config['read_only'] = 'any'
    field_config['ui_options'] = {
        'invisible': data['ui_options']['invisible'],
        'advanced': data['ui_options']['advanced'],
    }
    config_dict['config'] = [field_config]
    config = [config_dict]
    expected_result = generate_config_expected_result(data)
    return (config, expected_result)


def prepare_config(config):
    config_info = config[0][0]['config'][0]
    templ = "type_{}_required_{}_ro_{}_content_{}_invisible_{}_advanced_{}"
    config_folder_name = templ.format(
        config_info['type'],
        config_info['required'],
        bool('read_only' in config_info.keys()),
        bool('default' in config_info.keys()),
        config_info['ui_options']['invisible'],
        config_info['ui_options']['advanced'],
    )
    temdir = tempfile.mkdtemp()
    d_name = f"{temdir}/configs/fields/{config_info['type']}/{config_folder_name}"

    os.makedirs(d_name)
    config[0][0]["name"] = random_string()
    if config_info['name'] == 'file':
        with open(f"{d_name}/file.txt", 'w', encoding='utf_8') as file:
            file.write("test")
    with open(f"{d_name}/{CONFIG_FILE}", 'w', encoding='utf_8') as yaml_file:
        yaml.dump(config[0], yaml_file)
    allure.attach.file("/".join([d_name, CONFIG_FILE]), attachment_type=allure.attachment_type.YAML, name=CONFIG_FILE)
    return config[0][0], config[1], d_name


# Generate config for group fields


@allure.step('Generate expected result for groups')
def generate_group_expected_result(group_config) -> dict:
    """Generate expected result for groups"""

    expected_result = {
        'group_visible': not group_config['ui_options']['invisible'],
        'editable': not group_config['read_only'],
        "content": group_config['default'],
    }
    expected_result['alerts'] = group_config['required'] and not group_config['default']
    group_advanced = group_config['ui_options']['advanced']
    group_invisible = group_config['ui_options']['invisible']
    expected_result['group_visible_advanced'] = group_advanced and not group_invisible
    field_advanced = group_config['field_ui_options']['advanced']
    field_invisible = group_config['field_ui_options']['invisible']
    expected_result['field_visible_advanced'] = field_advanced and not field_invisible
    expected_result['field_visible'] = not field_invisible
    config_valid = not ((group_config['required'] and not group_config['default']) or group_config['read_only'])
    expected_result['config_valid'] = config_valid
    invisible = group_invisible or field_invisible
    if group_config['activatable']:
        required = group_config['required']
        default = group_config['default']
        group_active = group_config['active']
        expected_result['field_visible'] = group_active and not field_invisible
        expected_result['field_visible_advanced'] = field_advanced and group_active and not field_invisible
        expected_result['save'] = not (group_active and (required and not default))
        return expected_result
    expected_result['save'] = not (invisible or not config_valid)
    return expected_result


@allure.step('Generate ADCM config dictionaries for groups')
def generate_group_configs(
    field_type: str,
    activatable: bool = True,
    active: bool = True,
    group_invisible: bool = True,
    group_advanced: bool = True,
    default: bool = True,
    required: bool = True,
    read_only: bool = True,
    field_invisible: bool = True,
    field_advanced: bool = True,
) -> tuple:
    """Generate ADCM config dictionaries for groups"""

    data = {
        'default': default,
        "required": required,
        "activatable": activatable,
        'active': active,
        "read_only": read_only,
        "ui_options": {"invisible": group_invisible, 'advanced': group_advanced},
        "field_ui_options": {
            "invisible": field_invisible,
            'advanced': field_advanced,
        },
    }
    config_dict = {"type": "cluster", "version": "1", "config": []}
    cluster_config = {
        "name": "group",
        "type": "group",
        'ui_options': {
            "invisible": data['ui_options']['invisible'],
            'advanced': data['ui_options']['advanced'],
        },
    }
    sub_config = {'name': field_type, 'type': field_type, 'required': data['required']}
    if data['default']:
        sub_config['default'] = DEFAULT_VALUE[field_type]
    if data['read_only']:
        sub_config['read_only'] = 'any'
    if data['activatable']:
        cluster_config['activatable'] = True
        cluster_config['active'] = data['active']
    sub_config['ui_options'] = {
        'invisible': data['field_ui_options']['invisible'],
        'advanced': data['field_ui_options']['advanced'],
    }
    cluster_config['subs'] = [sub_config]
    config_dict['config'] = [cluster_config]
    config = ListWithoutRepr([config_dict])
    expected_result = generate_group_expected_result(data)
    return (config, expected_result)


def prepare_group_config(config):
    config_info = config[0][0]['config'][0]
    config_subs = config_info['subs'][0]
    if "activatable" in config_info.keys():
        activatable = True
        active = config_info['active']
    else:
        activatable = False
        active = False
    data_type = config_subs['type']
    read_only = bool('read_only' in config_subs.keys())
    default = bool('default' in config_subs.keys())
    temp = "{}_activatab_{}_act_{}_req_{}_ro_{}_cont_{}_grinvis_{}_gradv_{}_fiinvis_{}_fiadv_{}"
    config_folder_name = temp.format(
        data_type,
        activatable,
        active,
        config_subs['required'],
        read_only,
        default,
        config_info['ui_options']['invisible'],
        config_info['ui_options']['advanced'],
        config_subs['ui_options']['invisible'],
        config_subs['ui_options']['advanced'],
    )
    temdir = tempfile.mkdtemp()
    d_name = f"{temdir}/configs/groups/{config_folder_name}"
    os.makedirs(d_name)
    config[0][0]["name"] = random_string()
    if config_subs['name'] == 'file':
        with open(f"{d_name}/file.txt", 'w', encoding='utf_8') as file:
            file.write("test")
    with open(f"{d_name}/{CONFIG_FILE}", 'w', encoding='utf_8') as yaml_file:
        yaml.dump(list(config[0]), yaml_file)
    allure.attach.file("/".join([d_name, CONFIG_FILE]), attachment_type=allure.attachment_type.YAML, name=CONFIG_FILE)
    return config[0][0], config[1], d_name