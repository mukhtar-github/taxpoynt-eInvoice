import React from 'react';
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
  ChartData
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

// Default styling for all charts
const defaultOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: 'top' as const,
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
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
    },
    y: {
      beginAtZero: true,
    },
  },
};

// Common props for all chart components
interface ChartProps {
  data: ChartData<any>;
  options?: ChartOptions<any>;
  height?: number | string;
  width?: number | string;
  className?: string;
}

// Bar Chart Component
export const BarChart: React.FC<ChartProps> = ({
  data,
  options,
  height,
  width,
  className,
}) => {
  const mergedOptions = {
    ...defaultOptions,
    ...options,
  };

  return (
    <div className={className} style={{ height, width }}>
      <Bar data={data} options={mergedOptions} />
    </div>
  );
};

// Line Chart Component
export const LineChart: React.FC<ChartProps> = ({
  data,
  options,
  height,
  width,
  className,
}) => {
  const mergedOptions = {
    ...defaultOptions,
    ...options,
  };

  return (
    <div className={className} style={{ height, width }}>
      <Line data={data} options={mergedOptions} />
    </div>
  );
};

// Predefined chart themes
export const chartThemes = {
  // Primary theme using brand colors
  primary: {
    backgroundColor: [
      'rgba(59, 130, 246, 0.5)', // blue-500 with opacity
      'rgba(99, 102, 241, 0.5)', // indigo-500 with opacity
      'rgba(139, 92, 246, 0.5)', // purple-500 with opacity
    ],
    borderColor: [
      'rgb(59, 130, 246)', // blue-500
      'rgb(99, 102, 241)', // indigo-500
      'rgb(139, 92, 246)', // purple-500
    ],
    borderWidth: 1,
  },
  
  // Success theme for positive data
  success: {
    backgroundColor: 'rgba(34, 197, 94, 0.5)', // green-500 with opacity
    borderColor: 'rgb(34, 197, 94)', // green-500
    borderWidth: 1,
  },
  
  // Danger theme for negative data
  danger: {
    backgroundColor: 'rgba(239, 68, 68, 0.5)', // red-500 with opacity
    borderColor: 'rgb(239, 68, 68)', // red-500
    borderWidth: 1,
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
