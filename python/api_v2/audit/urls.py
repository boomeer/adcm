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
from api_v2.audit.views import AuditLogViewSet, AuditSessionViewSet
from audit.views import AuditRoot
from django.urls import path
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register("operations", AuditLogViewSet)
router.register("logins", AuditSessionViewSet)
urlpatterns = [path("", AuditRoot.as_view(), name="root"), *router.urls]