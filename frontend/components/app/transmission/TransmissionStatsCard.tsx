import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/Card';
import { TransmissionStatus } from '../../../services/transmissionApiService';
import { Badge } from '../../ui/Badge';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertCircle, 
  RotateCw, 
  Ban 
} from 'lucide-react';

interface TransmissionStatsCardProps {
  title: string;
  stats: TransmissionStatus;
}

const TransmissionStatsCard: React.FC<TransmissionStatsCardProps> = ({ title, stats }) => {
  const statusItems = [
    {
      label: 'Pending',
      value: stats.pending,
      icon: <Clock className="h-4 w-4 text-amber-500" />,
      color: 'bg-amber-100 text-amber-800 hover:bg-amber-200'
    },
    {
      label: 'In Progress',
      value: stats.in_progress,
      icon: <AlertCircle className="h-4 w-4 text-blue-500" />,
      color: 'bg-blue-100 text-blue-800 hover:bg-blue-200'
    },
    {
      label: 'Completed',
      value: stats.completed,
      icon: <CheckCircle2 className="h-4 w-4 text-green-500" />,
      color: 'bg-green-100 text-green-800 hover:bg-green-200'
    },
    {
      label: 'Failed',
      value: stats.failed,
      icon: <XCircle className="h-4 w-4 text-red-500" />,
      color: 'bg-red-100 text-red-800 hover:bg-red-200'
    },
    {
      label: 'Retrying',
      value: stats.retrying,
      icon: <RotateCw className="h-4 w-4 text-purple-500" />,
      color: 'bg-purple-100 text-purple-800 hover:bg-purple-200'
    },
    {
      label: 'Canceled',
      value: stats.canceled,
      icon: <Ban className="h-4 w-4 text-gray-500" />,
      color: 'bg-gray-100 text-gray-800 hover:bg-gray-200'
    }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>
          Total of {stats.total} transmissions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {statusItems.map((item) => (
            <div key={item.label} className="flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-2">
                {item.icon}
                <span className="text-sm font-medium">{item.label}</span>
              </div>
              <Badge variant="outline" className={item.color}>
                {item.value}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default TransmissionStatsCard;
