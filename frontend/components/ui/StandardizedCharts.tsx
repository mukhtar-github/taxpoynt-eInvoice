/**
 * Standardized Chart Types Library - Week 7 Implementation
 * 
 * Provides a unified interface for all chart types across the platform:
 * - Business Intelligence charts
 * - Performance monitoring charts
 * - Compliance visualization charts
 * - Revenue analytics charts
 * - Integration status charts
 */

import React from 'react';
import { 
  BarChart, 
  LineChart, 
  DoughnutChart, 
  AreaChart, 
  RechartsBarChart,
  ResponsiveChartContainer 
} from './Charts';
import { ResponsiveChartWrapper, ChartGrid, MobileMetricCard } from './ResponsiveCharts';
import { ChartWithTooltip, TooltipData } from './InteractiveTooltips';

// Standard chart data interfaces
export interface StandardChartData {
  labels?: string[];
  datasets?: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
    fill?: boolean;
  }>;
}

export interface RechartsData {
  name: string;
  [key: string]: string | number;
}

// Chart configuration presets
export const ChartPresets = {
  // Revenue and financial charts
  revenue: {
    gradientType: 'success' as const,
    height: 350,
    animate: true,
    options: {
      plugins: {
        legend: {
          display: true,
          position: 'top' as const
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value: any) {
              if (value >= 1000000) return `₦${(value / 1000000).toFixed(1)}M`;
              if (value >= 1000) return `₦${(value / 1000).toFixed(1)}K`;
              return `₦${value}`;
            }
          }
        }
      }
    }
  },

  // Performance monitoring charts
  performance: {
    gradientType: 'primary' as const,
    height: 300,
    animate: true,
    options: {
      plugins: {
        legend: {
          display: true
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value: any) {
              return `${value}%`;
            }
          }
        }
      }
    }
  },

  // Compliance status charts
  compliance: {
    gradientType: 'success' as const,
    height: 280,
    animate: true,
    options: {
      plugins: {
        legend: {
          position: 'bottom' as const
        }
      }
    }
  },

  // Integration status charts
  integration: {
    gradientType: 'purple' as const,
    height: 320,
    animate: true,
    options: {
      indexAxis: 'y' as const,
      plugins: {
        legend: {
          display: false
        }
      }
    }
  },

  // Invoice processing charts
  invoiceProcessing: {
    gradientType: 'primary' as const,
    height: 400,
    animate: true,
    options: {
      plugins: {
        legend: {
          display: true
        }
      }
    }
  }
};

// Standardized chart components for specific use cases

