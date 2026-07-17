<script setup lang="ts">
import { CalendarClock, Copy, Tags, X } from 'lucide-vue-next'
import type { KnowledgeFile } from '@/types'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import { pushToast } from '@/composables/useToast'
import { formatKnowledgeTime, formatReviewStatus } from '@/utils/knowledge'

const props = defineProps<{
  open: boolean
  knowledge: KnowledgeFile | null
  loading?: boolean
}>()

const emit = defineEmits<{ close: [] }>()

async function copyPath() {
  if (!props.knowledge) return
  try {
    await navigator.clipboard.writeText(props.knowledge.relative_path)
    pushToast('仓库路径已复制', 'success')
  } catch {
    pushToast('复制失败，请手动选择路径', 'error')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-backdrop file-modal-backdrop" @click.self="emit('close')">
        <section class="knowledge-file-modal" role="dialog" aria-modal="true" aria-label="知识文件">
          <header>
            <div>
              <span class="eyebrow">知识文件</span>
              <h2>{{ knowledge?.title ?? '正在读取…' }}</h2>
            </div>
            <button type="button" aria-label="关闭" @click="emit('close')"><X :size="23" /></button>
          </header>
          <div v-if="loading" class="modal-loading"><span class="loading-spinner" />正在读取知识文件…</div>
          <template v-else-if="knowledge">
            <div class="file-meta-line">
              <span>{{ knowledge.id }}</span>
              <span class="knowledge-tag">{{ knowledge.scope }}</span>
              <span class="knowledge-tag">{{ knowledge.layer }}</span>
              <span class="knowledge-tag">{{ knowledge.maturity }}</span>
            </div>
            <div class="file-review-line" :class="{ overdue: knowledge.review.overdue }">
              <span><CalendarClock :size="17" />Next Review</span>
              <time :datetime="knowledge.review.next_review_at">{{ formatKnowledgeTime(knowledge.review.next_review_at) }}</time>
              <em v-if="knowledge.review.overdue">{{ formatReviewStatus(knowledge.review.overdue) }}</em>
            </div>
            <div class="file-tag-section">
              <span class="file-section-label"><Tags :size="16" />标签</span>
              <div v-if="knowledge.tags.length" class="file-tag-list">
                <span v-for="tag in knowledge.tags" :key="tag">#{{ tag }}</span>
              </div>
              <span v-else class="file-no-tags">暂无标签</span>
            </div>
            <div class="path-box file-path-box">
              <code>{{ knowledge.relative_path }}</code>
              <button type="button" aria-label="复制仓库路径" @click="copyPath"><Copy :size="18" /></button>
            </div>
            <div class="file-content-scroll"><MarkdownPreview :content="knowledge.content" /></div>
          </template>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>
