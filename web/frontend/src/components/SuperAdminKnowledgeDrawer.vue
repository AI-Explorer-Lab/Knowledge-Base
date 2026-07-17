<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { LockKeyhole, X } from 'lucide-vue-next'
import type {
  KnowledgeLayer,
  KnowledgeOptions,
  KnowledgeScope,
  KnowledgeType,
  SuperAdminKnowledge,
  SuperAdminKnowledgeInput,
  TechnicalDirection,
} from '@/types'

const props = defineProps<{
  open: boolean
  knowledge: SuperAdminKnowledge | null
  options: KnowledgeOptions | null
  busy?: boolean
}>()

const emit = defineEmits<{
  close: []
  preview: [payload: SuperAdminKnowledgeInput]
}>()

type FormState = {
  scope: KnowledgeScope
  owner_id: string
  title: string
  type: KnowledgeType
  tags: string
  source_references: string
  layer: Exclude<KnowledgeLayer, 'layer0p'>
  technical_direction: TechnicalDirection | ''
  domain: string
  content: string
  reason: string
  owner_confirmed_by: string
}

const form = reactive<FormState>({
  scope: 'team',
  owner_id: '',
  title: '',
  type: 'guideline',
  tags: '',
  source_references: '',
  layer: 'layer1',
  technical_direction: '',
  domain: '',
  content: '',
  reason: '',
  owner_confirmed_by: '',
})
const errors = reactive({ title: '', sources: '', content: '', reason: '', owner: '', domain: '' })
const activeDomains = computed(() => props.options?.business_domains.filter((item) => item.status === 'active') ?? [])
const requiresOwnerConfirmation = computed(() => {
  const knowledge = props.knowledge
  if (!knowledge) return false
  if (knowledge.scope === 'personal' && form.scope === 'team') return true
  return form.scope === 'personal' && (
    knowledge.scope !== 'personal' || form.owner_id !== knowledge.owner_id
  )
})

watch(
  () => [props.open, props.knowledge] as const,
  ([open, knowledge]) => {
    if (!open || !knowledge) return
    Object.assign(form, {
      scope: knowledge.scope,
      owner_id: knowledge.owner_id ?? '',
      title: knowledge.title,
      type: knowledge.type,
      tags: knowledge.tags.join(', '),
      source_references: knowledge.source_references.join('\n'),
      layer: knowledge.layer === 'layer0p' ? 'layer1' : knowledge.layer,
      technical_direction: knowledge.technical_direction ?? '',
      domain: knowledge.domain ?? '',
      content: knowledge.content,
      reason: '',
      owner_confirmed_by: '',
    })
    Object.keys(errors).forEach((key) => { errors[key as keyof typeof errors] = '' })
  },
  { immediate: true },
)

