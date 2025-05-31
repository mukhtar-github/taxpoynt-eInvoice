import React, { useMemo } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area
} from 'recharts';
import { TransmissionTimeline } from '../../../services/transmissionApiService';

interface TransmissionTimelineChartProps {
  data: TransmissionTimeline;
}

const TransmissionTimelineChart: React.FC<TransmissionTimelineChartProps> = ({ data }) => {
  // Format date for display based on interval
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    
    switch (data.interval) {
      case 'hour':
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      case 'day':
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
      case 'week':
        return `Week ${date.getDate()}/${date.getMonth() + 1}`;
      case 'month':
        return date.toLocaleDateString([], { month: 'short', year: '2-digit' });
      default:
        return date.toLocaleDateString();
    }
  };

  // Process and format data for the chart
  const chartData = useMemo(() => {
    return data.timeline.map(point => ({
      ...point,
      period: formatDate(point.period),
      // Calculate success rate per point
      successRate: point.total > 0 
        ? Math.round((point.completed / point.total) * 100) 
        : 0
    }));
  }, [data.timeline]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <div className="space-y-6">
        {/* Total transmissions line chart */}
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [value, name === 'successRate' ? 'Success Rate %' : name]}
                labelFormatter={(label) => `Period: ${label}`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="total" 
                name="Total"
                stroke="#8884d8" 
                activeDot={{ r: 8 }} 
              />
              <Line 
                type="monotone" 
                dataKey="completed" 
                name="Completed"
                stroke="#82ca9d" 
              />
              <Line 
                type="monotone" 
                dataKey="failed" 
                name="Failed"
                stroke="#ff8042" 
              />
              <Line 
                type="monotone" 
                dataKey="successRate" 
                name="Success Rate %"
                stroke="#0088FE" 
                yAxisId={1}
                orientation="right"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Status breakdown stacked bar chart */}
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="pending" name="Pending" stackId="a" fill="#FFBB28" />
              <Bar dataKey="in_progress" name="In Progress" stackId="a" fill="#0088FE" />
              <Bar dataKey="completed" name="Completed" stackId="a" fill="#00C49F" />
              <Bar dataKey="failed" name="Failed" stackId="a" fill="#FF8042" />
              <Bar dataKey="retrying" name="Retrying" stackId="a" fill="#8884D8" />
              <Bar dataKey="cancelled" name="Cancelled" stackId="a" fill="#AAAAAA" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </ResponsiveContainer>
  );
};

export default TransmissionTimelineChart;
