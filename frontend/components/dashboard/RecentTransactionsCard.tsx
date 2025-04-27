import React from 'react';
import { Box, Badge, Text } from '@chakra-ui/react';
import { useColorModeValue } from '../ui/ChakraColorMode';
import { Table, Thead, Tbody, Tr, Th, Td } from '../ui/ChakraTable';

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
  const headerBgColor = useColorModeValue('gray.50', 'gray.700');

  // Format transaction type for display
  const formatTransactionType = (type: string) => {
    switch (type) {
      case 'irn_generation':
        return 'IRN Generation';
      case 'validation':
        return 'Invoice Validation';
      case 'submission':
        return 'Invoice Submission';
      default:
        return type;
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'green';
      case 'failed':
        return 'red';
      case 'pending':
        return 'yellow';
      default:
        return 'gray';
    }
  };

  return (
    <Box>
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Type</Th>
            <Th>Integration</Th>
            <Th>Timestamp</Th>
            <Th>Status</Th>
          </Tr>
        </Thead>
        <Tbody>
          {transactions.length > 0 ? (
            transactions.map((transaction) => (
              <Tr key={transaction.id}>
                <Td>
                  <Text fontWeight="medium">
                    {formatTransactionType(transaction.type)}
                  </Text>
                </Td>
                <Td>{transaction.integration}</Td>
                <Td>{formatTimestamp(transaction.timestamp)}</Td>
                <Td>
                  <Badge 
                    colorScheme={getStatusColor(transaction.status)}
                    borderRadius="full"
                    px="2"
                  >
                    {transaction.status}
                  </Badge>
                </Td>
              </Tr>
            ))
          ) : (
            <Tr>
              <Td>No transactions found</Td>
            </Tr>
          )}
        </Tbody>
      </Table>
    </Box>
  );
};

export default RecentTransactionsCard; 