import { httpClient } from '@api/httpClient';
import {
  Batch,
  AdcmConfigShortView,
  AdcmConfig,
  ConfigurationSchema,
  ConfigurationData,
  ConfigurationAttributes,
} from '@models/adcm';

type GetConfigArgs = {
  hostProviderId: number;
  configGroupId: number;
  configId: number;
};

type GetConfigSchemaArgs = {
  hostProviderId: number;
  configGroupId: number;
};

export class AdcmHostProviderGroupConfigsConfigsApi {
  public static async getConfigs(hostProviderId: number, configGroupId: number) {
    const response = await httpClient.get<Batch<AdcmConfigShortView>>(
      `/api/v2/hostproviders/${hostProviderId}/config-groups/${configGroupId}/configs/?offset=0&limit=1000`,
    );
    return response.data;
  }

  public static async getConfig(args: GetConfigArgs) {
    const response = await httpClient.get<AdcmConfig>(
      `/api/v2/hostproviders/${args.hostProviderId}/config-groups/${args.configGroupId}/configs/${args.configId}/`,
    );
    return response.data;
  }

  public static async getConfigSchema(args: GetConfigSchemaArgs) {
    const response = await httpClient.get<ConfigurationSchema>(
      `/api/v2/hostproviders/${args.hostProviderId}/config-groups/${args.configGroupId}/config-schema/`,
    );
    return response.data;
  }

  public static async createConfiguration(
    hostProviderId: number,
    configGroupId: number,
    configurationData: ConfigurationData,
    attributes: ConfigurationAttributes,
    description = '',
  ) {
    const response = await httpClient.post<AdcmConfig>(
      `/api/v2/hostproviders/${hostProviderId}/config-groups/${configGroupId}/configs/`,
      {
        description,
        adcmMeta: attributes,
        config: configurationData,
      },
    );
    return response.data;
  }
}
