<script setup lang="ts">
import { ChevronLeft, ChevronRight, Inbox } from 'lucide-vue-next'
import Button from './Button.vue'

export interface Column {
  key: string
  label: string
  align?: 'left' | 'center' | 'right'
  width?: string
}

interface Props {
  columns: Column[]
  items: any[]
  loading?: boolean
  total?: number
  limit?: number
  offset?: number
  emptyTitle?: string
  emptyMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  total: 0,
  limit: 20,
  offset: 0,
  emptyTitle: 'No items found',
  emptyMessage: 'There is no data to display right now.'
})

const emit = defineEmits<{
  (e: 'page-change', newOffset: number): void
}>()

function prevPage() {
  const newOffset = Math.max(0, props.offset - props.limit)
  emit('page-change', newOffset)
}

function nextPage() {
  if (props.offset + props.limit < props.total) {
    const newOffset = props.offset + props.limit
    emit('page-change', newOffset)
  }
}
</script>

<template>
  <div class="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden flex flex-col">
    <!-- Top Table Actions Toolbar if any -->
    <div v-if="$slots.toolbar" class="p-4 border-b border-slate-100 dark:border-slate-800">
      <slot name="toolbar" />
    </div>

    <!-- Table Container -->
    <div class="overflow-x-auto min-h-[220px]">
      <table class="w-full text-left border-collapse text-sm">
        <thead>
          <tr class="border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-800/40 text-slate-500 dark:text-slate-400 font-semibold text-xs uppercase tracking-wider">
            <th
              v-for="col in columns"
              :key="col.key"
              :style="col.width ? { width: col.width } : {}"
              :class="[
                'px-6 py-3.5',
                col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
              ]"
            >
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-800/80 text-slate-800 dark:text-slate-200">
          <!-- Loading State -->
          <template v-if="loading">
            <tr v-for="n in 5" :key="n" class="animate-pulse">
              <td
                v-for="col in columns"
                :key="col.key"
                class="px-6 py-4"
              >
                <div class="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
              </td>
            </tr>
          </template>

          <!-- Empty State -->
          <tr v-else-if="items.length === 0">
            <td :colspan="columns.length" class="px-6 py-12 text-center">
              <div class="flex flex-col items-center justify-center max-w-sm mx-auto">
                <div class="p-3 bg-slate-100 dark:bg-slate-800 rounded-2xl text-slate-400 dark:text-slate-500 mb-3">
                  <Inbox class="w-6 h-6" />
                </div>
                <h4 class="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  {{ emptyTitle }}
                </h4>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  {{ emptyMessage }}
                </p>
                <div v-if="$slots['empty-action']" class="mt-4">
                  <slot name="empty-action" />
                </div>
              </div>
            </td>
          </tr>

          <!-- Data Rows -->
          <tr
            v-else
            v-for="(item, index) in items"
            :key="item.id || index"
            class="hover:bg-slate-50/70 dark:hover:bg-slate-800/30 transition-colors"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-6 py-4 whitespace-nowrap',
                col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
              ]"
            >
              <slot :name="`cell-${col.key}`" :item="item" :value="item[col.key]">
                {{ item[col.key] }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Footer -->
    <div
      v-if="total > limit"
      class="px-6 py-3.5 bg-slate-50/50 dark:bg-slate-900/40 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400"
    >
      <div>
        Showing
        <span class="font-semibold text-slate-800 dark:text-slate-200">{{ offset + 1 }}</span>
        to
        <span class="font-semibold text-slate-800 dark:text-slate-200">{{ Math.min(offset + limit, total) }}</span>
        of
        <span class="font-semibold text-slate-800 dark:text-slate-200">{{ total }}</span>
        results
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="offset === 0 || loading"
          @click="prevPage"
        >
          <template #icon-left>
            <ChevronLeft class="w-4 h-4" />
          </template>
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          :disabled="offset + limit >= total || loading"
          @click="nextPage"
        >
          Next
          <template #icon-right>
            <ChevronRight class="w-4 h-4" />
          </template>
        </Button>
      </div>
    </div>
  </div>
</template>
