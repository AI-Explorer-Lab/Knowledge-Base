<script setup lang="ts">
import { CalendarClock, ChevronDown, Copy, GitBranch, History, Tags, X } from 'lucide-vue-next'
import { ref, watch } from 'vue'
import { getMaturityHistory } from '@/api'
import type { KnowledgeFile, MaturityHistory, MaturityHistoryEvent } from '@/types'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import { pushToast } from '@/composables/useToast'
import { formatKnowledgeTime, formatReviewStatus } from '@/utils/knowledge'

const props = defineProps<{
  open: boolean
  knowledge: KnowledgeFile | null
  loading?: boolean
}>()

const emit = defineEmits<{ close: [] }>()

const maturityHistory = ref<MaturityHistory | null>(null)
const historyLoading = ref(false)
const historyError = ref('')
const historyOpen = ref(false)
let historyRequest = 0

watch(
  () => props.knowledge?.id,
  () => {
    maturityHistory.value = null
    historyLoading.value = false
    historyError.value = ''
    historyOpen.value = false
  },
)

function maturityLabel(value: 'draft' | 'verified' | 'proven') {
  return { draft: 'Draft', verified: 'Verified', proven: 'Proven' }[value]
}

function eventLabel(event: MaturityHistoryEvent) {
  if (event.from_maturity && event.to_maturity) {
    return `${maturityLabel(event.from_maturity)} → ${maturityLabel(event.to_maturity)}`
  }
  const labels: Record<MaturityHistoryEvent['event_type'], string> = {
    created: '创建知识',
    revision_reset: '生成新 Revision',
    referenced: '记录真实引用',
    validated: '记录验证结果',
    maturity_changed: '成熟度变更',
    decayed: '成熟度衰减',
    restored: '恢复知识',
  }
  return labels[event.event_type]
}

async function loadMaturityHistory() {
  if (maturityHistory.value || historyLoading.value || !props.knowledge) return
  const request = ++historyRequest
  historyLoading.value = true
  historyError.value = ''
  try {
    const response = await getMaturityHistory(props.knowledge.id)
    if (request === historyRequest) maturityHistory.value = response
  } catch (reason) {
    if (request === historyRequest) {
      historyError.value = reason instanceof Error ? reason.message : '成熟度历史读取失败'
    }
  } finally {
    if (request === historyRequest) historyLoading.value = false
  }
}

async function toggleMaturityHistory() {
  historyOpen.value = !historyOpen.value
  if (historyOpen.value) await loadMaturityHistory()
}

async function retryMaturityHistory() {
  maturityHistory.value = null
  await loadMaturityHistory()
}

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
            <section class="maturity-history-section">
              <button type="button" class="maturity-history-toggle" :aria-expanded="historyOpen" @click="toggleMaturityHistory">
                <span><History :size="17" />成熟度旅程</span>
                <ChevronDown :size="18" :class="{ rotated: historyOpen }" />
              </button>
              <div v-if="historyOpen" class="maturity-history-content">
                <div v-if="historyLoading" class="maturity-history-loading"><span class="loading-spinner" />正在读取成熟度历史…</div>
                <div v-else-if="historyError" class="maturity-history-error">
                  <span>{{ historyError }}</span>
                  <button type="button" class="text-button" @click="retryMaturityHistory">重试</button>
                </div>
                <template v-else-if="maturityHistory">
                  <p class="maturity-history-current"><GitBranch :size="16" />当前：{{ maturityLabel(maturityHistory.current_maturity) }} · Revision {{ maturityHistory.current_revision }}</p>
                  <ol class="maturity-timeline">
                    <li v-for="event in maturityHistory.events" :key="`${event.occurred_at}-${event.event_type}-${event.revision}`">
                      <span class="maturity-timeline-dot" :class="`event-${event.event_type}`" />
                      <div>
                        <strong>{{ eventLabel(event) }}</strong>
                        <p>{{ event.summary }}</p>
                        <small>
                          <time :datetime="event.occurred_at">{{ formatKnowledgeTime(event.occurred_at) }}</time>
                          <template v-if="event.actor"> · {{ event.actor }}</template>
                          <template v-if="event.revision !== null"> · Rev {{ event.revision }}</template>
                        </small>
                        <p v-if="event.reason" class="maturity-event-reason">原因：{{ event.reason }}</p>
                        <p v-if="event.changed_fields.length" class="maturity-event-fields">变更字段：{{ event.changed_fields.join('、') }}</p>
                        <ul v-if="event.evidence.length" class="maturity-evidence-list">
                          <li v-for="evidence in event.evidence" :key="`${evidence.kind}-${evidence.occurred_at}-${evidence.workflow_id}`">
                            <span>{{ evidence.kind === 'reference' ? '真实引用' : `验证 ${evidence.result ?? ''}` }}</span>
                            <template v-if="evidence.project_id"> · 项目 {{ evidence.project_id }}</template>
                            <template v-if="evidence.used_in"> · {{ evidence.used_in }}</template>
                            <template v-if="evidence.workflow_id"> · {{ evidence.workflow_id }}</template>
                            <p v-if="evidence.source">{{ evidence.source }}</p>
                          </li>
                        </ul>
                      </div>
                    </li>
                  </ol>
                </template>
              </div>
            </section>
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
