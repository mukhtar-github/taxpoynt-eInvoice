import React from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent 
} from '../../components/ui/Card';
import { Progress } from '../../components/ui/Progress';
import { Badge } from '../../components/ui/Badge';
import { Clock, AlertCircle, CheckCircle, Activity } from 'lucide-react';

// Types for IRN status data
export type IRNStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface IRNStatusItem {
  id: string;
  invoiceNumber: string;
  status: IRNStatus;
  timestamp: string;
  businessName: string;
  errorMessage?: string;
}

interface IRNStatusSummary {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  successRate: number;
}

interface IRNStatusMonitorProps {
  recentItems: IRNStatusItem[];
  summary: IRNStatusSummary;
  isLoading?: boolean;
}

// Helper function to get badge color based on status
const getStatusBadge = (status: IRNStatus) => {
  switch (status) {
    case 'pending':
      return <Badge variant="outline" className="flex items-center gap-1"><Clock size={12} /> Pending</Badge>;
    case 'processing':
      return <Badge variant="secondary" className="flex items-center gap-1"><Activity size={12} /> Processing</Badge>;
    case 'completed':
      return <Badge variant="success" className="flex items-center gap-1"><CheckCircle size={12} /> Completed</Badge>;
    case 'failed':
      return <Badge variant="destructive" className="flex items-center gap-1"><AlertCircle size={12} /> Failed</Badge>;
    default:
      return <Badge variant="outline">Unknown</Badge>;
  }
};

const IRNStatusMonitor: React.FC<IRNStatusMonitorProps> = ({ 
  recentItems, 
  summary,
  isLoading = false
}) => {
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <h2 className="text-lg font-semibold">IRN Generation Status</h2>
        <p className="text-sm text-text-secondary">Live monitoring of Invoice Reference Numbers</p>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="py-4 text-center">Loading IRN status data...</div>
        ) : (
          <>
            {/* Summary stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="p-3 bg-background-alt rounded-md">
                <div className="text-sm text-text-secondary mb-1">Success Rate</div>
                <div className="text-xl font-semibold">{summary.successRate}%</div>
              </div>
              <div className="p-3 bg-background-alt rounded-md">
                <div className="text-sm text-text-secondary mb-1">Completed</div>
                <div className="text-xl font-semibold">{summary.completed}</div>
              </div>
              <div className="p-3 bg-background-alt rounded-md">
                <div className="text-sm text-text-secondary mb-1">Pending</div>
                <div className="text-xl font-semibold">{summary.pending + summary.processing}</div>
              </div>
              <div className="p-3 bg-background-alt rounded-md">
                <div className="text-sm text-text-secondary mb-1">Failed</div>
                <div className="text-xl font-semibold">{summary.failed}</div>
              </div>
            </div>

            {/* Progress indicators */}
            <div className="mb-6 space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Processing Status</span>
                  <span className="text-sm text-text-secondary">{summary.completed} of {summary.total}</span>
                </div>
                <Progress value={(summary.completed / summary.total) * 100} />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Failure Rate</span>
                  <span className="text-sm text-text-secondary">{summary.failed} of {summary.total}</span>
                </div>
                <Progress 
                  value={(summary.failed / summary.total) * 100} 
                  variant="destructive"
                />
              </div>
            </div>

            {/* Recent IRN Generation */}
            <h3 className="text-md font-semibold mb-3">Recent IRN Generations</h3>
            <div className="space-y-3">
              {recentItems.length > 0 ? (
                recentItems.map((item) => (
                  <div 
                    key={item.id} 
                    className="flex items-center justify-between p-3 bg-background-alt rounded-md"
                  >
                    <div>
                      <div className="font-medium">{item.invoiceNumber}</div>
                      <div className="text-sm text-text-secondary">{item.businessName}</div>
                      {item.errorMessage && (
                        <div className="text-sm text-destructive mt-1">
                          {item.errorMessage}
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {getStatusBadge(item.status)}
                      <span className="text-xs text-text-secondary">{item.timestamp}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-4 text-text-secondary">
                  No recent IRN generations
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default IRNStatusMonitor;
