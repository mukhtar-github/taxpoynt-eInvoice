import React from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent, 
  CardTitle, 
  CardDescription 
} from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Badge } from '../ui/Badge';
import { BarChart, LineChart } from '../ui/Charts';

export interface TransactionMetricsData {
  daily: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
    }[];
  };
  weekly: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
    }[];
  };
  monthly: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
    }[];
  };
  summary: {
    totalCount: number;
    successCount: number;
    failureCount: number;
    averagePerDay: number;
    trend: 'up' | 'down' | 'stable';
    changePercentage: number;
  };
}

interface TransactionMetricsProps {
  data: TransactionMetricsData;
  isLoading?: boolean;
}

const TransactionMetrics: React.FC<TransactionMetricsProps> = ({ 
  data,
  isLoading = false
}) => {
  const trendBadge = () => {
    const { trend, changePercentage } = data.summary;
    
    if (trend === 'up') {
      return (
        <Badge variant="success" className="ml-2">
          +{changePercentage}%
        </Badge>
      );
    } else if (trend === 'down') {
      return (
        <Badge variant="destructive" className="ml-2">
          -{changePercentage}%
        </Badge>
      );
    } 
    
    return (
      <Badge variant="outline" className="ml-2">
        {changePercentage}%
      </Badge>
    );
  };

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Transaction Metrics</CardTitle>
        <CardDescription>Invoice transaction volume and trends</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="py-4 text-center">Loading transaction metrics...</div>
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="p-3 bg-background-alt rounded-md">
                <div className="text-sm text-text-secondary mb-1">Total Transactions</div>
                <div className="text-xl font-semibold flex items-center">
                  {data.summary.totalCount}
                  {trendBadge()}
                </div>
              </div>
              <div className="p-3 bg-background-alt rounded-md">
                <div className="text-sm text-text-secondary mb-1">Successful</div>
                <div className="text-xl font-semibold">{data.summary.successCount}</div>
              </div>
              <div className="p-3 bg-background-alt rounded-md">
                <div className="text-sm text-text-secondary mb-1">Failed</div>
                <div className="text-xl font-semibold">{data.summary.failureCount}</div>
              </div>
              <div className="p-3 bg-background-alt rounded-md">
                <div className="text-sm text-text-secondary mb-1">Avg. Daily</div>
                <div className="text-xl font-semibold">{data.summary.averagePerDay}</div>
              </div>
            </div>

            <Tabs defaultValue="daily" className="w-full">
              <TabsList>
                <TabsTrigger value="daily">Daily</TabsTrigger>
                <TabsTrigger value="weekly">Weekly</TabsTrigger>
                <TabsTrigger value="monthly">Monthly</TabsTrigger>
              </TabsList>
              
              <div className="h-64 mt-4">
                <TabsContent value="daily" className="h-full">
                  <BarChart 
                    data={data.daily}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                        }
                      }
                    }}
                  />
                </TabsContent>
                
                <TabsContent value="weekly" className="h-full">
                  <BarChart 
                    data={data.weekly}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                        }
                      }
                    }}
                  />
                </TabsContent>
                
                <TabsContent value="monthly" className="h-full">
                  <LineChart 
                    data={data.monthly}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                        }
                      }
                    }}
                  />
                </TabsContent>
              </div>
            </Tabs>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default TransactionMetrics;
