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
} from './Table';

export interface Transaction {
  id: string;
  date: string;
  reference: string;
  type: string;
  status: 'success' | 'pending' | 'failed';
  amount: number;
}

interface TransactionTableProps {
  transactions: Transaction[];
  isLoading?: boolean;
  onViewTransaction?: (id: string) => void;
}

export const TransactionTable: React.FC<TransactionTableProps> = ({
  transactions,
  isLoading = false,
  onViewTransaction
}) => {
  // Status indicator component
  const StatusIndicator = ({ status }: { status: Transaction['status'] }) => {
    const statusConfig = {
      success: { color: 'bg-success', label: 'Success' },
      pending: { color: 'bg-warning', label: 'Pending' },
      failed: { color: 'bg-error', label: 'Failed' },
    };
    
    const config = statusConfig[status];
    
    return (
      <div className="flex items-center">
        <div className={`w-2 h-2 rounded-full ${config.color} mr-2`} />
        <span>{config.label}</span>
      </div>
    );
  };
  
  return (
    <TableContainer variant="card">
      <Table minWidth="650px">
        <TableHeader sticky>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Reference ID</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableLoading colSpan={6} />
          ) : transactions.length === 0 ? (
            <TableEmpty colSpan={6} message="No transaction records found" />
          ) : (
            transactions.map((transaction) => (
              <TableRow key={transaction.id}>
                <TableCell className="font-medium">{transaction.date}</TableCell>
                <TableCell>{transaction.reference}</TableCell>
                <TableCell>{transaction.type}</TableCell>
                <TableCell>
                  <StatusIndicator status={transaction.status} />
                </TableCell>
                <TableCell className="text-right font-medium">
                  ₦{transaction.amount.toLocaleString('en-NG')}
                </TableCell>
                <TableCell className="text-right">
                  <button
                    onClick={() => onViewTransaction?.(transaction.id)}
                    className="text-primary hover:underline text-sm"
                  >
                    View
                  </button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}; 