export type ConfigFieldItem = {
  key: string
  label?: string
  description?: string
  input_type?: 'text' | 'textarea' | 'password' | 'switch' | 'number'
  required?: boolean
  secret?: boolean
  placeholder?: string
  default?: any
}

export type DriveTypeItem = {
  code: string
  drive_name: string
  class_name: string
  config_format: 'raw' | 'kv'
  default_config: Record<string, any>
  config_fields: ConfigFieldItem[]
}

export type Cloud189FamilyItem = {
  family_id: string
  remark_name: string
  type?: number | null
  user_role?: number | null
  count?: number | null
  create_time?: string
}

export type DriveAccountProfile = {
  drive_type?: string
  drive_name?: string
  nickname?: string
  username?: string
  used_space?: number | null
  total_space?: number | null
  member_type?: string | null
  member_status?: string | Record<string, any> | null
  raw?: Record<string, any> | null
}

export type DriveAccountLsdirCacheStatus = {
  account_id: number
  drive_type?: string
  status: 'idle' | 'queued' | 'running' | 'completed' | 'failed' | 'interrupted' | string
  kind?: string
  source?: string
  savepath?: string
  target_dirs?: number
  queued_at?: string | null
  started_at?: string | null
  updated_at?: string | null
  finished_at?: string | null
  scanned_dirs?: number
  cached_items?: number
  current_path?: string
  pending_dirs?: number
  duration_ms?: number
  waiting?: boolean
  pending_count?: number
  last_error?: string | null
}

export type DriveAccountItem = {
  id: number
  name: string
  drive_type: string
  config: Record<string, any>
  profile: DriveAccountProfile
  enabled: boolean
  is_default: boolean
  capacity_warning_threshold: number
  used_space?: number | null
  total_space?: number | null
  usage_ratio?: number | null
  runtime_status?: string | null
  probe_fail_count?: number | null
  last_checked_at?: string | null
  profile_updated_at?: string | null
  last_error?: string | null
  has_302_path?: boolean
  lsdir_cache_base_path?: string | null
  lsdir_cache_file_total?: number
  lsdir_cache_updated_at?: string | null
  lsdir_cache_refresh?: DriveAccountLsdirCacheStatus | null
  created_at: string
  updated_at: string
}

export type DriveAccountLsdirCacheRefreshResult = {
  account_id: number
  cleared: number
  queued: boolean
  base_path?: string | null
  reason?: string | null
  static_requested?: boolean
  static_queued?: boolean
  static_skipped_reason?: string | null
  refresh_status?: DriveAccountLsdirCacheStatus | null
}

export type DriveAccountProbeScheduler = {
  enabled: boolean
  crontab: string
  timezone: string
  enabled_only: boolean
}

export type DriveAccountAuthMethod = 'captcha' | 'sms' | 'qrcode'

export type DriveAccountAuthChallenge = {
  account_id: number
  drive_type: string
  method: DriveAccountAuthMethod
  session_id: string
  payload?: Record<string, any>
}

export type DriveAccountSignInJob = {
  status: string
  message?: string | null
  result?: Record<string, any> | null
  error?: { message?: string } | null
}

export type PluginItem = {
  id: number
  plugin_key: string
  module_name: string
  source_type: string
  version?: string | null
  installed: boolean
  discovered_at: string
  enabled: boolean
  priority: number
  runtime_status?: string | null
  last_checked_at?: string | null
  last_error?: string | null
  config: Record<string, any>
  config_fields: ConfigFieldItem[]
  default_task_config: Record<string, any>
  task_config_fields: ConfigFieldItem[]
}
