<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { FileCheck2, Info, LockKeyhole, ShieldCheck } from 'lucide-vue-next'
import KnowledgeForm from '@/components/KnowledgeForm.vue'
import MetadataCard from '@/components/MetadataCard.vue'
import StepProgress from '@/components/StepProgress.vue'
import { identity, options, sessionOptionsError } from '@/composables/useSession'
import { useKnowledgeFlow } from '@/composables/useKnowledgeFlow'
import { pushToast } from '@/composables/useToast'
import { ApiError, type KnowledgeLayer } from '@/types'
import {
  fingerprintDraft,
  firstFieldError,
  validateKnowledgeDraft,
  type KnowledgeErrors,
} from '@/utils/knowledge'

const router = useRouter()
const {
  draft,
  preview,
  previewing,
  previewIsCurrent,
  invalidatePreview,
  requestPreview,
} = useKnowledgeFlow()

const errors = ref<KnowledgeErrors>({})
const requestError = ref('')
const baseline = ref('')

const ownerId = computed(() => identity.value?.member.id ?? '')
const pendingMetadata = computed(() => {
  if (preview.value && previewIsCurrent.value) return preview.value.preview
  const layer: KnowledgeLayer = draft.scope === 'personal' ? 'layer0p' : (draft.layer ?? 'layer1')
  return {
    id: '待后端生成',
    scope: draft.scope,
    owner_id: draft.scope === 'personal' ? ownerId.value : null,
    layer,
    maturity: 'draft' as const,
    relative_path: '预览校验后由后端生成',
  }
})

watch(
  draft,
  () => {
    if (preview.value && !previewIsCurrent.value) invalidatePreview()
    requestError.value = ''
    errors.value = {}
  },
  { deep: true, flush: 'post' },
)

onMounted(() => {
  baseline.value = fingerprintDraft(draft)
  window.addEventListener('beforeunload', warnBeforeUnload)
})

onBeforeUnmount(() => window.removeEventListener('beforeunload', warnBeforeUnload))

function warnBeforeUnload(event: BeforeUnloadEvent) {
  if (fingerprintDraft(draft) === baseline.value && !preview.value) return
  event.preventDefault()
  event.returnValue = ''
}

onBeforeRouteLeave((to) => {
  if (to.name === 'knowledge-preview') return true
  if (fingerprintDraft(draft) === baseline.value && !preview.value) return true
  return window.confirm('当前填写内容尚未完成注入，确认离开吗？')
})

async function goToPreview() {
  if (!options.value) {
    requestError.value = sessionOptionsError.value || '知识治理选项尚未加载，请稍后重试'
    pushToast(requestError.value, 'error')
    return
  }
  const nextErrors = validateKnowledgeDraft(draft)
  errors.value = nextErrors
  const firstError = firstFieldError(nextErrors)
  if (firstError) {
    pushToast(firstError, 'error')
    return
  }

  requestError.value = ''
  try {
    if (!previewIsCurrent.value) await requestPreview()
    await router.push({ name: 'knowledge-preview' })
  } catch (reason) {
    if (reason instanceof ApiError) {
      requestError.value = reason.message
      const fieldErrors: KnowledgeErrors = {}
      for (const item of reason.fieldErrors) {
        const field = item.field === 'source_references' ? 'source' : item.field
        fieldErrors[field as keyof KnowledgeErrors] = item.message
      }
      errors.value = { ...errors.value, ...fieldErrors }
    } else {
      requestError.value = reason instanceof Error ? reason.message : '预览校验失败，请重试'
    }
    pushToast(requestError.value, 'error')
  }
}
</script>

<template>
  <div class="workflow-page">
    <div class="workflow-heading">
      <div>
        <h1>人工注入知识</h1>
        <p>将个人经验或团队知识安全写入知识库</p>
      </div>
      <StepProgress :current="1" />
    </div>

    <div v-if="requestError" class="inline-alert error-alert" role="alert">
      <Info :size="19" />
      <span>{{ requestError }}</span>
    </div>
    <div v-else-if="sessionOptionsError" class="inline-alert error-alert" role="alert">
      <Info :size="19" />
      <span>{{ sessionOptionsError }}。为避免提交无效分类，当前暂不能预览。</span>
    </div>

    <div class="create-layout">
      <KnowledgeForm
        :draft="draft"
        :owner-id="ownerId"
        :options="options"
        :errors="errors"
      />

      <aside class="create-sidebar">
        <MetadataCard
          title="元数据预览"
          :id="pendingMetadata.id"
          :scope="pendingMetadata.scope"
          :owner-id="pendingMetadata.owner_id"
          :layer="pendingMetadata.layer"
          :maturity="pendingMetadata.maturity"
          :relative-path="pendingMetadata.relative_path"
        />

        <section class="assurance-card">
          <div class="assurance-item">
            <span class="assurance-icon shield"><ShieldCheck :size="30" /></span>
            <div>
              <h3>后端权限校验</h3>
              <p>注入请求将由后端进行权限校验，确保数据安全与访问合规。</p>
            </div>
          </div>
          <div class="assurance-item">
            <span class="assurance-icon document"><FileCheck2 :size="30" /></span>
            <div>
              <h3>自动更新索引与日志</h3>
              <p>成功注入后，系统将自动更新知识索引与审计日志，便于检索与追溯。</p>
            </div>
          </div>
        </section>
      </aside>
    </div>

    <footer class="workflow-actions">
      <p><Info :size="18" />完成预览校验后即可确认注入</p>
      <div>
        <button class="button button-secondary button-wide" type="button" :disabled="previewing" @click="goToPreview">
          <span v-if="previewing" class="button-spinner dark" />
          {{ previewing ? '正在校验…' : '预览并校验' }}
        </button>
        <button class="button button-muted button-wide" type="button" disabled><LockKeyhole :size="17" />确认注入</button>
      </div>
    </footer>
  </div>
</template>
