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

"""Endpoint data classes definition"""
# pylint: disable=too-few-public-methods

from abc import ABC
from typing import List

from tests.api.utils.tools import PARAMETRIZED_BY_LIST
from tests.api.utils.types import (
    Field,
    PositiveInt,
    String,
    Text,
    Json,
    Enum,
    ForeignKey,
    BackReferenceFK,
    DateTime,
    Relation,
    Boolean,
    ForeignKeyM2M,
    Email,
    ListOf,
    Password,
    EmptyList,
    GenericForeignKeyList,
    StaticBoolean,
    ObjectForeignKey,
    Username,
)


class BaseClass(ABC):
    """Base data class"""

    # List of BaseClass that are NOT included in POST method for current Class
    # but should exist before data preparation
    # and creation of current object
    predefined_dependencies: List["BaseClass"] = []

    # List of BaseClass that are NOT included in POST method for current Class
    # and should be generated implicitly after data preparation
    # and creation of current object
    implicitly_depends_on: List["BaseClass"] = []


class ClusterFields(BaseClass):
    """
    Data type class for Cluster object
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    name = Field(name="name", f_type=String(max_length=255))


class ServiceFields(BaseClass):
    """
    Data type class for Service object
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    name = Field(name="name", f_type=String(max_length=255))


class ComponentFields(BaseClass):
    """
    Data type class for Component object
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    name = Field(name="name", f_type=String(max_length=255))


class ProviderFields(BaseClass):
    """
    Data type class for Provider object
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    name = Field(name="name", f_type=String(max_length=255))


class HostFields(BaseClass):
    """
    Data type class for Host object
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    fqdn = Field(name="fqdn", f_type=String(max_length=255))


class ObjectConfigFields(BaseClass):
    """
    Data type class for ObjectConfig object
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    url = Field(name="url", f_type=String(), default_value="auto")


class GroupConfigFields(BaseClass):
    """
    Data type class for Config Group object
    https://spec.adsw.io/adcm_core/objects.html#group
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    object_type = Field(
        name="object_type",
        f_type=Enum(enum_values=["cluster", "service", "component", "provider"]),
        required=True,
        postable=True,
    )
    object_id = Field(
        name="object_id",
        f_type=ForeignKey(relates_on=Relation(field=object_type)),
        required=True,
        postable=True,
    )
    name = Field(name="name", f_type=String(max_length=30), required=True, postable=True, changeable=True)
    description = Field(name="description", f_type=Text(), postable=True, changeable=True, default_value="")
    config = Field(
        name="config",
        f_type=ForeignKey(fk_link=ObjectConfigFields),
        default_value="auto",
    )
    config_id = Field(name='config_id', f_type=PositiveInt(), default_value="auto", nullable=True)
    host_candidate = Field(
        # Link to host candidates url for this object. Auto-filled when group-config object creates
        # Candidates list depends on ADCM object for which group-config was created.
        name="host_candidate",
        f_type=String(),
        default_value="auto",
    )
    url = Field(name="url", f_type=String(), default_value="auto")


class ConfigLogFields(BaseClass):
    """
    Data type class for ConfigLog object
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    date = Field(name="date", f_type=DateTime(), default_value="auto")
    obj_ref = Field(name="obj_ref", f_type=ForeignKey(fk_link=ObjectConfigFields), required=True, postable=True)
    description = Field(
        name="description",
        f_type=Text(),
        default_value="",
        postable=True,
    )
    config = Field(
        name="config",
        f_type=Json(relates_on=Relation(field=obj_ref)),
        default_value={},
        postable=True,
        required=True,
    )
    attr = Field(
        name="attr",
        f_type=Json(relates_on=Relation(field=obj_ref)),
        default_value={},
        postable=True,
    )
    url = Field(name="url", f_type=String(), default_value="auto")


# Back-reference from ConfigLogFields
ObjectConfigFields.current = Field(
    name="current",
    f_type=BackReferenceFK(fk_link=ConfigLogFields),
    default_value="auto",
)
ObjectConfigFields.previous = Field(
    name="previous",
    f_type=BackReferenceFK(fk_link=ConfigLogFields),
    default_value="auto",
)
ObjectConfigFields.history = Field(
    name="history",
    f_type=BackReferenceFK(fk_link=ConfigLogFields),
    default_value="auto",
)


