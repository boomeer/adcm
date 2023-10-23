import React, { ReactNode, useState } from 'react';
import Collapse from '@uikit/Collapse/Collapse';
import { Node } from './CollapseNode.types';
import s from './CollapseNode.module.scss';
import cn from 'classnames';

interface CollapseNodeProps<T> {
  node: Node<T>;
  getNodeClassName: (node: Node<T>) => string;
  renderNodeContent: (node: Node<T>, isExpanded: boolean, onExpand: () => void) => ReactNode;
  dataSet?: string;
}

const CollapseNode = <T,>({
  node,
  getNodeClassName,
  renderNodeContent,
  dataSet = 'collapse-node-container',
}: CollapseNodeProps<T>) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = Boolean(node.children?.length);
  const children = (node.children ?? []) as Node<T>[];

  const toggleCollapseNode = () => {
    if (hasChildren) {
      setIsExpanded((prev) => !prev);
    }
  };

  return (
    <div className={cn(s.collapseNode, getNodeClassName(node))} data-test={dataSet}>
      <div className={s.collapseNode__trigger}>{renderNodeContent(node, isExpanded, toggleCollapseNode)}</div>
      {hasChildren && (
        <div className={s.collapseNode__children}>
          <Collapse isExpanded={isExpanded}>
            {children.map((childNode) => (
              <CollapseNode
                node={childNode}
                key={childNode.key}
                getNodeClassName={getNodeClassName}
                renderNodeContent={renderNodeContent}
              />
            ))}
          </Collapse>
        </div>
      )}
    </div>
  );
};

export default CollapseNode;
