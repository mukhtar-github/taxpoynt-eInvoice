import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { Box, Spinner, Center } from '@chakra-ui/react';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.push('/dashboard');
  }, [router]);

  return (
    <Center h="100vh">
      <Box textAlign="center">
        <Spinner size="xl" color="blue.500" mb={4} />
        <Box>Redirecting to dashboard...</Box>
      </Box>
    </Center>
  );
} 