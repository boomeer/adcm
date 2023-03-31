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

from cm.api import add_hc, add_service_to_cluster
from cm.errors import AdcmEx
from cm.models import Bundle, Cluster, Host, Prototype, ServiceComponent

from adcm.tests.base import BaseTestCase


class TestComponent(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.bundle = Bundle.objects.create()
        self.cluster = Cluster.objects.create(
            prototype=Prototype.objects.create(bundle=self.bundle, type="cluster"),
            name="test_cluster",
        )
        self.service_proto_1 = Prototype.objects.create(
            bundle=self.bundle,
            name="service_1",
            type="service",
        )
        self.service_proto_2 = Prototype.objects.create(
            bundle=self.bundle,
            name="service_2",
            type="service",
            requires=[{"service": "service_1", "component": "component_1_1"}, {"service": "service_3"}],
        )
        self.service_proto_3 = Prototype.objects.create(
            bundle=self.bundle,
            name="service_3",
            type="service",
        )
        self.component_1_1_proto = Prototype.objects.create(
            bundle=self.bundle,
            type="component",
            parent=self.service_proto_1,
            name="component_1_1",
            requires=[{"service": "service_1", "component": "component_1_1"}, {"service": "service_2"}],
        )
        self.component_2_1_proto = Prototype.objects.create(
            bundle=self.bundle,
            type="component",
            parent=self.service_proto_2,
            name="component_2_1",
            requires=[{"service": "service_1", "component": "component_1_1"}, {"service": "service_2"}],
        )

    def test_service_requires(self):
        with self.assertRaisesRegex(AdcmEx, 'No required component "component_1_1"  for service "service_2"'):
            add_service_to_cluster(cluster=self.cluster, proto=self.service_proto_2)

        add_service_to_cluster(cluster=self.cluster, proto=self.service_proto_1)
        with self.assertRaisesRegex(AdcmEx, 'No required service "service_3"  for service "service_2"'):
            add_service_to_cluster(cluster=self.cluster, proto=self.service_proto_2)

        add_service_to_cluster(cluster=self.cluster, proto=self.service_proto_3)
        add_service_to_cluster(cluster=self.cluster, proto=self.service_proto_2)

    def test_requires_hc(self):
        service_1 = add_service_to_cluster(cluster=self.cluster, proto=self.service_proto_1)
        component_1 = ServiceComponent.objects.get(prototype=self.component_1_1_proto, service=service_1)
        host = Host.objects.create(
            prototype=Prototype.objects.create(type="host", bundle=self.bundle), cluster=self.cluster
        )

        with self.assertRaisesRegex(
            AdcmEx, 'No required service service_2 for component "component_1_1" of service "service_1"'
        ):
            add_hc(self.cluster, [{"host_id": host.id, "service_id": service_1.id, "component_id": component_1.id}])