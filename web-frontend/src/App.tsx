import { useEffect, useState } from 'react';
import { Box, Button, Container, Flex, Heading } from '@chakra-ui/react';
import Dashboard from './features/Dashboard';
import { LoginCard } from './components/LoginCard';

const STORAGE_KEY = 'podcast-web-token';

export default function App() {
  const [token, setToken] = useState<string | undefined>();
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved) {
      setToken(saved);
      setAuthenticated(true);
    }
  }, []);

  const handleLogin = (value: string) => {
    const cleaned = value.trim();
    if (cleaned) {
      window.localStorage.setItem(STORAGE_KEY, cleaned);
      setToken(cleaned);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
      setToken(undefined);
    }
    setAuthenticated(true);
  };

  const handleLogout = () => {
    window.localStorage.removeItem(STORAGE_KEY);
    setToken(undefined);
    setAuthenticated(false);
  };

  return (
    <Box minH="100vh" bg="gray.900" color="gray.100" py={10}>
      <Container maxW="7xl">
        {!authenticated ? (
          <LoginCard onSubmit={handleLogin} />
        ) : (
          <Flex direction="column" gap={4}>
            <Flex justify="space-between" align="center">
              <Heading size="md">Automation Service 연결됨</Heading>
              <Button variant="outline" colorScheme="red" onClick={handleLogout}>
                로그아웃
              </Button>
            </Flex>
            <Dashboard token={token} />
          </Flex>
        )}
      </Container>
    </Box>
  );
}
