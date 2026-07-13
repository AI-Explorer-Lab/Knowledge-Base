import { computed, reactive, ref } from 'vue'
import { createKnowledge, previewKnowledge } from '@/api'
import type { CreateKnowledgeResponse, KnowledgeDraft, PreviewResponse } from '@/types'
import {
  buildKnowledgePayload,
  fingerprintDraft,
  initialKnowledgeDraft,
} from '@/utils/knowledge'

const draft = reactive<KnowledgeDraft>(initialKnowledgeDraft())
const preview = ref<PreviewResponse | null>(null)
const result = ref<CreateKnowledgeResponse | null>(null)
const previewFingerprint = ref('')
const previewing = ref(false)
const submitting = ref(false)

const previewIsCurrent = computed(
  () => Boolean(preview.value) && previewFingerprint.value === fingerprintDraft(draft),
)

function invalidatePreview() {
  preview.value = null
  result.value = null
  previewFingerprint.value = ''
}

async function requestPreview(): Promise<PreviewResponse> {
  previewing.value = true
  const payload = buildKnowledgePayload(draft)
  try {
    const response = await previewKnowledge(payload)
    preview.value = response
    previewFingerprint.value = fingerprintDraft(payload)
    result.value = null
    return response
  } finally {
    previewing.value = false
  }
}

async function submitKnowledge(): Promise<CreateKnowledgeResponse> {
  if (!preview.value || !previewIsCurrent.value) {
    throw new Error('预览内容已变化，请重新校验')
  }
  submitting.value = true
  try {
    const response = await createKnowledge(buildKnowledgePayload(draft), preview.value.preview_token)
    result.value = response
    return response
  } finally {
    submitting.value = false
  }
}

function resetFlow() {
  Object.assign(draft, initialKnowledgeDraft())
  preview.value = null
  result.value = null
  previewFingerprint.value = ''
}

export function useKnowledgeFlow() {
  return {
    draft,
    preview,
    result,
    previewing,
    submitting,
    previewIsCurrent,
    invalidatePreview,
    requestPreview,
    submitKnowledge,
    resetFlow,
  }
}
