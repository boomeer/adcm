import React from 'react';
import { TabsBlock } from '@uikit';
import TabButton from '@uikit/Tabs/TabButton';
import s from './ClusterOverviewFilter.module.scss';
import { AdcmClusterStatus } from '@models/adcm';

interface ClusterOverviewFilter {
  status: AdcmClusterStatus;
  onStatusChange: (status: AdcmClusterStatus) => void;
}

const ClusterOverviewFilter = ({ status, onStatusChange }: ClusterOverviewFilter) => {
  return (
    <TabsBlock variant="secondary" className={s.clusterOverviewFilter}>
      <TabButton isActive={status === AdcmClusterStatus.Up} onClick={() => onStatusChange(AdcmClusterStatus.Up)}>
        Up
      </TabButton>
      <TabButton isActive={status === AdcmClusterStatus.Down} onClick={() => onStatusChange(AdcmClusterStatus.Down)}>
        Down
      </TabButton>
    </TabsBlock>
  );
};

export default ClusterOverviewFilter;
