import axios from 'axios';
import type {
  Channel,
  CastopodPodcast,
  Playlist,
  Schedule,
  RunRecord,
  DashboardData,
  DashboardChannel,
  ChannelFormInput,
  PlaylistFormInput,
  ScheduleFormInput,
  Job,
  JobFormInput,
  PipelineStatus,
  JobQuickCreateInput,
  JobQuickCreateResponse,
} from './types';

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

function buildClient(token?: string) {
  return axios.create({
    baseURL,
    timeout: 8000,
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : undefined,
  });
}

export async function fetchDashboardData(token?: string): Promise<DashboardData> {
  const client = buildClient(token);
  const [channelsRes, playlistsRes, schedulesRes, runsRes, jobsRes] = await Promise.all([
    client.get<Channel[]>('/channels/'),
    client.get<Playlist[]>('/playlists/'),
    client.get<Schedule[]>('/schedules/'),
    client.get<RunRecord[]>('/runs/?limit=50').catch(() => ({ data: [] as RunRecord[] })),
    client.get<Job[]>('/jobs/').catch(() => ({ data: [] as Job[] })),
  ]);

  const runsByPlaylist = new Map<number, RunRecord[]>();
  for (const run of runsRes.data ?? []) {
    const bucket = runsByPlaylist.get(run.playlist_id) ?? [];
    bucket.push(run);
    runsByPlaylist.set(run.playlist_id, bucket);
  }

  const schedulesByPlaylist = new Map<number, Schedule[]>();
  for (const schedule of schedulesRes.data ?? []) {
    const bucket = schedulesByPlaylist.get(schedule.playlist_id) ?? [];
    bucket.push(schedule);
    schedulesByPlaylist.set(schedule.playlist_id, bucket);
  }

  const playlistsByChannel = new Map<number, Playlist[]>();
  for (const playlist of playlistsRes.data ?? []) {
    const bucket = playlistsByChannel.get(playlist.channel_id) ?? [];
    bucket.push(playlist);
    playlistsByChannel.set(playlist.channel_id, bucket);
  }

  const dashboardChannels: DashboardChannel[] = channelsRes.data.map((channel) => {
    const channelPlaylists = playlistsByChannel.get(channel.id) ?? [];
    return {
      ...channel,
      playlists: channelPlaylists.map((playlist) => ({
        playlist,
        schedules: schedulesByPlaylist.get(playlist.id) ?? [],
        recentRuns: runsByPlaylist.get(playlist.id) ?? [],
      })),
    };
  });

  return {
    channels: dashboardChannels,
    runs: runsRes.data ?? [],
    jobs: jobsRes.data ?? [],
    fetchedAt: new Date(),
  };
}

export async function createChannel(payload: ChannelFormInput, token?: string): Promise<Channel> {
  const client = buildClient(token);
  const { data } = await client.post<Channel>('/channels/', payload);
  return data;
}

export async function updateChannel(
  channelId: number,
  payload: Partial<ChannelFormInput>,
  token?: string,
): Promise<Channel> {
  const client = buildClient(token);
  const { data } = await client.patch<Channel>(`/channels/${channelId}`, payload);
  return data;
}

export async function deleteChannel(channelId: number, token?: string): Promise<void> {
  const client = buildClient(token);
  await client.delete(`/channels/${channelId}`);
}

export async function createPlaylist(payload: PlaylistFormInput, token?: string): Promise<Playlist> {
  const client = buildClient(token);
  const { data } = await client.post<Playlist>('/playlists/', payload);
  return data;
}

export async function createSchedule(payload: ScheduleFormInput, token?: string): Promise<Schedule> {
  const client = buildClient(token);
  const { data } = await client.post<Schedule>('/schedules/', payload);
  return data;
}

export async function updateSchedule(
  scheduleId: number,
  payload: Partial<ScheduleFormInput>,
  token?: string,
): Promise<Schedule> {
  const client = buildClient(token);
  const { data } = await client.patch<Schedule>(`/schedules/${scheduleId}`, payload);
  return data;
}

export async function deleteSchedule(scheduleId: number, token?: string): Promise<void> {
  const client = buildClient(token);
  await client.delete(`/schedules/${scheduleId}`);
}

export async function triggerManualRun(playlistId: number, token?: string): Promise<RunRecord> {
  const client = buildClient(token);
  const { data } = await client.post<RunRecord>('/runs/', {
    playlist_id: playlistId,
    status: 'manual_trigger',
    message: 'Triggered from web dashboard',
  });
  return data;
}

export async function createJob(payload: JobFormInput, token?: string): Promise<Job> {
  const client = buildClient(token);
  const { data } = await client.post<Job>('/jobs/', payload);
  return data;
}

export async function deleteJobById(jobId: number, token?: string): Promise<void> {
  const client = buildClient(token);
  await client.delete(`/jobs/${jobId}`);
}

export async function deleteAllJobs(token?: string): Promise<void> {
  const client = buildClient(token);
  await client.delete('/jobs/');
}

export async function updateJobById(jobId: number, payload: Partial<Job>, token?: string): Promise<Job> {
  const client = buildClient(token);
  const { data } = await client.patch<Job>(`/jobs/${jobId}`, payload);
  return data;
}

export async function fetchCastopodPodcasts(token?: string): Promise<CastopodPodcast[]> {
  const client = buildClient(token);
  const { data } = await client.get<CastopodPodcast[]>('/castopod/podcasts');
  return data;
}

export async function fetchPipelineStatus(token?: string): Promise<PipelineStatus> {
  const client = buildClient(token);
  const { data } = await client.get<PipelineStatus>('/pipeline/status');
  return data;
}

export async function triggerPipelineRun(token?: string): Promise<PipelineStatus> {
  const client = buildClient(token);
  const { data } = await client.post<PipelineStatus>('/pipeline/trigger');
  return data;
}

export async function quickCreateJob(
  payload: JobQuickCreateInput,
  token?: string,
): Promise<JobQuickCreateResponse> {
  const client = buildClient(token);
  const { data } = await client.post<JobQuickCreateResponse>('/jobs/quick-create', payload);
  return data;
}
