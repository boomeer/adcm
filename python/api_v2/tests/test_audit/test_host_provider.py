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
from audit.models import AuditObject
from cm.models import Action, HostProvider, Prototype, Upgrade
from rbac.services.user import create_user
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)


class TestHostProviderAudit(BaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()

        self.test_user_credentials = {"username": "test_user_username", "password": "test_user_password"}
        self.test_user = create_user(**self.test_user_credentials)

        self.config_post_data = {
            "config": {
                "group": {"map": {"integer_key": "100", "string_key": "new string"}},
                "activatable_group": {
                    "secretmap": {
                        "integer_key": "100",
                        "string_key": "new string",
                    }
                },
                "json": '{"key": "value", "new key": "new value"}',
            },
            "adcmMeta": {"/activatable_group": {"isActive": True}},
            "description": "new provider config",
        }
        self.provider_action = Action.objects.get(name="provider_action", prototype=self.provider.prototype)

        upgrade_bundle = self.add_bundle(source_dir=self.test_bundles_dir / "provider_upgrade")
        self.provider_upgrade = Upgrade.objects.get(bundle=upgrade_bundle, name="upgrade")

    def test_create_success(self):
        response = self.client.post(
            path=reverse(viewname="v2:hostprovider-list"),
            data={"prototypeId": self.provider.prototype.pk, "name": "test_provider"},
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

        self.check_last_audit_log(
            operation_name="Provider created",
            operation_type="create",
            operation_result="success",
            audit_object__object_id=response.json()["id"],
            audit_object__object_name="test_provider",
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            user__username="admin",
        )

    def test_create_no_perms_denied(self):
        self.client.login(**self.test_user_credentials)

        response = self.client.post(
            path=reverse(viewname="v2:hostprovider-list"),
            data={"prototypeId": self.provider.prototype.pk, "name": "test_provider"},
        )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        self.check_last_audit_log(
            operation_name="Provider created",
            operation_type="create",
            operation_result="denied",
            audit_object__isnull=True,
            user__username=self.test_user.username,
        )

    def test_create_duplicate_name_fail(self):
        response = self.client.post(
            path=reverse(viewname="v2:hostprovider-list"),
            data={"prototypeId": self.provider.prototype.pk, "name": self.provider.name},
        )
        self.assertEqual(response.status_code, HTTP_409_CONFLICT)

        self.check_last_audit_log(
            operation_name="Provider created",
            operation_type="create",
            operation_result="fail",
            audit_object__isnull=True,
            user__username="admin",
        )

    def test_create_non_existent_proto_fail(self):
        response = self.client.post(
            path=reverse(viewname="v2:hostprovider-list"),
            data={"prototypeId": self.get_non_existent_pk(model=Prototype), "name": "test_provider"},
        )
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        self.check_last_audit_log(
            operation_name="Provider created",
            operation_type="create",
            operation_result="fail",
            audit_object__isnull=True,
            user__username="admin",
        )

    def test_delete_success(self):
        AuditObject.objects.get_or_create(
            object_id=self.provider.pk,
            object_name=self.provider.name,
            object_type="provider",
            is_deleted=False,
        )

        response = self.client.delete(
            path=reverse(viewname="v2:hostprovider-detail", kwargs={"pk": self.provider.pk}),
        )
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        self.check_last_audit_log(
            operation_name="Provider deleted",
            operation_type="delete",
            operation_result="success",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=True,
            user__username="admin",
        )

    def test_delete_no_perms_denied(self):
        self.client.login(**self.test_user_credentials)

        with self.grant_permissions(to=self.test_user, on=self.provider, role_name="View provider configurations"):
            response = self.client.delete(
                path=reverse(viewname="v2:hostprovider-detail", kwargs={"pk": self.provider.pk}),
            )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        self.check_last_audit_log(
            operation_name="Provider deleted",
            operation_type="delete",
            operation_result="denied",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            user__username=self.test_user.username,
        )

    def test_delete_non_existent_fail(self):
        response = self.client.delete(
            path=reverse(
                viewname="v2:hostprovider-detail", kwargs={"pk": self.get_non_existent_pk(model=HostProvider)}
            ),
        )
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        self.check_last_audit_log(
            operation_name="Provider deleted",
            operation_type="delete",
            operation_result="fail",
            audit_object__isnull=True,
            user__username="admin",
        )

    def test_update_config_success(self):
        response = self.client.post(
            path=reverse(viewname="v2:provider-config-list", kwargs={"hostprovider_pk": self.provider.pk}),
            data=self.config_post_data,
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)

        self.check_last_audit_log(
            operation_name="Provider configuration updated",
            operation_type="update",
            operation_result="success",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username="admin",
        )

    def test_update_config_denied(self):
        self.client.login(**self.test_user_credentials)

        with self.grant_permissions(to=self.test_user, on=self.provider, role_name="View provider configurations"):
            response = self.client.post(
                path=reverse(viewname="v2:provider-config-list", kwargs={"hostprovider_pk": self.provider.pk}),
                data=self.config_post_data,
            )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        self.check_last_audit_log(
            operation_name="Provider configuration updated",
            operation_type="update",
            operation_result="denied",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username=self.test_user.username,
        )

    def test_update_config_wrong_data_fail(self):
        response = self.client.post(
            path=reverse(viewname="v2:provider-config-list", kwargs={"hostprovider_pk": self.provider.pk}),
            data={"wrong": ["d", "a", "t", "a"]},
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        self.check_last_audit_log(
            operation_name="Provider configuration updated",
            operation_type="update",
            operation_result="fail",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username="admin",
        )

    def test_update_config_not_exists_fail(self):
        response = self.client.post(
            path=reverse(
                viewname="v2:provider-config-list",
                kwargs={"hostprovider_pk": self.get_non_existent_pk(model=HostProvider)},
            ),
            data=self.config_post_data,
        )
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        self.check_last_audit_log(
            operation_name="Provider configuration updated",
            operation_type="update",
            operation_result="fail",
            audit_object__isnull=True,
            object_changes={},
            user__username="admin",
        )

    def test_run_action_success(self):
        response = self.client.post(
            path=reverse(
                viewname="v2:provider-action-run",
                kwargs={"hostprovider_pk": self.provider.pk, "pk": self.provider_action.pk},
            ),
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        self.check_last_audit_log(
            operation_name=f"{self.provider_action.display_name} action launched",
            operation_type="update",
            operation_result="success",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username="admin",
        )

    def test_run_action_no_perms_denied(self):
        self.client.login(**self.test_user_credentials)

        with self.grant_permissions(to=self.test_user, on=self.provider, role_name="View provider configurations"):
            response = self.client.post(
                path=reverse(
                    viewname="v2:provider-action-run",
                    kwargs={"hostprovider_pk": self.provider.pk, "pk": self.provider_action.pk},
                ),
            )
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        self.check_last_audit_log(
            operation_name=f"{self.provider_action.display_name} action launched",
            operation_type="update",
            operation_result="denied",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username=self.test_user.username,
        )

    def test_run_action_not_exists_fail(self):
        response = self.client.post(
            path=reverse(
                viewname="v2:provider-action-run",
                kwargs={"hostprovider_pk": self.provider.pk, "pk": self.get_non_existent_pk(model=Action)},
            ),
        )
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        self.check_last_audit_log(
            operation_name="{action_display_name} action launched",
            operation_type="update",
            operation_result="fail",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username="admin",
        )

    def test_upgrade_provider_success(self):
        response = self.client.post(
            path=reverse(
                viewname="v2:upgrade-run",
                kwargs={
                    "hostprovider_pk": self.provider.pk,
                    "pk": self.provider_upgrade.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        self.check_last_audit_log(
            operation_name=f"Upgraded to {self.provider_upgrade.name}",
            operation_type="update",
            operation_result="success",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username="admin",
        )

    def test_upgrade_provider_denied(self):
        self.client.login(**self.test_user_credentials)

        with self.grant_permissions(to=self.test_user, on=self.provider, role_name="View provider configurations"):
            response = self.client.post(
                path=reverse(
                    viewname="v2:upgrade-run",
                    kwargs={
                        "hostprovider_pk": self.provider.pk,
                        "pk": self.provider_upgrade.pk,
                    },
                ),
            )
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        self.check_last_audit_log(
            operation_name=f"Upgraded to {self.provider_upgrade.name}",
            operation_type="update",
            operation_result="denied",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username=self.test_user.username,
        )

    def test_upgrade_provider_fail(self):
        response = self.client.post(
            path=reverse(
                viewname="v2:upgrade-run",
                kwargs={
                    "hostprovider_pk": self.provider.pk,
                    "pk": self.get_non_existent_pk(model=Upgrade),
                },
            ),
        )
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        self.check_last_audit_log(
            operation_name="Upgraded to",
            operation_type="update",
            operation_result="fail",
            audit_object__object_id=self.provider.pk,
            audit_object__object_name=self.provider.name,
            audit_object__object_type="provider",
            audit_object__is_deleted=False,
            object_changes={},
            user__username="admin",
        )