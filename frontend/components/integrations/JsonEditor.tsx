import React, { useState } from 'react';
import { Box } from '@chakra-ui/react';
import { useColorModeValue } from '../ui/ChakraColorMode';

interface JsonEditorProps {
  value: Record<string, any>;
  onChange: (value: Record<string, any>) => void;
  height?: string;
}

export const JsonEditor: React.FC<JsonEditorProps> = ({ 
  value, 
  onChange,
  height = '200px'
}) => {
  const [error, setError] = useState<string | null>(null);
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'gray.100');
  
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    try {
      const parsedValue = JSON.parse(e.target.value);
      onChange(parsedValue);
      setError(null);
    } catch (err) {
      setError('Invalid JSON format');
      // Don't update the parent value when there's an error
    }
  };
  
  return (
    <Box position="relative" width="100%">
      <textarea
        value={JSON.stringify(value, null, 2)}
        onChange={handleChange}
        style={{
          fontFamily: 'monospace',
          padding: '12px',
          borderRadius: '4px',
          border: `1px solid ${error ? '#FC8181' : '#E2E8F0'}`,
          width: '100%',
          height,
          resize: 'vertical',
          backgroundColor: bgColor,
          color: textColor
        }}
      />
      
      {error && (
        <Box
          color="red.500"
          fontSize="sm"
          mt={1}
        >
          {error}
        </Box>
      )}
    </Box>
  );
}; 