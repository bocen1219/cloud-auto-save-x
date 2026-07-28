import { formatDateTime } from '@/lib/capacity'
import type { DriveAccountLsdirCacheStatus } from '@/types/extensions'

export type LsdirRefreshBadge = {
  label: string
  className: string
  title: string
}

/** 刷新类型文案：与后端 drive_account_lsdir_refresh_status 的 KIND_* 对应。 */
export function lsdirRefreshKindLabel(kind: string): string {
  if (kind === 'full') return '全量扫描'
  if (kind === 'cas_output') return 'CAS 输出目录'
  if (kind === 'targeted') return '定向刷新'
  return kind
}

/** 该账号是否正有刷新在排队或执行。 */
export function isLsdirRefreshActive(status?: DriveAccountLsdirCacheStatus | null): boolean {
  const text = String(status?.status || '')
  return text === 'running' || text === 'queued'
}

function buildTitle(status: DriveAccountLsdirCacheStatus): string {
  const detail: string[] = []
  if (status.savepath) detail.push(`目标：${status.savepath}`)
  if (status.kind) detail.push(`类型：${lsdirRefreshKindLabel(status.kind)}`)
  if (status.source) detail.push(`来源：${status.source}`)
  if (status.current_path) detail.push(`当前：${status.current_path}`)
  if (status.last_error) detail.push(`错误：${status.last_error}`)
  return detail.join('\n')
}

/** 账号卡片上的缓存刷新徽标；idle 或无状态时返回 null（不占位）。 */
export function lsdirRefreshBadge(status?: DriveAccountLsdirCacheStatus | null): LsdirRefreshBadge | null {
  if (!status || status.status === 'idle') return null
  const scanned = status.scanned_dirs ?? 0
  const cached = status.cached_items ?? 0
  const title = buildTitle(status)

  if (status.status === 'queued') {
    return {
      label: status.waiting ? '缓存刷新排队中（等待其他扫描）' : '缓存刷新已排队',
      className: 'border-transparent bg-blue-500/10 text-blue-600 dark:text-blue-400',
      title,
    }
  }
  if (status.status === 'running') {
    const progress = status.pending_dirs ? `，待扫 ${status.pending_dirs}` : ''
    const queued = status.pending_count ? `，另有 ${status.pending_count} 个刷新排队` : ''
    return {
      label: `缓存刷新中（已扫 ${scanned} 目录/${cached} 项${progress}${queued}）`,
      className: 'border-transparent bg-blue-500/10 text-blue-600 dark:text-blue-400',
      title,
    }
  }
  if (status.status === 'completed') {
    return {
      label: `缓存刷新完成（${scanned} 目录/${cached} 项·${formatDateTime(status.finished_at)}）`,
      className: 'border-transparent bg-green-500/10 text-green-600 dark:text-green-400',
      title,
    }
  }
  if (status.status === 'failed') {
    return {
      label: `缓存刷新失败：${status.last_error || '未知错误'}`,
      className: 'border-transparent bg-red-500/10 text-red-600 dark:text-red-400',
      title,
    }
  }
  return {
    label: '缓存刷新被中断（可重新刷新）',
    className: 'border-transparent bg-amber-500/10 text-amber-600 dark:text-amber-400',
    title,
  }
}
