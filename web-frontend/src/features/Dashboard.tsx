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
  updateSchedule,
  deleteSchedule,
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
  Schedule,
  ScheduleFormInput,
  PipelineStatus,
  JobQuickCreateInput,
  DashboardChannel,
  Job,
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
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000';
  const downloadBaseUrl = `${apiBaseUrl.replace(/\/$/, '')}/downloads-browser`;

  const channelModal = useDisclosure();
  const scheduleModal = useDisclosure();
  const queueModal = useDisclosure();
  const jobCreateModal = useDisclosure();
  const [queueTarget, setQueueTarget] = useState<Playlist | null>(null);
  const [scheduleTarget, setScheduleTarget] = useState<Playlist | null>(null);
  const [scheduleMode, setScheduleMode] = useState<'create' | 'edit'>('create');
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);
  const [deletingScheduleId, setDeletingScheduleId] = useState<number | null>(null);
  const scheduleJobToastInitialized = useRef(false);
  const knownScheduleJobIds = useRef<Set<number>>(new Set());
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

  const maybeToastScheduleJobs = (jobs: Job[], channels: DashboardChannel[]) => {
    if (!scheduleJobToastInitialized.current) {
      knownScheduleJobIds.current = new Set(jobs.map((job) => job.id));
      scheduleJobToastInitialized.current = true;
      return;
    }
    const playlistNameMap = new Map<number, string>();
    channels.forEach((channel) => {
      channel.playlists.forEach(({ playlist }) => {
        playlistNameMap.set(playlist.id, playlist.title || playlist.youtube_playlist_id);
      });
    });
    const seen = knownScheduleJobIds.current;
    const now = Date.now();
    const newJobs = jobs.filter((job) => {
      if (seen.has(job.id)) {
        return false;
      }
      const note = job.note ?? '';
      if (!note.includes('스케줄') && !note.toLowerCase().includes('schedule')) {
        return false;
      }
      if (!job.created_at) {
        return false;
      }
      const created = new Date(job.created_at).getTime();
      if (Number.isNaN(created)) {
        return false;
      }
      return now - created <= 90_000;
    });
    newJobs.forEach((job) => {
      const title = playlistNameMap.get(job.playlist_id) ?? `Playlist #${job.playlist_id}`;
      toast({
        title: '스케줄 실행 시작',
        description: `${title} 작업이 자동으로 시작되었습니다.`,
        status: 'info',
        duration: 2500,
      });
    });
    knownScheduleJobIds.current = new Set(jobs.map((job) => job.id));
  };

  const load = async (withSpinner = true, notifyStatusError = false) => {
    if (withSpinner) {
      setLoading(true);
    }
    setError(null);
    try {
      const response = await fetchDashboardData(token);
      maybeToastScheduleJobs(response.jobs ?? [], response.channels ?? []);
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
    () => flatChannels.flatMap((channel) => channel.playlists.map((entry) => entry.playlist)),
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

  const openScheduleModalForCreate = (playlist: Playlist) => {
    setScheduleMode('create');
    setEditingSchedule(null);
    setScheduleTarget(playlist);
    scheduleModal.onOpen();
  };

  const openScheduleModalForEdit = (playlist: Playlist, schedule: Schedule) => {
    setScheduleMode('edit');
    setEditingSchedule(schedule);
    setScheduleTarget(playlist);
    scheduleModal.onOpen();
  };

  const closeScheduleModal = () => {
    setScheduleMode('create');
    setEditingSchedule(null);
    setScheduleTarget(null);
    scheduleModal.onClose();
  };

  const handleScheduleSave = async (payload: ScheduleFormInput, scheduleId?: number) => {
    const isUpdate = typeof scheduleId === 'number';
    try {
      if (isUpdate) {
        await updateSchedule(scheduleId, payload, token);
      } else {
        await createSchedule(payload, token);
      }
      toast({
        title: isUpdate ? '스케줄이 수정되었습니다.' : '스케줄이 생성되었습니다.',
        status: 'success',
        duration: 2000,
      });
      await load(false);
    } catch (err) {
      toast({
        title: isUpdate ? '스케줄 수정 실패' : '스케줄 생성 실패',
        description: err instanceof Error ? err.message : '알 수 없는 오류',
        status: 'error',
        duration: 3000,
      });
      throw err;
    }
  };

  const performScheduleDelete = async (scheduleId: number) => {
    try {
      await deleteSchedule(scheduleId, token);
      toast({ title: '스케줄이 삭제되었습니다.', status: 'success', duration: 2000 });
      await load(false);
    } catch (err) {
      toast({
        title: '스케줄 삭제 실패',
        description: err instanceof Error ? err.message : '알 수 없는 오류',
        status: 'error',
        duration: 3000,
      });
      throw err;
    }
  };

  const handleInlineScheduleDelete = async (schedule: Schedule) => {
    if (!window.confirm('선택한 스케줄을 삭제할까요?')) {
      return;
    }
    setDeletingScheduleId(schedule.id);
    try {
      await performScheduleDelete(schedule.id);
    } finally {
      setDeletingScheduleId(null);
    }
  };

  const handleModalScheduleDelete = async (scheduleId: number) => {
    await performScheduleDelete(scheduleId);
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
        <Button leftIcon={<AddIcon />} variant="solid" colorScheme="teal" onClick={jobCreateModal.onOpen}>
          작업 생성
        </Button>
        <HStack ml="auto" spacing={2}>
          <Text fontSize="sm">자동 새로고침</Text>
          <Switch isChecked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
        </HStack>
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
                      <HStack justify="space-between" mt={3} align="center">
                        <Text fontSize="sm" fontWeight="bold">
                          스케줄
                        </Text>
                        <Button
                          size="xs"
                          variant="ghost"
                          onClick={() => openScheduleModalForCreate(playlist)}
                        >
                          추가
                        </Button>
                      </HStack>
                      {schedules.length === 0 ? (
                        <Text fontSize="sm" color="gray.500">
                          등록된 스케줄 없음
                        </Text>
                      ) : (
                        <Stack spacing={2} mt={2}>
                          {schedules.map((schedule) => (
                            <Flex key={schedule.id} align="center" justify="space-between">
                              <Box>
                                <Text fontSize="sm">
                                  {schedule.days_of_week.join('/')} {schedule.run_time} ({schedule.timezone})
                                </Text>
                                <Text fontSize="xs" color="gray.500">
                                  다음: {schedule.next_run_at || '-'}
                                </Text>
                              </Box>
                              <HStack spacing={1}>
                                <Tooltip label="스케줄 수정">
                                  <IconButton
                                    aria-label="edit schedule"
                                    icon={<EditIcon />}
                                    size="xs"
                                    variant="ghost"
                                    onClick={() => openScheduleModalForEdit(playlist, schedule)}
                                  />
                                </Tooltip>
                                <Tooltip label="스케줄 삭제">
                                  <IconButton
                                    aria-label="delete schedule"
                                    icon={<DeleteIcon />}
                                    size="xs"
                                    colorScheme="red"
                                    variant="ghost"
                                    isLoading={deletingScheduleId === schedule.id}
                                    onClick={() => handleInlineScheduleDelete(schedule)}
                                  />
                                </Tooltip>
                              </HStack>
                            </Flex>
                          ))}
                        </Stack>
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
          <QueuePanel
            jobs={data.jobs}
            playlists={flatPlaylists}
            token={token}
            onChanged={() => load(false)}
            pipelineStatus={pipelineStatus}
            onTriggerPipeline={handleTriggerPipeline}
            triggeringPipeline={triggeringPipeline}
            downloadUrl={downloadBaseUrl}
          />
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
        onClose={closeScheduleModal}
        playlist={scheduleTarget}
        mode={scheduleMode}
        schedule={editingSchedule}
        onSubmit={handleScheduleSave}
        onDelete={
          scheduleMode === 'edit' && editingSchedule
            ? async (scheduleId) => {
                await handleModalScheduleDelete(scheduleId);
              }
            : undefined
        }
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
