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

from typing import Sequence

from api_v2.imports.types import (
    ClusterImportCandidate,
    CommonImportCandidate,
    ServiceImportCandidate,
    UIBind,
    UIBindSource,
    UICluster,
    UIImportCluster,
    UIImportServices,
    UIObjectImport,
)
from cm.api import is_version_suitable
from cm.errors import raise_adcm_ex
from cm.models import (
    Cluster,
    ClusterBind,
    ClusterObject,
    ObjectType,
    Prototype,
    PrototypeExport,
    PrototypeImport,
)
from cm.status_api import get_obj_status
from django.db.models import QuerySet


def _format_binds(binds: Sequence[ClusterBind]) -> list[UIBind]:
    binds_data = []

    for bind in binds:
        source = bind.source_service
        if source is None:
            source = bind.source_cluster

        binds_data.append(UIBind(id=bind.pk, source=UIBindSource(id=source.pk, type=source.prototype.type)))

    return binds_data


def _format_cluster(cluster: Cluster) -> UICluster:
    return UICluster(id=cluster.pk, name=cluster.name, status=get_obj_status(obj=cluster), state=cluster.state)


def _format_import_cluster(cluster: Cluster, prototype_import: PrototypeImport | None) -> UIImportCluster | None:
    if prototype_import is None:
        return None

    return UIImportCluster(
        id=cluster.pk, is_multi_bind=prototype_import.multibind, is_required=prototype_import.required
    )


def _format_import_services(service_candidates: list[ServiceImportCandidate]) -> list[UIImportServices] | None:
    if not service_candidates:
        return None

    out = []
    for service_data in service_candidates:
        service: ClusterObject = service_data["obj"]
        prototype_import: PrototypeImport = service_data["prototype_import"]

        out.append(
            UIImportServices(
                id=service.pk,
                name=service.name,
                display_name=service.display_name,
                version=service.version,
                is_required=prototype_import.required,
                is_multi_bind=prototype_import.multibind,
            )
        )

    return out


def _get_import_candidates_of_single_prototype_export(
    prototype_export: PrototypeExport,
    prototype_import: PrototypeImport,
    queryset: QuerySet[Cluster] | QuerySet[ClusterObject],
) -> list[CommonImportCandidate] | None:
    if not is_version_suitable(version=prototype_export.prototype.version, prototype_import=prototype_import):
        return None

    out = []
    for obj in queryset:
        out.append(CommonImportCandidate(obj=obj, prototype_import=prototype_import))

    return out


def _get_import_candidates(prototype: Prototype) -> tuple[ClusterImportCandidate, ...]:
    cluster_candidates: dict[int, ClusterImportCandidate] = {}
    service_candidates: list[ServiceImportCandidate] = []

    for prototype_import in PrototypeImport.objects.filter(prototype=prototype):
        checked_export_proto: set[int] = set()

        for cluster_export in PrototypeExport.objects.filter(
            prototype__name=prototype_import.name, prototype__type=ObjectType.CLUSTER
        ).select_related("prototype"):
            if cluster_export.prototype.pk in checked_export_proto:
                continue

            checked_export_proto.add(cluster_export.prototype.pk)

            cluster_import_candidates = _get_import_candidates_of_single_prototype_export(
                prototype_export=cluster_export,
                prototype_import=prototype_import,
                queryset=Cluster.objects.filter(prototype=cluster_export.prototype),
            )
            if cluster_import_candidates is not None:
                for cluster_export_data in cluster_import_candidates:
                    cluster_candidates[cluster_export_data["obj"].pk] = ClusterImportCandidate(
                        obj=cluster_export_data["obj"],
                        prototype_import=cluster_export_data["prototype_import"],
                        services=[],
                    )

        for service_export in PrototypeExport.objects.filter(
            prototype__name=prototype_import.name, prototype__type=ObjectType.SERVICE
        ).select_related("prototype"):
            if service_export.prototype.pk in checked_export_proto:
                continue

            checked_export_proto.add(service_export.prototype.pk)

            service_import_candidates = _get_import_candidates_of_single_prototype_export(
                prototype_export=service_export,
                prototype_import=prototype_import,
                queryset=ClusterObject.objects.filter(prototype=service_export.prototype).select_related("cluster"),
            )
            if service_import_candidates is not None:
                service_candidates.extend(service_import_candidates)

    # attach services to corresponding clusters
    for service_data in service_candidates:
        cluster_pk = service_data["obj"].cluster.pk
        cluster_data = cluster_candidates.get(cluster_pk)
        if cluster_data is None:
            cluster_candidates[cluster_pk] = ClusterImportCandidate(
                obj=Cluster.objects.get(pk=cluster_pk),
                services=[service_data],
                prototype_import=None,
            )
        else:
            cluster_data["services"].append(service_data)

    return tuple(cluster_candidates.values())


def get_imports(obj: Cluster | ClusterObject) -> list[UIObjectImport]:
    if isinstance(obj, ClusterObject):
        cluster = obj.cluster
        service = obj
    elif isinstance(obj, Cluster):
        cluster = obj
        service = None
    else:
        raise ValueError("Wrong obj type")

    out_data = []
    import_candidates = _get_import_candidates(prototype=obj.prototype)
    binds = ClusterBind.objects.filter(cluster=cluster, service=service)

    for import_candidate in import_candidates:
        out_data.append(
            UIObjectImport(
                cluster=_format_cluster(cluster=import_candidate["obj"]),
                import_cluster=_format_import_cluster(
                    cluster=import_candidate["obj"], prototype_import=import_candidate["prototype_import"]
                ),
                import_services=_format_import_services(service_candidates=import_candidate["services"]),
                binds=_format_binds(binds=binds.filter(source_cluster=import_candidate["obj"])),
            )
        )

    return out_data


def cook_data_for_multibind(validated_data: list, obj: Cluster | ClusterObject) -> list:
    bind_data = []

    for item in validated_data:
        if item["source"]["type"] == ObjectType.CLUSTER:
            export_obj = Cluster.objects.get(pk=item["source"]["id"])
            cluster_id = export_obj.pk
            service_id = None

        elif item["source"]["type"] == ObjectType.SERVICE:
            export_obj = ClusterObject.objects.get(pk=item["source"]["id"])
            cluster_id = export_obj.cluster.pk
            service_id = export_obj.pk

        proto_import = PrototypeImport.objects.filter(name=export_obj.prototype.name, prototype=obj.prototype).first()

        if not proto_import:
            raise_adcm_ex(code="INVALID_INPUT", msg="Needed import doesn't exist")

        export_id_data = {"cluster_id": cluster_id}
        if service_id is not None:
            export_id_data["service_id"] = service_id
        bind_data.append(
            {
                "import_id": proto_import.pk,
                "export_id": export_id_data,
            }
        )

    return bind_data