function submit() {
  const knowledge = props.knowledge
  if (!knowledge) return
  errors.title = form.title.trim() ? '' : '请输入标题'
  errors.sources = form.source_references.split('\n').some((item) => item.trim()) ? '' : '至少填写一条来源'
  errors.content = form.content.trim() ? '' : '请输入知识正文'
  errors.reason = form.reason.trim().length >= 3 ? '' : '请填写至少 3 个字的修改原因'
  errors.owner = form.scope === 'personal' && !form.owner_id.trim() ? '个人知识必须指定所有者' : ''
  errors.domain = form.scope === 'team' && form.layer === 'layer2' && !form.domain ? '请选择业务领域' : ''
  if (Object.values(errors).some(Boolean)) return

  const payload: SuperAdminKnowledgeInput = {
    scope: form.scope,
    title: form.title.trim(),
    type: form.type,
    tags: form.tags.split(',').map((item) => item.trim()).filter(Boolean),
    source_references: form.source_references.split('\n').map((item) => item.trim()).filter(Boolean),
    content: form.content.trim(),
    reason: form.reason.trim(),
    base_digest: knowledge.base_digest,
  }
  if (form.scope === 'personal') {
    payload.owner_id = form.owner_id.trim()
  } else {
    payload.layer = form.layer
    if (form.layer === 'layer1' && form.technical_direction) {
      payload.technical_direction = form.technical_direction
    }
    if (form.layer === 'layer2') payload.domain = form.domain
  }
  if (requiresOwnerConfirmation.value) {
    payload.owner_confirmed_by = form.owner_confirmed_by.trim()
  }
  emit('preview', payload)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="drawer-layer admin-drawer-layer" @click.self="emit('close')">
        <aside class="super-admin-drawer" role="dialog" aria-modal="true" aria-label="修改已有知识">
          <header class="drawer-header">
            <div><span class="eyebrow">Super Admin</span><h2>修改已有知识</h2></div>
            <button type="button" aria-label="关闭" @click="emit('close')"><X :size="23" /></button>
          </header>

          <form v-if="knowledge" class="admin-edit-form" @submit.prevent="submit">
            <div class="admin-locked-summary">
              <span><LockKeyhole :size="16" />稳定 ID</span><code>{{ knowledge.id }}</code>
              <span>当前版本</span><strong>revision {{ knowledge.revision }}</strong>
              <span>当前路径</span><code>{{ knowledge.relative_path }}</code>
            </div>

            <div class="admin-form-grid">
              <label class="drawer-field"><span>知识范围</span><select v-model="form.scope"><option value="personal">个人知识</option><option value="team">团队知识</option></select></label>
              <label v-if="form.scope === 'personal'" class="drawer-field"><span>所有者 ID</span><input v-model="form.owner_id" /><small v-if="errors.owner" class="field-error">{{ errors.owner }}</small></label>
              <label class="drawer-field admin-field-wide"><span>标题</span><input v-model="form.title" maxlength="160" /><small v-if="errors.title" class="field-error">{{ errors.title }}</small></label>
              <label class="drawer-field"><span>类型</span><select v-model="form.type"><option v-for="item in options?.knowledge_types ?? []" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
              <label v-if="form.scope === 'team'" class="drawer-field"><span>Layer</span><select v-model="form.layer"><option v-for="item in options?.layers ?? []" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
              <label v-if="form.scope === 'team' && form.layer === 'layer1'" class="drawer-field"><span>技术方向</span><select v-model="form.technical_direction"><option value="">未指定</option><option v-for="item in options?.technical_directions ?? []" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
              <label v-if="form.scope === 'team' && form.layer === 'layer2'" class="drawer-field"><span>业务领域</span><select v-model="form.domain"><option value="">请选择</option><option v-for="item in activeDomains" :key="item.id" :value="item.id">{{ item.name }}</option></select><small v-if="errors.domain" class="field-error">{{ errors.domain }}</small></label>
              <label class="drawer-field admin-field-wide"><span>标签（逗号分隔）</span><input v-model="form.tags" /></label>
              <label class="drawer-field admin-field-wide"><span>来源（每行一条）</span><textarea v-model="form.source_references" rows="3" /><small v-if="errors.sources" class="field-error">{{ errors.sources }}</small></label>
              <label class="drawer-field admin-field-wide"><span>Markdown 正文</span><textarea v-model="form.content" class="admin-content-editor" rows="16" /><small v-if="errors.content" class="field-error">{{ errors.content }}</small></label>
              <label class="drawer-field admin-field-wide"><span>修改原因</span><textarea v-model="form.reason" rows="3" placeholder="说明为什么需要修改，审计日志会记录此原因" /><small v-if="errors.reason" class="field-error">{{ errors.reason }}</small></label>
              <label v-if="requiresOwnerConfirmation" class="drawer-field admin-field-wide"><span>所有者确认 ID</span><input v-model="form.owner_confirmed_by" placeholder="必须与需要确认的所有者 ID 一致" /></label>
            </div>

            <div class="admin-drawer-footer">
              <p>提交修改后 revision 会增加，成熟度会回到 draft。</p>
              <div><button class="button button-secondary" type="button" :disabled="busy" @click="emit('close')">取消</button><button class="button button-primary" type="submit" :disabled="busy">{{ busy ? '正在校验…' : '预览修改' }}</button></div>
            </div>
          </form>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>
