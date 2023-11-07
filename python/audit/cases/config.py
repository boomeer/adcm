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

from audit.cases.common import get_obj_name, get_or_create_audit_obj
from audit.models import (
    MODEL_TO_AUDIT_OBJECT_TYPE_MAP,
    PATH_STR_TO_OBJ_CLASS_MAP,
    AuditLogOperationType,
    AuditObject,
    AuditOperation,
)
from cm.models import GroupConfig, Host, ObjectConfig
from django.contrib.contenttypes.models import ContentType
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from adcm.utils import get_obj_type


# pylint: disable-next=too-many-locals,too-many-branches,too-many-statements
def config_case(
    path: list[str],
    view: ViewSet,
    response: Response,
    deleted_obj: GroupConfig,
) -> tuple[AuditOperation, AuditObject | None, str | None]:
    audit_operation = None
    audit_object = None
    operation_name = None

    match path:
        case ["config-log"]:
            audit_operation = AuditOperation(
                name=f"configuration {AuditLogOperationType.UPDATE}d",
                operation_type=AuditLogOperationType.UPDATE,
            )

            config = None
            if response:
                config = response.data.serializer.instance.obj_ref
            elif view.request.data.get("obj_ref"):
                config = ObjectConfig.objects.filter(pk=view.request.data["obj_ref"]).first()

            if config:
                object_type = ContentType.objects.get_for_model(config.object).name
                object_type = get_obj_type(obj_type=object_type)
                object_name = get_obj_name(obj=config.object, obj_type=object_type)

                audit_object = get_or_create_audit_obj(
                    object_id=config.object.pk,
                    object_name=object_name,
                    object_type=object_type,
                )
                if object_type == "adcm":
                    object_type = "ADCM"
                else:
                    object_type = object_type.capitalize()

                operation_name = f"{object_type} {audit_operation.name}"
            else:
                audit_object = None

        case ["group-config", group_config_pk, "config", _, "config-log"]:
            audit_operation = AuditOperation(
                name=f"configuration group {AuditLogOperationType.UPDATE}d",
                operation_type=AuditLogOperationType.UPDATE,
            )

            config = None
            if response:
                config = response.data.serializer.instance.obj_ref
                if getattr(config, "group_config", None):
                    config = config.group_config
            elif view.request.data.get("obj_ref"):
                config = ObjectConfig.objects.filter(pk=view.request.data["obj_ref"]).first()

            if not config:
                config = GroupConfig.objects.filter(pk=group_config_pk).first()

            if config:
                object_type = ContentType.objects.get_for_model(config.object).name
                object_type = get_obj_type(object_type)
                object_name = get_obj_name(obj=config.object, obj_type=object_type)

                audit_object = get_or_create_audit_obj(
                    object_id=config.object.pk,
                    object_name=object_name,
                    object_type=object_type,
                )
                object_type = object_type.capitalize()
                if isinstance(config, GroupConfig):
                    object_type = config.name

                operation_name = f"{object_type} {audit_operation.name}"
            else:
                audit_object = None

        case [*_, "group-config"] | [*_, "config-groups"] | [*_, "config-groups", _]:
            is_deleted = False
            if view.action == "create":
                operation_type = AuditLogOperationType.CREATE
            elif view.action in {"update", "partial_update"}:
                operation_type = AuditLogOperationType.UPDATE
            else:
                operation_type = AuditLogOperationType.DELETE
                is_deleted = True

            audit_operation = AuditOperation(
                name=f"configuration group {operation_type}d",
                operation_type=operation_type,
            )
            if response:
                if view.action == "destroy":
                    deleted_obj: GroupConfig
                    obj = deleted_obj
                else:
                    obj = response.data.serializer.instance

                object_type = get_obj_type(obj.object_type.name)
                object_name = get_obj_name(obj=obj.object, obj_type=object_type)
                audit_object = get_or_create_audit_obj(
                    object_id=obj.object.id,
                    object_name=object_name,
                    object_type=object_type,
                )
                audit_object.is_deleted = is_deleted
                audit_object.save()
                operation_name = f"{obj.name} {audit_operation.name}"
            else:
                audit_object = None

        case ["group-config", group_config_pk] | ["config-groups", group_config_pk]:
            if view.action in {"update", "partial_update"}:
                operation_type = AuditLogOperationType.UPDATE
            else:
                operation_type = AuditLogOperationType.DELETE

            audit_operation = AuditOperation(
                name=f"configuration group {operation_type}d",
                operation_type=operation_type,
            )
            if response:
                if view.action == "destroy":
                    deleted_obj: GroupConfig
                    obj = deleted_obj
                else:
                    obj = response.data.serializer.instance
            else:
                obj = GroupConfig.objects.filter(pk=group_config_pk).first()

            if obj:
                object_type = get_obj_type(obj.object_type.name)
                object_name = get_obj_name(obj=obj.object, obj_type=object_type)
                audit_object = get_or_create_audit_obj(
                    object_id=obj.object.id,
                    object_name=object_name,
                    object_type=object_type,
                )
                operation_name = f"{obj.name} {audit_operation.name}"
            else:
                audit_object = None

        case ["group-config", config_group_pk, "host"] | ["config-groups", config_group_pk, "hosts"]:
            config_group = GroupConfig.objects.get(pk=config_group_pk)
            audit_operation = AuditOperation(
                name=f"host added to {config_group.name} configuration group",
                operation_type=AuditLogOperationType.UPDATE,
            )
            object_type = get_obj_type(config_group.object_type.name)
            object_name = get_obj_name(obj=config_group.object, obj_type=object_type)
            audit_object = get_or_create_audit_obj(
                object_id=config_group.object.pk,
                object_name=object_name,
                object_type=object_type,
            )

            fqdn = None
            if response:
                fqdn = response.data["fqdn"]
            elif "id" in view.request.data:
                host = Host.objects.filter(pk=view.request.data["id"]).first()
                if host:
                    fqdn = host.fqdn

            if fqdn:
                audit_operation.name = f"{fqdn} {audit_operation.name}"

        case [*_, obj_type, obj_pk, "config-groups", config_group_pk, "hosts"]:
            config_group = GroupConfig.objects.filter(pk=config_group_pk).first()
            config_group_name = config_group.name if config_group else ""
            audit_operation = AuditOperation(
                name=f"host added to {config_group_name} configuration group",
                operation_type=AuditLogOperationType.UPDATE,
            )
            obj = PATH_STR_TO_OBJ_CLASS_MAP[obj_type].objects.filter(pk=obj_pk).first()
            if obj:
                object_type = MODEL_TO_AUDIT_OBJECT_TYPE_MAP[PATH_STR_TO_OBJ_CLASS_MAP[obj_type]]
                audit_object = get_or_create_audit_obj(
                    object_id=obj_pk,
                    object_name=get_obj_name(obj=obj, obj_type=object_type),
                    object_type=object_type,
                )
            fqdn = None
            if "host_id" in view.request.data:
                host = Host.objects.filter(pk=view.request.data["host_id"]).first()
                if host:
                    fqdn = host.fqdn

            if fqdn:
                audit_operation.name = f"{fqdn} {audit_operation.name}"

        case ["group-config", config_group_pk, "host", host_pk] | ["config-groups", config_group_pk, "hosts", host_pk]:
            config_group = GroupConfig.objects.get(pk=config_group_pk)
            obj = Host.objects.get(pk=host_pk)
            audit_operation = AuditOperation(
                name=f"{obj.fqdn} host removed from {config_group.name} configuration group",
                operation_type=AuditLogOperationType.UPDATE,
            )
            object_type = get_obj_type(config_group.object_type.name)
            object_name = get_obj_name(obj=config_group.object, obj_type=object_type)
            audit_object = get_or_create_audit_obj(
                object_id=config_group.object.pk,
                object_name=object_name,
                object_type=object_type,
            )
        case [*_, obj_type, obj_pk, "config-groups", pk, "configs"]:
            operation_type = AuditLogOperationType.UPDATE
            audit_operation = AuditOperation(
                name=f"configuration group {operation_type}d",
                operation_type=operation_type,
            )
            group_config = GroupConfig.objects.filter(pk=pk).first()
            operation_name = f"{group_config.name} {audit_operation.name}" if group_config else audit_operation.name
            obj = PATH_STR_TO_OBJ_CLASS_MAP[obj_type].objects.filter(pk=obj_pk).first()
            if obj:
                object_type = MODEL_TO_AUDIT_OBJECT_TYPE_MAP[PATH_STR_TO_OBJ_CLASS_MAP[obj_type]]
                audit_object = get_or_create_audit_obj(
                    object_id=obj_pk,
                    object_name=get_obj_name(obj=obj, obj_type=object_type),
                    object_type=object_type,
                )

    return audit_operation, audit_object, operation_name
