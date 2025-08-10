/**
 * Charts Components Index
 * ======================
 * 
 * Central export for all TaxPoynt Platform chart components.
 * Provides data visualization components with consistent styling and theming.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

// Chart Components
export { BaseChart } from './BaseChart';
export type { BaseChartProps, ChartDataPoint, ChartSeries } from './BaseChart';

export { BarChart } from './BarChart';
export type { BarChartProps } from './BarChart';

export { LineChart } from './LineChart';
export type { LineChartProps } from './LineChart';

// Chart utilities and constants
export const ChartTypes = {
  BAR: 'bar',
  LINE: 'line',
  AREA: 'area',
  PIE: 'pie',
  DONUT: 'donut',
} as const;

export type ChartType = typeof ChartTypes[keyof typeof ChartTypes];

// Common chart color palettes
export const ChartColorPalettes = {
  DEFAULT: [
    '#0054B0', // TaxPoynt Blue
    '#10B981', // Success Green
    '#F59E0B', // Warning Amber
    '#3B82F6', // Info Blue
    '#008751', // Nigerian Green
    '#64748B', // Neutral Gray
    '#EF4444', // Error Red
  ],
  
  ROLE_BASED: {
    si: '#0054B0',     // System Integrator
    app: '#008751',    // Access Point Provider
    hybrid: '#6366F1', // Hybrid users
    admin: '#7C3AED',  // Admin interface
  },
  
  SEMANTIC: {
    success: '#10B981',
    warning: '#F59E0B', 
    error: '#EF4444',
    info: '#3B82F6',
  },
  
  NIGERIAN: {
    green: '#008751',
    emerald: '#00A86B',
    forest: '#006341',
  },
} as const;

// Chart formatting utilities
export const ChartFormatters = {
  currency: (value: number, currency = 'NGN') => {
    const formatter = new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
    return formatter.format(value);
  },

  percentage: (value: number, decimals = 1) => {
    return `${value.toFixed(decimals)}%`;
  },

  number: (value: number, compact = false) => {
    const formatter = new Intl.NumberFormat('en-NG', {
      notation: compact ? 'compact' : 'standard',
      compactDisplay: 'short',
    });
    return formatter.format(value);
  },

  date: (date: Date | string, format: 'short' | 'long' | 'month' = 'short') => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    switch (format) {
      case 'long':
        return dateObj.toLocaleDateString('en-NG', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        });
      case 'month':
        return dateObj.toLocaleDateString('en-NG', {
          month: 'short',
          year: 'numeric',
        });
      default:
        return dateObj.toLocaleDateString('en-NG');
    }
  },
};

// Common chart data generators for development/testing
export const ChartDataGenerators = {
  generateRandomData: (count: number, min = 0, max = 100): ChartDataPoint[] => {
    return Array.from({ length: count }, (_, index) => ({
      label: `Item ${index + 1}`,
      value: Math.floor(Math.random() * (max - min + 1)) + min,
    }));
  },

  generateTimeSeriesData: (
    months: number, 
    baseValue = 100, 
    volatility = 0.2
  ): ChartDataPoint[] => {
    const data: ChartDataPoint[] = [];
    let currentValue = baseValue;
    
    for (let i = 0; i < months; i++) {
      const date = new Date();
      date.setMonth(date.getMonth() - (months - 1 - i));
      
      // Add some random variation
      const change = (Math.random() - 0.5) * volatility * currentValue;
      currentValue += change;
      
      data.push({
        label: ChartFormatters.date(date, 'month'),
        value: Math.max(0, Math.round(currentValue)),
      });
    }
    
    return data;
  },

  generateBusinessMetrics: (): ChartDataPoint[] => [
    { label: 'Invoices Processed', value: 1547, color: ChartColorPalettes.DEFAULT[0] },
    { label: 'FIRS Submissions', value: 1423, color: ChartColorPalettes.DEFAULT[1] },
    { label: 'Validation Errors', value: 87, color: ChartColorPalettes.SEMANTIC.error },
    { label: 'Pending Reviews', value: 234, color: ChartColorPalettes.SEMANTIC.warning },
    { label: 'Completed', value: 1310, color: ChartColorPalettes.SEMANTIC.success },
  ],

  generateRevenueData: (months = 12): ChartDataPoint[] => {
    const baseRevenue = 500000; // Base monthly revenue in Naira
    return ChartDataGenerators.generateTimeSeriesData(months, baseRevenue, 0.15)
      .map(point => ({
        ...point,
        value: Math.round(point.value),
      }));
  },

  generateComplianceScores: (): ChartDataPoint[] => [
    { label: 'UBL Standards', value: 94.8, color: ChartColorPalettes.DEFAULT[0] },
    { label: 'WCO HS Codes', value: 89.2, color: ChartColorPalettes.DEFAULT[1] },
    { label: 'NITDA GDPR', value: 92.6, color: ChartColorPalettes.DEFAULT[2] },
    { label: 'ISO 20022', value: 87.5, color: ChartColorPalettes.SEMANTIC.warning },
    { label: 'ISO 27001', value: 95.3, color: ChartColorPalettes.SEMANTIC.success },
    { label: 'LEI', value: 98.7, color: ChartColorPalettes.DEFAULT[3] },
    { label: 'PEPPOL', value: 85.1, color: ChartColorPalettes.SEMANTIC.warning },
  ],
};

// Chart configuration presets
export const ChartPresets = {
  BUSINESS_METRICS: {
    height: 300,
    showLegend: true,
    showGrid: true,
    animated: true,
  },
  
  COMPLIANCE_DASHBOARD: {
    height: 250,
    showLegend: true,
    showGrid: false,
    animated: true,
  },
  
  FINANCIAL_CHARTS: {
    height: 350,
    showLegend: false,
    showGrid: true,
    animated: true,
  },
  
  COMPACT_WIDGET: {
    height: 200,
    showLegend: false,
    showGrid: false,
    animated: false,
  },
};

// Responsive breakpoints for charts
export const ChartBreakpoints = {
  mobile: 480,
  tablet: 768,
  desktop: 1024,
  wide: 1200,
};

// Chart accessibility helpers
export const ChartA11y = {
  getAriaLabel: (type: ChartType, title?: string, dataCount?: number) => {
    const baseLabel = `${type} chart`;
    const titlePart = title ? ` titled "${title}"` : '';
    const dataPart = dataCount ? ` with ${dataCount} data points` : '';
    return `${baseLabel}${titlePart}${dataPart}`;
  },
  
  getDataDescription: (data: ChartDataPoint[] | ChartSeries[]) => {
    if (Array.isArray(data) && data.length > 0 && 'label' in data[0]) {
      const points = data as ChartDataPoint[];
      const values = points.map(p => p.value);
      const min = Math.min(...values);
      const max = Math.max(...values);
      return `Data ranges from ${min} to ${max} across ${points.length} categories`;
    }
    return 'Chart data';
  },
};