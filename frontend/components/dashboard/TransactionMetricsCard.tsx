import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Typography } from '../ui/Typography';
import { FiCalendar, FiClock } from 'react-icons/fi';

interface TransactionMetricsCardProps {
  title: string;
  count: number;
  icon: string;
}

const TransactionMetricsCard: React.FC<TransactionMetricsCardProps> = ({
  title,
  count,
  icon
}) => {

  // Choose icon based on icon prop
  const getIcon = () => {
    switch (icon) {
      case 'today':
        return FiClock;
      case 'week':
        return FiCalendar;
      case 'month':
        return FiCalendar;
      default:
        return FiClock;
    }
  };

  return (
    <Card className="h-full">
      <CardContent className="p-5">
        <div className="flex justify-between items-center">
          <div>
            <Typography.Text size="sm" variant="secondary">{title}</Typography.Text>
            <Typography.Text size="xl" weight="bold" className="block mt-1">{count.toLocaleString()}</Typography.Text>
            <Typography.Text size="sm" variant="secondary" className="mt-1">transactions</Typography.Text>
          </div>
          <div className="w-12 h-12 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center">
            {React.createElement(getIcon(), { className: 'w-6 h-6' })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TransactionMetricsCard; 