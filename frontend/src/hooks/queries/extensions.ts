import { useQuery } from '@tanstack/vue-query'
import {
  fetchDriveAccounts,
  fetchDriveAccountLsdirCacheStatuses,
  fetchDriveTypes,
  fetchDriveAccountProbeScheduler,
  fetchPlugins,
  fetchSyncPlugins,
} from '@/api/extensions'
import { fetchNotificationConfig } from '@/api/notifications'
import type { DriveAccountLsdirCacheStatus, DriveAccountProbeScheduler } from '@/types/extensions'

export function useDriveAccountsQuery() {
  return useQuery({
    queryKey: ['drive-accounts'],
    queryFn: () => fetchDriveAccounts(),
  })
}

/** 缓存刷新状态：有账号正在排队/刷新时自动提频轮询，否则停轮询。 */
export function useDriveAccountLsdirCacheStatusQuery(enabled: () => boolean = () => true) {
  return useQuery({
    queryKey: ['drive-account-lsdir-cache-status'],
    queryFn: () => fetchDriveAccountLsdirCacheStatuses(),
    enabled,
    refetchInterval: (query) => {
      const items = (query.state.data || []) as DriveAccountLsdirCacheStatus[]
      const active = items.some((item) => item.status === 'running' || item.status === 'queued')
      return active ? 2000 : false
    },
  })
}

export function useDriveTypesQuery() {
  return useQuery({
    queryKey: ['drive-types'],
    queryFn: () => fetchDriveTypes(),
    staleTime: 5 * 60 * 1000,
  })
}

export function useDriveAccountProbeSchedulerQuery() {
  return useQuery({
    queryKey: ['drive-account-probe-scheduler'],
    queryFn: () => fetchDriveAccountProbeScheduler() as Promise<DriveAccountProbeScheduler>,
  })
}

export function usePluginsQuery() {
  return useQuery({
    queryKey: ['plugins'],
    queryFn: () => fetchPlugins(),
  })
}

export function useSyncPluginsQuery() {
  return useQuery({
    queryKey: ['sync-plugins'],
    queryFn: () => fetchSyncPlugins(),
  })
}

export function useNotificationsQuery() {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: () => fetchNotificationConfig(),
  })
}
