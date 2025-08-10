/**
 * BaseChart Component
 * ==================
 * 
 * Foundation chart component with TaxPoynt design system integration.
 * Provides consistent styling, theming, and responsive behavior for all charts.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React from 'react';
import { colors, typography, spacing, borders, shadows } from '../../design_system/tokens';

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
  metadata?: Record<string, any>;
}

export interface ChartSeries {
  name: string;
  data: ChartDataPoint[];
  color?: string;
  type?: 'line' | 'bar' | 'area' | 'pie';
}

export interface BaseChartProps {
  data: ChartSeries[] | ChartDataPoint[];
  title?: string;
  subtitle?: string;
  height?: number;
  width?: number;
  role?: 'si' | 'app' | 'hybrid' | 'admin';
  showLegend?: boolean;
  showTooltip?: boolean;
  showGrid?: boolean;
  responsive?: boolean;
  loading?: boolean;
  error?: string;
  empty?: boolean;
  emptyMessage?: string;
  className?: string;
  onDataPointClick?: (dataPoint: ChartDataPoint, seriesIndex?: number) => void;
  'data-testid'?: string;
}

export const BaseChart: React.FC<BaseChartProps> = ({
  data,
  title,
  subtitle,
  height = 300,
  width,
  role,
  showLegend = true,
  showTooltip = true,
  showGrid = true,
  responsive = true,
  loading = false,
  error,
  empty = false,
  emptyMessage = 'No data available',
  className = '',
  onDataPointClick,
  'data-testid': testId,
  children,
}) => {
  const roleColor = role ? colors.roles[role] : colors.brand.primary;
  const chartColors = [
    roleColor,
    colors.semantic.success,
    colors.semantic.warning,
    colors.semantic.info,
    colors.nigeria.green,
    colors.neutral[600],
    colors.semantic.error,
  ];

  const containerStyles = {
    width: responsive ? '100%' : width ? `${width}px` : '100%',
    height: `${height}px`,
    padding: spacing[4],
    backgroundColor: '#FFFFFF',
    border: `${borders.width[1]} solid ${colors.neutral[200]}`,
    borderRadius: borders.radius.lg,
    boxShadow: shadows.sm,
    position: 'relative' as const,
    display: 'flex',
    flexDirection: 'column' as const,
    fontFamily: typography.fonts.sans.join(', '),
  };

  const headerStyles = {
    marginBottom: spacing[4],
    textAlign: 'center' as const,
  };

  const titleStyles = {
    fontSize: typography.sizes.lg,
    fontWeight: typography.weights.semibold,
    color: colors.neutral[900],
    margin: 0,
    marginBottom: subtitle ? spacing[1] : 0,
  };

  const subtitleStyles = {
    fontSize: typography.sizes.sm,
    color: colors.neutral[600],
    margin: 0,
  };

  const chartAreaStyles = {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative' as const,
  };

  const loadingStyles = {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing[3],
    color: colors.neutral[600],
  };

  const loadingSpinnerStyles = {
    width: '32px',
    height: '32px',
    border: `3px solid ${colors.neutral[200]}`,
    borderTop: `3px solid ${roleColor}`,
    borderRadius: borders.radius.full,
    animation: 'spin 1s linear infinite',
  };

  const errorStyles = {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing[3],
    color: colors.semantic.error,
    textAlign: 'center' as const,
  };

  const emptyStyles = {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing[3],
    color: colors.neutral[500],
    textAlign: 'center' as const,
  };

  const legendStyles = {
    display: 'flex',
    flexWrap: 'wrap' as const,
    justifyContent: 'center',
    gap: spacing[3],
    marginTop: spacing[4],
    padding: `${spacing[3]} 0`,
    borderTop: `${borders.width[1]} solid ${colors.neutral[200]}`,
  };

  const legendItemStyles = {
    display: 'flex',
    alignItems: 'center',
    gap: spacing[2],
    fontSize: typography.sizes.sm,
    color: colors.neutral[700],
  };

  const legendColorBoxStyles = (color: string) => ({
    width: '12px',
    height: '12px',
    borderRadius: borders.radius.sm,
    backgroundColor: color,
  });

  // Generate legend data
  const getLegendData = () => {
    if (Array.isArray(data) && data.length > 0 && 'name' in data[0]) {
      // Multiple series data
      return (data as ChartSeries[]).map((series, index) => ({
        name: series.name,
        color: series.color || chartColors[index % chartColors.length],
      }));
    } else if (Array.isArray(data) && data.length > 0 && 'label' in data[0]) {
      // Single series data
      return (data as ChartDataPoint[]).map((point, index) => ({
        name: point.label,
        color: point.color || chartColors[index % chartColors.length],
      }));
    }
    return [];
  };

  const legendData = getLegendData();

  // Chart role accent
  const accentBarStyles = role ? {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    width: '100%',
    height: '3px',
    backgroundColor: roleColor,
    borderRadius: `${borders.radius.lg} ${borders.radius.lg} 0 0`,
  } : undefined;

  if (loading) {
    return (
      <div
        style={containerStyles}
        className={className}
        data-testid={testId}
      >
        {role && <div style={accentBarStyles} />}
        
        {(title || subtitle) && (
          <div style={headerStyles}>
            {title && <h3 style={titleStyles}>{title}</h3>}
            {subtitle && <p style={subtitleStyles}>{subtitle}</p>}
          </div>
        )}
        
        <div style={chartAreaStyles}>
          <div style={loadingStyles}>
            <div style={loadingSpinnerStyles} />
            <span>Loading chart data...</span>
          </div>
        </div>
        
        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={containerStyles}
        className={className}
        data-testid={testId}
      >
        {role && <div style={accentBarStyles} />}
        
        {(title || subtitle) && (
          <div style={headerStyles}>
            {title && <h3 style={titleStyles}>{title}</h3>}
            {subtitle && <p style={subtitleStyles}>{subtitle}</p>}
          </div>
        )}
        
        <div style={chartAreaStyles}>
          <div style={errorStyles}>
            <span style={{ fontSize: '32px' }}>⚠️</span>
            <span style={{ fontWeight: typography.weights.medium }}>Chart Error</span>
            <span style={{ fontSize: typography.sizes.sm }}>{error}</span>
          </div>
        </div>
      </div>
    );
  }

  if (empty || !data || (Array.isArray(data) && data.length === 0)) {
    return (
      <div
        style={containerStyles}
        className={className}
        data-testid={testId}
      >
        {role && <div style={accentBarStyles} />}
        
        {(title || subtitle) && (
          <div style={headerStyles}>
            {title && <h3 style={titleStyles}>{title}</h3>}
            {subtitle && <p style={subtitleStyles}>{subtitle}</p>}
          </div>
        )}
        
        <div style={chartAreaStyles}>
          <div style={emptyStyles}>
            <span style={{ fontSize: '48px', opacity: 0.5 }}>📊</span>
            <span style={{ fontWeight: typography.weights.medium }}>No Data</span>
            <span style={{ fontSize: typography.sizes.sm }}>{emptyMessage}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={containerStyles}
      className={className}
      data-testid={testId}
    >
      {role && <div style={accentBarStyles} />}
      
      {(title || subtitle) && (
        <div style={headerStyles}>
          {title && <h3 style={titleStyles}>{title}</h3>}
          {subtitle && <p style={subtitleStyles}>{subtitle}</p>}
        </div>
      )}
      
      <div style={chartAreaStyles}>
        {children}
      </div>
      
      {showLegend && legendData.length > 0 && (
        <div style={legendStyles}>
          {legendData.map((item, index) => (
            <div key={index} style={legendItemStyles}>
              <div style={legendColorBoxStyles(item.color)} />
              <span>{item.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BaseChart;