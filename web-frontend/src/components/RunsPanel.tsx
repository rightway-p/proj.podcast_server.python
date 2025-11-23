import {
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  Input,
  Progress,
  Stack,
  Text,
} from '@chakra-ui/react';
import { useMemo, useState } from 'react';
import dayjs from 'dayjs';
import type { RunRecord, Playlist } from '../api/types';
import { triggerManualRun } from '../api/client';

interface RunsPanelProps {
  runs: RunRecord[];
  playlists: Playlist[];
  token?: string;
  onTriggered: () => Promise<void>;
}

export function RunsPanel({ runs, playlists, token, onTriggered }: RunsPanelProps) {
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState<number | null>(null);

  const filtered = useMemo(() => {
    const phrase = filter.trim().toLowerCase();
    if (!phrase) return runs;
    return runs.filter((run) => run.status.toLowerCase().includes(phrase) || (run.message ?? '').toLowerCase().includes(phrase));
  }, [runs, filter]);

  const playlistMap = useMemo(() => new Map(playlists.map((p) => [p.id, p])), [playlists]);

  const colorForStatus = (status: string) => {
    if (status === 'finished') return 'green';
    if (status === 'failed') return 'red';
    if (status === 'manual_trigger') return 'purple';
    return 'yellow';
  };

  const handleTrigger = async (playlistId: number) => {
    setLoading(playlistId);
    try {
      await triggerManualRun(playlistId, token);
      await onTriggered();
    } finally {
      setLoading(null);
    }
  };

  return (
    <Box borderWidth="1px" borderRadius="lg" p={5}>
      <Flex justify="space-between" align={{ base: 'flex-start', md: 'center' }} direction={{ base: 'column', md: 'row' }} mb={4} gap={3}>
        <Box>
          <Heading size="md">실행 로그</Heading>
          <Text fontSize="sm" color="gray.500">
            상태/메시지 필터로 검색하고 필요 시 수동 실행을 트리거할 수 있습니다.
          </Text>
        </Box>
        <Input placeholder="status 또는 메시지 필터" value={filter} onChange={(e) => setFilter(e.target.value)} maxW="300px" />
      </Flex>
      <Stack spacing={3} maxH="360px" overflowY="auto">
        {filtered.map((run) => {
          const playlist = playlistMap.get(run.playlist_id);
          const total = run.progress_total ?? 0;
          const completed = run.progress_completed ?? 0;
          const percent = total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : null;
          return (
            <Box key={run.id} borderWidth="1px" borderRadius="md" p={3}>
              <Flex justify="space-between" align="center" flexWrap="wrap" gap={2}>
                <Stack spacing={1}>
                  <Text fontWeight="bold">{playlist?.title || playlist?.youtube_playlist_id || `Playlist #${run.playlist_id}`}</Text>
                  <Text fontSize="sm" color="gray.400">
                    {dayjs(run.started_at).format('YYYY-MM-DD HH:mm:ss')} → {run.finished_at ? dayjs(run.finished_at).format('HH:mm:ss') : '진행 중'}
                  </Text>
                  {run.message ? (
                    <Text fontSize="sm" color="gray.300">
                      {run.message}
                    </Text>
                  ) : null}
                  {(run.current_task || run.progress_message || percent !== null) && (
                    <Box>
                      {run.current_task ? (
                        <Text fontSize="xs" color="gray.400">
                          {run.current_task}
                        </Text>
                      ) : null}
                      {run.progress_message ? (
                        <Text fontSize="xs" color="gray.400">
                          {run.progress_message}
                          {percent !== null ? ` (${completed}/${total})` : null}
                        </Text>
                      ) : null}
                      {percent !== null ? (
                        <Progress value={percent} size="xs" colorScheme="blue" borderRadius="sm" mt={1} />
                      ) : null}
                    </Box>
                  )}
                </Stack>
                <Stack direction="row" spacing={2} align="center">
                  <Badge colorScheme={colorForStatus(run.status)}>{run.status}</Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleTrigger(run.playlist_id)}
                    isLoading={loading === run.playlist_id}
                  >
                    수동 실행
                  </Button>
                </Stack>
              </Flex>
            </Box>
          );
        })}
        {filtered.length === 0 ? <Text color="gray.500">조건에 맞는 실행 로그가 없습니다.</Text> : null}
      </Stack>
    </Box>
  );
}
