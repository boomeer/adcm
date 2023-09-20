import { httpClient } from '@api/httpClient';
import {
  AdcmMaintenanceMode,
  AdcmServiceComponent,
  Batch,
  AdcmClusterHost,
  AdcmClusterHostComponentsStates,
  AdcmClusterHostsFilter,
  AddClusterHostsPayload,
} from '@models/adcm';
import { AdcmDynamicAction, AdcmDynamicActionDetails, AdcmDynamicActionRunConfig } from '@models/adcm/dynamicAction';
import { PaginationParams, SortParams } from '@models/table';
import { prepareQueryParams } from '@utils/apiUtils';
import qs from 'qs';

export class AdcmClusterHostsApi {
  public static async getClusterHosts(
    clusterId: number,
    filter: AdcmClusterHostsFilter,
    sortParams: SortParams,
    paginationParams: PaginationParams,
  ) {
    const queryParams = prepareQueryParams(filter, sortParams, paginationParams);

    const query = qs.stringify(queryParams);
    const response = await httpClient.get<Batch<AdcmClusterHost>>(`/api/v2/clusters/${clusterId}/hosts/?${query}`);
    return response.data;
  }

  public static async getHost(clusterId: number, hostId: number) {
    const response = await httpClient.get<AdcmClusterHost>(`/api/v2/clusters/${clusterId}/hosts/${hostId}/`);
    return response.data;
  }

  public static async addClusterHosts(payload: AddClusterHostsPayload) {
    const hostIds = payload.hostIds.map((id) => ({ hostId: id }));
    const response = await httpClient.post<AddClusterHostsPayload>(
      `/api/v2/clusters/${payload.clusterId}/hosts/`,
      hostIds,
    );
    return response.data;
  }

  public static async toggleMaintenanceMode(clusterId: number, hostId: number, maintenanceMode: AdcmMaintenanceMode) {
    const response = await httpClient.post(`/api/v2/clusters/${clusterId}/hosts/${hostId}/maintenance-mode/`, {
      maintenanceMode,
    });

    return response.data;
  }

  public static async getClusterHostComponents(
    clusterId: number,
    hostId: number,
    sortParams: SortParams,
    paginationParams: PaginationParams,
    filter: AdcmClusterHostsFilter,
  ) {
    const queryParams = prepareQueryParams(filter, sortParams, paginationParams);

    const query = qs.stringify(queryParams);
    const response = await httpClient.get<Batch<AdcmServiceComponent>>(
      `/api/v2/clusters/${clusterId}/hosts/${hostId}/components/?${query}`,
    );

    return response.data;
  }

  public static async getClusterHostComponentsStates(clusterId: number, hostId: number) {
    const response = await httpClient.get<AdcmClusterHostComponentsStates>(
      `/api/v2/clusters/${clusterId}/hosts/${hostId}/statuses/`,
    );
    return response.data;
  }

  public static async getClusterHostActions(clusterId: number, hostId: number) {
    const response = await httpClient.get<AdcmDynamicAction[]>(
      `/api/v2/clusters/${clusterId}/hosts/${hostId}/actions/`,
    );
    return response.data;
  }

  public static async getClusterHostActionsDetails(clusterId: number, hostId: number, actionId: number) {
    const response = await httpClient.get<AdcmDynamicActionDetails>(
      `/api/v2/clusters/${clusterId}/hosts/${hostId}/actions/${actionId}/`,
    );
    return response.data;
  }

  public static async runClusterHostAction(
    clusterId: number,
    hostId: number,
    actionId: number,
    actionRunConfig: AdcmDynamicActionRunConfig,
  ) {
    const response = await httpClient.post(
      `/api/v2/clusters/${clusterId}/hosts/${hostId}/actions/${actionId}/run/`,
      actionRunConfig,
    );

    return response.data;
  }
}
