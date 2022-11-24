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

from django.conf import settings
from django.core.validators import RegexValidator
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    HyperlinkedIdentityField,
    IntegerField,
    JSONField,
    ModelSerializer,
    SerializerMethodField,
)
from rest_framework.validators import UniqueValidator

from adcm.serializers import EmptySerializer
from api.action.serializers import ActionShort
from api.component.serializers import ComponentShortSerializer
from api.concern.serializers import ConcernItemSerializer, ConcernItemUISerializer
from api.group_config.serializers import GroupConfigsHyperlinkedIdentityField
from api.host.serializers import HostSerializer
from api.serializers import DoUpgradeSerializer
from api.utils import UrlField, check_obj, filter_actions
from cm.adcm_config import get_main_info
from cm.api import add_hc, bind, multi_bind
from cm.errors import AdcmEx
from cm.models import Action, Cluster, Host, Prototype, ServiceComponent
from cm.status_api import get_cluster_status, get_hc_status
from cm.upgrade import get_upgrade


class ClusterSerializer(ModelSerializer):
    prototype_id = IntegerField(read_only=False, required=True)
    name = CharField(
        min_length=2,
        max_length=80,
        validators=[
            UniqueValidator(queryset=Cluster.objects.all()),
            RegexValidator(regex=settings.CLUSTER_NAME_REGEX),
        ],
        required=True,
    )

    class Meta:
        model = Cluster
        fields = (
            "id",
            "prototype_id",
            "name",
            "description",
            "state",
            "before_upgrade",
        )
        extra_kwargs = {"url": {"lookup_url_kwarg": "cluster_id"}}


class ClusterUISerializer(ModelSerializer):
    action = HyperlinkedIdentityField(view_name="object-action", lookup_url_kwarg="cluster_id")
    prototype_version = CharField(source="prototype.version")
    prototype_name = CharField(source="prototype.name")
    prototype_display_name = CharField(source="prototype.display_name")
    upgrade = HyperlinkedIdentityField(view_name="cluster-upgrade", lookup_url_kwarg="cluster_id")
    upgradable = SerializerMethodField()
    concerns = ConcernItemUISerializer(many=True, read_only=True)
    status = SerializerMethodField()

    class Meta:
        model = Cluster
        fields = (
            *ClusterSerializer.Meta.fields,
            "action",
            "edition",
            "prototype_version",
            "prototype_name",
            "prototype_display_name",
            "upgrade",
            "upgradable",
            "concerns",
            "status",
        )
        extra_kwargs = {"url": {"lookup_url_kwarg": "cluster_id"}}

    @staticmethod
    def get_upgradable(obj: Cluster) -> bool:
        return bool(get_upgrade(obj))

    @staticmethod
    def get_status(obj: Cluster) -> int:
        return get_cluster_status(obj)


class ClusterDetailSerializer(ModelSerializer):
    action = HyperlinkedIdentityField(view_name="object-action", lookup_url_kwarg="cluster_id")
    service = HyperlinkedIdentityField(view_name="service", lookup_url_kwarg="cluster_id")
    host = HyperlinkedIdentityField(view_name="host", lookup_url_kwarg="cluster_id")
    hostcomponent = HyperlinkedIdentityField(
        view_name="host-component", lookup_field="id", lookup_url_kwarg="cluster_id"
    )
    status = SerializerMethodField()
    status_url = HyperlinkedIdentityField(view_name="cluster-status", lookup_url_kwarg="cluster_id")
    config = HyperlinkedIdentityField(view_name="object-config", lookup_url_kwarg="cluster_id")
    serviceprototype = HyperlinkedIdentityField(view_name="cluster-service-prototype", lookup_url_kwarg="cluster_id")
    upgrade = HyperlinkedIdentityField(view_name="cluster-upgrade", lookup_url_kwarg="cluster_id")
    imports = HyperlinkedIdentityField(view_name="cluster-import", lookup_url_kwarg="cluster_id")
    bind = HyperlinkedIdentityField(view_name="cluster-bind", lookup_url_kwarg="cluster_id")
    prototype = HyperlinkedIdentityField(view_name="cluster-prototype-detail", lookup_url_kwarg="prototype_pk")
    concerns = ConcernItemSerializer(many=True, read_only=True)
    group_config = GroupConfigsHyperlinkedIdentityField(view_name="group-config-list")

    class Meta:
        model = Cluster
        fields = (
            *ClusterSerializer.Meta.fields,
            "bundle_id",
            "edition",
            "license",
            "action",
            "service",
            "host",
            "status",
            "concerns",
            "status",
            "status_url",
            "config",
            "serviceprototype",
            "upgrade",
            "imports",
            "bind",
            "prototype",
            "multi_state",
            "concerns",
            "group_config",
        )
        extra_kwargs = {"url": {"lookup_url_kwarg": "cluster_id"}}

    @staticmethod
    def get_status(obj: Cluster) -> int:
        return get_cluster_status(obj)