class GroupConfigHostCandidatesFields(BaseClass):
    """
    Data type class for GroupConfigHostCandidates object
    """

    predefined_dependencies = [GroupConfigFields]

    id = Field(
        name="id",
        f_type=PositiveInt(),
        default_value="auto",
    )
    cluster_id = Field(name="cluster_id", f_type=PositiveInt(), default_value="auto")
    prototype_id = Field(name="prototype_id", f_type=PositiveInt(), default_value="auto")
    provider_id = Field(name="provider_id", f_type=PositiveInt(), default_value="auto")
    fqdn = Field(name="fqdn", f_type=String(), default_value="auto")
    description = Field(name="description", f_type=Text(), default_value="auto")
    state = Field(name="state", f_type=String(), default_value="auto")
    url = Field(name="url", f_type=String(), default_value="auto")


class GroupConfigHostsFields(BaseClass):
    """
    Data type class for GroupConfigHostsFields object
    https://spec.adsw.io/adcm_core/objects.html#group-config-hosts
    """

    predefined_dependencies = [GroupConfigFields]

    id = Field(
        name="id",
        f_type=ForeignKey(fk_link=GroupConfigHostCandidatesFields),
        required=True,
        postable=True,
    )
    cluster_id = Field(name="cluster_id", f_type=PositiveInt(), default_value="auto")
    prototype_id = Field(name="prototype_id", f_type=PositiveInt(), default_value="auto")
    provider_id = Field(name="provider_id", f_type=PositiveInt(), default_value="auto")
    fqdn = Field(name="fqdn", f_type=String(), default_value="auto")
    description = Field(name="description", f_type=Text(), default_value="auto")
    state = Field(name="state", f_type=String(), default_value="auto")
    url = Field(name="url", f_type=String(), default_value="auto")


# Back-reference from GroupConfigHostsFields
GroupConfigFields.hosts = Field(
    name="hosts",
    f_type=BackReferenceFK(fk_link=GroupConfigHostsFields),
    default_value="auto",
)


class RbacUserFields(BaseClass):
    """
    Data type class for RbacUser object
    """

    id = Field(
        name="id",
        f_type=PositiveInt(),
        default_value="auto",
    )
    username = Field(
        name="username", f_type=Username(max_length=150, special_chars="@.+-_"), required=True, postable=True
    )
    first_name = Field(
        name="first_name", default_value="", f_type=String(max_length=150), postable=True, changeable=True
    )
    last_name = Field(name="last_name", default_value="", f_type=String(max_length=150), postable=True, changeable=True)
    email = Field(name="email", default_value="", f_type=Email(), postable=True, changeable=True)
    password = Field(name="password", f_type=Password(), required=True, postable=True, changeable=True)
    is_superuser = Field(name="is_superuser", f_type=Boolean(), default_value=False, postable=True, changeable=True)
    profile = Field(name="profile", f_type=Json(), default_value="", postable=True, changeable=True)
    url = Field(name="url", f_type=String(), default_value="auto")


class RbacGroupFields(BaseClass):
    """
    Data type class for RbacGroup object
    """

    id = Field(
        name="id",
        f_type=PositiveInt(),
        default_value="auto",
    )
    user = Field(
        name="user", f_type=ForeignKeyM2M(fk_link=RbacUserFields), postable=True, changeable=True, default_value=[]
    )
    name = Field(name="name", f_type=String(max_length=150), required=True, postable=True, changeable=True)
    description = Field(name="description", f_type=Text(), postable=True, changeable=True, default_value="")
    url = Field(name="url", f_type=String(), default_value="auto")


RbacUserFields.group = Field(
    name="group", f_type=ForeignKeyM2M(fk_link=RbacGroupFields), postable=True, changeable=True, default_value=[]
)


