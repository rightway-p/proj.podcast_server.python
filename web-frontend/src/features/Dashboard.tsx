import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  AlertDescription,
  AlertIcon,
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  IconButton,
  SimpleGrid,
  Spinner,
  Stack,
  Text,
  Tooltip,
  useColorMode,
  useColorModeValue,
  useDisclosure,
  Switch,
  useToast,
  AlertDialog,
  AlertDialogOverlay,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
} from '@chakra-ui/react';
import { RepeatIcon, SunIcon, MoonIcon, AddIcon, EditIcon, DeleteIcon } from '@chakra-ui/icons';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

import {
  fetchDashboardData,
  createSchedule,
  createJob,
  updateChannel,
  deleteChannel,
  fetchCastopodPodcasts,
  deleteJobById,
  triggerManualRun,
  updateJobById,
  fetchPipelineStatus,
  triggerPipelineRun,
  quickCreateJob,
} from '../api/client';
import type {
  CastopodPodcast,
  DashboardData,
  Playlist,
  Channel,
  ChannelFormInput,
  PipelineStatus,
  JobQuickCreateInput,
} from '../api/types';
import { ChannelModal } from '../components/forms/ChannelModal';
import { ScheduleModal } from '../components/forms/ScheduleModal';
import { QueueModal } from '../components/forms/QueueModal';
import { JobCreateModal } from '../components/forms/JobCreateModal';
import { RunsPanel } from '../components/RunsPanel';
import { QueuePanel } from '../components/QueuePanel';

dayjs.extend(utc);
dayjs.extend(timezone);

type DashboardProps = {
  token?: string;
};

