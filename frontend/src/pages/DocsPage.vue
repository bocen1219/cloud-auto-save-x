<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { BookOpen, Link as LinkIcon, ExternalLink, ChevronDown } from 'lucide-vue-next'

const route = useRoute()

// 目录按主题分组：后续新增主题（如网盘账号、同步任务等）直接往 tocGroups 里加一组即可，
// 各 section 的 id 保持全局唯一，支持 /docs#id 直达。
type TocSection = { id: string; label: string }
type TocGroup = { id: string; label: string; emoji: string; children: TocSection[] }

const tocGroups: TocGroup[] = [
  {
    id: 'regex-guide',
    label: '正则重命名',
    emoji: '✨',
    children: [
      { id: 'regex', label: '总览' },
      { id: 'regex-modes', label: '三种使用模式' },
      { id: 'regex-basics', label: '正则入门（小白版）' },
      { id: 'magic-rules', label: '内置魔法规则' },
      { id: 'magic-variables', label: '魔法变量表' },
      { id: 'regex-examples', label: '实战示例' },
      { id: 'regex-tips', label: '常见问题与建议' },
    ],
  },
  {
    id: 'tmdb-guide',
    label: 'TMDB 智能重命名',
    emoji: '🎬',
    children: [
      { id: 'tmdb-overview', label: 'TMDB 设置总览' },
      { id: 'tmdb-variables', label: '模板变量表' },
      { id: 'tmdb-examples', label: '模板实战示例' },
      { id: 'tmdb-guessit', label: 'Guessit 兜底机制' },
    ],
  },
  {
    id: 'dl302-guide',
    label: '302 代理 / CAS / STRM',
    emoji: '🌐',
    children: [
      { id: 'dl302-overview', label: '概念速览' },
      { id: 'cas-settings', label: 'CAS 参数说明' },
      { id: 'strm-settings', label: 'STRM 参数说明' },
      { id: 'proxy-settings', label: '反代参数说明' },
    ],
  },
  {
    id: 'drive-guide',
    label: '网盘账号',
    emoji: '☁️',
    children: [
      { id: 'drive-paths', label: '三个路径配置的区别' },
    ],
  },
  {
    id: 'cache-guide',
    label: '缓存管理',
    emoji: '💾',
    children: [
      { id: 'cache-overview', label: '三类缓存说明' },
      { id: 'tmdb-cache', label: 'TMDB 缓存与定时刷新' },
    ],
  },
  {
    id: 'misc-guide',
    label: '通知与其他',
    emoji: '🔔',
    children: [
      { id: 'notifications', label: '通知渠道' },
      { id: 'transfer-settings', label: '转存设置' },
      { id: 'resource-search', label: '资源搜索' },
      { id: 'openlist', label: 'OpenList' },
    ],
  },
  {
    id: 'schedule-guide',
    label: '定时任务',
    emoji: '⏰',
    children: [
      { id: 'crontab', label: 'crontab 表达式' },
    ],
  },
]

// 目录分组折叠状态：默认全部展开；hash 命中某组内条目时自动展开该组
const collapsedGroups = ref<Set<string>>(new Set())

function toggleGroup(groupId: string) {
  const next = new Set(collapsedGroups.value)
  if (next.has(groupId)) next.delete(groupId)
  else next.add(groupId)
  collapsedGroups.value = next
}

function groupOfSection(sectionId: string): string {
  for (const group of tocGroups) {
    if (group.id === sectionId) return group.id
    if (group.children.some((s) => s.id === sectionId)) return group.id
  }
  return ''
}

