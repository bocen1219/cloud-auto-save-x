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
