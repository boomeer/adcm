import Dialog from '@uikit/Dialog/Dialog';
import { useDispatch, useStore } from '@hooks';
import { deleteWithUpdateHostProviders, closeDeleteDialog } from '@store/adcm/hostProviders/hostProvidersActionsSlice';

const HostProvidersDeleteDialog = () => {
  const dispatch = useDispatch();

  const deletableHostProvider = useStore(
    ({
      adcm: {
        hostProviders: { hostProviders },
        hostProvidersActions: {
          deleteDialog: { id: deletableId },
        },
      },
    }) => {
      if (!deletableId) return null;
      return hostProviders.find(({ id }) => id === deletableId) ?? null;
    },
  );

  const isOpenDeleteDialog = !!deletableHostProvider;

  const handleCloseDialog = () => {
    dispatch(closeDeleteDialog());
  };

  const handleConfirmDialog = () => {
    if (!deletableHostProvider?.id) return;

    dispatch(deleteWithUpdateHostProviders(deletableHostProvider.id));
  };

  const hostProviderName = deletableHostProvider?.name;

  return (
    <Dialog
      //
      isOpen={isOpenDeleteDialog}
      onOpenChange={handleCloseDialog}
      title={`Delete "${hostProviderName}" hostprovider`}
      onAction={handleConfirmDialog}
      actionButtonLabel="Delete"
    >
      Are you sure?
    </Dialog>
  );
};
export default HostProvidersDeleteDialog;
