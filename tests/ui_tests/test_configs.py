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

"""UI tests for config page"""

import os
import tempfile

import allure
import pytest
import yaml
from adcm_client.objects import ADCMClient
from adcm_pytest_plugin.utils import random_string

from tests.ui_tests.utils import prepare_cluster_and_get_config

pytestmark = [pytest.mark.full()]

PAIR = (True, False)
UI_OPTIONS_PAIRS = ((False, False), (False, True), (True, False))
UI_OPTIONS_PAIRS_GROUPS = [
    (True, False, True, False),
    (True, False, False, True),
    (True, False, False, False),
    (False, True, True, False),
    (False, True, False, True),
    (False, True, False, False),
    (False, False, True, False),
    (False, False, False, True),
    (False, False, False, False),
]


@pytest.fixture()
def adcm_fs(adcm_ms):
    """
    ADCM instance with a module scope
    This fixture override a base adcm_fs.
    It allows do not duplicate all depended fixtures like `app_fs` with browser instance
    Note that all depended fixtures will still be called on each function
    """
    return adcm_ms


def _generate_fields():
    fields = []
    for read_only in True, False:
        for required in True, False:
            for default in True, False:
                if read_only and required and not default:
                    continue
                fields.append((read_only, required, default))
    return fields


FIELDS = _generate_fields()

TYPES = ('string', 'password', 'integer', 'text', 'boolean', 'float', 'list', 'map', 'json', 'file', 'secrettext')