export default function Dashboard({ token }: DashboardProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { colorMode, toggleColorMode } = useColorMode();
  const toast = useToast();

  const channelModal = useDisclosure();
  const scheduleModal = useDisclosure();
  const queueModal = useDisclosure();
  const jobCreateModal = useDisclosure();
  const [queueTarget, setQueueTarget] = useState<Playlist | null>(null);
  const [editingChannel, setEditingChannel] = useState<Channel | null>(null);
  const [channelToDelete, setChannelToDelete] = useState<Channel | null>(null);
  const deleteDialog = useDisclosure();
  const cancelDeleteRef = useRef<HTMLButtonElement | null>(null);
  const [deletingChannel, setDeletingChannel] = useState(false);
  const [castopodPodcasts, setCastopodPodcasts] = useState<CastopodPodcast[]>([]);
  const [fetchingCastopod, setFetchingCastopod] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [triggeringPipeline, setTriggeringPipeline] = useState(false);

  const loadPipelineStatus = async (notifyError = false) => {
    try {
      const status = await fetchPipelineStatus(token);
      setPipelineStatus(status);
    } catch (err) {
      setPipelineStatus(null);
      if (notifyError) {
        toast({
          title: '파이프라인 상태 조회 실패',
          description: err instanceof Error ? err.message : '알 수 없는 오류',
          status: 'error',
          duration: 2500,
        });
      }
    }
  };

  const load = async (withSpinner = true, notifyStatusError = false) => {
    if (withSpinner) {
      setLoading(true);
    }
    setError(null);
    try {
      const response = await fetchDashboardData(token);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      await loadPipelineStatus(notifyStatusError);
      if (withSpinner) {
        setLoading(false);
      }
    }
  };

  const loadCastopodPodcasts = async () => {
    setFetchingCastopod(true);
    try {
      const list = await fetchCastopodPodcasts(token);
      setCastopodPodcasts(list);
      if (!list.length) {
        toast({
          title: '목록이 비어 있습니다.',
          description: 'Castopod DB 접근 설정을 확인하세요.',
          status: 'info',
          duration: 2500,
        });
      }
    } catch (err) {
      toast({
        title: 'Castopod 목록 조회 실패',
        description: err instanceof Error ? err.message : '알 수 없는 오류',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setFetchingCastopod(false);
    }
  };

  const handleQuickJobCreate = async (payload: JobQuickCreateInput) => {
    try {
      const result = await quickCreateJob(payload, token);
      toast({
        title: '작업이 생성되었습니다.',
        description: `${result.playlist.title ?? result.playlist.youtube_playlist_id} → 큐에 추가됨`,
        status: 'success',
        duration: 2500,
      });
      await load();
    } catch (err) {
      const detail = (err as any)?.response?.data?.detail;
      toast({
        title: '작업 생성 실패',
        description: detail ?? (err instanceof Error ? err.message : '알 수 없는 오류'),
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleTriggerPipeline = async () => {
    setTriggeringPipeline(true);
    try {
      const status = await triggerPipelineRun(token);
      setPipelineStatus(status);
      toast({
        title: '파이프라인 실행 시작',
        description: '실행 로그에서 진행률을 확인하세요.',
        status: 'success',
        duration: 2500,
      });
    } catch (err) {
      const detail = (err as any)?.response?.data?.detail;
      toast({
        title: '파이프라인 실행 실패',
        description: detail ?? (err instanceof Error ? err.message : '알 수 없는 오류'),
        status: 'error',
        duration: 3000,
      });
    } finally {
      setTriggeringPipeline(false);
      await loadPipelineStatus(false);
    }
  };

  useEffect(() => {
    load(true, true);
  }, [token]);

  useEffect(() => {
    if (!autoRefresh) {
      return () => undefined;
    }
    const id = setInterval(() => {
      load(false);
    }, 30000);
    return () => clearInterval(id);
  }, [autoRefresh, token]);

  const bgCard = useColorModeValue('gray.50', 'gray.700');
  const flatChannels = data?.channels ?? [];
  const flatPlaylists: Playlist[] = useMemo(
    () =>
      flatChannels.flatMap((channel) =>
        channel.playlists.map((entry) => ({ channel_id: channel.id, ...entry.playlist }))
      ),
    [flatChannels]
  );

  const openEditChannelModal = (channel: Channel) => {
    setEditingChannel(channel);
    channelModal.onOpen();
  };

  const handleUpdateChannel = async (payload: ChannelFormInput) => {
    if (!editingChannel) return;
    await updateChannel(editingChannel.id, { title: payload.title, description: payload.description });
    toast({ title: '채널이 수정되었습니다.', status: 'success', duration: 2000 });
    setEditingChannel(null);
    await load();
  };

  const openDeleteChannelDialog = (channel: Channel) => {
    setChannelToDelete(channel);
    deleteDialog.onOpen();
  };

  const handleDeleteChannel = async () => {
    if (!channelToDelete) return;
    setDeletingChannel(true);
    try {
      await deleteChannel(channelToDelete.id, token);
      toast({ title: '채널이 삭제되었습니다.', status: 'success', duration: 2000 });
      setChannelToDelete(null);
      deleteDialog.onClose();
      await load();
    } catch (err) {
      toast({
        title: '채널 삭제 실패',
        description: err instanceof Error ? err.message : '알 수 없는 오류',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setDeletingChannel(false);
    }
  };

  return (
    <Stack spacing={6} py={6} px={4} maxW="6xl" mx="auto">
      <Flex justify="space-between" align="center">
        <Box>
          <Heading size="lg">파이프라인 대시보드</Heading>
          <Text fontSize="sm" color="gray.500">
            Automation Service에서 직접 읽어온 채널/플레이리스트/스케줄 현황
          </Text>
        </Box>
        <HStack>
          <Tooltip label="색상 모드 전환">
            <IconButton
              aria-label="toggle color mode"
              icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
              onClick={toggleColorMode}
            />
          </Tooltip>
          <Button leftIcon={<RepeatIcon />} onClick={() => load()} isLoading={loading}>
            새로고침
          </Button>
        </HStack>
      </Flex>

      <Flex gap={3} wrap="wrap" align="center">
        <Button leftIcon={<AddIcon />} variant="outline" onClick={scheduleModal.onOpen} isDisabled={!flatPlaylists.length}>
          스케줄 추가
        </Button>
        <Button leftIcon={<AddIcon />} variant="solid" colorScheme="teal" onClick={jobCreateModal.onOpen}>
          작업 생성
        </Button>
        <Flex ml="auto" gap={4} wrap="wrap" align="center" justify="flex-end">
          <HStack spacing={2}>
            <Text fontSize="sm">자동 새로고침</Text>
            <Switch isChecked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
          </HStack>
          <Stack spacing={1} align="flex-end" minW="220px">
            <HStack spacing={2}>
              <Badge colorScheme={pipelineStatus?.running ? 'green' : 'gray'}>
                {pipelineStatus?.running ? '실행 중' : '대기 중'}
              </Badge>
              {pipelineStatus?.running && pipelineStatus?.pid ? (
                <Text fontSize="sm" color="gray.300">
                  PID {pipelineStatus.pid}
                </Text>
              ) : null}
            </HStack>
            <Text fontSize="xs" color="gray.400">
              {pipelineStatus?.running
                ? `시작 ${pipelineStatus.started_at ? dayjs(pipelineStatus.started_at).format('MM-DD HH:mm:ss') : '-'}`
                : pipelineStatus?.last_finished_at
                ? `마지막 종료 ${dayjs(pipelineStatus.last_finished_at).format('MM-DD HH:mm:ss')} (코드 ${
                    pipelineStatus.last_exit_code ?? '-'
                  })`
                : '실행 이력 없음'}
            </Text>
            <Button
              size="sm"
              colorScheme="blue"
              onClick={handleTriggerPipeline}
              isLoading={triggeringPipeline}
              isDisabled={pipelineStatus?.running}
            >
              파이프라인 실행
            </Button>
          </Stack>
        </Flex>
      </Flex>

      {error ? (
        <Alert status="error">
          <AlertIcon />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {loading && !data ? (
        <Flex justify="center" py={12}>
          <Spinner size="xl" />
        </Flex>
      ) : null}

      {data ? (
        <Stack spacing={4}>
          <Text fontSize="sm" color="gray.500">
            마지막 동기화: {dayjs(data.fetchedAt).format('YYYY-MM-DD HH:mm:ss')}
          </Text>
          {data.channels.length === 0 ? (
            <Alert status="info">
              <AlertIcon />
              채널이 없습니다. TUI나 API를 통해 채널을 등록해 주세요.
            </Alert>
          ) : (
            data.channels.map((channel) => (
              <Box key={channel.id} borderWidth="1px" borderRadius="lg" p={5} bg={bgCard}>
                <Flex justify="space-between" align={{ base: 'flex-start', md: 'center' }} direction={{ base: 'column', md: 'row' }}>
                  <Box>
                    <Heading size="md">{channel.title}</Heading>
                    <Text fontSize="sm" color="gray.500">
                      slug: {channel.slug}
                    </Text>
                    {channel.description ? <Text mt={2}>{channel.description}</Text> : null}
                  </Box>
                  <HStack spacing={2} mt={{ base: 4, md: 0 }}>
                    <Badge colorScheme="purple">{channel.playlists.length} playlists</Badge>
                    <Tooltip label="채널 수정">
                      <IconButton
                        aria-label="edit channel"
                        size="sm"
                        icon={<EditIcon />}
                        onClick={() => openEditChannelModal(channel)}
                      />
                    </Tooltip>
                    <Tooltip label="채널 삭제">
                      <IconButton
                        aria-label="delete channel"
                        size="sm"
                        colorScheme="red"
                        icon={<DeleteIcon />}
                        onClick={() => openDeleteChannelDialog(channel)}
                      />
                    </Tooltip>
                  </HStack>
                </Flex>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mt={4}>
                  {channel.playlists.map(({ playlist, schedules, recentRuns }) => (
                    <Box key={playlist.id} borderWidth="1px" borderRadius="md" p={4}>
                      <Heading size="sm" mb={1}>
                        {playlist.title || playlist.youtube_playlist_id}
                      </Heading>
                      <Badge colorScheme={playlist.is_active ? 'green' : 'gray'}>
                        {playlist.is_active ? '활성' : '비활성'}
                      </Badge>
                      <Text fontSize="xs" color="gray.500" mt={2}>
                        YT playlist: {playlist.youtube_playlist_id}
                      </Text>
                      {playlist.castopod_slug || playlist.castopod_uuid ? (
                        <Stack spacing={1} mt={2} fontSize="xs" color="gray.400">
                          {playlist.castopod_slug ? <Text>Castopod slug: {playlist.castopod_slug}</Text> : null}
                          {playlist.castopod_uuid ? <Text>Castopod UUID: {playlist.castopod_uuid}</Text> : null}
                        </Stack>
                      ) : null}
                      <Text fontSize="sm" mt={3} fontWeight="bold">
                        스케줄
                      </Text>
                      {schedules.length === 0 ? (
                        <Text fontSize="sm" color="gray.500">
                          등록된 스케줄 없음
                        </Text>
                      ) : (
                        schedules.map((schedule) => (
                          <Text key={schedule.id} fontSize="sm">
                            {schedule.cron_expression} ({schedule.timezone}) · 다음: {schedule.next_run_at || '-'}
                          </Text>
                        ))
                      )}
                      <Text fontSize="sm" mt={3} fontWeight="bold">
                        최근 실행
                      </Text>
                      {recentRuns.length === 0 ? (
                        <Text fontSize="sm" color="gray.500">
                          실행 기록 없음
                        </Text>
                      ) : (
                        recentRuns.slice(0, 3).map((run) => (
                          <HStack key={run.id} spacing={3} align="center">
                            <Badge
                              colorScheme={
                                run.status === 'finished'
                                  ? 'green'
                                  : run.status === 'failed'
                                  ? 'red'
                                  : 'yellow'
                              }
                            >
                              {run.status}
                            </Badge>
                            <Text fontSize="xs">
                              {dayjs(run.started_at).format('MM-DD HH:mm')} →{' '}
                              {run.finished_at ? dayjs(run.finished_at).format('HH:mm') : '진행 중'}
                            </Text>
                          </HStack>
                        ))
                      )}
                      <HStack justify="flex-end" mt={3}>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setQueueTarget({ ...playlist, channel_id: channel.id });
                            queueModal.onOpen();
                          }}
                        >
                          큐에 추가
                        </Button>
                      </HStack>
                    </Box>
                  ))}
                </SimpleGrid>
              </Box>
            ))
          )}
          <QueuePanel jobs={data.jobs} playlists={flatPlaylists} token={token} onChanged={() => load()} />
          <RunsPanel runs={data.runs} playlists={flatPlaylists} token={token} onTriggered={() => load()} />
        </Stack>
      ) : null}

      <ChannelModal
        isOpen={channelModal.isOpen}
        mode="edit"
        initialValue={
          editingChannel
            ? {
                slug: editingChannel.slug,
                title: editingChannel.title,
                description: editingChannel.description ?? '',
              }
            : undefined
        }
        onClose={() => {
          setEditingChannel(null);
          channelModal.onClose();
        }}
        onSubmit={handleUpdateChannel}
      />
      <ScheduleModal
        isOpen={scheduleModal.isOpen}
        onClose={scheduleModal.onClose}
        playlists={flatPlaylists}
        onSubmit={async (payload) => {
          await createSchedule(payload, token);
          toast({ title: '스케줄이 생성되었습니다.', status: 'success', duration: 2000 });
          await load();
        }}
      />
      <JobCreateModal
        isOpen={jobCreateModal.isOpen}
        onClose={jobCreateModal.onClose}
        castopodPodcasts={castopodPodcasts}
        onFetchCastopodPodcasts={loadCastopodPodcasts}
        isFetchingCastopod={fetchingCastopod}
        onSubmit={async (payload) => {
          await handleQuickJobCreate(payload);
          jobCreateModal.onClose();
        }}
      />
      <QueueModal
        isOpen={queueModal.isOpen}
        onClose={queueModal.onClose}
        playlists={flatPlaylists}
        defaultPlaylist={queueTarget ?? undefined}
        onSubmit={async (payload) => {
          await createJob(payload, token);
          toast({ title: '작업이 큐에 추가되었습니다.', status: 'success', duration: 2000 });
          await load();
        }}
      />
      <AlertDialog
        isOpen={deleteDialog.isOpen}
        leastDestructiveRef={cancelDeleteRef}
        onClose={() => {
          deleteDialog.onClose();
          setChannelToDelete(null);
        }}
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              채널 삭제
            </AlertDialogHeader>

            <AlertDialogBody>
              {channelToDelete
                ? `"${channelToDelete.title}" 채널과 연결된 플레이리스트/스케줄을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`
                : '선택된 채널이 없습니다.'}
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button ref={cancelDeleteRef} onClick={() => deleteDialog.onClose()}>
                취소
              </Button>
              <Button colorScheme="red" onClick={handleDeleteChannel} ml={3} isLoading={deletingChannel}>
                삭제
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Stack>
  );
}
