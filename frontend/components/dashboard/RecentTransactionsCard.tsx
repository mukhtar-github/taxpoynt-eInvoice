import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { TransactionLogTable } from '../ui/ResponsiveTable';
import { Typography } from '../ui/Typography';

interface Transaction {
  id: string;
  type: 'irn_generation' | 'validation' | 'submission';
  status: 'success' | 'failed' | 'pending';
  integration: string;
  timestamp: string;
}

interface RecentTransactionsCardProps {
  transactions: Transaction[];
}

const RecentTransactionsCard: React.FC<RecentTransactionsCardProps> = ({ transactions }) => {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>
          <Typography.Heading level="h3">Recent Transactions</Typography.Heading>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <TransactionLogTable transactions={transactions} />
      </CardContent>
    </Card>
  );
};

export default RecentTransactionsCard; 