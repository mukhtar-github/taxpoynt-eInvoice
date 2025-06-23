import React, { useRef, useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData,
  ArcElement,
  RadialLinearScale,
  Filler
} from 'chart.js';
import { Bar, Line, Doughnut, PolarArea } from 'react-chartjs-2';
import { LineChart as RechartsLineChart, BarChart as RechartsBarChartOriginal, Area, AreaChart as RechartsAreaChart, Bar as RechartsBar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Design system colors for gradients
const gradientColors = {
  primary: {
    start: 'rgba(59, 130, 246, 0.8)',
    middle: 'rgba(59, 130, 246, 0.4)', 
    end: 'rgba(59, 130, 246, 0.1)',
    solid: 'rgb(59, 130, 246)'
  },
  success: {
    start: 'rgba(16, 185, 129, 0.8)',
    middle: 'rgba(16, 185, 129, 0.4)',
    end: 'rgba(16, 185, 129, 0.1)',
    solid: 'rgb(16, 185, 129)'
  },
  warning: {
    start: 'rgba(245, 158, 11, 0.8)',
    middle: 'rgba(245, 158, 11, 0.4)',
    end: 'rgba(245, 158, 11, 0.1)',
    solid: 'rgb(245, 158, 11)'
  },
  error: {
    start: 'rgba(239, 68, 68, 0.8)',
    middle: 'rgba(239, 68, 68, 0.4)',
    end: 'rgba(239, 68, 68, 0.1)',
    solid: 'rgb(239, 68, 68)'
  },
  purple: {
    start: 'rgba(139, 92, 246, 0.8)',
    middle: 'rgba(139, 92, 246, 0.4)',
    end: 'rgba(139, 92, 246, 0.1)',
    solid: 'rgb(139, 92, 246)'
  }
};

// Default styling for all charts with gradients
const defaultOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        pointStyle: 'circle',
        padding: 20,
        font: {
          size: 12,
          weight: '500'
        }
      }
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
      displayColors: true,
      callbacks: {
        labelColor: function(context: any) {
          return {
            borderColor: context.dataset.borderColor,
            backgroundColor: context.dataset.backgroundColor,
            borderWidth: 2,
            borderRadius: 2
          };
        }
      }
    },
  },
  interaction: {
    mode: 'nearest' as const,
    intersect: false,
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      border: {
        color: 'rgba(156, 163, 175, 0.3)'
      },
      ticks: {
        color: 'rgba(107, 114, 128, 0.8)',
        font: {
          size: 11
        }
      }
    },
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(156, 163, 175, 0.1)',
        borderDash: [2, 4]
      },
      border: {
        color: 'rgba(156, 163, 175, 0.3)'
      },
      ticks: {
        color: 'rgba(107, 114, 128, 0.8)',
        font: {
          size: 11
        }
      }
    },
  },
  animation: {
    duration: 1000,
    easing: 'easeInOutCubic' as const
  }
};

// Common props for all chart components
interface ChartProps {
  data: ChartData<any>;
  options?: ChartOptions<any>;
  height?: number | string;
  width?: number | string;
  className?: string;
  gradientType?: keyof typeof gradientColors;
  animate?: boolean;
}

// Responsive container component
interface ResponsiveChartContainerProps {
  children: React.ReactNode;
  height?: number | string;
  className?: string;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const ResponsiveChartContainer: React.FC<ResponsiveChartContainerProps> = ({
  children,
  height = 400,
  className = '',
  title,
  subtitle,
  actions
}) => {
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setContainerSize({ width: clientWidth, height: clientHeight });
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {(title || subtitle || actions) && (
        <div className="px-6 py-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              )}
              {subtitle && (
                <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
              )}
            </div>
            {actions && (
              <div className="flex items-center gap-2">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}
      <div 
        ref={containerRef}
        className="p-6"
        style={{ height: typeof height === 'number' ? `${height}px` : height }}
      >
        {children}
      </div>
    </div>
  );
};

// Helper function to create gradient background
const createGradient = (ctx: CanvasRenderingContext2D, chartArea: any, colorType: keyof typeof gradientColors) => {
  const colors = gradientColors[colorType];
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  gradient.addColorStop(0, colors.start);
  gradient.addColorStop(0.5, colors.middle);
  gradient.addColorStop(1, colors.end);
  return gradient;
};

// Enhanced Bar Chart Component with gradients
export const BarChart: React.FC<ChartProps> = ({
  data,
  options,
  height = 400,
  width,
  className,
  gradientType = 'primary',
  animate = true
}) => {
  const chartRef = useRef<any>(null);
  const [chartData, setChartData] = useState(data);

  useEffect(() => {
    if (chartRef.current) {
      const chart = chartRef.current;
      const ctx = chart.ctx;
      const chartArea = chart.chartArea;

      if (chartArea) {
        const updatedData = {
          ...data,
          datasets: data.datasets.map((dataset) => ({
            ...dataset,
            backgroundColor: createGradient(ctx, chartArea, gradientType),
            borderColor: gradientColors[gradientType].solid,
            borderWidth: 2,
            borderRadius: 8,
            borderSkipped: false,
          }))
        };
        setChartData(updatedData);
      }
    }
  }, [data, gradientType]);

  const mergedOptions = {
    ...defaultOptions,
    ...options,
    animation: animate ? defaultOptions.animation : false,
    plugins: {
      ...defaultOptions.plugins,
      ...options?.plugins,
    }
  };

  return (
    <div className={className} style={{ height, width, position: 'relative' }}>
      <Bar 
        ref={chartRef}
        data={chartData} 
        options={mergedOptions} 
      />
    </div>
  );
};

// Enhanced Line Chart Component with gradients
export const LineChart: React.FC<ChartProps> = ({
  data,
  options,
  height = 400,
  width,
  className,
  gradientType = 'primary',
  animate = true
}) => {
  const chartRef = useRef<any>(null);
  const [chartData, setChartData] = useState(data);

  useEffect(() => {
    if (chartRef.current) {
      const chart = chartRef.current;
      const ctx = chart.ctx;
      const chartArea = chart.chartArea;

      if (chartArea) {
        const updatedData = {
          ...data,
          datasets: data.datasets.map((dataset) => ({
            ...dataset,
            backgroundColor: createGradient(ctx, chartArea, gradientType),
            borderColor: gradientColors[gradientType].solid,
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: gradientColors[gradientType].solid,
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 6,
            pointHoverRadius: 8,
            pointHoverBackgroundColor: gradientColors[gradientType].solid,
            pointHoverBorderColor: '#ffffff',
            pointHoverBorderWidth: 3
          }))
        };
        setChartData(updatedData);
      }
    }
  }, [data, gradientType]);

  const mergedOptions = {
    ...defaultOptions,
    ...options,
    animation: animate ? defaultOptions.animation : false,
    plugins: {
      ...defaultOptions.plugins,
      ...options?.plugins,
      filler: {
        propagate: false
      }
    },
    elements: {
      point: {
        radius: 0,
        hoverRadius: 8
      }
    }
  };

  return (
    <div className={className} style={{ height, width, position: 'relative' }}>
      <Line 
        ref={chartRef}
        data={chartData} 
        options={mergedOptions} 
      />
    </div>
  );
};

// Doughnut Chart Component
export const DoughnutChart: React.FC<ChartProps> = ({
  data,
  options,
  height = 400,
  width,
  className,
  gradientType = 'primary'
}) => {
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    cutout: '60%',
    plugins: {
      ...defaultOptions.plugins,
      ...options?.plugins,
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 20,
          usePointStyle: true
        }
      }
    }
  };

