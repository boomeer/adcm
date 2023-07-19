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

from api_v2.tests.base import BaseAPITestCase
from cm.models import Action, HostProvider
from django.conf import settings
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)


class TestHostProvider(BaseAPITestCase):
    def setUp(self) -> None:
        self.client.login(username="admin", password="admin")

        host_provider_path = settings.BASE_DIR / "python" / "api_v2" / "tests" / "bundles" / "provider"

        self.host_provider_bundle = self.add_bundle(source_dir=host_provider_path)
        self.host_provider = self.add_provider(self.host_provider_bundle, "test host provider")

    def test_list_success(self):
        response = self.client.get(path=reverse(viewname="v2:hostprovider-list"))

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)

    def test_retrieve_success(self):
        response = self.client.get(
            path=reverse(viewname="v2:hostprovider-detail", kwargs={"pk": self.host_provider.pk}),
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json()["id"], self.host_provider.pk)

    def test_retrieve_not_found_fail(self):
        response = self.client.get(
            path=reverse(viewname="v2:hostprovider-detail", kwargs={"pk": self.host_provider.pk + 1}),
        )

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_host_provider_create_success(self):
        response = self.client.post(
            path=reverse(viewname="v2:hostprovider-list"),
            data={
                "prototype": self.host_provider_bundle.pk,
                "name": self.host_provider.name + " new",
                "description": "newly created host provider",
            },
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(response.json()["name"], self.host_provider.name + " new")

    def test_host_provider_duplicate_fail(self):
        response = self.client.post(
            path=reverse(viewname="v2:hostprovider-list"),
            data={
                "prototype": self.host_provider.pk,
                "name": self.host_provider.name,
                "description": self.host_provider.description,
            },
        )
        self.assertEqual(response.status_code, HTTP_409_CONFLICT)

    def test_delete_success(self):
        response = self.client.delete(
            path=reverse(viewname="v2:hostprovider-detail", kwargs={"pk": self.host_provider.pk}),
        )

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertFalse(HostProvider.objects.filter(pk=self.host_provider.pk).exists())

    def test_delete_not_found_fail(self):
        response = self.client.delete(
            path=reverse(viewname="v2:hostprovider-detail", kwargs={"pk": self.host_provider.pk + 1}),
        )

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)


class TestProviderActions(BaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()

        self.action = Action.objects.get(prototype=self.provider.prototype, name="provider_action")

    def test_action_list_success(self):
        response: Response = self.client.get(
            path=reverse(
                viewname="v2:provider-action-list",
                kwargs={"provider_pk": self.provider.pk},
            ),
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_action_retrieve_success(self):
        response: Response = self.client.get(
            path=reverse(
                viewname="v2:provider-action-detail",
                kwargs={
                    "provider_pk": self.provider.pk,
                    "pk": self.action.pk,
                },
            ),
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertTrue(response.json())

    def test_action_run_success(self):
        response: Response = self.client.post(
            path=reverse(
                viewname="v2:provider-action-run",
                kwargs={
                    "provider_pk": self.provider.pk,
                    "pk": self.action.pk,
                },
            ),
            data={"host_component_map": {}, "config": {}, "attr": {}, "is_verbose": False},
        )

        self.assertEqual(response.status_code, HTTP_200_OK)