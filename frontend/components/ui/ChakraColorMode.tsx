import React from 'react';

// Simple implementation of useColorModeValue that always returns the light mode value
export function useColorModeValue(lightValue: any, darkValue: any) {
  // Since we don't have access to the actual color mode, 
  // we'll default to light mode
  return lightValue;
} 