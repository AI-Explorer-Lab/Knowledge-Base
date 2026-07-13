<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { Check, CheckCircle2, Info } from 'lucide-vue-next'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import MetadataCard from '@/components/MetadataCard.vue'
import StepProgress from '@/components/StepProgress.vue'
import { useKnowledgeFlow } from '@/composables/useKnowledgeFlow'
import { pushToast } from '@/composables/useToast'
import { ApiError } from '@/types'
import { shouldResetPreviewForError } from '@/utils/recovery'

const router = useRouter()
const {
  preview,
  previewIsCurrent,
  submitting,
  invalidatePreview,
  submitKnowledge,
} = useKnowledgeFlow()

const submissionError = ref('')
const serverPreview = computed(() => preview.value!.preview)
function isPreviewExpired() {
  return !preview.value || Date.parse(preview.value.expires_at) <= Date.now()
}

const serverChecks = computed(() => Array.isArray(preview.value?.checks) ? preview.value.checks : [])
const allChecksPassed = computed(() => serverChecks.value.length > 0 && serverChecks.value.every((check) => check.status === 'passed'))

onMounted(() => window.addEventListener('beforeunload', warnBeforeUnload))
onBeforeUnmount(() => window.removeEventListener('beforeunload', warnBeforeUnload))

function warnBeforeUnload(event: BeforeUnloadEvent) {
  event.preventDefault()
  event.returnValue = ''
}

onBeforeRouteLeave((to) => {
  if (to.name === 'knowledge-create' || to.name === 'knowledge-completed') return true
  return window.confirm('当前知识尚未确认注入，确认离开吗？')
})

async function confirmInjection() {
  if (isPreviewExpired()) {
    pushToast('预览凭证已过期，请重新预览校验', 'error')
    invalidatePreview()
    await router.replace({ name: 'knowledge-create' })
    return
  }
  submissionError.value = ''
  try {
    await submitKnowledge()
    await router.replace({ name: 'knowledge-completed' })
  } catch (reason) {
    const message = reason instanceof Error ? reason.message : '知识注入失败，请重试'
    submissionError.value = message
    pushToast(message, 'error')
    if (reason instanceof ApiError && shouldResetPreviewForError(reason.code)) {
      invalidatePreview()
      await router.replace({ name: 'knowledge-create' })
    }
  }
}

async function returnToEdit() {
  await router.push({ name: 'knowledge-create' })
}
</script>

<template>
  <div v-if="preview && previewIsCurrent" class="workflow-page">
    <div class="workflow-heading">
      <div>
        <h1>预览校验</h1>
        <p>确认知识内容与治理规则，校验通过后再写入知识库</p>
      </div>
      <StepProgress :current="2" />
    </div>

    <div class="inline-alert" :class="allChecksPassed ? 'success-alert' : 'error-alert'">
      <CheckCircle2 :size="21" fill="currentColor" />
      <strong>{{ allChecksPassed ? '校验通过，当前内容尚未写入知识库' : '校验未通过，请返回修改' }}</strong>
      <span v-if="allChecksPassed" class="validation-badge">预览凭证有效</span>
    </div>

    <div v-if="submissionError" class="inline-alert error-alert" role="alert">
      <Info :size="19" /><span>{{ submissionError }}</span>
    </div>

    <div class="preview-layout">
      <section class="content-preview-card">
        <h2>知识内容预览</h2>
        <div class="preview-title">{{ serverPreview.title }}</div>
        <div class="tag-row">
          <span class="knowledge-tag type-tag">{{ serverPreview.type }}</span>
          <span v-for="tag in serverPreview.tags" :key="tag" class="knowledge-tag">{{ tag }}</span>
        </div>
        <div class="content-divider" />
        <MarkdownPreview :content="serverPreview.content" />
        <p class="source-line">来源：{{ serverPreview.source_references.join('；') }}</p>
      </section>

      <aside class="preview-sidebar">
        <MetadataCard
          title="元数据确认"
          :id="serverPreview.id"
          :scope="serverPreview.scope"
          :owner-id="serverPreview.owner_id"
          :layer="serverPreview.layer"
          :maturity="serverPreview.maturity"
          :relative-path="serverPreview.relative_path"
        />

        <section class="validation-card">
          <h2>校验结果</h2>
          <ul>
            <li v-for="item in serverChecks" :key="item.key" :class="{ failed: item.status === 'failed' }" :title="item.detail">
              <span><Check :size="13" stroke-width="3" /></span>
              {{ item.label }}
              <em>{{ item.status === 'passed' ? '通过' : '未通过' }}</em>
            </li>
          </ul>
          <p><Info :size="17" />提交时后端将再次校验</p>
        </section>
      </aside>
    </div>

    <footer class="workflow-actions">
      <p><Info :size="18" />预览内容变更后需要重新校验</p>
      <div>
        <button class="button button-secondary button-wide" type="button" :disabled="submitting" @click="returnToEdit">返回修改</button>
        <button class="button button-primary button-wide" type="button" :disabled="submitting || !allChecksPassed" @click="confirmInjection">
          <span v-if="submitting" class="button-spinner" />
          {{ submitting ? '正在注入…' : '确认注入' }}
        </button>
      </div>
    </footer>
  </div>
</template>
