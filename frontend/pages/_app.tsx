import React from 'react';
import type { AppProps } from 'next/app';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import '../styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ChakraProvider value={defaultSystem}>
      <Component {...pageProps} />
    </ChakraProvider>
  );
}

export default MyApp; 