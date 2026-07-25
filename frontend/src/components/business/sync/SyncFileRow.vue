<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { formatSize, statusLabel, statusColorClass, fileProgressPercent, type SyncFileEvent } from '@/lib/syncFile'

const props = defineProps<{ ev: SyncFileEvent }>()

const percent = computed(() => fileProgressPercent(props.ev))
</script>

<template>
  <div
    class="grid grid-cols-[70px_60px_1fr_80px_140px] gap-1 px-4 py-1.5 text-xs border-b border-[hsl(var(--border)/.5)] hover:bg-[hsl(var(--accent)/.3)]"
  >
    <span
      class="inline-flex items-center justify-center rounded px-1.5 py-0.5 text-[10px] font-semibold border h-fit w-fit"
      :class="statusColorClass(ev.status)"
    >
      {{ statusLabel(ev.status) }}
    </span>
    <Badge :variant="ev.action === 'delete' ? 'destructive' : 'secondary'" class="text-[10px] w-fit h-fit">
      {{ ev.action }}
    </Badge>
    <span class="truncate text-[hsl(var(--foreground))]" :title="ev.path">{{ ev.path }}</span>
    <span class="text-[hsl(var(--muted-foreground))]">{{ ev.size ? formatSize(ev.size) : '-' }}</span>
    <div class="min-w-0">
      <span
        class="block truncate text-[hsl(var(--muted-foreground))]"
        :title="ev.message || ev.ts || ''"
      >{{ ev.message || ev.ts || '-' }}</span>
      <div
        v-if="percent !== null"
        class="mt-0.5 h-1 w-full overflow-hidden rounded-full bg-[hsl(var(--muted))]"
      >
        <div
          class="h-full rounded-full bg-blue-500 transition-all duration-300"
          :style="{ width: `${percent}%` }"
        />
      </div>
    </div>
  </div>
</template>
