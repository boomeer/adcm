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


from datetime import datetime
from unittest.mock import patch

from audit.models import (
    AuditLog,
    AuditLogOperationResult,
    AuditLogOperationType,
    AuditObjectType,
)
from cm.job import finish_task
from cm.models import ADCM, Action, Bundle, ConfigLog, ObjectConfig, Prototype, TaskLog
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rbac.models import User
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN

from adcm.tests.base import APPLICATION_JSON, BaseTestCase


class TestComponent(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        bundle = Bundle.objects.create()
        self.prototype = Prototype.objects.create(bundle=bundle, type="adcm")
        config = ObjectConfig.objects.create(current=1, previous=0)
        ConfigLog.objects.create(
            obj_ref=config, config="{}", attr={"ldap_integration": {"active": True}}
        )
        self.adcm = ADCM.objects.create(prototype=self.prototype, name="ADCM", config=config)
        self.action = Action.objects.create(
            display_name="test_adcm_action",
            prototype=self.prototype,
            type="job",
            state_available="any",
        )
        self.task = TaskLog.objects.create(
            object_id=self.adcm.pk,
            object_type=ContentType.objects.get(app_label="cm", model="adcm"),
            start_date=datetime.now(),
            finish_date=datetime.now(),
            action=self.action,
        )

    def check_adcm_updated(
        self, log: AuditLog, operation_name: str, operation_result: str, user: User | None = None
    ):
        if log.audit_object:
            self.assertEqual(log.audit_object.object_id, self.adcm.pk)
            self.assertEqual(log.audit_object.object_name, self.adcm.name)
            self.assertEqual(log.audit_object.object_type, AuditObjectType.ADCM)
            self.assertFalse(log.audit_object.is_deleted)
        else:
            self.assertFalse(log.audit_object)

        self.assertEqual(log.operation_name, operation_name)
        self.assertEqual(log.operation_type, AuditLogOperationType.Update)
        self.assertEqual(log.operation_result, operation_result)
        self.assertIsInstance(log.operation_time, datetime)

        if log.user:
            self.assertEqual(log.user.pk, user.pk)

        self.assertIsInstance(log.object_changes, dict)

    def test_update_and_restore(self):
        self.client.post(
            path=reverse("config-history", kwargs={"adcm_id": self.adcm.pk}),
            data={"config": {}},
            content_type=APPLICATION_JSON,
        )

        log: AuditLog = AuditLog.objects.order_by("operation_time").last()

        self.check_adcm_updated(
            log=log,
            operation_name="ADCM configuration updated",
            operation_result=AuditLogOperationResult.Success,
            user=self.test_user,
        )

        res: Response = self.client.patch(
            path=reverse(
                "config-history-version-restore",
                kwargs={"adcm_id": self.adcm.pk, "version": 1},
            ),
            content_type=APPLICATION_JSON,
        )

        log: AuditLog = AuditLog.objects.order_by("operation_time").last()

        self.assertEqual(res.status_code, HTTP_200_OK)
        self.check_adcm_updated(
            log=log,
            operation_name="ADCM configuration updated",
            operation_result=AuditLogOperationResult.Success,
            user=self.test_user,
        )

    def test_denied(self):
        with self.no_rights_user_logged_in:
            res: Response = self.client.post(
                path=reverse("config-history", kwargs={"adcm_id": self.adcm.pk}),
                data={"config": {}},
                content_type=APPLICATION_JSON,
            )

        log: AuditLog = AuditLog.objects.order_by("operation_time").last()

        self.assertEqual(res.status_code, HTTP_403_FORBIDDEN)
        self.check_adcm_updated(
            log=log,
            operation_name="ADCM configuration updated",
            operation_result=AuditLogOperationResult.Denied,
            user=self.no_rights_user,
        )

    def test_action_launch(self):
        with patch("api.action.views.create", return_value=Response(status=HTTP_201_CREATED)):
            self.client.post(
                path=reverse(
                    "run-task", kwargs={"adcm_id": self.adcm.pk, "action_id": self.action.pk}
                )
            )

        log: AuditLog = AuditLog.objects.order_by("operation_time").last()

        self.check_adcm_updated(
            log=log,
            operation_name=f"{self.action.display_name} action launched",
            operation_result=AuditLogOperationResult.Success,
            user=self.test_user,
        )

        with patch("api.action.views.create", return_value=Response(status=HTTP_201_CREATED)):
            self.client.post(
                path=reverse("run-task", kwargs={"adcm_id": 999, "action_id": self.action.pk})
            )

        log: AuditLog = AuditLog.objects.order_by("operation_time").last()

        self.check_adcm_updated(
            log=log,
            operation_name=f"{self.action.display_name} action launched",
            operation_result=AuditLogOperationResult.Fail,
            user=self.test_user,
        )

    def test_action_finish_success(self):
        finish_task(task=self.task, job=None, status="success")

        log: AuditLog = AuditLog.objects.order_by("operation_time").last()

        self.check_adcm_updated(
            log=log,
            operation_name=f"{self.action.display_name} action completed",
            operation_result=AuditLogOperationResult.Success,
        )

    def test_action_finish_fail(self):
        finish_task(task=self.task, job=None, status="fail")

        log: AuditLog = AuditLog.objects.order_by("operation_time").last()

        self.check_adcm_updated(
            log=log,
            operation_name=f"{self.action.display_name} action completed",
            operation_result=AuditLogOperationResult.Fail,
        )
