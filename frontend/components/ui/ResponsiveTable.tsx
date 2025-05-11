import React from 'react';
import { Typography } from './Typography';
import { Badge, BadgeProps } from './Badge';

interface Column {
  id: string;
  header: React.ReactNode;
  accessor: (row: any) => React.ReactNode;
  width?: string;
  minWidth?: string;
}

interface ResponsiveTableProps {
  columns: Column[];
  data: any[];
  emptyMessage?: string;
  isLoading?: boolean;
  maxHeight?: string;
  stickyHeader?: boolean;
}

/**
 * ResponsiveTable component with horizontal scroll for transaction logs and data
 * Mobile-first design that handles overflow with horizontal scrolling
 */
export const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
  columns,
  data,
  emptyMessage = 'No data available',
  isLoading = false,
  maxHeight,
  stickyHeader = false,
}) => {
  return (
    <div className="w-full overflow-x-auto border border-border rounded-lg shadow-sm">
      <table className="w-full border-collapse" style={{ minWidth: '600px' }}>
        <thead className={`bg-background-alt ${stickyHeader ? 'sticky top-0 z-10' : ''}`}>
          <tr>
            {columns.map((column) => (
              <th
                key={column.id}
                className="px-4 py-3 text-left text-sm font-semibold border-b border-border"
                style={{
                  width: column.width,
                  minWidth: column.minWidth
                }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border" style={{ 
          maxHeight: maxHeight,
          overflowY: maxHeight ? 'auto' : 'visible',
          display: maxHeight ? 'block' : 'table-row-group',
          width: maxHeight ? '100%' : 'auto'
        }}>
          {isLoading ? (
            <tr>
              <td 
                colSpan={columns.length}
                className="px-6 py-6 text-center border-b border-border"
              >
                <span className="text-text-secondary">Loading...</span>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td 
                colSpan={columns.length}
                className="px-6 py-6 text-center border-b border-border"
              >
                <span className="text-text-secondary">{emptyMessage}</span>
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="bg-white hover:bg-background-alt transition-colors duration-200"
              >
                {columns.map((column) => (
                  <td
                    key={`${rowIndex}-${column.id}`}
                    className="px-4 py-3 text-sm"
                  >
                    {column.accessor(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

/**
 * Simplified transaction log table component specifically for transaction data
 */
export interface TransactionLogProps {
  transactions: any[];
  isLoading?: boolean;
}

export const TransactionLogTable: React.FC<TransactionLogProps> = ({
  transactions,
  isLoading = false,
}) => {
  const columns = [
    {
      id: 'type',
      header: 'Transaction Type',
      accessor: (row: any) => (
        <Typography.Text weight="medium">
          {row.type === 'irn_generation' ? 'IRN Generation' : 
           row.type === 'validation' ? 'Validation' : 
           row.type === 'submission' ? 'Submission' : row.type}
        </Typography.Text>
      ),
      width: '30%',
    },
    {
      id: 'integration',
      header: 'Integration',
      accessor: (row: any) => row.integration,
      width: '20%',
    },
    {
      id: 'status',
      header: 'Status',
      accessor: (row: any) => {
        let variant = 'secondary';
        
        if (row.status === 'success') {
          variant = 'success';
        } else if (row.status === 'failed') {
          variant = 'destructive';
        } else if (row.status === 'pending') {
          variant = 'warning';
        }
        
        return (
          <Badge variant={variant as BadgeProps['variant']} className="inline-flex items-center justify-center max-w-[100px]">
            {row.status.charAt(0).toUpperCase() + row.status.slice(1)}
          </Badge>
        );
      },
      width: '20%',
    },
    {
      id: 'timestamp',
      header: 'Date & Time',
      accessor: (row: any) => {
        const date = new Date(row.timestamp);
        return date.toLocaleString();
      },
      width: '30%',
    },
  ];

  return (
    <ResponsiveTable
      columns={columns}
      data={transactions}
      isLoading={isLoading}
      emptyMessage="No transaction records found"
      stickyHeader
      maxHeight="400px"
    />
  );
};

export default ResponsiveTable; 