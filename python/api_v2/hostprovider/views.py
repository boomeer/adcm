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

from api_v2.hostprovider.filters import HostProviderFilter
from api_v2.hostprovider.serializers import (
    HostProviderCreateSerializer,
    HostProviderSerializer,
)
from api_v2.views import CamelCaseReadOnlyModelViewSet
from cm.api import add_host_provider, delete_host_provider
from cm.models import HostProvider, ObjectType, Prototype
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_409_CONFLICT,
)

from adcm.permissions import VIEW_HOST_PERM, DjangoModelPermissionsAudit


class HostProviderViewSet(CamelCaseReadOnlyModelViewSet):  # pylint:disable=too-many-ancestors
    queryset = HostProvider.objects.select_related("prototype").order_by("name")
    serializer_class = HostProviderSerializer
    permission_classes = [DjangoModelPermissionsAudit]
    permission_required = [VIEW_HOST_PERM]
    filterset_class = HostProviderFilter
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.action == "create":
            return HostProviderCreateSerializer

        return self.serializer_class

    def create(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_409_CONFLICT)

        host_provider = add_host_provider(
            prototype=Prototype.objects.get(pk=serializer.validated_data["prototype_id"], type=ObjectType.PROVIDER),
            name=serializer.validated_data["name"],
            description=serializer.validated_data["description"],
        )

        return Response(data=HostProviderSerializer(host_provider).data, status=HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        host_provider = self.get_object()
        delete_host_provider(host_provider)
        return Response(status=HTTP_204_NO_CONTENT)