function scrollToHash(hash: string) {
  const id = String(hash || '').replace(/^#/, '')
  if (!id) return
  const groupId = groupOfSection(id)
  if (groupId && collapsedGroups.value.has(groupId)) {
    const next = new Set(collapsedGroups.value)
    next.delete(groupId)
    collapsedGroups.value = next
  }
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(() => {
  nextTick(() => scrollToHash(route.hash))
})

watch(
  () => route.hash,
  (hash) => scrollToHash(hash),
)

function copyAnchor(id: string) {
  const url = `${window.location.origin}/docs#${id}`
  window.history.replaceState(null, '', `#${id}`)
  try {
    navigator.clipboard?.writeText(url)
  } catch {
    // clipboard 不可用时忽略，仅更新地址栏 hash
  }
}

// 内置规则说明（与后端 MagicRename.magic_regex / builtin_magic_regex_labels 对齐）
const builtinRuleDocs = [
  {
    key: '$TV_REGEX',
    name: '剧集集数（SxxExx）',
    usage: '从文件名中提取季号和集数，重命名为「S01E02.mp4」这种简洁格式。适合文件名里已带集数的剧集。',
    example: '「败犬女主.S02E03.1080p.mp4」→「S02E03.mp4」',
  },
  {
    key: '$TV_MAGIC',
    name: '通用视频命名',
    usage: '匹配所有常见视频文件，重命名为「任务名.SxxEyy.扩展名」。识别不到季号时默认 S01。',
    example: '「第3集.mp4」→「任务名.S01E3.mp4」',
  },
  {
    key: '$SHOW_MAGIC',
    name: '综艺期数命名',
    usage: '匹配带「第x期」的综艺文件（自动排除纯享/加更/抢先/预告），重命名为「任务名.SxxEyy.第y期(上/中/下).扩展名」，序号自动递增。',
    example: '「xx综艺第5期上.mp4」→「任务名.S01E06.第5期上.mp4」',
  },
  {
    key: '$SHOW_PRO',
    name: '综艺期数命名（含日期）',
    usage: '和 $SHOW_MAGIC 类似，但文件名里带日期，格式为「序号.任务名.日期.第y期(上/中/下).扩展名」。',
    example: '「xx综艺20240102第5期.mp4」→「06.任务名.20240102.第5期.mp4」',
  },
  {
    key: '$BLACK_WORD',
    name: '黑名单过滤（仅筛选不改名）',
    usage: '只转存不含「纯享/加更/超前企划/训练室」等黑名单词的文件，不做重命名。',
    example: '「正片第1期.mp4」保留；「第1期纯享版.mp4」跳过',
  },
]

// 魔法变量说明（与后端 MagicRename.magic_variable 对齐）
const magicVariableDocs = [
  { name: '{TASKNAME}', desc: '任务名称', example: '任务叫「庆余年」→ 庆余年' },
  { name: '{EXT}', desc: '文件扩展名（不带点）', example: 'abc.mp4 → mp4' },
  { name: '{CHINESE}', desc: '文件名中第一段连续 2 个以上的中文', example: '「EP01庆余年.mp4」→ 庆余年' },
  { name: '{DATE}', desc: '日期，自动补全为 8 位数字', example: '「1.2期.mp4」→ 20260102' },
  { name: '{YEAR}', desc: '四位年份', example: '「2024.EP01.mp4」→ 2024' },
  { name: '{S}', desc: '季号数字（不带 S 前缀），识别不到则为空', example: 'S02E03 → 2' },
  { name: '{SXX}', desc: '带 S 前缀的季号，识别不到时默认 S01', example: 'S02E03 → S02；无季号 → S01' },
  { name: '{E}', desc: '集数/期数数字，按多种规则依次尝试识别', example: '「第12集」「E12」「EP12」→ 12' },
  { name: '{PART}', desc: '上/中/下等部分标识', example: '「第5期上」→ 上' },
  { name: '{VER}', desc: '「xx版」版本标识', example: '「精编版」→ 精编版' },
  { name: '{I} / {II} / {III}', desc: '自动递增序号，I 的个数决定补零位数；会接着目标目录里已有的序号继续编号', example: '{II} → 01、02、03…' },
]

// TMDB 重命名模板变量（与后端 guessit_fallback._build_guessit_tags / ctx 对齐）
const tmdbVariableDocs = [
  { name: '{title}', desc: 'TMDB 剧集/电影标题（已按语言设置本地化）', example: '庆余年' },
  { name: '{title_dot}', desc: '标题中的空格替换为点号', example: '庆余年 第二季 → 庆余年.第二季' },
  { name: '{season}', desc: '季号，两位补零', example: 'S02' },
  { name: '{episode}', desc: '集号，两位补零', example: 'E03' },
  { name: '{season_num}', desc: '季号数字（不补零）', example: '2' },
  { name: '{episode_num}', desc: '集号数字（不补零）', example: '3' },
  { name: '{year}', desc: '年份（电影为上映年，剧集为首播年）', example: '2024' },
  { name: '{ext}', desc: '扩展名（带点）', example: '.mp4' },
  { name: '{orig}', desc: '原始完整文件名（含扩展名）', example: '庆余年.S02E03.1080p.mp4' },
  { name: '{orig_base}', desc: '原始文件名（不含扩展名）', example: '庆余年.S02E03.1080p' },
  { name: '{orig_base_dot}', desc: '原始文件名（不含扩展名，空格转点）', example: '庆余年.S02E03.1080p' },
  { name: '{screen_size}', desc: '分辨率（guessit 识别）', example: '1080p' },
  { name: '{source}', desc: '片源（guessit 识别）', example: 'Web' },
  { name: '{video_codec}', desc: '视频编码', example: 'H.265' },
  { name: '{audio_codec}', desc: '音频编码', example: 'AAC' },
  { name: '{audio_channels}', desc: '声道数', example: '5.1' },
  { name: '{release_group}', desc: '压制组', example: 'Group' },
  { name: '{container}', desc: '容器格式', example: 'mp4' },
  { name: '{language}', desc: '语言', example: '中文' },
  { name: '{subtitle_language}', desc: '字幕语言', example: '简中' },
  { name: '{other}', desc: '其他标签（HDR 等）', example: 'HDR' },
  { name: '{tags} / {tags_dot}', desc: '上述媒体标签用点号拼接', example: '1080p.Web.H.265' },
  { name: '{tags_space}', desc: '上述媒体标签用空格拼接', example: '1080p Web H.265' },
]

const tmdbTemplateExamples = [
  {
    name: '标准剧集（默认）',
    tpl: '{title}.S{season}E{episode}{ext}',
    result: '庆余年.S02E03.mp4',
  },
  {
    name: '剧集带分辨率',
    tpl: '{title}.S{season}E{episode}.{screen_size}{ext}',
    result: '庆余年.S02E03.1080p.mp4',
  },
  {
    name: '剧集带完整标签',
    tpl: '{title}.S{season}E{episode}.{tags_dot}{ext}',
    result: '庆余年.S02E03.1080p.Web.H.265.mp4',
  },
  {
    name: '电影（默认）',
    tpl: '{title_dot}.{year}{ext}',
    result: '流浪地球.2.2023.mp4',
  },
  {
    name: '电影带分辨率',
    tpl: '{title_dot}.{year}.{screen_size}{ext}',
    result: '流浪地球.2.2023.2160p.mp4',
  },
]

// crontab 常用示例
const cronExamples = [
  { expr: '0 */6 * * *', desc: '每 6 小时执行一次（0 点、6 点、12 点、18 点）' },
  { expr: '30 8 * * *', desc: '每天早上 8:30 执行' },
  { expr: '0 9,21 * * *', desc: '每天 9:00 和 21:00 各执行一次' },
  { expr: '0 22 * * 5', desc: '每周五晚上 22:00 执行' },
  { expr: '*/30 18-23 * * *', desc: '每天 18 点到 23 点之间，每 30 分钟执行一次' },
  { expr: '0 4 1 * *', desc: '每月 1 号凌晨 4 点执行' },
]
</script>

<template>
  <div class="mx-auto max-w-5xl px-4 py-6 md:px-8">
    <!-- Page header -->
    <div class="mb-6 flex items-center gap-3">
      <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[hsl(var(--primary))]/10">
        <BookOpen class="h-5 w-5 text-[hsl(var(--primary))]" />
      </div>
      <div>
        <h1 class="text-xl font-bold text-[hsl(var(--foreground))]">说明文档</h1>
        <p class="text-xs text-[hsl(var(--muted-foreground))]">正则重命名、定时表达式等功能的使用说明，点击标题旁的 🔗 可复制该条目的直达链接</p>
      </div>
    </div>

    <div class="flex flex-col gap-6 lg:flex-row">
      <!-- TOC -->
      <nav class="lg:w-56 lg:flex-shrink-0">
        <div class="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-3 shadow-sm lg:sticky lg:top-4">
          <div class="mb-2 px-2 text-xs font-semibold uppercase tracking-wide text-[hsl(var(--muted-foreground))]">目录</div>
          <div class="space-y-1">
            <div v-for="group in tocGroups" :key="group.id">
              <!-- 分组标题：点击折叠/展开 -->
              <button
                class="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm font-medium text-[hsl(var(--foreground))] transition-colors hover:bg-[hsl(var(--accent))]"
                @click="toggleGroup(group.id)"
              >
                <span class="flex items-center gap-1.5">
                  <span>{{ group.emoji }}</span>
                  {{ group.label }}
                </span>
                <ChevronDown
                  class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))] transition-transform"
                  :class="collapsedGroups.has(group.id) ? '-rotate-90' : ''"
                />
              </button>
              <!-- 组内条目 -->
              <div v-if="!collapsedGroups.has(group.id)" class="mt-0.5 flex flex-wrap gap-1 lg:ml-3 lg:flex-col lg:gap-0.5 lg:border-l lg:border-[hsl(var(--border))] lg:pl-2">
                <a
                  v-for="item in group.children"
                  :key="item.id"
                  :href="`#${item.id}`"
                  class="rounded-md px-2 py-1 text-sm text-[hsl(var(--muted-foreground))] transition-colors hover:bg-[hsl(var(--accent))] hover:text-[hsl(var(--accent-foreground))]"
                  :class="route.hash === `#${item.id}` ? 'bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]' : ''"
                >
                  {{ item.label }}
                </a>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <!-- Content -->
      <div class="min-w-0 flex-1 space-y-6">
        <!-- ================= 章节：正则重命名 ================= -->
        <div id="regex-guide" class="flex scroll-mt-4 items-center gap-2 pt-1">
          <h2 class="text-lg font-bold text-[hsl(var(--foreground))]">✨ 正则重命名</h2>
          <div class="h-px flex-1 bg-[hsl(var(--border))]" />
        </div>

        <!-- ===== 正则总览 ===== -->
        <section id="regex" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            📌 总览
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('regex')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-3 text-sm leading-relaxed text-[hsl(var(--foreground))]">
            <p>
              追剧任务里有两个和正则相关的输入框：<strong>匹配正则（pattern）</strong> 和 <strong>替换字符串（replace）</strong>。
              简单记：<strong>pattern 决定「转存哪些文件」，replace 决定「转存后叫什么名字」</strong>。
            </p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li>系统会拿 pattern 去匹配分享里的每个文件名，<strong>匹配不上的文件直接跳过</strong>（不转存）。</li>
              <li>匹配上的文件，如果填了 replace，就按 replace 生成新文件名；replace 里可以用 <code class="rounded bg-[hsl(var(--muted))] px-1">\1</code> 引用 pattern 括号里捕获的内容，也可以用 <a href="#magic-variables" class="text-[hsl(var(--primary))] hover:underline">魔法变量</a>。</li>
              <li>不想自己写？pattern 直接填内置规则的 key（如 <code class="rounded bg-[hsl(var(--muted))] px-1">$TV_REGEX</code>），replace 留空即可套用<a href="#magic-rules" class="text-[hsl(var(--primary))] hover:underline">内置魔法规则</a>。任务编辑页的「内置规则」下拉框就是干这个的。</li>
              <li>正则语法为 Python <code class="rounded bg-[hsl(var(--muted))] px-1">re</code> 模块语法，反向引用写 <code class="rounded bg-[hsl(var(--muted))] px-1">\1</code>（不是 <code class="rounded bg-[hsl(var(--muted))] px-1">$1</code>）。</li>
            </ul>
          </div>
        </section>

        <!-- ===== 三种模式 ===== -->
        <section id="regex-modes" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🔀 三种使用模式
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('regex-modes')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
            <table class="w-full min-w-[560px] text-sm">
              <thead class="bg-[hsl(var(--muted))]/60">
                <tr>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">pattern</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">replace</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">效果</th>
                </tr>
              </thead>
              <tbody class="text-[hsl(var(--foreground))]">
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2">留空</td>
                  <td class="px-3 py-2">留空</td>
                  <td class="px-3 py-2">全部文件按原名转存。若任务关联了 TMDB 且未关闭智能重命名，会自动用 guessit 识别剧集并按模板重命名（智能兜底）。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2">填写</td>
                  <td class="px-3 py-2">留空</td>
                  <td class="px-3 py-2"><strong>仅筛选模式</strong>：只转存 pattern 匹配到的文件，不改名。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2">填写</td>
                  <td class="px-3 py-2">填写</td>
                  <td class="px-3 py-2"><strong>筛选 + 重命名</strong>：匹配到的文件按 replace 模板改名后转存。</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="mt-3 text-xs text-[hsl(var(--muted-foreground))]">
            注：pattern 填内置规则 key（如 $TV_REGEX）且 replace 留空时，自动使用该内置规则的 replace，属于「筛选 + 重命名」模式。
          </p>
        </section>

        <!-- ===== 正则入门 ===== -->
        <section id="regex-basics" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🧑‍🏫 正则入门（小白版）
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('regex-basics')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <p class="mb-3 text-sm text-[hsl(var(--muted-foreground))]">正则就是「文件名的搜索规则」。记住下面这几个符号，90% 的场景就够用了：</p>
          <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
            <table class="w-full min-w-[560px] text-sm">
              <thead class="bg-[hsl(var(--muted))]/60">
                <tr>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">写法</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">意思</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">例子</th>
                </tr>
              </thead>
              <tbody class="text-[hsl(var(--foreground))]">
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">.</td><td class="px-3 py-2">任意一个字符</td><td class="px-3 py-2 font-mono text-xs">a.c 可匹配 abc、a1c</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">\d</td><td class="px-3 py-2">一个数字（0-9）</td><td class="px-3 py-2 font-mono text-xs">\d\d 匹配 01、12</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">+ / * / ?</td><td class="px-3 py-2">前面的内容重复 1 次以上 / 0 次以上 / 0 或 1 次</td><td class="px-3 py-2 font-mono text-xs">\d+ 匹配 3、42、100</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">.*</td><td class="px-3 py-2">任意长度的任意内容（最常用的「随便什么」）</td><td class="px-3 py-2 font-mono text-xs">第.*集 匹配「第3集」「第12集」</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">( )</td><td class="px-3 py-2">分组捕获，把括号里匹配到的内容「存下来」，在 replace 里用 \1、\2 取出</td><td class="px-3 py-2 font-mono text-xs">第(\d+)集 → replace 里 \1 就是集数</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">[ ]</td><td class="px-3 py-2">方括号内任选一个字符</td><td class="px-3 py-2 font-mono text-xs">[Ee]p 匹配 Ep、ep</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">(a|b)</td><td class="px-3 py-2">a 或 b</td><td class="px-3 py-2 font-mono text-xs">\.(mp4|mkv) 匹配 .mp4 或 .mkv</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">^ / $</td><td class="px-3 py-2">开头 / 结尾</td><td class="px-3 py-2 font-mono text-xs">\.mp4$ 表示以 .mp4 结尾</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">\.</td><td class="px-3 py-2">真正的点号（. 是特殊符号，要加 \ 转义；( ) [ ] 同理）</td><td class="px-3 py-2 font-mono text-xs">\.mp4 匹配 .mp4</td></tr>
                <tr class="border-t border-[hsl(var(--border))]"><td class="px-3 py-2 font-mono">^(?!.*词)</td><td class="px-3 py-2">排除：不含某个词才匹配（进阶但很实用）</td><td class="px-3 py-2 font-mono text-xs">^(?!.*预告).* 排除带「预告」的文件</td></tr>
              </tbody>
            </table>
          </div>
          <div class="mt-3 rounded-lg bg-[hsl(var(--muted))]/40 p-3 text-sm text-[hsl(var(--muted-foreground))]">
            💡 一个完整例子：文件名「庆余年 第03集.mp4」，pattern 写
            <code class="rounded bg-[hsl(var(--muted))] px-1 font-mono text-xs">第(\d+)集.*\.(mp4|mkv)</code>，
            replace 写 <code class="rounded bg-[hsl(var(--muted))] px-1 font-mono text-xs">E\1.\2</code>，
            结果就是「E03.mp4」——\1 取到了 03，\2 取到了 mp4。
          </div>
        </section>

        <!-- ===== 内置规则 ===== -->
        <section id="magic-rules" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🪄 内置魔法规则
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('magic-rules')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <p class="mb-3 text-sm text-[hsl(var(--muted-foreground))]">
            在 pattern 输入框里直接填下面的 key（replace 留空）即可套用。也可以在
            「设置 → 重命名规则」里覆盖内置规则、添加自定义规则（自定义 key 需以 $ 开头）。
          </p>
          <div class="space-y-3">
            <div v-for="rule in builtinRuleDocs" :key="rule.key" class="rounded-lg border border-[hsl(var(--border))] p-3">
              <div class="mb-1 flex flex-wrap items-center gap-2">
                <code class="rounded bg-[hsl(var(--primary))]/10 px-1.5 py-0.5 font-mono text-xs font-semibold text-[hsl(var(--primary))]">{{ rule.key }}</code>
                <span class="text-sm font-medium text-[hsl(var(--foreground))]">{{ rule.name }}</span>
              </div>
              <p class="text-sm text-[hsl(var(--muted-foreground))]">{{ rule.usage }}</p>
              <p class="mt-1 text-xs text-[hsl(var(--muted-foreground))]">例：{{ rule.example }}</p>
            </div>
          </div>
        </section>

        <!-- ===== 魔法变量 ===== -->
        <section id="magic-variables" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🧩 魔法变量表（用在 replace 里）
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('magic-variables')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <p class="mb-3 text-sm text-[hsl(var(--muted-foreground))]">
            replace 模板里可以直接写这些占位符，系统会从<strong>原文件名</strong>里自动提取对应内容填进去；提取不到时替换为空（{SXX} 例外，默认 S01）。
          </p>
          <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
            <table class="w-full min-w-[560px] text-sm">
              <thead class="bg-[hsl(var(--muted))]/60">
                <tr>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">变量</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">含义</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">示例</th>
                </tr>
              </thead>
              <tbody class="text-[hsl(var(--foreground))]">
                <tr v-for="mv in magicVariableDocs" :key="mv.name" class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-mono text-xs font-semibold">{{ mv.name }}</td>
                  <td class="px-3 py-2">{{ mv.desc }}</td>
                  <td class="px-3 py-2 text-xs text-[hsl(var(--muted-foreground))]">{{ mv.example }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- ===== 实战示例 ===== -->
        <section id="regex-examples" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            📚 实战示例
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('regex-examples')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-4 text-sm">
            <div>
              <p class="font-medium text-[hsl(var(--foreground))]">1. 只转存 mp4，不改名（仅筛选）</p>
              <p class="mt-1 font-mono text-xs text-[hsl(var(--muted-foreground))]">pattern：\.mp4$　　replace：留空</p>
            </div>
            <div>
              <p class="font-medium text-[hsl(var(--foreground))]">2. 排除预告和花絮</p>
              <p class="mt-1 font-mono text-xs text-[hsl(var(--muted-foreground))]">pattern：^(?!.*预告)(?!.*花絮).*\.(mp4|mkv)$　　replace：留空</p>
            </div>
            <div>
              <p class="font-medium text-[hsl(var(--foreground))]">3. 「第x集」重命名为标准剧集格式</p>
              <p class="mt-1 font-mono text-xs text-[hsl(var(--muted-foreground))]">pattern：.*第(\d+)集.*\.(mp4|mkv)　　replace：{TASKNAME}.S01E\1.\2</p>
              <p class="mt-1 text-xs text-[hsl(var(--muted-foreground))]">「庆余年 第3集 4K.mp4」→「庆余年.S01E3.mp4」</p>
            </div>
            <div>
              <p class="font-medium text-[hsl(var(--foreground))]">4. 全用魔法变量，不写捕获组</p>
              <p class="mt-1 font-mono text-xs text-[hsl(var(--muted-foreground))]">pattern：.*\.(mp4|mkv)$　　replace：{TASKNAME}.{SXX}E{E}.{EXT}</p>
              <p class="mt-1 text-xs text-[hsl(var(--muted-foreground))]">季号、集数、扩展名都由系统从原文件名自动识别。</p>
            </div>
            <div>
              <p class="font-medium text-[hsl(var(--foreground))]">5. 综艺按期数自动编号</p>
              <p class="mt-1 font-mono text-xs text-[hsl(var(--muted-foreground))]">pattern：$SHOW_MAGIC　　replace：留空</p>
              <p class="mt-1 text-xs text-[hsl(var(--muted-foreground))]">或自定义 replace：{TASKNAME}.S01E{II}.第{E}期{PART}.{EXT}，其中 {II} 会接着已保存的最大序号继续编号。</p>
            </div>
          </div>
        </section>

        <!-- ===== 常见问题 ===== -->
        <section id="regex-tips" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            💡 常见问题与建议
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('regex-tips')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <ul class="list-disc space-y-2 pl-5 text-sm text-[hsl(var(--muted-foreground))]">
            <li><strong class="text-[hsl(var(--foreground))]">先预览再保存</strong>：任务创建/编辑页有「预览」功能，能直接看到每个文件筛选、重命名后的结果，强烈建议每次改完正则先预览。</li>
            <li><strong class="text-[hsl(var(--foreground))]">别忘了扩展名</strong>：replace 结尾记得带上 <code class="rounded bg-[hsl(var(--muted))] px-1">.{EXT}</code> 或捕获组（如 \2），否则新文件名没有后缀。</li>
            <li><strong class="text-[hsl(var(--foreground))]">「忽略扩展名」开关</strong>：勾选后判断文件是否已存在时不比较扩展名，可避免同一集的 mp4/mkv 重复转存。</li>
            <li><strong class="text-[hsl(var(--foreground))]">重命名冲突</strong>：多个文件重命名后目标名相同时，系统只保留体积最大的那个，其余跳过。</li>
            <li><strong class="text-[hsl(var(--foreground))]">测试正则</strong>：「设置 → 重命名规则」的编辑弹窗里有测试面板，可输入文件名实时验证。</li>
            <li><strong class="text-[hsl(var(--foreground))]">替换写法</strong>：反向引用用 <code class="rounded bg-[hsl(var(--muted))] px-1">\1</code>（Python 风格），不要写成 $1。</li>
          </ul>
        </section>

        <!-- ================= 章节：TMDB 智能重命名 ================= -->
        <div id="tmdb-guide" class="flex scroll-mt-4 items-center gap-2 pt-2">
          <h2 class="text-lg font-bold text-[hsl(var(--foreground))]">🎬 TMDB 智能重命名</h2>
          <div class="h-px flex-1 bg-[hsl(var(--border))]" />
        </div>

        <!-- ===== TMDB 设置总览 ===== -->
        <section id="tmdb-overview" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🎬 TMDB 设置总览
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('tmdb-overview')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-3 text-sm leading-relaxed text-[hsl(var(--foreground))]">
            <p>
              TMDB（The Movie Database）用于<strong>影视元数据刮削、海报获取和智能重命名</strong>。
              在「设置 → TMDB 设置」中配置。各参数说明：
            </p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li><strong class="text-[hsl(var(--foreground))]">API Key</strong>：TMDB 开放平台的密钥，免费注册即可获取。未设置时 TMDB 相关功能（海报、智能重命名、影视发现）不可用。</li>
              <li><strong class="text-[hsl(var(--foreground))]">语言</strong>：刮削元数据（标题、简介）使用的语言，默认 zh-CN（中文）。</li>
              <li><strong class="text-[hsl(var(--foreground))]">海报语言</strong>：优先获取的海报语言，默认 zh-CN。无对应语言海报时自动回退英文。</li>
              <li><strong class="text-[hsl(var(--foreground))]">启用 Guessit 兜底重命名</strong>：当任务关联了 TMDB 但没有配置正则时，用 Guessit 解析文件名并按模板重命名（见下方说明）。关闭后未配正则的文件按原名转存。</li>
              <li><strong class="text-[hsl(var(--foreground))]">剧集 / 电影重命名模板</strong>：Guessit 兜底重命名使用的文件名模板，支持<a href="#tmdb-variables" class="text-[hsl(var(--primary))] hover:underline">模板变量</a>。</li>
            </ul>
          </div>
        </section>

        <!-- ===== TMDB 模板变量表 ===== -->
        <section id="tmdb-variables" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🧩 TMDB 模板变量表
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('tmdb-variables')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <p class="mb-3 text-sm text-[hsl(var(--muted-foreground))]">
            在「设置 → TMDB 设置」的<strong>剧集 / 电影重命名模板</strong>中可直接写这些占位符。
            标题、季号、集号、年份来自 TMDB 元数据；分辨率、编码等标签由 Guessit 从原文件名识别，识别不到时替换为空。
          </p>
          <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
            <table class="w-full min-w-[560px] text-sm">
              <thead class="bg-[hsl(var(--muted))]/60">
                <tr>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">变量</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">含义</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">示例</th>
                </tr>
              </thead>
              <tbody class="text-[hsl(var(--foreground))]">
                <tr v-for="mv in tmdbVariableDocs" :key="mv.name" class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-mono text-xs font-semibold">{{ mv.name }}</td>
                  <td class="px-3 py-2">{{ mv.desc }}</td>
                  <td class="px-3 py-2 text-xs text-[hsl(var(--muted-foreground))]">{{ mv.example }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="mt-3 text-xs text-[hsl(var(--muted-foreground))]">
            注：模板中若未包含 <code class="rounded bg-[hsl(var(--muted))] px-1">{ext}</code>，系统会自动在末尾补上扩展名。
          </p>
        </section>

        <!-- ===== TMDB 模板示例 ===== -->
        <section id="tmdb-examples" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            📚 TMDB 模板实战示例
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('tmdb-examples')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-4 text-sm">
            <div v-for="ex in tmdbTemplateExamples" :key="ex.name">
              <p class="font-medium text-[hsl(var(--foreground))]">{{ ex.name }}</p>
              <p class="mt-1 font-mono text-xs text-[hsl(var(--muted-foreground))]">模板：{{ ex.tpl }}</p>
              <p class="mt-0.5 text-xs text-[hsl(var(--muted-foreground))]">结果：<span class="font-mono text-[hsl(var(--foreground))]">{{ ex.result }}</span></p>
            </div>
          </div>
        </section>

        <!-- ===== Guessit 兜底机制 ===== -->
        <section id="tmdb-guessit" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🔁 Guessit 兜底重命名机制
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('tmdb-guessit')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-3 text-sm leading-relaxed text-[hsl(var(--foreground))]">
            <p>Guessit 是一个从文件名中识别剧集信息的库。当满足以下<strong>全部条件</strong>时触发兜底重命名：</p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li>任务已关联 TMDB（选择了剧集/电影）；</li>
              <li>任务<strong>没有配置</strong>匹配正则（pattern）和替换字符串（replace）；</li>
              <li>「启用 Guessit 兜底重命名」开关开启；</li>
              <li>文件是视频文件（非视频文件跳过，保持原名）。</li>
            </ul>
            <p class="text-[hsl(var(--muted-foreground))]">
              触发后：Guessit 从原文件名解析季号/集号，<strong>标题优先使用 TMDB 元数据</strong>（保证与媒体库一致），
              再套用「设置 → TMDB 设置」中的模板生成新文件名。若 TMDB 无法提供季信息且文件名也识别不出季号，
              会尝试用 TMDB 的季列表映射；仍无法确定时该剧集文件保持原名。
            </p>
            <div class="rounded-lg bg-[hsl(var(--muted))]/40 p-3 text-[hsl(var(--muted-foreground))]">
              💡 优先级：<strong class="text-[hsl(var(--foreground))]">配置了正则 → 按正则重命名</strong>；
              <strong class="text-[hsl(var(--foreground))]">未配置正则 + 关联 TMDB → Guessit 兜底</strong>；
              <strong class="text-[hsl(var(--foreground))]">未配置正则 + 未关联 TMDB → 原名转存</strong>。
            </div>
          </div>
        </section>

        <!-- ================= 章节：302 代理 / CAS / STRM ================= -->
        <div id="dl302-guide" class="flex scroll-mt-4 items-center gap-2 pt-2">
          <h2 class="text-lg font-bold text-[hsl(var(--foreground))]">🌐 302 代理 / CAS / STRM</h2>
          <div class="h-px flex-1 bg-[hsl(var(--border))]" />
        </div>

        <!-- ===== 概念速览 ===== -->
        <section id="dl302-overview" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🌐 概念速览
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('dl302-overview')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-3 text-sm leading-relaxed text-[hsl(var(--foreground))]">
            <p>「设置 → 302 代理」管理 DL302 服务，涉及三个核心概念：</p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li><strong class="text-[hsl(var(--foreground))]">302 直连</strong>：播放时不经过服务器中转流量，而是返回一个 302 跳转，让播放器直接从网盘下载，服务器只负责解析出真实下载地址，几乎不占带宽。</li>
              <li><strong class="text-[hsl(var(--foreground))]">CAS（秒传数据）</strong>：预先下载网盘文件计算哈希，生成 <code class="rounded bg-[hsl(var(--muted))] px-1">.cas</code> 元数据文件并上传回网盘。之后转存同一文件时可用哈希「秒传」，无需真正下载。</li>
              <li><strong class="text-[hsl(var(--foreground))]">STRM</strong>：生成只包含播放地址的 <code class="rounded bg-[hsl(var(--muted))] px-1">.strm</code> 文本文件，Emby/Jellyfin 等媒体库扫描到后直接按地址播放，无需下载整个文件。</li>
            </ul>
            <p class="text-[hsl(var(--muted-foreground))]">
              302 直连需保留端口 <strong class="text-[hsl(var(--foreground))]">5115 / 9000</strong>（5115 为统一代理端口）。
              不建议把 5115 直接暴露公网，推荐用反代代理 <code class="rounded bg-[hsl(var(--muted))] px-1">/dl</code> 路径。
            </p>
          </div>
        </section>

        <!-- ===== CAS 参数 ===== -->
        <section id="cas-settings" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            ⚡ CAS 参数说明
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('cas-settings')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
            <table class="w-full min-w-[560px] text-sm">
              <thead class="bg-[hsl(var(--muted))]/60">
                <tr>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">参数</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">说明</th>
                </tr>
              </thead>
              <tbody class="text-[hsl(var(--foreground))]">
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">CAS 文件生成目录</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">生成的 .cas 文件统一上传到网盘的该目录（如 /cas），所有驱动账号共用。留空则 CAS 功能不可用。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">CAS 并发 Worker</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">同时处理几个文件的 CAS 生成（1-32），默认 4。与复制任务的并发相互独立。值越大越快，但占用更多带宽和网盘请求配额。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">STRM 扫描路径</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">CAS 任务的扫描目录，<strong>复用各网盘账号配置中的「STRM 扫描路径」</strong>，仅处理目录缓存里缺少 rapid record 的视频文件。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">快速计算（cloud139）</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">移动云盘专属：优先用云端目录列表返回的 SHA256 生成 CAS，省去下载+本地哈希；拿不到哈希时自动回退原流程。</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- ===== STRM 参数 ===== -->
        <section id="strm-settings" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            📄 STRM 参数说明
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('strm-settings')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
            <table class="w-full min-w-[560px] text-sm">
              <thead class="bg-[hsl(var(--muted))]/60">
                <tr>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">参数</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">说明</th>
                </tr>
              </thead>
              <tbody class="text-[hsl(var(--foreground))]">
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">开启生成 STRM</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">扫描/缓存巡检完成后自动对账生成 .strm 文件。默认复用各账号的 STRM 扫描路径，为空时回退到缓存路径。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">包含 CAS 文件目录</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">对已配置 STRM 扫描路径的账号，额外扫描 CAS 生成目录，为 .cas 文件补充生成 STRM。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">源优先级</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">视频优先：优先用原始视频文件生成 STRM；CAS 优先：优先用 .cas 文件生成（配合秒传播放）。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">生成模式</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">自动：合并所有账号结果，链接统一指向 /dl/auto；独立：按账号名生成一级目录，链接带 account 参数区分账号。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">STRM 生成目录</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">.strm 文件输出目录（默认 /strm），媒体库需将此目录加入扫描。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">前缀 URL</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">.strm 文件内播放地址的前缀（如 http://192.168.1.10:9978），应为媒体库服务器可访问到本服务的地址。留空时访问时自动回填。</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- ===== 反代参数 ===== -->
        <section id="proxy-settings" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🔀 反代参数说明
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('proxy-settings')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-3 text-sm leading-relaxed text-[hsl(var(--foreground))]">
            <p>「反代设置」用于把 Emby/Jellyfin/飞牛影视等媒体服务的请求代理出去，并在播放时拦截下载请求改为 302 直连。每个反代目标包含：</p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li><strong class="text-[hsl(var(--foreground))]">系统类型</strong>：飞牛影视＝响应改写模式；Emby/Jellyfin＝下载接口 302 拦截；通用透传＝纯代理不干预。</li>
              <li><strong class="text-[hsl(var(--foreground))]">目标地址</strong>：被代理的媒体服务真实地址（如 http://192.168.1.100:8096）。</li>
              <li><strong class="text-[hsl(var(--foreground))]">监听端口</strong>：本服务为该反代目标开放的新端口，播放器/浏览器访问这个端口。</li>
              <li><strong class="text-[hsl(var(--foreground))]">路径偏移</strong>：目标服务部署在子路径时填写偏移量（一般为 0）。</li>
              <li><strong class="text-[hsl(var(--foreground))]">内网网段 (CIDR)</strong>：每行一个网段，客户端 IP 命中内网时直连目标、绕过 302（内网直连通常更快更稳）。所有反代目标共享。</li>
            </ul>
          </div>
        </section>

        <!-- ================= 章节：网盘账号 ================= -->
        <div id="drive-guide" class="flex scroll-mt-4 items-center gap-2 pt-2">
          <h2 class="text-lg font-bold text-[hsl(var(--foreground))]">☁️ 网盘账号</h2>
          <div class="h-px flex-1 bg-[hsl(var(--border))]" />
        </div>

        <!-- ===== 三个路径配置 ===== -->
        <section id="drive-paths" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            📂 三个路径配置的区别
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('drive-paths')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <p class="mb-3 text-sm text-[hsl(var(--muted-foreground))]">
            编辑网盘账号时有三个容易混淆的路径配置，它们用途不同，<strong>互不替代</strong>：
          </p>
          <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
            <table class="w-full min-w-[640px] text-sm">
              <thead class="bg-[hsl(var(--muted))]/60">
                <tr>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">配置项</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">用途</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">影响范围</th>
                </tr>
              </thead>
              <tbody class="text-[hsl(var(--foreground))]">
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">缓存路径<br /><span class="text-xs text-[hsl(var(--muted-foreground))]">lsdir_cache_path</span></td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">目录缓存（ls_dir）的扫描根目录，也是<strong>同步任务的默认目标基路径</strong>。</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">同步任务、追剧联动、目录浏览、秒传判断。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">STRM 扫描路径<br /><span class="text-xs text-[hsl(var(--muted-foreground))]">strm_scan_path</span></td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">STRM 生成与 CAS 生成的扫描目录，支持多个（逗号分隔）。<strong>同时也是 302 播放的代理基路径</strong>（取第一个）。</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">STRM 生成、CAS 生成、302 播放路径解析。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">302_path（旧参数）</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">历史遗留参数，<strong>已废弃</strong>。仅在缓存路径为空时作为回退。新配置请勿使用。</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">仅回退兼容。</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="mt-3 rounded-lg bg-amber-500/10 border border-amber-500/40 p-3 text-sm text-amber-600 dark:text-amber-400">
            ⚠️ 常见误区：STRM 扫描路径的第一项会被用作 302 播放的代理基路径。如果你的同步目标目录（缓存路径）不在 STRM 扫描路径下，
            302 播放解析时可能把目标路径错误地拼到扫描路径下。建议把<strong>缓存路径包含在 STRM 扫描路径列表中</strong>，或两者保持一致。
          </div>
        </section>

        <!-- ================= 章节：缓存管理 ================= -->
        <div id="cache-guide" class="flex scroll-mt-4 items-center gap-2 pt-2">
          <h2 class="text-lg font-bold text-[hsl(var(--foreground))]">💾 缓存管理</h2>
          <div class="h-px flex-1 bg-[hsl(var(--border))]" />
        </div>

        <!-- ===== 三类缓存 ===== -->
        <section id="cache-overview" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            💾 三类缓存说明
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('cache-overview')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <p class="mb-3 text-sm text-[hsl(var(--muted-foreground))]">「设置 → 缓存管理」管理三类本地缓存，作用是减少重复请求、加速页面加载：</p>
          <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
            <table class="w-full min-w-[640px] text-sm">
              <thead class="bg-[hsl(var(--muted))]/60">
                <tr>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">缓存</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">缓存内容</th>
                  <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">可配置项</th>
                </tr>
              </thead>
              <tbody class="text-[hsl(var(--foreground))]">
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">代理图片缓存</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">影视发现的海报/图片经本服务代理下载后的本地磁盘缓存，避免每次浏览都重新拉取。</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">TTL、单文件上限、总容量上限；支持「清理过期」「一键清空」。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">分享链接缓存</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">分享链接解析结果（pwd_id/stoken 等）缓存，减少重复解析、规避网盘风控。</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">TTL、容量；支持按条目清理。</td>
                </tr>
                <tr class="border-t border-[hsl(var(--border))]">
                  <td class="px-3 py-2 font-medium">TMDB 缓存</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">TMDB 详情（标题、季数、海报等）缓存，供任务统计与追剧信息复用。</td>
                  <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">定时刷新、批量刷新、冷数据清理、单条 TTL。</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- ===== TMDB 缓存 ===== -->
        <section id="tmdb-cache" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🎬 TMDB 缓存与定时刷新
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('tmdb-cache')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-3 text-sm leading-relaxed text-[hsl(var(--foreground))]">
            <p>TMDB 缓存页分三个子标签：</p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li><strong class="text-[hsl(var(--foreground))]">缓存列表</strong>：查看全部缓存条目，支持按类型/关键词/状态/是否过期筛选；每行可强制刷新、设置 TTL、删除。</li>
              <li><strong class="text-[hsl(var(--foreground))]">工具</strong>：「刷新任务关联缓存」从任务提取已关联的 TMDB 条目批量刷新；「清理冷数据」删除长期未访问的条目；「快速定位」按 tmdb_id 排查单条缓存状态。</li>
              <li><strong class="text-[hsl(var(--foreground))]">定时刷新</strong>：按 <a href="#crontab" class="text-[hsl(var(--primary))] hover:underline">crontab</a> 周期性刷新缓存，保持剧集更新状态（如更新星期、下一集播出时间）新鲜。</li>
            </ul>
            <p class="text-[hsl(var(--muted-foreground))]">定时刷新参数：</p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li><strong class="text-[hsl(var(--foreground))]">crontab / timezone</strong>：刷新周期与时区（默认 0 */6 * * *，Asia/Shanghai）。</li>
              <li><strong class="text-[hsl(var(--foreground))]">每次最多刷新条目</strong>：单次定时任务最多刷新多少条，避免一次性请求过多被 TMDB 限流。</li>
              <li><strong class="text-[hsl(var(--foreground))]">仅刷新任务关联条目</strong>：开启后只刷新已被追剧任务关联的条目（推荐），减少无效刷新。</li>
              <li><strong class="text-[hsl(var(--foreground))]">冷数据保留天数</strong>：超过该天数未访问的条目会在清理时删除。</li>
            </ul>
          </div>
        </section>

        <!-- ================= 章节：通知与其他 ================= -->
        <div id="misc-guide" class="flex scroll-mt-4 items-center gap-2 pt-2">
          <h2 class="text-lg font-bold text-[hsl(var(--foreground))]">🔔 通知与其他</h2>
          <div class="h-px flex-1 bg-[hsl(var(--border))]" />
        </div>

        <!-- ===== 通知渠道 ===== -->
        <section id="notifications" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🔔 通知渠道
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('notifications')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-3 text-sm leading-relaxed text-[hsl(var(--foreground))]">
            <p>「设置 → 通知配置」支持 18 种通知渠道。每个渠道<strong>填好必填项 → 打开启用开关 → 点「测试」验证</strong>即可。</p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li><strong class="text-[hsl(var(--foreground))]">手机推送</strong>：Bark（iOS）、PushPlus、Server酱、PushDeer、PushMe、WxPusher。</li>
              <li><strong class="text-[hsl(var(--foreground))]">IM 机器人</strong>：Telegram、钉钉、飞书、企业微信（机器人/应用）、go-cqhttp（QQ）、DoDo、微加机器人。</li>
              <li><strong class="text-[hsl(var(--foreground))]">自建/通用</strong>：SMTP 邮件、Gotify、Ntfy、自定义 Webhook。</li>
            </ul>
            <p class="text-[hsl(var(--muted-foreground))]">
              自定义 Webhook 的 URL 和 Body 支持 <code class="rounded bg-[hsl(var(--muted))] px-1">$title</code> /
              <code class="rounded bg-[hsl(var(--muted))] px-1">$content</code> 占位符，发送时自动替换为通知标题和正文。
              追剧任务、同步任务完成或失败时会向所有已启用渠道推送。
            </p>
          </div>
        </section>

        <!-- ===== 转存设置 ===== -->
        <section id="transfer-settings" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🔀 转存设置
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('transfer-settings')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <ul class="list-disc space-y-2 pl-5 text-sm text-[hsl(var(--muted-foreground))]">
            <li><strong class="text-[hsl(var(--foreground))]">跳过已转存历史</strong>：开启后转存时跳过历史记录中已成功转存过的文件，避免重复转存。适合分享链接长期有效的追剧场景。</li>
            <li><strong class="text-[hsl(var(--foreground))]">下载模式</strong>：CAS 复制任务的下载方式。流式（0）＝边下边传，不占本地磁盘；下载（1）＝先完整下载到本地再上传，更稳定但占磁盘。网络不稳定导致流式失败时可切换为下载模式。</li>
          </ul>
        </section>

        <!-- ===== 资源搜索 ===== -->
        <section id="resource-search" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🔎 资源搜索
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('resource-search')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <ul class="list-disc space-y-2 pl-5 text-sm text-[hsl(var(--muted-foreground))]">
            <li><strong class="text-[hsl(var(--foreground))]">网络搜索 (net)</strong>：内置聚合网络资源搜索，开箱即用，仅需启用。</li>
            <li><strong class="text-[hsl(var(--foreground))]">CloudSaver</strong>：对接自建 CloudSaver 服务，需填服务器地址、用户名、密码。</li>
            <li><strong class="text-[hsl(var(--foreground))]">盘搜 (pansou)</strong>：对接 pansou 搜索服务，需填服务器地址。</li>
          </ul>
          <p class="mt-2 text-sm text-[hsl(var(--muted-foreground))]">启用后在「资源搜索」页面即可聚合检索，搜索结果可一键创建追剧任务。</p>
        </section>

        <!-- ===== OpenList ===== -->
        <section id="openlist" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            🗂️ OpenList
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('openlist')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <p class="text-sm leading-relaxed text-[hsl(var(--muted-foreground))]">
            OpenList（原 AList）是聚合网盘的目录列表服务。配置其 URL 和 Token 后，同步任务可以把文件同步到 OpenList 挂载的存储。
            URL 形如 <code class="rounded bg-[hsl(var(--muted))] px-1">http://localhost:5245</code>，Token 在 OpenList 后台「用户」中获取。
          </p>
        </section>

        <!-- ================= 章节：定时任务 ================= -->
        <div id="schedule-guide" class="flex scroll-mt-4 items-center gap-2 pt-2">
          <h2 class="text-lg font-bold text-[hsl(var(--foreground))]">⏰ 定时任务</h2>
          <div class="h-px flex-1 bg-[hsl(var(--border))]" />
        </div>

        <!-- ===== crontab ===== -->
        <section id="crontab" class="scroll-mt-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm">
          <h2 class="group mb-3 flex items-center gap-2 text-base font-semibold text-[hsl(var(--foreground))]">
            ⏰ 定时表达式（crontab）
            <button class="opacity-0 transition-opacity group-hover:opacity-100" title="复制本节链接" @click="copyAnchor('crontab')">
              <LinkIcon class="h-3.5 w-3.5 text-[hsl(var(--muted-foreground))]" />
            </button>
          </h2>
          <div class="space-y-3 text-sm text-[hsl(var(--foreground))]">
            <p>
              系统的定时任务（追剧全局调度、账号探测、TMDB 缓存刷新等）都使用 5 段式 crontab 表达式，从左到右依次是：
              <code class="rounded bg-[hsl(var(--muted))] px-1 font-mono text-xs">分钟(0-59) 小时(0-23) 日(1-31) 月(1-12) 星期(0-6，0=周日)</code>，段之间用空格分隔。
            </p>
            <ul class="list-disc space-y-1 pl-5 text-[hsl(var(--muted-foreground))]">
              <li><code class="rounded bg-[hsl(var(--muted))] px-1">*</code> 表示「每」；<code class="rounded bg-[hsl(var(--muted))] px-1">*/6</code> 表示「每隔 6」；</li>
              <li><code class="rounded bg-[hsl(var(--muted))] px-1">1,3,5</code> 表示「1 和 3 和 5」；<code class="rounded bg-[hsl(var(--muted))] px-1">9-18</code> 表示「9 到 18」。</li>
            </ul>
            <div class="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
              <table class="w-full min-w-[480px] text-sm">
                <thead class="bg-[hsl(var(--muted))]/60">
                  <tr>
                    <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">表达式</th>
                    <th class="px-3 py-2 text-left font-medium text-[hsl(var(--muted-foreground))]">含义</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ex in cronExamples" :key="ex.expr" class="border-t border-[hsl(var(--border))]">
                    <td class="px-3 py-2 font-mono text-xs">{{ ex.expr }}</td>
                    <td class="px-3 py-2 text-[hsl(var(--muted-foreground))]">{{ ex.desc }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="text-[hsl(var(--muted-foreground))]">
              拿不准写法时，可以用在线工具验证：
              <a
                href="http://tool.lu/crontab"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1 text-[hsl(var(--primary))] hover:underline"
              >
                tool.lu/crontab
                <ExternalLink class="h-3.5 w-3.5" />
              </a>
              （注意选择 5 位表达式模式）。
            </p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