class ClusterDetailUISerializer(ModelSerializer):
    actions = SerializerMethodField()
    prototype_version = CharField(source="prototype.version")
    prototype_name = CharField(source="prototype.name")
    prototype_display_name = CharField(source="prototype.display_name")
    upgradable = SerializerMethodField()
    concerns = ConcernItemUISerializer(many=True, read_only=True)
    main_info = SerializerMethodField()

    class Meta:
        model = Cluster
        fields = (
            *ClusterDetailSerializer.Meta.fields,
            "actions",
            "prototype_version",
            "prototype_name",
            "prototype_display_name",
            "upgradable",
            "concerns",
            "main_info",
        )
        extra_kwargs = {"url": {"lookup_url_kwarg": "cluster_id"}}

    def get_actions(self, obj: Cluster):
        self.context["object"] = obj
        self.context["cluster_id"] = obj.id

        return ActionShort(
            filter_actions(obj, Action.objects.filter(prototype=obj.prototype)), many=True, context=self.context
        ).data

    @staticmethod
    def get_upgradable(obj: Cluster) -> bool:
        return bool(get_upgrade(obj))

    @staticmethod
    def get_main_info(obj: Cluster) -> str | None:
        return get_main_info(obj)


class ClusterUpdateSerializer(ModelSerializer):
    name = CharField(
        min_length=2,
        max_length=80,
        validators=[
            UniqueValidator(queryset=Cluster.objects.all()),
            RegexValidator(regex=settings.CLUSTER_NAME_REGEX),
        ],
    )

    class Meta:
        model = Cluster
        fields = (
            "id",
            "name",
            "description",
        )

    def validate_name(self, value: str) -> str:
        if self.instance.state != "created" and self.instance.name != value:
            raise ValidationError("Name change is available only in the 'created' state")

        return value


class StatusSerializer(EmptySerializer):
    id = IntegerField(read_only=True)
    component_id = IntegerField(read_only=True)
    service_id = IntegerField(read_only=True)
    state = CharField(read_only=True, required=False)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["component"] = instance.component.prototype.name
        data["component_display_name"] = instance.component.prototype.display_name
        data["host"] = instance.host.fqdn
        data["service_name"] = instance.service.prototype.name
        data["service_display_name"] = instance.service.prototype.display_name
        data["service_version"] = instance.service.prototype.version
        data["monitoring"] = instance.component.prototype.monitoring
        status = get_hc_status(instance)
        data["status"] = status

        return data


class HostComponentSerializer(EmptySerializer):
    class MyUrlField(UrlField):
        def get_kwargs(self, obj):
            return {
                "cluster_id": obj.cluster.id,
                "hs_id": obj.id,
            }

    id = IntegerField(read_only=True)
    host_id = IntegerField(help_text="host id")
    host = CharField(read_only=True)
    service_id = IntegerField()
    component = CharField(help_text="component name")
    component_id = IntegerField(read_only=True, help_text="component id")
    state = CharField(read_only=True, required=False)
    url = MyUrlField(read_only=True, view_name="host-comp-details")
    host_url = HyperlinkedIdentityField(view_name="host-details", lookup_field="host_id", lookup_url_kwarg="host_id")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["component"] = instance.component.prototype.name
        data["component_display_name"] = instance.component.prototype.display_name
        data["host"] = instance.host.fqdn
        data["service_name"] = instance.service.prototype.name
        data["service_display_name"] = instance.service.prototype.display_name
        data["service_version"] = instance.service.prototype.version

        return data


class HostComponentUISerializer(EmptySerializer):
    hc = HostComponentSerializer(many=True, read_only=True)
    host = SerializerMethodField()
    component = SerializerMethodField()

    def get_host(self, obj):
        hosts = Host.objects.filter(cluster=self.context.get("cluster"))

        return HostSerializer(hosts, many=True, context=self.context).data

    def get_component(self, obj):
        comps = ServiceComponent.objects.filter(cluster=self.context.get("cluster"))

        return HCComponentSerializer(comps, many=True, context=self.context).data


