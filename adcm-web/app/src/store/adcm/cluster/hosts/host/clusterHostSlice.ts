import { AdcmClusterHostsApi, AdcmClustersApi, RequestError } from '@api';
import { defaultSpinnerDelay } from '@constants';
import { AdcmClusterHost, AdcmClusterHostComponentsStatus, AdcmServiceComponent } from '@models/adcm';
import { createSlice } from '@reduxjs/toolkit';
import { wsActions } from '@store/middlewares/wsMiddleware.constants';
import { showError, showSuccess } from '@store/notificationsSlice';
import { createAsyncThunk } from '@store/redux';
import { getErrorMessage } from '@utils/httpResponseUtils';
import { executeWithMinDelay } from '@utils/requestUtils';

interface AdcmClusterHostState {
  clusterHost?: AdcmClusterHost;
  isLoading: boolean;
  hostComponentsCounters: {
    successfulHostComponentsCount: number;
    totalHostComponentsCount: number;
  };
  relatedData: {
    hostComponents: AdcmServiceComponent[];
  };
}

interface ClusterHostPayload {
  clusterId: number;
  hostId: number;
}

const loadClusterHost = createAsyncThunk(
  'adcm/cluster/hosts/host/loadClusterHost',
  async ({ clusterId, hostId }: ClusterHostPayload, thunkAPI) => {
    try {
      const host = await AdcmClusterHostsApi.getHost(clusterId, hostId);
      return host;
    } catch (error) {
      thunkAPI.dispatch(showError({ message: 'Host not found' }));
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const getClusterHost = createAsyncThunk(
  'adcm/cluster/hosts/host/getClusterHost',
  async (arg: ClusterHostPayload, thunkAPI) => {
    thunkAPI.dispatch(setIsLoading(true));
    const startDate = new Date();

    await thunkAPI.dispatch(loadClusterHost(arg));

    executeWithMinDelay({
      startDate,
      delay: defaultSpinnerDelay,

      callback: () => {
        thunkAPI.dispatch(setIsLoading(false));
      },
    });
  },
);

const getClusterHostComponentsStates = createAsyncThunk(
  'adcm/cluster/hosts/host/getClusterHostComponentsStates',
  async ({ clusterId, hostId }: ClusterHostPayload, thunkAPI) => {
    try {
      const states = AdcmClusterHostsApi.getClusterHostComponentsStates(clusterId, hostId);
      return states;
    } catch (error) {
      thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const unlinkClusterHost = createAsyncThunk(
  'adcm/cluster/hosts/host/unlinkClusterHost',
  async ({ clusterId, hostId }: ClusterHostPayload, thunkAPI) => {
    try {
      await AdcmClustersApi.unlinkHost(clusterId, hostId);
      thunkAPI.dispatch(showSuccess({ message: 'The host has been unlinked!' }));
    } catch (error) {
      thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const createInitialState = (): AdcmClusterHostState => ({
  clusterHost: undefined,
  isLoading: true,
  relatedData: {
    hostComponents: [],
  },
  hostComponentsCounters: {
    successfulHostComponentsCount: 0,
    totalHostComponentsCount: 0,
  },
});

const clusterHostSlice = createSlice({
  name: 'adcm/clusters/hosts/clusterHost',
  initialState: createInitialState(),
  reducers: {
    setIsLoading(state, action) {
      state.isLoading = action.payload;
    },
    cleanupClusterHost() {
      return createInitialState();
    },
  },
  extraReducers: (builder) => {
    builder.addCase(loadClusterHost.fulfilled, (state, action) => {
      state.clusterHost = action.payload;
    });
    builder.addCase(loadClusterHost.rejected, (state) => {
      state.clusterHost = undefined;
    });
    builder.addCase(getClusterHostComponentsStates.fulfilled, (state, action) => {
      state.hostComponentsCounters.totalHostComponentsCount = action.payload.hostComponents.length;
      state.hostComponentsCounters.successfulHostComponentsCount = action.payload.hostComponents.filter(
        ({ status }) => status === AdcmClusterHostComponentsStatus.Up,
      ).length;
    });
    builder.addCase(getClusterHostComponentsStates.rejected, (state) => {
      state.hostComponentsCounters.totalHostComponentsCount = 0;
      state.hostComponentsCounters.successfulHostComponentsCount = 0;
    });
    builder.addCase(wsActions.update_host, (state, action) => {
      const { id, changes } = action.payload.object;
      if (state.clusterHost?.id == id) {
        state.clusterHost = { ...state.clusterHost, ...changes };
      }
    });
    builder.addCase(wsActions.create_host_concern, (state, action) => {
      const { id: clusterHostId, changes: newConcern } = action.payload.object;
      if (
        state.clusterHost?.id === clusterHostId &&
        state.clusterHost.concerns.every((concern) => concern.id !== newConcern.id)
      ) {
        state.clusterHost = {
          ...state.clusterHost,
          concerns: [...state.clusterHost.concerns, newConcern],
        };
      }
    });
    builder.addCase(wsActions.delete_host_concern, (state, action) => {
      const { id, changes } = action.payload.object;
      if (state.clusterHost?.id === id) {
        state.clusterHost = {
          ...state.clusterHost,
          concerns: state.clusterHost.concerns.filter((concern) => concern.id !== changes.id),
        };
      }
    });
  },
});

const { setIsLoading, cleanupClusterHost } = clusterHostSlice.actions;
export { getClusterHost, cleanupClusterHost, getClusterHostComponentsStates, unlinkClusterHost };
export default clusterHostSlice.reducer;
