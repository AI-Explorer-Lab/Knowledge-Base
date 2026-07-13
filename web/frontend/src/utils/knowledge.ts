import type { KnowledgeDraft, KnowledgeLayer, KnowledgeOptions, KnowledgeType } from '@/types'

export type KnowledgeField = keyof KnowledgeDraft | 'source'
export type KnowledgeErrors = Partial<Record<KnowledgeField, string>>

const TYPE_CATEGORY: Record<KnowledgeType, string> = {
  model: 'models',
  decision: 'decisions',
  guideline: 'guidelines',
  pitfall: 'pitfalls',
  process: 'processes',
}

export function initialKnowledgeDraft(): KnowledgeDraft {
  return {
    scope: 'personal',
    title: '',
    type: 'guideline',
    tags: [],
    source_references: [''],
    content: '',
  }
}

export function buildKnowledgePayload(draft: KnowledgeDraft): KnowledgeDraft {
  const sources = draft.source_references.map((source) => source.trim()).filter(Boolean)
  const payload: KnowledgeDraft = {
    scope: draft.scope,
    title: draft.title.trim(),
    type: draft.type,
    tags: draft.tags.map((tag) => tag.trim()).filter(Boolean),
    source_references: sources,
    content: draft.content.trim(),
  }

  if (draft.scope === 'team') {
    payload.layer = draft.layer ?? 'layer1'
    payload.category = draft.category?.trim()
    if (payload.layer === 'layer2' && draft.domain?.trim()) payload.domain = draft.domain.trim()
  }

  return payload
}

export function fingerprintDraft(draft: KnowledgeDraft): string {
  return JSON.stringify(buildKnowledgePayload(draft))
}

export function validateKnowledgeDraft(draft: KnowledgeDraft): KnowledgeErrors {
  const errors: KnowledgeErrors = {}
  if (!draft.title.trim()) errors.title = '请输入知识标题'
  if (!draft.type) errors.type = '请选择知识类型'
  if (!draft.source_references.some((source) => source.trim())) errors.source = '请至少填写一条来源说明'
  if (!draft.content.trim()) errors.content = '请输入知识正文'
  if (draft.scope === 'team') {
    if (!draft.layer) errors.layer = '请选择团队知识层级'
    if (!draft.category?.trim()) errors.category = '请选择受控分类'
    if (draft.layer === 'layer2' && !draft.domain?.trim()) errors.domain = 'Layer 2 知识必须选择业务领域'
  }
  return errors
}

export function firstFieldError(errors: KnowledgeErrors): string | null {
  return Object.values(errors)[0] ?? null
}

export function categoryForType(type: KnowledgeType, layer: KnowledgeLayer, options?: KnowledgeOptions | null) {
  const preferred = TYPE_CATEGORY[type]
  if (!options) return ''
  const available = options?.categories[layer] ?? []
  return available.includes(preferred) ? preferred : (available[0] ?? '')
}

export function formatLayer(layer: KnowledgeLayer) {
  const labels: Record<KnowledgeLayer, string> = {
    layer0p: 'Layer 0-P · personal',
    layer1: 'Layer 1 · 技术知识',
    layer2: 'Layer 2 · 业务知识',
    layer3: 'Layer 3 · 项目知识',
  }
  return labels[layer]
}

export function formatKnowledgeTime(value?: string) {
  const date = value ? new Date(value) : new Date()
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date).replaceAll('/', '-').replace(',', '')
}
