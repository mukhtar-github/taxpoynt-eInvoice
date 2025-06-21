/**
 * @deprecated This component is deprecated as of Week 3. 
 * Use `EnhancedIntegrationStatusCard` from `/components/integrations/EnhancedIntegrationStatusCard.tsx` instead.
 * 
 * Migration Guide: See `/docs/Week3_Component_Migration_Guide.md`
 * 
 * This component will be removed in v2.0
 */

import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Typography } from '../ui/Typography';

interface IntegrationStatusCardProps {
  count: number;
  status: string;
  colorScheme: 'primary' | 'success' | 'warning' | 'error' | 'secondary';
}

const IntegrationStatusCard: React.FC<IntegrationStatusCardProps> = ({ 
  count, 
  status, 
  colorScheme 
}) => {
  // Deprecation warning
  React.useEffect(() => {
    console.warn(
      '⚠️ IntegrationStatusCard is deprecated. Use EnhancedIntegrationStatusCard instead. ' +
      'See /docs/Week3_Component_Migration_Guide.md for migration instructions.'
    );
  }, []);

  // Define color variants based on the colorScheme prop
  const getColors = () => {
    switch (colorScheme) {
      case 'success':
        return 'bg-success-100 text-success-600 dark:bg-success-900 dark:text-success-300';
      case 'warning':
        return 'bg-warning-100 text-warning-600 dark:bg-warning-900 dark:text-warning-300';
      case 'error':
        return 'bg-error-100 text-error-600 dark:bg-error-900 dark:text-error-300';
      case 'secondary':
        return 'bg-secondary-100 text-secondary-600 dark:bg-secondary-900 dark:text-secondary-300';
      default: // primary
        return 'bg-primary-100 text-primary-600 dark:bg-primary-900 dark:text-primary-300';
    }
  };

  return (
    <Card className="h-full">
      <CardContent className="p-5">
        <div className="flex justify-between items-center">
          <div>
            <Typography.Text size="sm" variant="secondary">{status} Integrations</Typography.Text>
            <Typography.Text size="xl" weight="bold" className="block mt-1">{count}</Typography.Text>
          </div>
          <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${getColors()}`}>
            {count}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default IntegrationStatusCard; 