import React from 'react';
import { IconButton, Table, TableCell, TableRow } from '@uikit';
import StatusableCell from '@commonComponents/Table/Cells/StatusableCell';
import { columns, hostStatusesMap } from '@pages/HostsPage/HostsTable/HostsTable.constants';
import { useDispatch, useStore } from '@hooks';
import { AdcmHost } from '@models/adcm/host';
import UnlinkHostToggleButton from '@pages/HostsPage/HostsTable/Buttons/UnlinkHostToggleButton/UnlinkHostToggleButton';
import { SortParams } from '@uikit/types/list.types';
import { setSortParams } from '@store/adcm/hosts/hostsTableSlice';
import { orElseGet } from '@utils/checkUtils';
import { openDeleteDialog, openMaintenanceModeDialog, openUpdateDialog } from '@store/adcm/hosts/hostsActionsSlice';
import MaintenanceModeButton from '@commonComponents/MaintenanceModeButton/MaintenanceModeButton';
import HostDynamicActionsIcon from '../HostDynamicActionsIcon/HostDynamicActionsIcon';
import MultiStateCell from '@commonComponents/Table/Cells/MultiStateCell';
import Concern from '@commonComponents/Concern/Concern';
import { AdcmEntitySystemState } from '@models/adcm';
import { Link } from 'react-router-dom';

const HostsTable: React.FC = () => {
  const dispatch = useDispatch();

  const hosts = useStore(({ adcm }) => adcm.hosts.hosts);
  const isLoading = useStore(({ adcm }) => adcm.hosts.isLoading);
  const sortParams = useStore((s) => s.adcm.hostsTable.sortParams);

  const handleClickMaintenanceMode = (host: AdcmHost) => () => {
    if (host.isMaintenanceModeAvailable) {
      dispatch(openMaintenanceModeDialog(host.id));
    }
  };

  const getHandleDeleteClick = (hostId: number) => () => {
    // set deletable id for show Delete Confirm Dialog
    dispatch(openDeleteDialog(hostId));
  };

  const handleUpdateClick = (host: AdcmHost) => {
    dispatch(openUpdateDialog(host));
  };

  const handleSorting = (sortParams: SortParams) => {
    dispatch(setSortParams(sortParams));
  };

  return (
    <Table isLoading={isLoading} columns={columns} sortParams={sortParams} onSorting={handleSorting}>
      {hosts.map((host: AdcmHost) => {
        const hostLinked = !!host.cluster?.id;

        return (
          <TableRow key={host.id}>
            <StatusableCell status={hostStatusesMap[host.status]}>
              <Link to={`/hosts/${host.id}`} className="text-link">
                {host.name}
              </Link>
              {host.state === AdcmEntitySystemState.Created && (
                <IconButton icon="g1-edit" size={32} title="Edit" onClick={() => handleUpdateClick(host)} />
              )}
            </StatusableCell>
            <MultiStateCell entity={host} />
            <TableCell>{host.hostprovider.name}</TableCell>
            <TableCell>{orElseGet(host.cluster?.name)}</TableCell>
            <TableCell>
              <Concern concerns={host.concerns} />
            </TableCell>
            <TableCell hasIconOnly align="center">
              <HostDynamicActionsIcon host={host} />
              <MaintenanceModeButton
                isMaintenanceModeAvailable={host.isMaintenanceModeAvailable}
                maintenanceModeStatus={host.maintenanceMode}
                onClick={handleClickMaintenanceMode(host)}
              />
              <UnlinkHostToggleButton host={host} />
              <IconButton
                icon="g1-delete"
                size={32}
                disabled={hostLinked}
                onClick={getHandleDeleteClick(host.id)}
                title={hostLinked ? 'Unlink host to enable Delete button' : 'Delete'}
              />
            </TableCell>
          </TableRow>
        );
      })}
    </Table>
  );
};

export default HostsTable;
