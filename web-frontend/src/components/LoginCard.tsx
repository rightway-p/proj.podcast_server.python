import { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
  Text,
} from '@chakra-ui/react';

interface LoginCardProps {
  defaultToken?: string;
  onSubmit: (token: string) => void;
}

export function LoginCard({ defaultToken = '', onSubmit }: LoginCardProps) {
  const [token, setToken] = useState(defaultToken);

  return (
    <Box borderWidth="1px" borderRadius="lg" p={6} maxW="sm" mx="auto">
      <Stack spacing={4}>
        <Heading size="md">API 토큰 입력</Heading>
        <Text fontSize="sm" color="gray.500">
          현재 Automation Service는 인증 없이 사용하지만, 향후 Bearer 토큰 기반 인증을 대비해 입력 필드를 제공합니다.
          토큰이 없다면 비워둬도 됩니다.
        </Text>
        <FormControl>
          <FormLabel>Bearer Token (선택)</FormLabel>
          <Input value={token} onChange={(event) => setToken(event.target.value)} placeholder="예: eyJhbGci..." />
        </FormControl>
        <Stack direction={{ base: 'column', sm: 'row' }} spacing={3}>
          <Button colorScheme="purple" flex={1} onClick={() => onSubmit(token)}>
            토큰 저장
          </Button>
          <Button variant="outline" flex={1} onClick={() => onSubmit('')}>
            토큰 없이 계속
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
}
