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

from rest_framework.fields import CharField

from adcm.serializers import EmptySerializer


class LoginSerializer(EmptySerializer):
    username = CharField(write_only=True)
    password = CharField(style={"input_type": "password"}, trim_whitespace=False, write_only=True)
