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

from adcm.serializers import EmptySerializer
from cm.adcm_config.config import get_main_info
from cm.models import (
    Cluster,
    ClusterObject,
    Host,
    HostComponent,
    Prototype,
    ServiceComponent,
)
from cm.upgrade import get_upgrade
from cm.validators import ClusterUniqueValidator, StartMidEndValidator
from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import (
    BooleanField,
    ModelSerializer,
    SerializerMethodField,
)

from api_v2.cluster.utils import get_depend_on
from api_v2.concern.serializers import ConcernSerializer
from api_v2.prototype.serializers import LicenseSerializer, PrototypeRelatedSerializer
from api_v2.prototype.utils import get_license_text
from api_v2.serializers import DependOnSerializer, WithStatusSerializer


class ClusterSerializer(WithStatusSerializer):
    prototype = PrototypeRelatedSerializer()
    concerns = ConcernSerializer(many=True, read_only=True)
    is_upgradable = SerializerMethodField()
    main_info = SerializerMethodField()

    class Meta:
        model = Cluster
        fields = [
            "id",
            "name",
            "description",
            "state",
            "multi_state",
            "status",
            "prototype",
            "description",
            "concerns",
            "is_upgradable",
            "main_info",
        ]

    @staticmethod
    def get_is_upgradable(cluster: Cluster) -> bool:
        return bool(get_upgrade(obj=cluster))

    @staticmethod
    def get_main_info(cluster: Cluster) -> str | None:
        return get_main_info(obj=cluster)


class ClusterRelatedSerializer(ModelSerializer):
    class Meta:
        model = Cluster
        fields = ["id", "name"]


class ClusterCreateSerializer(EmptySerializer):
    prototype_id = IntegerField()
    name = CharField(
        min_length=2,
        max_length=150,
        trim_whitespace=False,
        validators=[
            ClusterUniqueValidator(queryset=Cluster.objects.all()),
            StartMidEndValidator(
                start=settings.ALLOWED_CLUSTER_NAME_START_END_CHARS,
                mid=settings.ALLOWED_CLUSTER_NAME_MID_CHARS,
                end=settings.ALLOWED_CLUSTER_NAME_START_END_CHARS,
                err_code="BAD_REQUEST",
                err_msg="Wrong cluster name.",
            ),
        ],
    )
    description = CharField(required=False, allow_blank=True, default="")


class ClusterUpdateSerializer(ModelSerializer):
    name = CharField(
        min_length=2,
        max_length=150,
        trim_whitespace=False,
        validators=[
            ClusterUniqueValidator(queryset=Cluster.objects.all()),
            StartMidEndValidator(
                start=settings.ALLOWED_CLUSTER_NAME_START_END_CHARS,
                mid=settings.ALLOWED_CLUSTER_NAME_MID_CHARS,
                end=settings.ALLOWED_CLUSTER_NAME_START_END_CHARS,
                err_code="BAD_REQUEST",
                err_msg="Wrong cluster name.",
            ),
        ],
        required=False,
        help_text="Cluster name",
    )

    class Meta:
        model = Cluster
        fields = ["name", "description"]


class ClusterAuditSerializer(ModelSerializer):
    name = CharField(max_length=80, required=False)

    class Meta:
        model = Cluster
        fields = ("name", "description")


class ServicePrototypeSerializer(ModelSerializer):
    is_required = BooleanField(source="required")
    depend_on = SerializerMethodField()
    license = SerializerMethodField()

    class Meta:
        model = Prototype
        fields = ["id", "name", "display_name", "version", "is_required", "depend_on", "license"]

    @staticmethod
    @extend_schema_field(field=DependOnSerializer(many=True))
    def get_depend_on(prototype: Prototype) -> list[dict] | None:
        if prototype.requires:
            return get_depend_on(prototype=prototype)

        return None

    @staticmethod
    @extend_schema_field(field=LicenseSerializer)
    def get_license(prototype: Prototype) -> dict:
        return {
            "status": prototype.license,
            "text": get_license_text(
                license_path=prototype.license_path,
                bundle_hash=prototype.bundle.hash,
            ),
        }


class SetMappingSerializer(EmptySerializer):
    host_id = IntegerField()
    component_id = IntegerField()


class MappingSerializer(ModelSerializer):
    host_id = IntegerField()
    component_id = IntegerField()

    class Meta:
        model = HostComponent
        fields = ["id", "host_id", "component_id"]
        extra_kwargs = {"id": {"read_only": True}}


class RelatedComponentStatusSerializer(WithStatusSerializer):
    class Meta:
        model = ServiceComponent
        fields = ["id", "name", "display_name", "status"]


class RelatedServicesStatusesSerializer(WithStatusSerializer):
    components = RelatedComponentStatusSerializer(many=True, source="servicecomponent_set")

    class Meta:
        model = ClusterObject
        fields = ["id", "name", "display_name", "status", "components"]


class RelatedHostsStatusesSerializer(WithStatusSerializer):
    class Meta:
        model = Host
        fields = ["id", "name", "status"]


class ClusterStatusSerializer(WithStatusSerializer):
    class Meta:
        model = Cluster
        fields = ["id", "name", "state", "status"]
