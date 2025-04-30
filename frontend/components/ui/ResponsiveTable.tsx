import React from 'react';
import { Box, Text, Flex } from '@chakra-ui/react';

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
    <Box
      width="100%"
      overflowX="auto"
      borderWidth="1px"
      borderColor="var(--color-border)"
      borderRadius="var(--border-radius-lg)"
      boxShadow="sm"
    >
      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '600px' }}>
        <thead style={{ 
          backgroundColor: 'var(--color-background-alt)',
          position: stickyHeader ? 'sticky' : 'static',
          top: 0,
          zIndex: 1
        }}>
          <tr>
            {columns.map((column) => (
              <th
                key={column.id}
                style={{
                  padding: 'var(--spacing-3) var(--spacing-4)',
                  textAlign: 'left',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: 'var(--font-weight-semibold)',
                  borderBottom: '1px solid var(--color-border)',
                  width: column.width,
                  minWidth: column.minWidth
                }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody style={{ 
          maxHeight: maxHeight,
          overflowY: maxHeight ? 'auto' : 'visible',
          display: maxHeight ? 'block' : 'table-row-group',
          width: maxHeight ? '100%' : 'auto'
        }}>
          {isLoading ? (
            <tr>
              <td 
                colSpan={columns.length}
                style={{
                  padding: 'var(--spacing-6)',
                  textAlign: 'center',
                  borderBottom: '1px solid var(--color-border)'
                }}
              >
                <Text color="var(--color-text-secondary)">Loading...</Text>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td 
                colSpan={columns.length}
                style={{
                  padding: 'var(--spacing-6)',
                  textAlign: 'center',
                  borderBottom: '1px solid var(--color-border)'
                }}
              >
                <Text color="var(--color-text-secondary)">{emptyMessage}</Text>
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                style={{
                  backgroundColor: 'white',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-background-alt)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'white';
                }}
              >
                {columns.map((column) => (
                  <td
                    key={`${rowIndex}-${column.id}`}
                    style={{
                      padding: 'var(--spacing-3) var(--spacing-4)',
                      borderBottom: '1px solid var(--color-border)',
                      fontSize: 'var(--font-size-sm)'
                    }}
                  >
                    {column.accessor(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </Box>
  );
};

/**
 * Simplified transaction log table component specifically for transaction data
 */
interface TransactionLogProps {
  transactions: any[];
  isLoading?: boolean;
}

export const TransactionLogTable: React.FC<TransactionLogProps> = ({
  transactions,
  isLoading = false,
}) => {
  const columns: Column[] = [
    {
      id: 'date',
      header: 'Date',
      accessor: (row) => (
        <Text fontWeight="var(--font-weight-medium)">{row.date}</Text>
      ),
      width: '120px',
    },
    {
      id: 'reference',
      header: 'Reference ID',
      accessor: (row) => row.reference,
      width: '200px',
    },
    {
      id: 'type',
      header: 'Type',
      accessor: (row) => row.type,
      width: '150px',
    },
    {
      id: 'status',
      header: 'Status',
      accessor: (row) => {
        const colorMap: Record<string, string> = {
          success: 'var(--color-success)',
          pending: 'var(--color-warning)',
          failed: 'var(--color-error)',
          default: 'var(--color-text-secondary)',
        };
        
        const color = colorMap[row.status.toLowerCase()] || colorMap.default;
        
        return (
          <Flex 
            alignItems="center" 
            justifyContent="flex-start"
          >
            <Box 
              width="8px" 
              height="8px" 
              borderRadius="full" 
              bg={color} 
              mr="var(--spacing-2)" 
            />
            <Text>{row.status}</Text>
          </Flex>
        );
      },
      width: '120px',
    },
    {
      id: 'amount',
      header: 'Amount',
      accessor: (row) => (
        <Text fontWeight="var(--font-weight-medium)" textAlign="right">
          ₦{row.amount.toLocaleString('en-NG')}
        </Text>
      ),
      width: '120px',
    },
    {
      id: 'actions',
      header: '',
      accessor: (row) => (
        <Flex justifyContent="flex-end">
          <Text 
            color="var(--color-primary)" 
            cursor="pointer"
            _hover={{ textDecoration: 'underline' }}
          >
            View
          </Text>
        </Flex>
      ),
      width: '80px',
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