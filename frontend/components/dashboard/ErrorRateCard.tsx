import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Typography } from '../ui/Typography';

interface ErrorRateCardProps {
  successRate: number;
}

const ErrorRateCard: React.FC<ErrorRateCardProps> = ({ successRate }) => {
  
  // Determine color based on success rate
  const getColor = () => {
    if (successRate >= 98) return 'text-success-600 border-success-500';
    if (successRate >= 90) return 'text-primary-600 border-primary-500';
    if (successRate >= 80) return 'text-warning-600 border-warning-500';
    return 'text-error-600 border-error-500';
  };

  return (
    <Card className="h-full">
      <CardContent className="p-5">
        <div className="flex justify-between items-center">
          <div>
            <Typography.Text size="sm" variant="secondary">Success Rate</Typography.Text>
            <Typography.Text size="xl" weight="bold" className="block mt-1 text-3xl">{successRate}%</Typography.Text>
            <Typography.Text size="sm" variant="secondary" className="mt-1">of transactions</Typography.Text>
          </div>
          
          <div className="relative h-16 w-16 flex items-center justify-center">
            {/* Circular progress background */}
            <div className="absolute inset-0 rounded-full border-8 border-gray-100 dark:border-gray-700"></div>
            
            {/* Circular progress indicator */}
            <svg className="absolute inset-0" width="64" height="64" viewBox="0 0 64 64">
              <circle
                className={getColor()}
                strokeWidth="8"
                stroke="currentColor"
                fill="transparent"
                r="26"
                cx="32"
                cy="32"
                strokeDasharray={`${2 * Math.PI * 26}`}
                strokeDashoffset={`${2 * Math.PI * 26 * (1 - successRate / 100)}`}
                transform="rotate(-90 32 32)"
              />
            </svg>
            
            {/* Progress label */}
            <Typography.Text weight="bold" className="relative z-10 text-sm">
              {successRate}%
            </Typography.Text>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ErrorRateCard; 