import type { TaskItem } from '@/types/tasks'
import type { DriveAccountItem } from '@/types/extensions'
import { detectDriveTypeByUrl } from '@/utils/driveType'

export type ResolvedTaskAccount = {
  /** 任务生效的网盘类型（无法识别时为空串） */
  driveType: string
  /** 任务生效的账号名：显式指定的账号，或自动模式下按网盘类型解析出的默认账号 */
  accountName: string
  /** 任务是否未显式指定账号（自动选择） */
  isAuto: boolean
}

export function pickDefaultAccountByType(accounts: DriveAccountItem[] | undefined | null, driveType: string) {
  const list = accounts || []
  return (
    list.find((acc) => acc.enabled && acc.drive_type === driveType && acc.is_default) ||
    list.find((acc) => acc.enabled && acc.drive_type === driveType) ||
    null
  )
}

export function resolveTaskAccount(task: TaskItem, accounts: DriveAccountItem[] | undefined | null): ResolvedTaskAccount {
  const explicit = String(task.account_name || '').trim()
  if (explicit) {
    const acc = (accounts || []).find((item) => item.name === explicit)
    const driveType = String(acc?.drive_type || '').trim() || detectDriveTypeByUrl(task.shareurl) || ''
    return { driveType, accountName: explicit, isAuto: false }
  }
  const driveType = detectDriveTypeByUrl(task.shareurl) || ''
  const auto = driveType ? pickDefaultAccountByType(accounts, driveType) : null
  return { driveType, accountName: auto?.name || '', isAuto: true }
}
