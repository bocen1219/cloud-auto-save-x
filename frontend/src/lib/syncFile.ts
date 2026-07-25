
export interface SyncFileEvent {
  ts?: string
  action?: string
  status: string
  path: string
  size?: number | null
  message?: string | null
  progress_percent?: number | null
  stage?: string
  stage_label?: string
}

export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)}GB`
}

export function statusLabel(s: string): string {
  const map: Record<string, string> = { success: 'OK', syncing: 'SYNC', pending: 'PEND', skipped: 'SKIP', aborted: 'ABRT' }
  return map[s] || 'FAIL'
}

export function statusColorClass(s: string): string {
  if (s === 'syncing' || s === 'pending') return 'text-blue-500 border-blue-300 bg-blue-50 dark:bg-blue-950/30'
  if (s === 'success') return 'text-emerald-500 border-emerald-300 bg-emerald-50 dark:bg-emerald-950/30'
  if (s === 'skipped' || s === 'aborted') return 'text-gray-400 border-gray-300 bg-gray-50 dark:bg-gray-800/30'
  return 'text-red-500 border-red-300 bg-red-50 dark:bg-red-950/30'
}

export function fileProgressPercent(ev: Pick<SyncFileEvent, 'status' | 'message' | 'progress_percent'> | null | undefined): number | null {
  if (!ev || (ev.status !== 'syncing' && ev.status !== 'SYNC')) return null
  const raw = ev.progress_percent
  if (typeof raw === 'number' && isFinite(raw)) {
    return Math.max(0, Math.min(100, raw))
  }
  const msg = String(ev.message || '')
  const m = msg.match(/(\d+(?:\.\d+)?)\s*%/)
  if (m) {
    const v = parseFloat(m[1])
    if (isFinite(v)) return Math.max(0, Math.min(100, v))
  }
  return null
}
