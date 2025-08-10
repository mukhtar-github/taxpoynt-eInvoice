/**
 * Breadcrumb Component
 * ===================
 * 
 * Navigation breadcrumb component showing hierarchical page location.
 * Integrates with TaxPoynt design system and supports custom separators.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React from 'react';
import { TaxPoyntDesignSystem } from '../../../design_system/core/TaxPoyntDesignSystem';

// Breadcrumb item interface
export interface BreadcrumbItem {
  label: string;
  href?: string;
  active?: boolean;
  icon?: React.ReactNode;
  onClick?: (item: BreadcrumbItem, index: number) => void;
}

// Breadcrumb props
export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
  className?: string;
  showHomeIcon?: boolean;
  maxItems?: number;
  onItemClick?: (item: BreadcrumbItem, index: number) => void;
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  separator = '/',
  className = '',
  showHomeIcon = true,
  maxItems,
  onItemClick
}) => {
  const { colors, spacing, typography } = TaxPoyntDesignSystem;

  const breadcrumbStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    fontSize: typography.sizes.sm,
    color: colors.neutral.gray[600],
    listStyle: 'none',
    margin: 0,
    padding: 0
  };

  const itemStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs
  };

  const linkStyles: React.CSSProperties = {
    color: colors.primary.blue[600],
    textDecoration: 'none',
    cursor: 'pointer',
    transition: 'color 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs
  };

  const activeLinkStyles: React.CSSProperties = {
    color: colors.neutral.gray[800],
    cursor: 'default',
    fontWeight: typography.weights.medium
  };

  const separatorStyles: React.CSSProperties = {
    color: colors.neutral.gray[400],
    margin: `0 ${spacing.xs}`,
    userSelect: 'none'
  };

  const homeIconStyles: React.CSSProperties = {
    width: '16px',
    height: '16px',
    fill: 'currentColor'
  };

  const ellipsisStyles: React.CSSProperties = {
    color: colors.neutral.gray[400],
    cursor: 'default',
    userSelect: 'none'
  };

  // Handle max items display with ellipsis
  const getDisplayItems = (): BreadcrumbItem[] => {
    if (!maxItems || items.length <= maxItems) {
      return items;
    }

    if (maxItems <= 1) {
      return [items[items.length - 1]];
    }

    if (maxItems <= 2) {
      return [items[0], items[items.length - 1]];
    }

    // Show first item, ellipsis, and last (maxItems - 2) items
    const visibleEndItems = maxItems - 2;
    const endItems = items.slice(-visibleEndItems);
    
    return [items[0], { label: '...', active: false }, ...endItems];
  };

  const displayItems = getDisplayItems();

  const HomeIcon = () => (
    <svg style={homeIconStyles} viewBox="0 0 20 20" fill="currentColor">
      <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
    </svg>
  );

  const handleItemClick = (item: BreadcrumbItem, index: number) => {
    if (item.label === '...') return;
    
    if (item.onClick) {
      item.onClick(item, index);
    } else if (onItemClick) {
      onItemClick(item, index);
    }
  };

  return (
    <nav className={`taxpoynt-breadcrumb ${className}`} aria-label="Breadcrumb">
      <ol style={breadcrumbStyles}>
        {displayItems.map((item, index) => (
          <React.Fragment key={index}>
            <li style={itemStyles}>
              {item.label === '...' ? (
                <span style={ellipsisStyles}>...</span>
              ) : (
                <span
                  style={{
                    ...linkStyles,
                    ...(item.active && activeLinkStyles)
                  }}
                  onClick={() => !item.active && handleItemClick(item, index)}
                  onMouseEnter={(e) => {
                    if (!item.active) {
                      e.currentTarget.style.color = colors.primary.blue[700];
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!item.active) {
                      e.currentTarget.style.color = colors.primary.blue[600];
                    }
                  }}
                  aria-current={item.active ? 'page' : undefined}
                >
                  {showHomeIcon && index === 0 && <HomeIcon />}
                  {item.icon}
                  <span>{item.label}</span>
                </span>
              )}
            </li>
            
            {index < displayItems.length - 1 && (
              <li style={separatorStyles} aria-hidden="true">
                {separator}
              </li>
            )}
          </React.Fragment>
        ))}
      </ol>
    </nav>
  );
};

export default Breadcrumb;