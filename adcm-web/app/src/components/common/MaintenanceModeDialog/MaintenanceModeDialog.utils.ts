import { AdcmHost, AdcmMaintenanceMode, AdcmService, AdcmServiceComponent } from '@models/adcm';

export type EntityWithMaintenanceModeType = AdcmHost | AdcmService | AdcmServiceComponent;

export const getRevertedMaintenanceModeStatus = (entity: EntityWithMaintenanceModeType) => {
  return entity?.maintenanceMode === AdcmMaintenanceMode.Off ? AdcmMaintenanceMode.On : AdcmMaintenanceMode.Off;
};
