import React from 'react';
import { Box, Flex } from '@chakra-ui/react';
import { useColorModeValue } from '../ui/ChakraColorMode';
import { Stat, StatLabel, StatNumber } from '../ui/ChakraStat';

interface IntegrationStatusCardProps {
  count: number;
  status: string;
  colorScheme: string;
}

const IntegrationStatusCard: React.FC<IntegrationStatusCardProps> = ({ 
  count, 
  status, 
  colorScheme 
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const statusColor = useColorModeValue(`${colorScheme}.500`, `${colorScheme}.300`);
  const statusBgColor = useColorModeValue(`${colorScheme}.50`, `${colorScheme}.900`);

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
          <StatLabel fontSize="sm" color="gray.500">{status} Integrations</StatLabel>
          <StatNumber fontSize="3xl" fontWeight="bold">{count}</StatNumber>
        </Box>
        <Flex
          w="12"
          h="12"
          bg={statusBgColor}
          color={statusColor}
          rounded="full"
          alignItems="center"
          justifyContent="center"
          fontSize="xl"
          fontWeight="bold"
        >
          {count}
        </Flex>
      </Flex>
    </Box>
  );
};

export default IntegrationStatusCard; 