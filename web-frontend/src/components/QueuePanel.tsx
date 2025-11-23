import {
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Progress,
  Stack,
  Text,
  useToast,
} from '@chakra-ui/react';
import dayjs from 'dayjs';
import type { Job, PipelineStatus, Playlist } from '../api/types';
import { deleteJobById, triggerManualRun, updateJobById } from '../api/client';

interface QueuePanelProps {
  jobs: Job[];
  playlists: Playlist[];
  token?: string;
  onChanged: () => Promise<void>;
  pipelineStatus: PipelineStatus | null;
  onTriggerPipeline: () => Promise<void>;
  triggeringPipeline: boolean;
}

export function QueuePanel({
  jobs,
  playlists,
  token,
  onChanged,
  pipelineStatus,
  onTriggerPipeline,
  triggeringPipeline,
}: QueuePanelProps) {
  const toast = useToast();
  const playlistLookup = new Map(playlists.map((p) => [p.id, p]));
  const taskLabels: Record<string, string> = {
    downloading: '다운로드 중',
    metadata: '메타데이터 생성 중',
    uploading: 'Castopod 업로드 중',
  };

  const handleDelete = async (jobId: number) => {
    await deleteJobById(jobId, token);
    toast({ title: '작업이 제거되었습니다.', status: 'info', duration: 2000 });
    await onChanged();
  };

  const handleRun = async (job: Job) => {
    await updateJobById(job.id, { status: 'in_progress', progress_message: '웹에서 즉시 실행', current_task: 'manual' }, token);
    await triggerManualRun(job.playlist_id, token);
    await updateJobById(job.id, { status: 'finished', current_task: null, progress_message: '수동 실행 완료' }, token);
    toast({ title: '작업이 실행되었습니다.', status: 'success', duration: 2000 });
    await onChanged();
  };

  const handleCancel = async (job: Job) => {
    await updateJobById(job.id, { status: 'cancelling', progress_message: '취소 요청 중' }, token);
    toast({ title: '취소 요청을 보냈습니다.', status: 'info', duration: 2000 });
    await onChanged();
  };

  const canCancel = (job: Job) => ['queued', 'in_progress'].includes(job.status);
  const canRun = (job: Job) => job.status === 'queued';

  const statusText = pipelineStatus?.running
    ? pipelineStatus.started_at
      ? `시작 ${dayjs(pipelineStatus.started_at).format('MM-DD HH:mm:ss')}`
      : '실행 중'
    : pipelineStatus?.last_finished_at
    ? `마지막 종료 ${dayjs(pipelineStatus.last_finished_at).format('MM-DD HH:mm:ss')} (코드 ${
        pipelineStatus.last_exit_code ?? '-'
      })`
    : '실행 이력 없음';

  return (
    <Box borderWidth="1px" borderRadius="lg" p={5}>
      <Flex justify="space-between" align={{ base: 'flex-start', md: 'center' }} direction={{ base: 'column', md: 'row' }} gap={4}>
        <Stack spacing={1}>
          <Heading size="md">작업 큐</Heading>
          <Text fontSize="sm" color="gray.500">
            등록된 작업을 관리하고 필요 시 바로 실행하세요.
          </Text>
        </Stack>
        <Stack spacing={1} align="flex-end">
          <HStack spacing={2}>
            <Badge colorScheme={pipelineStatus?.running ? 'green' : 'gray'}>
              {pipelineStatus?.running ? '실행 중' : '대기 중'}
            </Badge>
            {pipelineStatus?.running && pipelineStatus.pid ? (
              <Text fontSize="sm" color="gray.400">
                PID {pipelineStatus.pid}
              </Text>
            ) : null}
          </HStack>
          <Text fontSize="xs" color="gray.400">
            {statusText}
          </Text>
          <Button
            size="sm"
            colorScheme="blue"
            onClick={onTriggerPipeline}
            isLoading={triggeringPipeline}
            isDisabled={pipelineStatus?.running}
          >
            큐 실행
          </Button>
        </Stack>
      </Flex>
      <Stack spacing={3} mt={4}>
        {jobs.length === 0 ? <Text color="gray.500">대기 중인 작업이 없습니다.</Text> : null}
        {jobs.map((job) => {
          const playlist = playlistLookup.get(job.playlist_id);
          return (
            <Box key={job.id} borderWidth="1px" borderRadius="md" p={3}>
              <Flex justify="space-between" align={{ base: 'flex-start', md: 'center' }} direction={{ base: 'column', md: 'row' }} gap={2}>
                <Stack spacing={1}>
                  <Text fontWeight="bold">{playlist?.title || playlist?.youtube_playlist_id || `Playlist #${job.playlist_id}`}</Text>
                  <HStack>
                    <Badge>{job.action}</Badge>
                    <Badge colorScheme={job.status === 'queued' ? 'yellow' : job.status === 'finished' ? 'green' : 'purple'}>
                      {job.status}
                    </Badge>
                    {job.should_castopod_upload ? <Badge colorScheme="purple">Castopod 자동 업로드</Badge> : null}
                  </HStack>
                  {job.castopod_slug ? <Text fontSize="sm">Castopod: {job.castopod_slug}</Text> : null}
                  {job.current_task ? (
                    <Text fontSize="sm" color="purple.500">
                      진행 단계: {taskLabels[job.current_task] ?? job.current_task}
                    </Text>
                  ) : null}
                  {job.progress_total > 0 ? (
                    <Stack spacing={1}>
                      <Progress
                        value={
                          job.progress_total
                            ? Math.min(100, Math.round((job.progress_completed / job.progress_total) * 100))
                            : 0
                        }
                        size="sm"
                        colorScheme="purple"
                      />
                      <Text fontSize="xs" color="gray.500">
                        {job.progress_completed}/{job.progress_total}
                      </Text>
                    </Stack>
                  ) : null}
                  {job.progress_message ? (
                    <Text fontSize="sm" color="gray.500">
                      {job.progress_message}
                    </Text>
                  ) : null}
                  {job.note ? (
                    <Text fontSize="sm" color="gray.400">
                      {job.note}
                    </Text>
                  ) : null}
                  <Text fontSize="xs" color="gray.500">
                    등록: {dayjs(job.created_at).format('YYYY-MM-DD HH:mm:ss')}
                  </Text>
                </Stack>
                <HStack>
                  <Button size="sm" variant="outline" onClick={() => handleRun(job)} isDisabled={!canRun(job)}>
                    실행
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    colorScheme="orange"
                    onClick={() => handleCancel(job)}
                    isDisabled={!canCancel(job)}
                  >
                    취소
                  </Button>
                  <Button size="sm" colorScheme="red" variant="ghost" onClick={() => handleDelete(job.id)}>
                    제거
                  </Button>
                </HStack>
              </Flex>
            </Box>
          );
        })}
      </Stack>
    </Box>
  );
}
