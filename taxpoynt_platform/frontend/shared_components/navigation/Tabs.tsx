/**
 * Tabs Component
 * ==============
 * 
 * Tab navigation component for organizing content into separate views.
 * Supports various tab styles and integrates with TaxPoynt design system.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { TaxPoyntDesignSystem } from '../../../design_system/core/TaxPoyntDesignSystem';

// Tab item interface
export interface TabItem {
  key: string;
  label: string;
  content?: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
  closable?: boolean;
}

// Tabs props
export interface TabsProps {
  items: TabItem[];
  activeKey?: string;
  defaultActiveKey?: string;
  type?: 'line' | 'card' | 'pill';
  size?: 'small' | 'default' | 'large';
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
  animated?: boolean;
  centered?: boolean;
  onChange?: (activeKey: string) => void;
  onEdit?: (targetKey: string, action: 'add' | 'remove') => void;
  children?: React.ReactNode;
}

const Tabs: React.FC<TabsProps> = ({
  items,
  activeKey,
  defaultActiveKey,
  type = 'line',
  size = 'default',
  position = 'top',
  className = '',
  animated = true,
  centered = false,
  onChange,
  onEdit,
  children
}) => {
  const { colors, spacing, typography, borderRadius, shadows } = TaxPoyntDesignSystem;
  
  const [internalActiveKey, setInternalActiveKey] = useState(
    activeKey || defaultActiveKey || (items.length > 0 ? items[0].key : '')
  );

  const currentActiveKey = activeKey !== undefined ? activeKey : internalActiveKey;

  useEffect(() => {
    if (activeKey !== undefined) {
      setInternalActiveKey(activeKey);
    }
  }, [activeKey]);

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          fontSize: typography.sizes.sm,
          padding: `${spacing.sm} ${spacing.md}`,
          minHeight: '32px'
        };
      case 'large':
        return {
          fontSize: typography.sizes.lg,
          padding: `${spacing.md} ${spacing.lg}`,
          minHeight: '48px'
        };
      default:
        return {
          fontSize: typography.sizes.base,
          padding: `${spacing.sm} ${spacing.lg}`,
          minHeight: '40px'
        };
    }
  };

  const sizeStyles = getSizeStyles();

  const containerStyles: React.CSSProperties = {
    display: 'flex',
    flexDirection: position === 'left' || position === 'right' ? 'row' : 'column',
    width: '100%'
  };

  const tabListStyles: React.CSSProperties = {
    display: 'flex',
    flexDirection: position === 'left' || position === 'right' ? 'column' : 'row',
    gap: type === 'card' ? spacing.xs : 0,
    borderBottom: position === 'top' && type === 'line' ? `2px solid ${colors.neutral.gray[200]}` : 'none',
    borderTop: position === 'bottom' && type === 'line' ? `2px solid ${colors.neutral.gray[200]}` : 'none',
    borderRight: position === 'left' && type === 'line' ? `2px solid ${colors.neutral.gray[200]}` : 'none',
    borderLeft: position === 'right' && type === 'line' ? `2px solid ${colors.neutral.gray[200]}` : 'none',
    justifyContent: centered ? 'center' : 'flex-start',
    order: position === 'bottom' || position === 'right' ? 2 : 1
  };

  const getTabStyles = (item: TabItem, isActive: boolean) => {
    const baseStyles: React.CSSProperties = {
      ...sizeStyles,
      border: 'none',
      background: 'transparent',
      cursor: item.disabled ? 'not-allowed' : 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: spacing.xs,
      position: 'relative',
      transition: 'all 0.2s ease',
      opacity: item.disabled ? 0.5 : 1,
      textDecoration: 'none',
      fontWeight: typography.weights.medium,
      whiteSpace: 'nowrap'
    };

    switch (type) {
      case 'card':
        return {
          ...baseStyles,
          backgroundColor: isActive ? colors.neutral.white : colors.neutral.gray[100],
          border: `1px solid ${colors.neutral.gray[300]}`,
          borderRadius: `${borderRadius.md} ${borderRadius.md} 0 0`,
          borderBottom: isActive ? `1px solid ${colors.neutral.white}` : `1px solid ${colors.neutral.gray[300]}`,
          marginBottom: '-1px',
          color: isActive ? colors.primary.blue[600] : colors.neutral.gray[600]
        };
      case 'pill':
        return {
          ...baseStyles,
          backgroundColor: isActive ? colors.primary.blue[500] : colors.neutral.gray[100],
          borderRadius: borderRadius.full,
          color: isActive ? colors.neutral.white : colors.neutral.gray[600],
          margin: `0 ${spacing.xs}`
        };
      default: // line
        return {
          ...baseStyles,
          color: isActive ? colors.primary.blue[600] : colors.neutral.gray[600],
          borderBottom: position === 'top' && isActive ? `2px solid ${colors.primary.blue[500]}` : 'none',
          borderTop: position === 'bottom' && isActive ? `2px solid ${colors.primary.blue[500]}` : 'none',
          borderRight: position === 'left' && isActive ? `2px solid ${colors.primary.blue[500]}` : 'none',
          borderLeft: position === 'right' && isActive ? `2px solid ${colors.primary.blue[500]}` : 'none',
          marginBottom: position === 'top' ? '-2px' : 0,
          marginTop: position === 'bottom' ? '-2px' : 0,
          marginRight: position === 'left' ? '-2px' : 0,
          marginLeft: position === 'right' ? '-2px' : 0
        };
    }
  };

  const contentStyles: React.CSSProperties = {
    flex: 1,
    padding: spacing.lg,
    backgroundColor: type === 'card' ? colors.neutral.white : 'transparent',
    border: type === 'card' ? `1px solid ${colors.neutral.gray[300]}` : 'none',
    borderTop: type === 'card' && position === 'top' ? 'none' : undefined,
    borderBottom: type === 'card' && position === 'bottom' ? 'none' : undefined,
    borderRight: type === 'card' && position === 'left' ? 'none' : undefined,
    borderLeft: type === 'card' && position === 'right' ? 'none' : undefined,
    borderRadius: type === 'card' ? `0 ${borderRadius.md} ${borderRadius.md} ${borderRadius.md}` : 0,
    order: position === 'bottom' || position === 'right' ? 1 : 2,
    transition: animated ? 'opacity 0.3s ease' : 'none'
  };

  const handleTabClick = (item: TabItem) => {
    if (item.disabled) return;
    
    setInternalActiveKey(item.key);
    onChange?.(item.key);
  };

  const handleClose = (e: React.MouseEvent, item: TabItem) => {
    e.stopPropagation();
    onEdit?.(item.key, 'remove');
  };

  const activeItem = items.find(item => item.key === currentActiveKey);

  const CloseIcon = () => (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="currentColor"
      style={{ opacity: 0.6 }}
    >
      <path d="M6 4.586L10.293.293a1 1 0 011.414 1.414L7.414 6l4.293 4.293a1 1 0 01-1.414 1.414L6 7.414l-4.293 4.293a1 1 0 01-1.414-1.414L4.586 6 .293 1.707A1 1 0 011.707.293L6 4.586z" />
    </svg>
  );

  return (
    <div className={`taxpoynt-tabs ${type} ${className}`} style={containerStyles}>
      <div className="tab-list" style={tabListStyles} role="tablist">
        {items.map((item) => {
          const isActive = item.key === currentActiveKey;
          const tabStyles = getTabStyles(item, isActive);
          
          return (
            <button
              key={item.key}
              style={tabStyles}
              onClick={() => handleTabClick(item)}
              disabled={item.disabled}
              role="tab"
              aria-selected={isActive}
              aria-controls={`tabpanel-${item.key}`}
              onMouseEnter={(e) => {
                if (!item.disabled && !isActive && type !== 'pill') {
                  e.currentTarget.style.color = colors.primary.blue[500];
                }
              }}
              onMouseLeave={(e) => {
                if (!item.disabled && !isActive && type !== 'pill') {
                  e.currentTarget.style.color = colors.neutral.gray[600];
                }
              }}
            >
              {item.icon}
              <span>{item.label}</span>
              {item.closable && (
                <span
                  onClick={(e) => handleClose(e, item)}
                  style={{
                    marginLeft: spacing.xs,
                    padding: '2px',
                    borderRadius: '2px',
                    cursor: 'pointer'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <CloseIcon />
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div
        className="tab-content"
        style={contentStyles}
        role="tabpanel"
        id={`tabpanel-${currentActiveKey}`}
        aria-labelledby={`tab-${currentActiveKey}`}
      >
        {children || activeItem?.content}
      </div>
    </div>
  );
};

export default Tabs;