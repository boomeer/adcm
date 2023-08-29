import { AdcmClustersApi, AdcmPrototypesApi, RequestError } from '@api';
import { createAsyncThunk } from '@store/redux';
import { refreshClusters } from './clustersSlice';
import { showError, showInfo } from '@store/notificationsSlice';
import { getErrorMessage } from '@utils/httpResponseUtils';
import { createSlice } from '@reduxjs/toolkit';
import {
  AdcmCluster,
  AdcmClusterActionDetails,
  AdcmClusterUpgrade,
  AdcmPrototypeType,
  AdcmPrototypeVersions,
  CreateAdcmClusterPayload,
} from '@models/adcm';

interface AdcmClusterActionsState {
  cluster: AdcmCluster | undefined;
  isCreateClusterDialogOpen: boolean;
  isUpgradeClusterDialogOpen: boolean;
  deletableId: {
    id: number | null;
  };
  relatedData: {
    prototypeVersions: AdcmPrototypeVersions[];
    isLoaded: boolean;
    upgrades: AdcmClusterUpgrade[];
    upgradeActionDetails: AdcmClusterActionDetails | undefined;
  };
}

type OpenUpgradeClusterDialogArgs = {
  cluster: AdcmCluster;
};

type LoadAdcmClusterUpgradesArgs = {
  clusterId: number;
};

type LoadAdcmClusterUpgradeActionDetailsArgs = {
  clusterId: number;
  upgradeId: number;
};

const createCluster = createAsyncThunk(
  'adcm/clustersActions/createCluster',
  async (arg: CreateAdcmClusterPayload, thunkAPI) => {
    try {
      if (!arg.isLicenseAccepted) {
        await AdcmPrototypesApi.postAcceptLicense(arg.prototypeId);
      }

      const cluster = await AdcmClustersApi.postCluster(arg);
      return cluster;
    } catch (error) {
      thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
      return thunkAPI.rejectWithValue(error);
    } finally {
      thunkAPI.dispatch(refreshClusters());
    }
  },
);

const loadPrototypeVersions = createAsyncThunk('adcm/clustersActions/loadPrototypeVersions', async (arg, thunkAPI) => {
  try {
    const prototypeVersions = await AdcmPrototypesApi.getPrototypeVersions({ type: AdcmPrototypeType.Cluster });
    return prototypeVersions;
  } catch (error) {
    thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
    return thunkAPI.rejectWithValue(error);
  }
});

const loadPrototypesRelatedData = createAsyncThunk('adcm/clustersActions/loadRelatedData', async (arg, thunkAPI) => {
  await thunkAPI.dispatch(loadPrototypeVersions());
});

const openClusterCreateDialog = createAsyncThunk(
  'adcm/clustersActions/openClusterCreateDialog',
  async (arg, thunkAPI) => {
    try {
      thunkAPI.dispatch(loadPrototypesRelatedData());
    } catch (error) {
      thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const loadClusterUpgrades = createAsyncThunk(
  'adcm/clustersActions/loadClusterUpgrades',
  async (arg: LoadAdcmClusterUpgradesArgs, thunkAPI) => {
    try {
      const upgrades = await AdcmClustersApi.getClusterUpgrades(arg.clusterId);
      return upgrades;
    } catch (error) {
      thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const loadClusterUpgradeActionDetails = createAsyncThunk(
  'adcm/clustersActions/loadClusterUpgradeActionDetails',
  async (arg: LoadAdcmClusterUpgradeActionDetailsArgs, thunkAPI) => {
    try {
      const upgradeActionDetails = await AdcmClustersApi.getClusterUpgrade(arg.clusterId, arg.upgradeId);
      return upgradeActionDetails;
    } catch (error) {
      thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const loadClusterUpgradesRelatedData = createAsyncThunk(
  'adcm/clustersActions/loadClusterUpgradesRelatedData',
  async (arg, thunkAPI) => {
    const {
      adcm: {
        clustersActions: { cluster },
      },
    } = thunkAPI.getState();
    if (cluster) {
      await thunkAPI.dispatch(loadClusterUpgrades({ clusterId: cluster.id }));
    }
  },
);

const openClusterUpgradeDialog = createAsyncThunk(
  'adcm/clustersActions/openClusterUpgradeDialog',
  async (arg: OpenUpgradeClusterDialogArgs, thunkAPI) => {
    try {
      thunkAPI.dispatch(loadClusterUpgradesRelatedData());
    } catch (error) {
      thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const deleteClusterWithUpdate = createAsyncThunk(
  'adcm/clustersActions/deleteClusterWithUpdate',
  async (clusterId: number, thunkAPI) => {
    try {
      await AdcmClustersApi.deleteCluster(clusterId);
      await thunkAPI.dispatch(refreshClusters());
      thunkAPI.dispatch(showInfo({ message: 'The cluster has been deleted' }));
    } catch (error) {
      thunkAPI.dispatch(showError({ message: getErrorMessage(error as RequestError) }));
      return thunkAPI.rejectWithValue(error);
    }
  },
);

const createInitialState = (): AdcmClusterActionsState => ({
  cluster: undefined,
  isCreateClusterDialogOpen: false,
  isUpgradeClusterDialogOpen: false,
  relatedData: {
    prototypeVersions: [],
    upgrades: [],
    upgradeActionDetails: undefined,
    isLoaded: false,
  },
  deletableId: {
    id: null,
  },
});

const clustersActionsSlice = createSlice({
  name: 'adcm/clustersActions',
  initialState: createInitialState(),
  reducers: {
    cleanupClustersActions() {
      return createInitialState();
    },
    openClusterDeleteDialog(state, action) {
      state.deletableId.id = action.payload;
    },
    closeClusterDeleteDialog(state) {
      state.deletableId.id = null;
    },
  },
  extraReducers(builder) {
    builder.addCase(openClusterCreateDialog.fulfilled, (state) => {
      state.isCreateClusterDialogOpen = true;
    });
    builder.addCase(loadPrototypesRelatedData.fulfilled, (state) => {
      state.relatedData.isLoaded = true;
    });
    builder.addCase(loadPrototypeVersions.fulfilled, (state, action) => {
      state.relatedData.prototypeVersions = action.payload;
    });
    builder.addCase(createCluster.fulfilled, () => {
      return createInitialState();
    });
    builder.addCase(openClusterUpgradeDialog.pending, (state, action) => {
      state.cluster = action.meta.arg.cluster;
    });
    builder.addCase(openClusterUpgradeDialog.fulfilled, (state) => {
      state.isUpgradeClusterDialogOpen = true;
    });
    builder.addCase(loadClusterUpgradesRelatedData.fulfilled, (state) => {
      state.relatedData.isLoaded = true;
    });
    builder.addCase(loadClusterUpgrades.fulfilled, (state, action) => {
      state.relatedData.upgrades = action.payload;
    });
    builder.addCase(loadClusterUpgradeActionDetails.fulfilled, (state, action) => {
      state.relatedData.upgradeActionDetails = action.payload;
    });
    builder.addCase(deleteClusterWithUpdate.pending, (state) => {
      clustersActionsSlice.caseReducers.closeClusterDeleteDialog(state);
    });
  },
});

const { openClusterDeleteDialog, closeClusterDeleteDialog, cleanupClustersActions } = clustersActionsSlice.actions;
export {
  createCluster,
  openClusterCreateDialog,
  deleteClusterWithUpdate,
  openClusterDeleteDialog,
  closeClusterDeleteDialog,
  openClusterUpgradeDialog,
  loadClusterUpgradeActionDetails,
  cleanupClustersActions,
};
export default clustersActionsSlice.reducer;
