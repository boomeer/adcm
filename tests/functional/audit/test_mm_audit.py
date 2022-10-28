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

"""Test designed to check audit on mm"""

import allure
import pytest
import requests
from adcm_client.objects import ADCMClient, Cluster, Component, Host, Provider, Service

from tests.functional.audit.conftest import (
    NEW_USER,
    check_failed,
    check_succeed,
    make_auth_header,
    parametrize_audit_scenario_parsing,
)
from tests.functional.conftest import only_clean_adcm
from tests.functional.maintenance_mode.conftest import (
    ANOTHER_SERVICE_NAME,
    BUNDLES_DIR,
    CLUSTER_WITH_MM_NAME,
    DEFAULT_SERVICE_NAME,
    MM_IS_ON,
    PROVIDER_NAME,
    add_hosts_to_cluster,
)

# pylint: disable=redefined-outer-name

pytestmark = [only_clean_adcm]


@pytest.fixture()
def hosts(provider) -> tuple[Host, ...]:
    """Create 6 hosts from the default bundle"""
    return tuple(provider.host_create(f'test-host-{i}') for i in range(6))


@pytest.fixture()
def provider(sdk_client_fs: ADCMClient) -> Provider:
    """Upload bundle and create default provider"""
    bundle = sdk_client_fs.upload_from_fs(BUNDLES_DIR / 'default_provider')
    return bundle.provider_create(PROVIDER_NAME)


@pytest.fixture()
def cluster_with_mm(sdk_client_fs: ADCMClient) -> Cluster:
    """
    Upload cluster bundle with allowed MM,
    create and return cluster with default service
    """
    bundle = sdk_client_fs.upload_from_fs(BUNDLES_DIR / 'cluster_mm_allowed')
    cluster = bundle.cluster_create(CLUSTER_WITH_MM_NAME)
    cluster.service_add(name=DEFAULT_SERVICE_NAME)
    return cluster


def change_service_mm(client: ADCMClient, cluster: Cluster, service: Service, user: ADCMClient) -> None:
    """Method to change service to maintenance mode"""
    url_list = [
        f'{client.url}/api/v1/cluster/{cluster.id}/service/{service.id}/maintenance-mode/',
        f'{client.url}/api/v1/service/{service.id}/maintenance-mode/',
    ]

    for url in url_list:
        body = {"maintenance_mode": True}
        with allure.step(f'Fail update service via POST {url} with body: {body}'):
            check_failed(requests.post(url, json=body, headers=make_auth_header(client)), 400)

        body = {"maintenance_mode": MM_IS_ON}
        with allure.step(f'Success update service via POST {url} with body: {body}'):
            check_succeed(requests.post(url, json=body, headers=make_auth_header(client)))

        with allure.step(f'Deny update service via POST {url} with body: {body} with wrong user'):
            check_failed(requests.post(url, json=body, headers=make_auth_header(user)), exact_code=404)


def change_component_mm(
    client: ADCMClient, cluster: Cluster, service: Service, component: Component, user: ADCMClient
) -> None:
    """Method to change component to maintenance mode"""
    url_list = [
        f'{client.url}/api/v1/cluster/{cluster.id}/service/{service.id}/component/{component.id}/maintenance-mode/',
        f'{client.url}/api/v1/service/{service.id}/component/{component.id}/maintenance-mode/',
        f'{client.url}/api/v1/component/{component.id}/maintenance-mode/',
    ]

    for url in url_list:
        body = {"maintenance_mode": True}
        with allure.step(f'Fail update component via POST {url} with body: {body}'):
            check_failed(requests.post(url, json=body, headers=make_auth_header(client)), 400)

        body = {"maintenance_mode": MM_IS_ON}
        with allure.step(f'Success update component via POST {url} with body: {body}'):
            check_succeed(requests.post(url, json=body, headers=make_auth_header(client)))

        with allure.step(f'Deny update component via POST {url} with body: {body} with wrong user'):
            check_failed(requests.post(url, json=body, headers=make_auth_header(user)), exact_code=404)


def change_host_mm(client: ADCMClient, cluster: Cluster, provider: Provider, host: Host, user: ADCMClient) -> None:
    """Method to change host to maintenance mode"""
    url_list = [
        f'{client.url}/api/v1/cluster/{cluster.id}/host/{host.id}/maintenance-mode/',
        f'{client.url}/api/v1/host/{host.id}/maintenance-mode/',
        f'{client.url}/api/v1/provider/{provider.id}/host/{host.id}/maintenance-mode/',
    ]

    for url in url_list:
        body = {"maintenance_mode": True}
        with allure.step(f'Deny update host via POST {url} with body: {body}'):
            check_failed(requests.post(url, json=body, headers=make_auth_header(client)), 400)

        body = {"maintenance_mode": MM_IS_ON}
        with allure.step(f'Success update host via POST {url} with body: {body}'):
            check_succeed(requests.post(url, json=body, headers=make_auth_header(client)))

        with allure.step(f'Deny update host via POST {url} with body: {body} with wrong user'):
            check_failed(requests.post(url, json=body, headers=make_auth_header(user)), exact_code=404)


@parametrize_audit_scenario_parsing("mm_audit.yaml", NEW_USER)  # pylint: disable-next=too-many-arguments
def test_mm_audit(sdk_client_fs, audit_log_checker, cluster_with_mm, hosts, provider, new_user_client):
    """Test to check audit logs for service and components in maintenance mode"""
    first_host, *_ = hosts
    first_service = cluster_with_mm.service(name=DEFAULT_SERVICE_NAME)
    first_component = first_service.component(name='first_component')
    second_service = cluster_with_mm.service_add(name=ANOTHER_SERVICE_NAME)

    add_hosts_to_cluster(cluster_with_mm, (first_host,))

    change_service_mm(client=sdk_client_fs, cluster=cluster_with_mm, service=second_service, user=new_user_client)
    change_component_mm(
        client=sdk_client_fs,
        cluster=cluster_with_mm,
        service=first_service,
        component=first_component,
        user=new_user_client,
    )
    change_host_mm(
        client=sdk_client_fs, cluster=cluster_with_mm, provider=provider, host=first_host, user=new_user_client
    )

    audit_log_checker.set_user_map(sdk_client_fs)
    audit_log_checker.check(list(sdk_client_fs.audit_operation_list()))
