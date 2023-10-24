import { createSlice } from '@reduxjs/toolkit';
import { AdcmClusterHostsApi } from '@api';
import { createAsyncThunk } from '@store/redux';
import { executeWithMinDelay } from '@utils/requestUtils';
import { defaultSpinnerDelay } from '@constants';
import { AdcmClusterHost } from '@models/adcm/clusterHosts';
import { wsActions } from '@store/middlewares/wsMiddleware.constants';
import { updateIfExists } from '@utils/objectUtils';

type AdcmClusterHostsState = {
  hosts: AdcmClusterHost[];
  totalCount: number;
  isLoading: boolean;
};

const loadClusterHostsFromBackend = createAsyncThunk(
  'adcm/clusters/loadClusterHostsFromBackend',
  async (clusterId: number, thunkAPI) => {
    const {
      adcm: {
        clusterHostsTable: { filter, sortParams, paginationParams },
      },
    } = thunkAPI.getState();

    try {
      const batch = await AdcmClusterHostsApi.getClusterHosts(clusterId, filter, sortParams, paginationParams);
      return batch;
    } catch (error) {
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const getClusterHosts = createAsyncThunk('adcm/clusters/getClusterHosts', async (clusterId: number, thunkAPI) => {
  thunkAPI.dispatch(setIsLoading(true));
  const startDate = new Date();

  await thunkAPI.dispatch(loadClusterHostsFromBackend(clusterId));

  executeWithMinDelay({
    startDate,
    delay: defaultSpinnerDelay,
    callback: () => {
      thunkAPI.dispatch(setIsLoading(false));
    },
  });
});

const refreshClusterHosts = createAsyncThunk(
  'adcm/clusters/refreshClusterHosts',
  async (clusterId: number, thunkAPI) => {
    thunkAPI.dispatch(loadClusterHostsFromBackend(clusterId));
  },
);

const createInitialState = (): AdcmClusterHostsState => ({
  hosts: [],
  totalCount: 0,
  isLoading: false,
});

const clusterHostsSlice = createSlice({
  name: 'adcm/clusterHosts',
  initialState: createInitialState(),
  reducers: {
    setIsLoading(state, action) {
      state.isLoading = action.payload;
    },
    cleanupClusterHosts() {
      return createInitialState();
    },
  },
  extraReducers: (builder) => {
    builder.addCase(loadClusterHostsFromBackend.fulfilled, (state, action) => {
      state.hosts = action.payload.results;
      state.totalCount = action.payload.count;
    });
    builder.addCase(loadClusterHostsFromBackend.rejected, (state) => {
      state.hosts = [];
    });
    builder.addCase(wsActions.update_host, (state, action) => {
      const { id, changes } = action.payload.object;
      state.hosts = updateIfExists<AdcmClusterHost>(
        state.hosts,
        (host) => host.id === id,
        () => changes,
      );
    });
    builder.addCase(wsActions.delete_host_concern, (state, action) => {
      const { id, changes } = action.payload.object;
      state.hosts = updateIfExists<AdcmClusterHost>(
        state.hosts,
        (host) => host.id === id,
        (host) => ({
          concerns: host.concerns.filter((concern) => concern.id !== changes.id),
        }),
      );
    });
  },
});

const { setIsLoading, cleanupClusterHosts } = clusterHostsSlice.actions;
export { getClusterHosts, refreshClusterHosts, cleanupClusterHosts };
export default clusterHostsSlice.reducer;