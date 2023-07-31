import { Link } from 'react-router-dom';
import { Table, TableRow, TableCell, IconButton } from '@uikit';
import StatusableCell from '@commonComponents/Table/Cells/StatusableCell';
import { useDispatch, useStore } from '@hooks';
import { columns, clusterStatusesMap } from './ClustersTable.constants';
import { setDeletableId } from '@store/adcm/clusters/clustersSlice';
import Concern from '@commonComponents/Concern/Concern';
import { setSortParams } from '@store/adcm/clusters/clustersTableSlice';
import { SortParams } from '@uikit/types/list.types';

const ClustersTable = () => {
  const dispatch = useDispatch();
  const clusters = useStore((s) => s.adcm.clusters.clusters);
  const isLoading = useStore((s) => s.adcm.clusters.isLoading);
  const sortParams = useStore((s) => s.adcm.clustersTable.sortParams);

  const getHandleDeleteClick = (clusterId: number) => () => {
    dispatch(setDeletableId(clusterId));
  };

  const handleSorting = (sortParams: SortParams) => {
    dispatch(setSortParams(sortParams));
  };

  return (
    <Table isLoading={isLoading} columns={columns} sortParams={sortParams} onSorting={handleSorting}>
      {clusters.map((cluster) => {
        return (
          <TableRow key={cluster.id}>
            <StatusableCell status={clusterStatusesMap[cluster.status]}>
              <Link to={`/clusters/${cluster.id}`}>{cluster.name}</Link>
            </StatusableCell>
            <TableCell>{cluster.state}</TableCell>
            <TableCell>{cluster.prototype.displayName}</TableCell>
            <TableCell>{cluster.prototype.version}</TableCell>
            <TableCell>{cluster.description}</TableCell>
            <TableCell hasIconOnly>
              <Concern concerns={cluster.concerns} />
            </TableCell>
            <TableCell hasIconOnly align="center">
              <IconButton icon="g1-delete" size={32} onClick={getHandleDeleteClick(cluster.id)} title="Delete" />
            </TableCell>
          </TableRow>
        );
      })}
    </Table>
  );
};

export default ClustersTable;
