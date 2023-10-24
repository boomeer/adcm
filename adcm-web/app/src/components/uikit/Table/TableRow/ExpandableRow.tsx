import React, { useRef, useState, useEffect, useCallback } from 'react';
import { useResizeObserver } from '@hooks';
import Collapse from '@uikit/Collapse/Collapse';
import TableRow from '@uikit/Table/TableRow/TableRow';
import cn from 'classnames';
import s from './ExpandableRow.module.scss';
import tableStyles from '@uikit/Table/Table.module.scss';

export interface ExpandableRowProps extends React.PropsWithChildren {
  isExpanded: boolean;
  expandedContent?: React.ReactNode;
  colSpan: number;
  className?: string;
  expandedClassName?: string;
  isInactive?: boolean;
}

const ExpandableRow = ({
  children,
  isExpanded,
  expandedContent = undefined,
  colSpan,
  className = '',
  expandedClassName = '',
  isInactive = false,
}: ExpandableRowProps) => {
  const [isMainHovered, setIsMainHovered] = useState(false);
  const [isExpandHovered, setIsExpandHovered] = useState(false);
  const [rowWidth, setRowWidth] = useState(0);
  const refRow = useRef<HTMLTableRowElement>(null);

  const rowClasses = cn(className, s.expandableRowMain, {
    [tableStyles.hovered]: isMainHovered || isExpandHovered,
    [s.expanded]: isExpanded,
    [s.expandableRowMain_inactive]: isInactive,
  });

  const expandedRowClasses = cn(s.expandableRowContent, expandedClassName, {
    [tableStyles.hovered]: isMainHovered || isExpandHovered,
  });

  const onMainMouseEnterHandler = () => setIsMainHovered(true);
  const onMainMouseLeaveHandler = () => setIsMainHovered(false);

  const setRowNewWidth = useCallback(() => {
    if (!refRow.current) return;
    setRowWidth(refRow.current.offsetWidth);
  }, []);

  useEffect(() => {
    if (!refRow.current) return;
    const ref = refRow.current;
    ref.addEventListener('mouseenter', onMainMouseEnterHandler);
    ref.addEventListener('mouseleave', onMainMouseLeaveHandler);

    return () => {
      if (!ref) return;
      ref.removeEventListener('mouseenter', onMainMouseEnterHandler);
      ref.removeEventListener('mouseleave', onMainMouseLeaveHandler);
    };
  }, [refRow]);

  useResizeObserver(refRow, setRowNewWidth);

  return (
    <>
      <TableRow isInactive={isInactive} ref={refRow} className={rowClasses}>
        {children}
      </TableRow>
      {expandedContent && isExpanded && (
        <tr
          className={expandedRowClasses}
          onMouseEnter={() => setIsExpandHovered(true)}
          onMouseLeave={() => setIsExpandHovered(false)}
        >
          <td colSpan={colSpan}>
            <div style={{ width: `${rowWidth}px` }}>
              <Collapse isExpanded={true}>
                <div className={s.expandableRowContent_wrapper}>{expandedContent}</div>
              </Collapse>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

export default ExpandableRow;