class RbacSimpleRoleFields(BaseClass):
    """
    Data type class for RbacSimpleRoleFields (type='role').
    Used for Role creation only
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    # default_value="auto" because we can't change name after it's set
    # it's "not postable", because we can only set this field during creation, not change it after
    # and currently framework can't resolve it correctly
    name = Field(name="name", f_type=String(max_length=160), default_value="auto", nullable=True)
    display_name = Field(
        name="display_name",
        f_type=String(max_length=160),
        default_value="",
        required=True,
        postable=True,
        changeable=True,
    )
    description = Field(name="description", f_type=Text(), default_value="", postable=True, changeable=True)
    built_in = Field(name="built_in", f_type=StaticBoolean(value=False), default_value=False)
    # type is actually changeable=True and postable=True, but now it's only value
    # (since it's shouldn't be 'hidden' or 'business') is 'role', so we can't actually change it
    type = Field(name="type", f_type=Enum(['role']), default_value='role')
    category = Field(name="category", f_type=ListOf(String()), default_value=[], postable=True, changeable=True)
    parametrized_by_type = Field(
        name="parametrized_by_type",
        f_type=ListOf(Enum(PARAMETRIZED_BY_LIST)),
        required=True,
        postable=True,
        changeable=True,
    )

    url = Field(name="url", f_type=String(), default_value="auto")


class RbacBuiltInRoleFields(BaseClass):
    """
    Data type class for RbacBuiltinRoleFields
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    name = Field(name="name", f_type=String(max_length=160), nullable=True)
    display_name = Field(
        name="display_name",
        f_type=String(max_length=160),
        default_value="",
        required=True,
        postable=True,
        changeable=True,
    )
    description = Field(name="description", f_type=Text(), default_value="")
    category = Field(name="category", f_type=ListOf(String()), default_value=[])
    parametrized_by_type = Field(
        name="parametrized_by_type",
        f_type=ListOf(Enum(PARAMETRIZED_BY_LIST)),
        required=True,
        postable=True,
    )
    built_in = Field(name="built_in", f_type=StaticBoolean(value=True), default_value="auto")
    type = Field(name="type", f_type=Enum(['role', 'business', 'hidden']), default_value='role')
    child = Field(name="child", f_type=EmptyList(), default_value=[])
    url = Field(name="url", f_type=String(), default_value="auto")


class RbacBusinessRoleFields(RbacBuiltInRoleFields):
    """Technical BaseClass for getting only business roles"""


RbacSimpleRoleFields.child = Field(
    name="child", f_type=ForeignKeyM2M(fk_link=RbacBusinessRoleFields), default_value=[], postable=True, changeable=True
)


class RbacRoleFields(BaseClass):
    """Technical BaseClass for adding it to get roles with type 'role'"""

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    name = Field(name="name", f_type=String(max_length=160), nullable=True, postable=True)
    display_name = Field(
        name="display_name",
        f_type=String(max_length=160),
        default_value="",
        postable=True,
        changeable=True,
    )
    description = Field(
        name="description", f_type=Text(), default_value="", nullable=False, postable=True, changeable=True
    )
    built_in = Field(name="built_in", f_type=StaticBoolean(value=False), default_value="auto")
    type = Field(name="type", f_type=Enum(['role', 'business', 'hidden']), default_value='role')
    category = Field(name="category", f_type=ListOf(String()), default_value=[], postable=True, changeable=True)
    parametrized_by_type = Field(
        name="parametrized_by_type",
        f_type=ListOf(Enum(PARAMETRIZED_BY_LIST)),
        required=True,
        postable=True,
        changeable=True,
    )
    url = Field(name="url", f_type=String(), default_value="auto")
    child = Field(name="child", f_type=EmptyList(), default_value=[])


class RbacNotBuiltInPolicyFields(BaseClass):
    """
    Data type class for RbacPolicyFields objects
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    name = Field(name="name", f_type=String(max_length=255), postable=True, required=True)
    role = Field(name="role", f_type=ObjectForeignKey(RbacRoleFields), required=True, postable=True, changeable=True)
    built_in = Field(name="built_in", f_type=StaticBoolean(False), default_value="auto")
    object = Field(
        name="object",
        f_type=GenericForeignKeyList(relates_on=Relation(field=role)),
        postable=True,
        changeable=True,
        default_value=[],
    )
    user = Field(
        name="user", f_type=ForeignKeyM2M(fk_link=RbacUserFields), default_value=[], postable=True, changeable=True
    )
    group = Field(
        name="group", f_type=ForeignKeyM2M(fk_link=RbacGroupFields), default_value=[], postable=True, changeable=True
    )
    url = Field(name="url", f_type=String(), default_value="auto")


class RbacBuiltInPolicyFields(BaseClass):
    """
    Data type class for RbacBuiltinPolicyFields
    """

    id = Field(name="id", f_type=PositiveInt(), default_value="auto")
    name = Field(name="name", f_type=String(max_length=160), required=True, postable=True)
    role = Field(name="role", f_type=ObjectForeignKey(RbacRoleFields), required=True, postable=True)
    built_in = Field(name="built_in", f_type=StaticBoolean(value=True), default_value="auto")
    object = Field(
        name="object",
        f_type=GenericForeignKeyList(relates_on=Relation(field=role)),
        default_value=[],
    )
    user = Field(name="user", f_type=ForeignKeyM2M(fk_link=RbacUserFields), default_value=[])
    group = Field(name="group", f_type=ForeignKeyM2M(fk_link=RbacGroupFields), default_value=[])
    url = Field(name="url", f_type=String(), default_value="auto")
