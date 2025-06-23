import React from 'react';
import { 
  TableContainer,
  Table, 
  TableHeader, 
  TableBody, 
  TableRow, 
  TableHead, 
  TableCell,
  TableEmpty,
  TableLoading
} from '../../ui/Table';
import { Badge } from '../../ui/Badge';
import { Spinner } from '../../ui/Spinner';

interface Transaction {
  id: string;
  external_transaction_id: string;
  transaction_amount: number;
  tax_amount: number;
  transaction_timestamp: string;
  invoice_generated: boolean;
  invoice_transmitted: boolean;
  pos_type: string;
  status: 'pending' | 'processed' | 'failed';
}

interface TransactionsListProps {
  transactions: Transaction[];
  isLoading: boolean;
  error: string | null;
}

const TransactionsList: React.FC<TransactionsListProps> = ({ 
  transactions, 
  isLoading, 
  error 
}) => {
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN'
    }).format(amount);
  };

  const formatDateTime = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString('en-NG', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (transaction: Transaction) => {
    if (transaction.status === 'failed') {
      return <Badge variant="destructive">Failed</Badge>;
    }
    if (transaction.invoice_transmitted) {
      return <Badge variant="success">Transmitted</Badge>;
    }
    if (transaction.invoice_generated) {
      return <Badge variant="warning">Generated</Badge>;
    }
    return <Badge variant="secondary">Pending</Badge>;
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-medium">Error Loading Transactions</h3>
        <p className="text-red-600 text-sm mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Recent Transactions</h3>
        {isLoading && (
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Spinner size="sm" />
            <span>Refreshing...</span>
          </div>
        )}
      </div>
      
      <TableContainer variant="card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Transaction ID</TableHead>
              <TableHead>POS Type</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Tax</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && transactions.length === 0 ? (
              <TableLoading colSpan={6} message="Loading transactions..." />
            ) : transactions.length === 0 ? (
              <TableEmpty 
                colSpan={6} 
                message="No transactions found. Connect a POS system to start processing transactions." 
              />
            ) : (
              transactions.map((transaction) => (
                <TableRow key={transaction.id}>
                  <TableCell className="font-mono text-xs">
                    {transaction.external_transaction_id}
                  </TableCell>
                  <TableCell>
                    <span className="capitalize">{transaction.pos_type}</span>
                  </TableCell>
                  <TableCell className="font-medium">
                    {formatCurrency(transaction.transaction_amount)}
                  </TableCell>
                  <TableCell>
                    {formatCurrency(transaction.tax_amount)}
                  </TableCell>
                  <TableCell>
                    {formatDateTime(transaction.transaction_timestamp)}
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(transaction)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {transactions.length > 0 && (
        <div className="text-sm text-gray-500 text-center">
          Showing {transactions.length} recent transactions
        </div>
      )}
    </div>
  );
};

export { TransactionsList };