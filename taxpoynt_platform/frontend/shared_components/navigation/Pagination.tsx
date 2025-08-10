/**
 * Pagination Component
 * ===================
 * 
 * Pagination component for navigating through large datasets.
 * Supports various pagination styles and integrates with TaxPoynt design system.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React from 'react';
import { TaxPoyntDesignSystem } from '../../../design_system/core/TaxPoyntDesignSystem';

// Pagination props
export interface PaginationProps {
  current: number;
  total: number;
  pageSize?: number;
  showSizeChanger?: boolean;
  pageSizeOptions?: number[];
  showQuickJumper?: boolean;
  showTotal?: boolean | ((total: number, range: [number, number]) => React.ReactNode);
  className?: string;
  size?: 'small' | 'default' | 'large';
  simple?: boolean;
  disabled?: boolean;
  onChange?: (page: number, pageSize: number) => void;
  onShowSizeChange?: (current: number, size: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({
  current = 1,
  total = 0,
  pageSize = 10,
  showSizeChanger = false,
  pageSizeOptions = [10, 20, 50, 100],
  showQuickJumper = false,
  showTotal = false,
  className = '',
  size = 'default',
  simple = false,
  disabled = false,
  onChange,
  onShowSizeChange
}) => {
  const { colors, spacing, typography, borderRadius } = TaxPoyntDesignSystem;

  const totalPages = Math.ceil(total / pageSize);
  const startRecord = (current - 1) * pageSize + 1;
  const endRecord = Math.min(current * pageSize, total);

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          fontSize: typography.sizes.xs,
          padding: `${spacing.xs} ${spacing.sm}`,
          minWidth: '32px',
          height: '32px'
        };
      case 'large':
        return {
          fontSize: typography.sizes.base,
          padding: `${spacing.sm} ${spacing.md}`,
          minWidth: '44px',
          height: '44px'
        };
      default:
        return {
          fontSize: typography.sizes.sm,
          padding: `${spacing.sm} ${spacing.sm}`,
          minWidth: '36px',
          height: '36px'
        };
    }
  };

  const sizeStyles = getSizeStyles();

  const containerStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    flexWrap: 'wrap'
  };

  const buttonStyles: React.CSSProperties = {
    ...sizeStyles,
    border: `1px solid ${colors.neutral.gray[300]}`,
    backgroundColor: colors.neutral.white,
    color: colors.neutral.gray[700],
    cursor: disabled ? 'not-allowed' : 'pointer',
    borderRadius: borderRadius.sm,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    textDecoration: 'none',
    transition: 'all 0.2s ease',
    opacity: disabled ? 0.5 : 1
  };

  const activeButtonStyles: React.CSSProperties = {
    ...buttonStyles,
    backgroundColor: colors.primary.blue[500],
    borderColor: colors.primary.blue[500],
    color: colors.neutral.white,
    fontWeight: typography.weights.medium
  };

  const disabledButtonStyles: React.CSSProperties = {
    ...buttonStyles,
    cursor: 'not-allowed',
    opacity: 0.4
  };

  const selectStyles: React.CSSProperties = {
    ...sizeStyles,
    border: `1px solid ${colors.neutral.gray[300]}`,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.neutral.white,
    cursor: disabled ? 'not-allowed' : 'pointer',
    minWidth: '80px'
  };

  const inputStyles: React.CSSProperties = {
    ...sizeStyles,
    border: `1px solid ${colors.neutral.gray[300]}`,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.neutral.white,
    width: '60px',
    textAlign: 'center'
  };

  const textStyles: React.CSSProperties = {
    fontSize: sizeStyles.fontSize,
    color: colors.neutral.gray[600]
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages && !disabled) {
      onChange?.(page, pageSize);
    }
  };

  const handleSizeChange = (newSize: number) => {
    if (!disabled) {
      const newPage = Math.min(current, Math.ceil(total / newSize));
      onShowSizeChange?.(newPage, newSize);
      onChange?.(newPage, newSize);
    }
  };

  const getPageNumbers = (): (number | string)[] => {
    if (simple || totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const delta = 2;
    const range: (number | string)[] = [];
    const rangeWithDots: (number | string)[] = [];

    for (let i = Math.max(2, current - delta); i <= Math.min(totalPages - 1, current + delta); i++) {
      range.push(i);
    }

    if (current - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    if (current + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages);
    } else {
      rangeWithDots.push(totalPages);
    }

    return rangeWithDots;
  };

  const ArrowIcon = ({ direction }: { direction: 'left' | 'right' }) => (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="currentColor"
      style={{ transform: direction === 'left' ? 'rotate(180deg)' : 'none' }}
    >
      <path d="M4.5 3l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  );

  if (simple) {
    return (
      <div className={`taxpoynt-pagination simple ${className}`} style={containerStyles}>
        <button
          style={current <= 1 ? disabledButtonStyles : buttonStyles}
          onClick={() => handlePageChange(current - 1)}
          disabled={current <= 1 || disabled}
          onMouseEnter={(e) => {
            if (current > 1 && !disabled) {
              e.currentTarget.style.backgroundColor = colors.neutral.gray[50];
            }
          }}
          onMouseLeave={(e) => {
            if (current > 1 && !disabled) {
              e.currentTarget.style.backgroundColor = colors.neutral.white;
            }
          }}
        >
          <ArrowIcon direction="left" />
        </button>
        
        <span style={textStyles}>
          {current} / {totalPages}
        </span>
        
        <button
          style={current >= totalPages ? disabledButtonStyles : buttonStyles}
          onClick={() => handlePageChange(current + 1)}
          disabled={current >= totalPages || disabled}
          onMouseEnter={(e) => {
            if (current < totalPages && !disabled) {
              e.currentTarget.style.backgroundColor = colors.neutral.gray[50];
            }
          }}
          onMouseLeave={(e) => {
            if (current < totalPages && !disabled) {
              e.currentTarget.style.backgroundColor = colors.neutral.white;
            }
          }}
        >
          <ArrowIcon direction="right" />
        </button>
      </div>
    );
  }

  return (
    <div className={`taxpoynt-pagination ${className}`} style={containerStyles}>
      {/* Total info */}
      {showTotal && (
        <span style={textStyles}>
          {typeof showTotal === 'function' 
            ? showTotal(total, [startRecord, endRecord])
            : `Showing ${startRecord}-${endRecord} of ${total} items`
          }
        </span>
      )}

      {/* Page size changer */}
      {showSizeChanger && (
        <select
          style={selectStyles}
          value={pageSize}
          onChange={(e) => handleSizeChange(Number(e.target.value))}
          disabled={disabled}
        >
          {pageSizeOptions.map(size => (
            <option key={size} value={size}>
              {size} / page
            </option>
          ))}
        </select>
      )}

      {/* Previous button */}
      <button
        style={current <= 1 ? disabledButtonStyles : buttonStyles}
        onClick={() => handlePageChange(current - 1)}
        disabled={current <= 1 || disabled}
        onMouseEnter={(e) => {
          if (current > 1 && !disabled) {
            e.currentTarget.style.backgroundColor = colors.neutral.gray[50];
          }
        }}
        onMouseLeave={(e) => {
          if (current > 1 && !disabled) {
            e.currentTarget.style.backgroundColor = colors.neutral.white;
          }
        }}
      >
        <ArrowIcon direction="left" />
      </button>

      {/* Page numbers */}
      {getPageNumbers().map((page, index) => (
        <React.Fragment key={index}>
          {page === '...' ? (
            <span style={{ ...textStyles, padding: sizeStyles.padding }}>...</span>
          ) : (
            <button
              style={page === current ? activeButtonStyles : buttonStyles}
              onClick={() => handlePageChange(page as number)}
              disabled={disabled}
              onMouseEnter={(e) => {
                if (page !== current && !disabled) {
                  e.currentTarget.style.backgroundColor = colors.neutral.gray[50];
                }
              }}
              onMouseLeave={(e) => {
                if (page !== current && !disabled) {
                  e.currentTarget.style.backgroundColor = colors.neutral.white;
                }
              }}
            >
              {page}
            </button>
          )}
        </React.Fragment>
      ))}

      {/* Next button */}
      <button
        style={current >= totalPages ? disabledButtonStyles : buttonStyles}
        onClick={() => handlePageChange(current + 1)}
        disabled={current >= totalPages || disabled}
        onMouseEnter={(e) => {
          if (current < totalPages && !disabled) {
            e.currentTarget.style.backgroundColor = colors.neutral.gray[50];
          }
        }}
        onMouseLeave={(e) => {
          if (current < totalPages && !disabled) {
            e.currentTarget.style.backgroundColor = colors.neutral.white;
          }
        }}
      >
        <ArrowIcon direction="right" />
      </button>

      {/* Quick jumper */}
      {showQuickJumper && (
        <>
          <span style={textStyles}>Go to</span>
          <input
            type="number"
            min={1}
            max={totalPages}
            style={inputStyles}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                const page = parseInt((e.target as HTMLInputElement).value);
                if (page >= 1 && page <= totalPages) {
                  handlePageChange(page);
                  (e.target as HTMLInputElement).value = '';
                }
              }
            }}
            disabled={disabled}
          />
        </>
      )}
    </div>
  );
};

export default Pagination;