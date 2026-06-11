export type ResourceSearchSourceKey = 'net' | 'cloudsaver' | 'pansou'

export type ResourceSearchSourceItem = {
  key: ResourceSearchSourceKey
  enabled: boolean
  server?: string | null
  username?: string | null
  password?: string | null
  token?: string | null
}

export type ResourceSearchSourceListResponse = {
  sources: ResourceSearchSourceItem[]
}

export type TaskSuggestionItem = {
  taskname: string
  shareurl: string
  content?: string | null
  datetime?: string | null
  channel?: string | null
  source?: string | null
  verify?: boolean | null
  // Episode grouping fields (added for series grouping)
  group_key?: string | null
  episode?: string | null
  season?: string | null
  series_name?: string | null
}

export type TaskSuggestionResponse = {
  success: boolean
  data: TaskSuggestionItem[]
  message?: string | null
}

