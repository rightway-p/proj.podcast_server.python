export interface Channel {
  id: number;
  slug: string;
  title: string;
  description?: string | null;
}

export interface Playlist {
  id: number;
  channel_id: number;
  youtube_playlist_id: string;
  title?: string | null;
  is_active: boolean;
  castopod_slug?: string | null;
  castopod_uuid?: string | null;
}

export interface CastopodPodcast {
  id: number;
  uuid: string;
  title: string;
  slug: string;
}

export interface Schedule {
  id: number;
  playlist_id: number;
  days_of_week: string[];
  run_time: string;
  timezone: string;
  is_active: boolean;
  next_run_at?: string | null;
  last_run_at?: string | null;
}

export interface RunRecord {
  id: number;
  playlist_id: number;
  status: string;
  message?: string | null;
  started_at: string;
  finished_at?: string | null;
  progress_total: number;
  progress_completed: number;
  current_task?: string | null;
  progress_message?: string | null;
}

export interface DashboardChannel extends Channel {
  playlists: Array<{
    playlist: Playlist;
    schedules: Schedule[];
    recentRuns: RunRecord[];
  }>;
}

export interface DashboardData {
  channels: DashboardChannel[];
  runs: RunRecord[];
  jobs: Job[];
  fetchedAt: Date;
}

export interface PipelineStatus {
  running: boolean;
  pid?: number | null;
  command: string;
  started_at?: string | null;
  last_started_at?: string | null;
  last_finished_at?: string | null;
  last_exit_code?: number | null;
  log_path?: string | null;
}

export interface ChannelFormInput {
  slug: string;
  title: string;
  description?: string;
}

export interface PlaylistFormInput {
  channel_id: number;
  youtube_playlist_id: string;
  title?: string;
  is_active?: boolean;
  castopod_slug?: string;
  castopod_uuid?: string;
}

export interface ScheduleFormInput {
  playlist_id: number;
  days_of_week: string[];
  run_time: string;
  timezone: string;
  is_active?: boolean;
}

export interface JobFormInput {
  playlist_id: number;
  action?: string;
  castopod_slug?: string;
  castopod_playlist_uuid?: string;
  note?: string;
  should_castopod_upload?: boolean;
}

export interface Job {
  id: number;
  playlist_id: number;
  action: string;
  status: string;
  castopod_slug?: string | null;
  castopod_playlist_uuid?: string | null;
  note?: string | null;
  should_castopod_upload: boolean;
  progress_total: number;
  progress_completed: number;
  current_task?: string | null;
  progress_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobQuickCreateInput {
  job_name: string;
  youtube_playlist: string;
  castopod_slug?: string;
  castopod_uuid?: string;
  should_castopod_upload?: boolean;
  note?: string;
  channel_description?: string;
}

export interface JobQuickCreateResponse {
  channel: Channel;
  playlist: Playlist;
  job: Job;
  created_channel: boolean;
  created_playlist: boolean;
}
