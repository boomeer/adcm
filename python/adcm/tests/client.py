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

from abc import ABC, abstractmethod
from itertools import chain
from typing import Protocol

from cm.models import Bundle, Cluster, ClusterObject, GroupConfig, Host, HostProvider, JobLog, ServiceComponent, TaskLog
from rest_framework.response import Response
from rest_framework.test import APIClient

PathObject = Bundle | Cluster | ClusterObject | ServiceComponent | HostProvider | Host | TaskLog | JobLog | GroupConfig


class WithID(Protocol):
    id: int


class APINode:
    __slots__ = ("_client", "_path", "_resolved_path")

    def __init__(self, *path: str, client: APIClient):
        self._client = client
        self._path = tuple(path)
        self._resolved_path = None

    def __truediv__(self, other: str | int | WithID):
        if isinstance(other, (str, int)):
            return APINode(*self._path, str(other), client=self._client)

        return APINode(*self._path, str(other.id), client=self._client)

    @property
    def path(self) -> str:
        if self._resolved_path:
            return self._resolved_path

        cleaned_path_parts = filter(bool, chain.from_iterable(sub_path.split("/") for sub_path in self._path))
        self._resolved_path = f"/{'/'.join(cleaned_path_parts)}/"

        return self._resolved_path

    def get(self, *, query: dict | None = None) -> Response:
        return self._client.get(path=self.path, data=query)

    def post(self, *, data: dict | list[dict]) -> Response:
        return self._client.post(path=self.path, data=data)

    def patch(self, *, data: dict) -> Response:
        return self._client.patch(path=self.path, data=data)

    def delete(self) -> Response:
        return self._client.delete(path=self.path)


class RootNode(APINode, ABC):
    @abstractmethod
    def __getitem__(self, item) -> APINode:
        ...


class V2RootNode(RootNode):
    _CLASS_ROOT_EP_MAP = {
        Bundle: "bundles",
        Cluster: "clusters",
        HostProvider: "hostproviders",
        Host: "hosts",
        TaskLog: "tasks",
        JobLog: "jobs",
    }

    def __getitem__(self, item: PathObject | tuple[PathObject, str | int | WithID, ...]) -> APINode:
        if isinstance(item, tuple):
            path_object, *tail_ = item
            tail = tuple(str(entry) if isinstance(entry, (str, int)) else str(entry.id) for entry in tail_)
        else:
            path_object, tail = item, ()

        root_endpoint = self._CLASS_ROOT_EP_MAP.get(path_object.__class__)
        if root_endpoint:
            return APINode(*self._path, root_endpoint, str(path_object.id), *tail, client=self._client)

        if isinstance(path_object, ClusterObject):
            return APINode(
                *self._path,
                "clusters",
                str(path_object.cluster_id),
                "services",
                str(path_object.id),
                *tail,
                client=self._client,
            )

        if isinstance(path_object, ServiceComponent):
            return APINode(
                *self._path,
                "clusters",
                str(path_object.cluster_id),
                "services",
                str(path_object.service_id),
                "components",
                str(path_object.id),
                *tail,
                client=self._client,
            )

        if isinstance(path_object, GroupConfig):
            # generally it's move clean and obvious when multiple `/` is used, but in here it looks like an overkill
            return self[path_object.object] / "/".join(("config-groups", str(path_object.id), *tail))

        message = f"Node auto-detection isn't defined for {path_object.__class__}"
        raise NotImplementedError(message)


class ADCMTestClient(APIClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.v2 = V2RootNode("api", "v2", client=self)