DEFAULT_VALUE = {
    "string": "string",
    "text": "text",
    "password": "password",
    "integer": 4,
    "float": 4.0,
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


@allure.step('Generate data set for groups')
def generate_group_data() -> list:
    """Generate data set for groups"""
    group_data = []
    for required, default, read_only in FIELDS:
        for activatable in PAIR:
            for active in PAIR:
                for ui_options in UI_OPTIONS_PAIRS_GROUPS:
                    if (ui_options[0] or ui_options[2]) and required and not default:
                        continue
                    if activatable and not ui_options[0]:
                        data = {
                            'default': default,
                            "required": required,
                            "activatable": activatable,
                            'active': active,
                            "read_only": read_only,
                            "ui_options": {"invisible": ui_options[0], 'advanced': ui_options[1]},
                            "field_ui_options": {
                                "invisible": ui_options[2],
                                'advanced': ui_options[3],
                            },
                        }
                    else:
                        data = {
                            'default': default,
                            "required": required,
                            "activatable": False,
                            'active': False,
                            "read_only": read_only,
                            "ui_options": {"invisible": ui_options[0], 'advanced': ui_options[1]},
                            "field_ui_options": {
                                "invisible": ui_options[2],
                                'advanced': ui_options[3],
                            },
                        }
                    if data not in group_data:
                        group_data.append(data)
    return group_data


@allure.step('Generate expected result for groups')
def generate_group_expected_result(group_config) -> dict:
    """Generate expected result for groups"""
    expected_result = {
        'group_visible': not group_config['ui_options']['invisible'],
        'editable': not group_config['read_only'],
        "content": group_config['default'],
    }
    if group_config['required'] and not group_config['default']:
        expected_result['alerts'] = True
    else:
        expected_result['alerts'] = False
    group_advanced = group_config['ui_options']['advanced']
    group_invisible = group_config['ui_options']['invisible']
    expected_result['group_visible_advanced'] = group_advanced and not group_invisible
    field_advanced = group_config['field_ui_options']['advanced']
    field_invisible = group_config['field_ui_options']['invisible']
    expected_result['field_visible_advanced'] = field_advanced and not field_invisible
    expected_result['field_visible'] = not field_invisible
    config_valid = _validate_config(group_config['required'], group_config['default'], group_config['read_only'])
    expected_result['config_valid'] = config_valid
    invisible = group_invisible or field_invisible
    if group_config['activatable']:
        required = group_config['required']
        default = group_config['default']
        group_active = group_config['active']
        expected_result['field_visible'] = group_active and not field_invisible
        expected_result['field_visible_advanced'] = field_advanced and group_active and not field_invisible
        if group_active and (required and not default):
            expected_result['save'] = False
        else:
            expected_result['save'] = True
        return expected_result
    if invisible or not config_valid:
        expected_result['save'] = False
    else:
        expected_result['save'] = True
    return expected_result


def _validate_config(field_required, default_presented, field_ro) -> bool:
    if (field_required and not default_presented) or field_ro:
        return False
    return True


@allure.step('Generate data set for configs without groups')
def generate_config_data() -> list:
    """Generate data set for configs without groups"""
    data = []
    for default, required, read_only in FIELDS:
        for ui_options in UI_OPTIONS_PAIRS:
            data.append(
                {
                    'default': default,
                    "required": required,
                    "read_only": read_only,
                    "ui_options": {"invisible": ui_options[0], 'advanced': ui_options[1]},
                }
            )
    return data


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
    if config['read_only']:
        expected_result['save'] = False
    if config['ui_options']['invisible']:
        expected_result['save'] = False
    if config['ui_options']['advanced'] and not config['ui_options']['invisible']:
        expected_result['visible_advanced'] = True
    else:
        expected_result['visible_advanced'] = False
    return expected_result


@allure.step('Generate ADCM config dictionaries for groups')
def generate_group_configs() -> list:
    """Generate ADCM config dictionaries for groups"""
    group_config_data = generate_group_data()
    group_configs = []
    for _type in TYPES:
        for data in group_config_data:
            config_dict = {"type": "cluster", "version": "1", "config": []}
            unsupported_options = all([data['read_only'], data['required']])
            if not data['default'] and unsupported_options:
                continue
            cluster_config = {
                "name": "group",
                "type": "group",
                'ui_options': {
                    "invisible": data['ui_options']['invisible'],
                    'advanced': data['ui_options']['advanced'],
                },
            }
            sub_config = {'name': _type, 'type': _type, 'required': data['required']}
            if data['default']:
                sub_config['default'] = DEFAULT_VALUE[_type]
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
            group_configs.append((config, expected_result))
    return group_configs


@allure.step('Generate ADCM config dictionaries for fields')
def generate_configs() -> list:
    """Generate ADCM config dictionaries for fields"""
    config_data = generate_config_data()
    configs = []
    for _type in TYPES:
        for data in config_data:
            config_dict = {"type": "cluster", "version": "1", "config": []}
            unsupported_options = all([data['read_only'], data['required']])
            if not data['default'] and unsupported_options:
                continue
            field_config = {'name': _type, 'type': _type, 'required': data['required']}
            if data['default']:
                field_config['default'] = DEFAULT_VALUE[_type]
            if data['read_only']:
                field_config['read_only'] = 'any'
            field_config['ui_options'] = {
                'invisible': data['ui_options']['invisible'],
                'advanced': data['ui_options']['advanced'],
            }
            config_dict['config'] = [field_config]
            config = [config_dict]
            expected_result = generate_config_expected_result(data)
            configs.append((config, expected_result))
    return configs


def _prepare_config(config):
    read_only = bool('read_only' in config[0][0]['config'][0].keys())
    default = bool('default' in config[0][0]['config'][0].keys())
    templ = "type_{}_required_{}_ro_{}_content_{}_invisible_{}_advanced_{}"
    config_folder_name = templ.format(
        config[0][0]['config'][0]['type'],
        config[0][0]['config'][0]['required'],
        read_only,
        default,
        config[0][0]['config'][0]['ui_options']['invisible'],
        config[0][0]['config'][0]['ui_options']['advanced'],
    )
    temdir = tempfile.mkdtemp()
    d_name = f"{temdir}/configs/fields/{config[0][0]['config'][0]['type']}/{config_folder_name}"

    os.makedirs(d_name)
    config[0][0]["name"] = random_string()
    if config[0][0]['config'][0]['name'] == 'file':
        with open(f"{d_name}/file.txt", 'w', encoding='utf_8') as file:
            file.write("test")
    with open(f"{d_name}/config.yaml", 'w', encoding='utf_8') as yaml_file:
        yaml.dump(config[0], yaml_file)
    return config[0][0], config[1], d_name


def _prepare_group_config(config):
    if "activatable" in config[0]['config'][0].keys():
        activatable = True
        active = config[0]['config'][0]['active']
    else:
        activatable = False
        active = False
    data_type = config[0]['config'][0]['subs'][0]['type']
    read_only = bool('read_only' in config[0]['config'][0]['subs'][0].keys())
    default = bool('default' in config[0]['config'][0]['subs'][0].keys())
    temp = "{}_activatab_{}_act_{}_req_{}_ro_{}_cont_{}_grinvis_{}_gradv_{}_fiinvis_{}_fiadv_{}"
    config_folder_name = temp.format(
        data_type,
        activatable,
        active,
        config[0]['config'][0]['subs'][0]['required'],
        read_only,
        default,
        config[0]['config'][0]['ui_options']['invisible'],
        config[0]['config'][0]['ui_options']['advanced'],
        config[0]['config'][0]['subs'][0]['ui_options']['invisible'],
        config[0]['config'][0]['subs'][0]['ui_options']['advanced'],
    )
    temdir = tempfile.mkdtemp()
    d_name = f"{temdir}/configs/groups/{config_folder_name}"
    os.makedirs(d_name)
    config[0]["name"] = random_string()
    if config[0]['config'][0]['subs'][0]['name'] == 'file':
        with open(f"{d_name}/file.txt", 'w', encoding='utf_8') as file:
            file.write("test")
    with open(f"{d_name}/config.yaml", 'w', encoding='utf_8') as yaml_file:
        yaml.dump(list(config), yaml_file)
    return config[0], d_name


@pytest.mark.parametrize("config_dict", generate_configs())
@pytest.mark.usefixtures("login_to_adcm_over_api")
def test_configs_fields(sdk_client_fs: ADCMClient, config_dict, app_fs):
    """Test UI configuration page without groups. Before start test actions
    we always create configuration and expected result. All logic for test
    expected result in functions before this test function.
    Scenario:
    1. Generate configuration and expected result for test
    2. Upload bundle
    3. Create cluster
    4. Open configuration page
    5. Check save button status
    6. Check field configuration (depends on expected result dict and bundle configuration"""

    config, expected, path = _prepare_config(config_dict)
    allure.attach.file(
        "/".join([path, 'config.yaml']),
        attachment_type=allure.attachment_type.YAML,
        name='config.yaml',
    )
    field_type = config['config'][0]['type']

    cluster, ui_config = prepare_cluster_and_get_config(sdk_client_fs, path, app_fs)

    fields = ui_config.get_app_fields()
    with allure.step('Check save button status'):
        save_err_mess = f"Correct status for save button {[expected['save']]}"
        button_state = ui_config.save_button_status()
        assert expected['save'] == button_state, save_err_mess
        if expected['save']:
            ui_config.save_configuration()
            ui_config.assert_no_popups_displayed()
    with allure.step('Check field configuration'):
        if expected['visible']:
            if expected['visible_advanced']:
                assert not fields, "Config fields presented, expected no"
                ui_config.show_advanced()
                assert ui_config.advanced, 'Advanced button not clicked'
            fields = ui_config.get_app_fields()
            assert fields, 'No config fields, expected yes'
            for field in fields:
                ui_config.assert_field_is_editable(field, expected['editable'])
            if expected['content']:
                ui_config.assert_field_content_equal(cluster, field_type, fields[0], config['config'][0]['default'])
            if expected['alerts']:
                ui_config.assert_alerts_presented(field_type)
        else:
            assert not fields, "Config fields presented, expected no"


@pytest.mark.parametrize(("config_dict", "expected"), generate_group_configs())
@pytest.mark.usefixtures("login_to_adcm_over_api")
def test_group_configs_field(sdk_client_fs: ADCMClient, config_dict, expected, app_fs):
    """Test for configuration fields with groups. Before start test actions
    we always create configuration and expected result. All logic for test
    expected result in functions before this test function. If we have
    advanced fields inside configuration and group visible we check
    field and group status after clicking advanced button. For activatable
    groups we don't change group status. We have two types of tests for activatable
    groups: the first one when group is active and the second when group not active.
    Scenario:
    1. Generate configuration and expected result for test
    2. Upload bundle
    3. Create cluster
    4. Open configuration page
    5. Check save button status
    6. Check field configuration (depends on expected result dict and bundle configuration)"""

    config, path = _prepare_group_config(config_dict)
    allure.attach.file(
        "/".join([path, 'config.yaml']),
        attachment_type=allure.attachment_type.YAML,
        name='config.yaml',
    )

    field_type = config['config'][0]['subs'][0]['type']

    cluster, ui_config = prepare_cluster_and_get_config(sdk_client_fs, path, app_fs)

    groups = ui_config.get_group_elements()
    fields = ui_config.get_app_fields()
    with allure.step('Check save button status'):
        save_err_mess = f"Correct status for save button {[expected['save']]}"
        assert expected['save'] == ui_config.save_button_status(), save_err_mess
        if expected['save']:
            ui_config.save_configuration()
            ui_config.assert_no_popups_displayed()
    with allure.step('Check configuration'):
        if expected['group_visible'] and not expected['field_visible']:
            if expected['group_visible_advanced']:
                assert not groups, 'Groups presented, expected no'
                assert not fields, 'Fields presented, expected no'
                ui_config.show_advanced()
                assert ui_config.advanced, 'Advanced button not clicked'
            groups = ui_config.get_group_elements()
            fields = ui_config.get_app_fields()
            assert groups, "Groups not presented, expected yes"
            for field in fields:
                assert not field.is_displayed()
            if "activatable" in config['config'][0].keys():
                ui_config.assert_group_status(groups[0], config['config'][0]['active'])

        if expected['group_visible'] and expected['field_visible']:
            if expected['field_visible_advanced'] or expected['group_visible_advanced']:
                assert not fields, 'Fields presented, expected no'
                ui_config.show_advanced()
                assert ui_config.advanced, 'Advanced button not clicked'
            groups = ui_config.get_group_elements()
            fields = ui_config.get_app_fields()
            assert groups, "Groups not presented, expected yes"
            assert fields, "Fields not presented, expected yes"
            for field in fields:
                ui_config.assert_field_is_editable(field, expected['editable'])
            if expected['content']:
                default_value = config['config'][0]['subs'][0]['default']
                ui_config.assert_field_content_equal(cluster, field_type, fields[0], default_value)
            if expected['alerts']:
                ui_config.assert_alerts_presented(field_type)
            if "activatable" in config['config'][0].keys():
                ui_config.assert_group_status(groups[0], config['config'][0]['active'])
        if not expected['group_visible']:
            assert not groups, 'Groups presented, expected no'
            ui_config.show_advanced()
            assert ui_config.advanced, 'Advanced button not clicked'
            groups = ui_config.get_group_elements()
            assert not groups, "Groups presented, expected no"
