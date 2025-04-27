import React from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import { useColorModeValue } from '../ui/ChakraColorMode';
import { CircularProgress, CircularProgressLabel } from '../ui/ChakraProgress';

interface ErrorRateCardProps {
  successRate: number;
}

const ErrorRateCard: React.FC<ErrorRateCardProps> = ({ successRate }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  // Determine color based on success rate
  const getColor = () => {
    if (successRate >= 98) return 'green';
    if (successRate >= 90) return 'blue';
    if (successRate >= 80) return 'orange';
    return 'red';
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
          <Text fontSize="sm" color="gray.500">Success Rate</Text>
          <Text fontSize="3xl" fontWeight="bold">{successRate}%</Text>
          <Text fontSize="sm" color="gray.500" mt={1}>of transactions</Text>
        </Box>
        <CircularProgress 
          value={successRate} 
          size="70px" 
          thickness="8px"
          color={`${getColor()}.500`}
          trackColor={useColorModeValue('gray.100', 'gray.700')}
        >
          <CircularProgressLabel fontWeight="bold">
            {successRate}%
          </CircularProgressLabel>
        </CircularProgress>
      </Flex>
    </Box>
  );
};

export default ErrorRateCard; 