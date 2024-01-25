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

from django.urls import include, path

from api_ui import views

urlpatterns = [
    path("", views.APIRoot.as_view()),
    path("rbac/", include(("rbac.urls_ui", "rbac"), namespace="rbac-ui")),
    path("stack/", include(("api_ui.stack.urls", "api_ui"), namespace="stack-ui")),
]