  return (
    <div className={className} style={{ height, width, position: 'relative' }}>
      <Doughnut data={data} options={mergedOptions} />
    </div>
  );
};

// Area Chart Component using Recharts
export const AreaChart: React.FC<{
  data: any[];
  height?: number;
  className?: string;
  dataKey: string;
  gradientType?: keyof typeof gradientColors;
  animate?: boolean;
}> = ({ 
  data, 
  height = 400, 
  className, 
  dataKey, 
  gradientType = 'primary',
  animate = true 
}) => {
  const colors = gradientColors[gradientType];
  
  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsAreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id={`gradient-${gradientType}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={colors.solid} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={colors.solid} stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(156, 163, 175, 0.2)" />
          <XAxis 
            dataKey="name" 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: 'rgba(107, 114, 128, 0.8)' }}
          />
          <YAxis 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: 'rgba(107, 114, 128, 0.8)' }}
          />
          <RechartsTooltip 
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              border: 'none',
              borderRadius: '8px',
              color: '#ffffff'
            }}
          />
          <Area 
            type="monotone" 
            dataKey={dataKey} 
            stroke={colors.solid}
            strokeWidth={3}
            fillOpacity={1}
            fill={`url(#gradient-${gradientType})`}
            animationDuration={animate ? 1000 : 0}
          />
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Enhanced Recharts Bar Chart
export const RechartsBarChart: React.FC<{
  data: any[];
  height?: number;
  className?: string;
  dataKey: string;
  gradientType?: keyof typeof gradientColors;
  animate?: boolean;
}> = ({ 
  data, 
  height = 400, 
  className, 
  dataKey, 
  gradientType = 'primary',
  animate = true 
}) => {
  const colors = gradientColors[gradientType];
  
  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChartOriginal data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id={`bar-gradient-${gradientType}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={colors.solid} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={colors.solid} stopOpacity={0.4}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(156, 163, 175, 0.2)" />
          <XAxis 
            dataKey="name" 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: 'rgba(107, 114, 128, 0.8)' }}
          />
          <YAxis 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: 'rgba(107, 114, 128, 0.8)' }}
          />
          <RechartsTooltip 
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              border: 'none',
              borderRadius: '8px',
              color: '#ffffff'
            }}
          />
          <RechartsBar 
            dataKey={dataKey} 
            fill={`url(#bar-gradient-${gradientType})`}
            radius={[4, 4, 0, 0]}
            animationDuration={animate ? 1000 : 0}
          />
        </RechartsBarChartOriginal>
      </ResponsiveContainer>
    </div>
  );
};

// Predefined chart themes (legacy support)
export const chartThemes = {
  primary: {
    backgroundColor: [gradientColors.primary.start, gradientColors.primary.middle, gradientColors.primary.end],
    borderColor: [gradientColors.primary.solid, gradientColors.primary.solid, gradientColors.primary.solid],
    borderWidth: 2,
  },
  success: {
    backgroundColor: gradientColors.success.start,
    borderColor: gradientColors.success.solid,
    borderWidth: 2,
  },
  danger: {
    backgroundColor: gradientColors.error.start,
    borderColor: gradientColors.error.solid,
    borderWidth: 2,
  },
};

// Helper to create dataset with theme
export const createDataset = (
  label: string,
  data: number[],
  theme: keyof typeof chartThemes = 'primary',
  index = 0
) => {
  const themeColors = chartThemes[theme];
  
  return {
    label,
    data,
    backgroundColor: Array.isArray(themeColors.backgroundColor)
      ? themeColors.backgroundColor[index % themeColors.backgroundColor.length]
      : themeColors.backgroundColor,
    borderColor: Array.isArray(themeColors.borderColor)
      ? themeColors.borderColor[index % themeColors.borderColor.length]
      : themeColors.borderColor,
    borderWidth: themeColors.borderWidth,
  };
};
