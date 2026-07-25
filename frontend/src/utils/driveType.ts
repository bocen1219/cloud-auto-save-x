export type DriveType = 'quark' | '115' | 'baidu' | 'xunlei' | 'aliyun' | 'uc' | '123pan' | 'cloud189' | 'cloud139' | 'guangya'

export const DRIVE_TYPE_LABELS: Record<string, string> = {
  quark: '夸克',
  '115': '115',
  baidu: '百度网盘',
  xunlei: '迅雷',
  aliyun: '阿里云盘',
  uc: 'UC',
  '123pan': '123 盘',
  cloud189: '天翼云盘',
  cloud139: '移动云盘',
  guangya: '光鸭云盘',
}

export function getDriveTypeLabel(code: string | null | undefined) {
  const key = String(code || '').trim()
  return DRIVE_TYPE_LABELS[key] || key || '未知类型'
}

export function detectDriveTypeByUrl(url: string): DriveType | null {
  const value = String(url || '')
  if (!value) return null
  if (/pan\.quark\.cn/i.test(value)) return 'quark'
  if (/(?:115|anxia|115cdn)\.com/i.test(value)) return '115'
  if (/pan\.baidu\.com/i.test(value)) return 'baidu'
  if (/pan\.xunlei\.com/i.test(value)) return 'xunlei'
  if (/(?:alipan|aliyundrive)\.com/i.test(value)) return 'aliyun'
  if (/drive\.uc\.cn/i.test(value)) return 'uc'
  if (/(?:(?:123pan|123865|123684|123952|123912)\.com|(?:[A-Za-z0-9-]+\.)?share\.123pan\.cn)/i.test(value)) return '123pan'
  if (/(?:cloud|m\.cloud)\.189\.cn/i.test(value)) return 'cloud189'
  if (/(?:yun|caiyun)\.139\.com/i.test(value)) return 'cloud139'
  if (/(?:www\.|app\.)?guangyapan\.com/i.test(value)) return 'guangya'
  return null
}
