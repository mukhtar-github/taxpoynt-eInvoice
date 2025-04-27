import React from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import { useColorModeValue } from '../ui/ChakraColorMode';
import { Icon } from '../ui/ChakraIcon';
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
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const iconColor = useColorModeValue('blue.500', 'blue.300');

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
    <Box
      bg={bgColor}
      p={5}
      borderRadius="lg"
      boxShadow="sm"
      border="1px"
      borderColor={borderColor}
    >
      <Flex justifyContent="space-between" alignItems="center">
        <Box>
          <Text fontSize="sm" color="gray.500">{title}</Text>
          <Text fontSize="3xl" fontWeight="bold">{count.toLocaleString()}</Text>
          <Text fontSize="sm" color="gray.500" mt={1}>transactions</Text>
        </Box>
        <Flex
          w="12"
          h="12"
          bg="blue.50"
          color={iconColor}
          rounded="full"
          alignItems="center"
          justifyContent="center"
        >
          <Icon as={getIcon()} boxSize="6" />
        </Flex>
      </Flex>
    </Box>
  );
};

export default TransactionMetricsCard; 