// Revenue Analytics Chart
export const RevenueChart: React.FC<{
  data: StandardChartData | RechartsData[];
  type?: 'line' | 'area' | 'bar';
  title?: string;
  subtitle?: string;
  className?: string;
}> = ({ data, type = 'area', title, subtitle, className }) => {
  const preset = ChartPresets.revenue;

  const renderChart = () => {
    if (Array.isArray(data)) {
      // Recharts data
      switch (type) {
        case 'area':
          return (
            <AreaChart
              data={data}
              dataKey="value"
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
        case 'bar':
          return (
            <RechartsBarChart
              data={data}
              dataKey="value"
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
        default:
          return (
            <AreaChart
              data={data}
              dataKey="value"
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
      }
    } else {
      // Chart.js data
      switch (type) {
        case 'line':
          return (
            <LineChart
              data={data}
              options={preset.options}
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
        case 'bar':
          return (
            <BarChart
              data={data}
              options={preset.options}
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
        default:
          return (
            <LineChart
              data={data}
              options={preset.options}
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
      }
    }
  };

  return (
    <ResponsiveChartWrapper
      title={title || "Revenue Analytics"}
      subtitle={subtitle || "Monthly revenue trends"}
      className={className}
    >
      {renderChart()}
    </ResponsiveChartWrapper>
  );
};

// Performance Monitoring Chart
export const PerformanceChart: React.FC<{
  data: StandardChartData | RechartsData[];
  title?: string;
  subtitle?: string;
  className?: string;
}> = ({ data, title, subtitle, className }) => {
  const preset = ChartPresets.performance;

  return (
    <ResponsiveChartWrapper
      title={title || "Performance Metrics"}
      subtitle={subtitle || "System performance overview"}
      className={className}
    >
      {Array.isArray(data) ? (
        <RechartsBarChart
          data={data}
          dataKey="value"
          gradientType={preset.gradientType}
          animate={preset.animate}
          height={preset.height}
        />
      ) : (
        <BarChart
          data={data}
          options={preset.options}
          gradientType={preset.gradientType}
          animate={preset.animate}
          height={preset.height}
        />
      )}
    </ResponsiveChartWrapper>
  );
};

// Compliance Status Chart
export const ComplianceChart: React.FC<{
  data: StandardChartData;
  title?: string;
  subtitle?: string;
  className?: string;
}> = ({ data, title, subtitle, className }) => {
  const preset = ChartPresets.compliance;

  return (
    <ResponsiveChartWrapper
      title={title || "Compliance Status"}
      subtitle={subtitle || "Current compliance distribution"}
      className={className}
    >
      <DoughnutChart
        data={data}
        options={preset.options}
        gradientType={preset.gradientType}
        height={preset.height}
      />
    </ResponsiveChartWrapper>
  );
};

// Integration Status Chart
export const IntegrationChart: React.FC<{
  data: StandardChartData | RechartsData[];
  title?: string;
  subtitle?: string;
  className?: string;
}> = ({ data, title, subtitle, className }) => {
  const preset = ChartPresets.integration;

  return (
    <ResponsiveChartWrapper
      title={title || "Integration Status"}
      subtitle={subtitle || "Connected systems performance"}
      className={className}
    >
      {Array.isArray(data) ? (
        <RechartsBarChart
          data={data}
          dataKey="value"
          gradientType={preset.gradientType}
          animate={preset.animate}
          height={preset.height}
        />
      ) : (
        <BarChart
          data={data}
          options={preset.options}
          gradientType={preset.gradientType}
          animate={preset.animate}
          height={preset.height}
        />
      )}
    </ResponsiveChartWrapper>
  );
};

// Invoice Processing Chart
export const InvoiceProcessingChart: React.FC<{
  data: StandardChartData | RechartsData[];
  type?: 'line' | 'area' | 'bar';
  title?: string;
  subtitle?: string;
  className?: string;
}> = ({ data, type = 'area', title, subtitle, className }) => {
  const preset = ChartPresets.invoiceProcessing;

  const renderChart = () => {
    if (Array.isArray(data)) {
      switch (type) {
        case 'area':
          return (
            <AreaChart
              data={data}
              dataKey="value"
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
        case 'bar':
          return (
            <RechartsBarChart
              data={data}
              dataKey="value"
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
        default:
          return (
            <AreaChart
              data={data}
              dataKey="value"
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
      }
    } else {
      switch (type) {
        case 'line':
          return (
            <LineChart
              data={data}
              options={preset.options}
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
        case 'bar':
          return (
            <BarChart
              data={data}
              options={preset.options}
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
        default:
          return (
            <LineChart
              data={data}
              options={preset.options}
              gradientType={preset.gradientType}
              animate={preset.animate}
              height={preset.height}
            />
          );
      }
    }
  };

  return (
    <ResponsiveChartWrapper
      title={title || "Invoice Processing"}
      subtitle={subtitle || "Invoice processing trends"}
      className={className}
    >
      {renderChart()}
    </ResponsiveChartWrapper>
  );
};

// Comprehensive dashboard layout
export const BusinessIntelligenceDashboard: React.FC<{
  revenueData?: any;
  performanceData?: any;
  complianceData?: any;
  integrationData?: any;
  invoiceData?: any;
}> = ({ 
  revenueData, 
  performanceData, 
  complianceData, 
  integrationData, 
  invoiceData 
}) => {
  return (
    <div className="space-y-6">
      {/* Top metrics row */}
      <ChartGrid columns={2} gap={6}>
        {revenueData && (
          <RevenueChart 
            data={revenueData} 
            type="area"
          />
        )}
        {performanceData && (
          <PerformanceChart 
            data={performanceData}
          />
        )}
      </ChartGrid>

      {/* Middle row */}
      <ChartGrid columns={3} gap={6}>
        {complianceData && (
          <ComplianceChart 
            data={complianceData}
          />
        )}
        {integrationData && (
          <IntegrationChart 
            data={integrationData}
          />
        )}
        {invoiceData && (
          <InvoiceProcessingChart 
            data={invoiceData}
            type="bar"
          />
        )}
      </ChartGrid>
    </div>
  );
};

// Chart type registry for dynamic chart creation
export const ChartTypeRegistry = {
  revenue: RevenueChart,
  performance: PerformanceChart,
  compliance: ComplianceChart,
  integration: IntegrationChart,
  invoiceProcessing: InvoiceProcessingChart
};

// Utility function to create charts dynamically
export const createChart = (
  type: keyof typeof ChartTypeRegistry,
  props: any
) => {
  const ChartComponent = ChartTypeRegistry[type];
  return <ChartComponent {...props} />;
};

export default {
  RevenueChart,
  PerformanceChart,
  ComplianceChart,
  IntegrationChart,
  InvoiceProcessingChart,
  BusinessIntelligenceDashboard,
  ChartPresets,
  ChartTypeRegistry,
  createChart
};