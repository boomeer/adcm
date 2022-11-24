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
import string

from django.urls import reverse
from rest_framework import status

from adcm.tests.base import APPLICATION_JSON, BaseTestCase
from cm.models import Bundle, Cluster, Prototype
from init_db import init


class TestCluster(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        init()

        self.allowed_name_chars_start_end = f"{string.ascii_letters}{string.digits}"
        self.allowed_name_chars_middle = f"{self.allowed_name_chars_start_end}-. _"

        self.valid_names = (
            "letters",
            "all-12 to.ge--t_he r",
            "Just cluster namE",
            "Another.clus-ter",
            "endswithdigit4",
            "1startswithdigit",
            "contains_underscore",
        )
        self.invalid_names = (
            "-starts with hyphen",
            ".starts with dot",
            "_starts with underscore",
            "Ends with hyphen-",
            "Ends with dot.",
            "Ends with underscore_",
        ) + tuple(f"forbidden{c}char" for c in set(string.punctuation) - set(self.allowed_name_chars_middle))

        self.bundle = Bundle.objects.create()
        self.prototype = Prototype.objects.create(name="test_prototype_name", type="cluster", bundle=self.bundle)
        self.cluster = Cluster.objects.create(name="test_cluster_name", prototype=self.prototype)

    def test_cluster_name_update_in_different_states(self):
        state_created = "created"
        state_another = "another state"
        valid_name = self.valid_names[0]
        url = reverse("cluster-detail", kwargs={"cluster_pk": self.cluster.pk})

        self.cluster.state = state_created
        self.cluster.save()

        with self.another_user_logged_in(username="admin", password="admin"):
            for method in ("patch", "put"):
                response = getattr(self.client, method)(
                    path=url, data={"name": valid_name}, content_type=APPLICATION_JSON
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json()["name"], valid_name)

            self.cluster.state = state_another
            self.cluster.save()

            for method in ("patch", "put"):
                response = getattr(self.client, method)(
                    path=url, data={"name": valid_name}, content_type=APPLICATION_JSON
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