class HostComponentSaveSerializer(EmptySerializer):
    hc = JSONField()

    @staticmethod
    def validate_hc(hc):
        if not hc:
            raise AdcmEx("INVALID_INPUT", "hc field is required")

        if not isinstance(hc, list):
            raise AdcmEx("INVALID_INPUT", "hc field should be a list")

        for item in hc:
            for key in ("component_id", "host_id", "service_id"):
                if key not in item:
                    msg = '"{}" sub-field is required'

                    raise AdcmEx("INVALID_INPUT", msg.format(key))

        return hc

    def create(self, validated_data):
        hc = validated_data.get("hc")

        return add_hc(self.context.get("cluster"), hc)


class HCComponentSerializer(ComponentShortSerializer):
    service_id = IntegerField(read_only=True)
    service_name = SerializerMethodField()
    service_display_name = SerializerMethodField()
    service_state = SerializerMethodField()
    requires = SerializerMethodField()

    @staticmethod
    def get_service_state(obj):
        return obj.service.state

    @staticmethod
    def get_service_name(obj):
        return obj.service.prototype.name

    @staticmethod
    def get_service_display_name(obj):
        return obj.service.prototype.display_name

    @staticmethod
    def get_requires(obj):
        if not obj.prototype.requires:
            return None

        comp_list = {}

        def process_requires(req_list):
            for c in req_list:
                _comp = Prototype.obj.get(
                    type="component",
                    name=c["component"],
                    parent__name=c["service"],
                    parent__bundle_id=obj.prototype.bundle_id,
                )
                if _comp == obj.prototype:
                    return

                if _comp.name not in comp_list:
                    comp_list[_comp.name] = {"components": {}, "service": _comp.parent}

                if _comp.name in comp_list[_comp.name]["components"]:
                    return

                comp_list[_comp.name]["components"][_comp.name] = _comp
                if _comp.requires:
                    process_requires(_comp.requires)

        process_requires(obj.requires)
        out = []
        for service_name, params in comp_list.items():
            comp_out = []
            service = params["service"]
            for comp_name in params["components"]:
                comp = params["components"][comp_name]
                comp_out.append(
                    {
                        "prototype_id": comp.id,
                        "name": comp_name,
                        "display_name": comp.display_name,
                    }
                )

            if not comp_out:
                continue

            out.append(
                {
                    "prototype_id": service.id,
                    "name": service_name,
                    "display_name": service.display_name,
                    "components": comp_out,
                }
            )

        return out


class BindSerializer(EmptySerializer):
    id = IntegerField(read_only=True)
    export_cluster_id = IntegerField(read_only=True, source="source_cluster_id")
    export_cluster_name = CharField(read_only=True, source="source_cluster")
    export_cluster_prototype_name = SerializerMethodField()
    export_service_id = SerializerMethodField()
    export_service_name = SerializerMethodField()
    import_service_id = SerializerMethodField()
    import_service_name = SerializerMethodField()

    @staticmethod
    def get_export_cluster_prototype_name(obj):
        return obj.source_cluster.prototype.name

    @staticmethod
    def get_export_service_name(obj):
        if obj.source_service:
            return obj.source_service.prototype.name

        return None

    @staticmethod
    def get_export_service_id(obj):
        if obj.source_service:
            return obj.source_service.id

        return None

    @staticmethod
    def get_import_service_id(obj):
        if obj.service:
            return obj.service.id

        return None

    @staticmethod
    def get_import_service_name(obj):
        if obj.service:
            return obj.service.prototype.name

        return None


class ClusterBindSerializer(BindSerializer):
    class MyUrlField(UrlField):
        def get_kwargs(self, obj):
            return {"bind_id": obj.id, "cluster_id": obj.cluster.id}

    url = MyUrlField(read_only=True, view_name="cluster-bind-details")


class DoBindSerializer(EmptySerializer):
    id = IntegerField(read_only=True)
    export_cluster_id = IntegerField()
    export_service_id = IntegerField(required=False, allow_null=True)
    export_cluster_name = CharField(read_only=True)
    export_cluster_prototype_name = CharField(read_only=True)

    def create(self, validated_data):
        export_cluster = check_obj(Cluster, validated_data.get("export_cluster_id"))

        return bind(
            validated_data.get("cluster"),
            None,
            export_cluster,
            validated_data.get("export_service_id", 0),
        )


class PostImportSerializer(EmptySerializer):
    bind = JSONField()

    def create(self, validated_data):
        bind_data = validated_data.get("bind")
        cluster = self.context.get("cluster")
        service = self.context.get("service")

        return multi_bind(cluster, service, bind_data)


class DoClusterUpgradeSerializer(DoUpgradeSerializer):
    hc = JSONField(required=False, default=list)


class ClusterAuditSerializer(ModelSerializer):
    name = CharField(max_length=80, required=False)
    description = CharField(required=False)

    class Meta:
        model = Cluster
        fields = (
            "name",
            "description",
        )
