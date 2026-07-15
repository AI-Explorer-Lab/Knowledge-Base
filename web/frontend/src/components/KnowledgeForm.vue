<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Bold,
  CheckSquare,
  ChevronDown,
  Code2,
  Eye,
  Heading2,
  Info,
  Italic,
  Link2,
  List,
  ListOrdered,
  LockKeyhole,
  Maximize2,
  Minimize2,
  Quote,
  RefreshCw,
  Strikethrough,
  Table2,
  X,
} from 'lucide-vue-next'
import { getKnowledgeTemplate } from '@/api'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import type {
  KnowledgeDraft,
  KnowledgeLayer,
  KnowledgeOptions,
  KnowledgeType,
  TechnicalDirection,
} from '@/types'
import { ApiError } from '@/types'
import type { KnowledgeErrors } from '@/utils/knowledge'
import {
  formatLayer,
  shouldConfirmTemplateReplacement,
} from '@/utils/knowledge'

const props = defineProps<{
  draft: KnowledgeDraft
  ownerId: string
  options: KnowledgeOptions | null
  errors: KnowledgeErrors
  canManageBusinessDomains: boolean
}>()

const emit = defineEmits<{
  'template-loading': [loading: boolean]
  'add-business-domain': []
}>()

interface TemplateSelection {
  type: KnowledgeType
  technicalDirection: TechnicalDirection | null
  change: 'type' | 'technical-direction'
}

const editor = ref<HTMLTextAreaElement | null>(null)
const editorFullscreen = ref(false)
const tagField = ref<HTMLInputElement | null>(null)
const tagInput = ref('')
const selectedType = ref<KnowledgeType>(props.draft.type)
const selectedTechnicalDirection = ref<TechnicalDirection | ''>(
  props.draft.technical_direction ?? '',
)
const templateLoading = ref(false)
const templateError = ref('')
const loadedTemplateKey = ref<string | null>(null)
const loadedTemplateContent = ref<string | null>(null)
const pendingTemplateSelection = ref<TemplateSelection | null>(null)
const retryTemplateSelection = ref<TemplateSelection | null>(null)
const templateCache = new Map<string, string>()
let templateRequestId = 0

onMounted(() => {
  window.addEventListener('keydown', onEditorKeydown)
})

onBeforeUnmount(() => {
  templateRequestId += 1
  templateLoading.value = false
  window.removeEventListener('keydown', onEditorKeydown)
  document.body.classList.remove('editor-fullscreen-open')
})

const knowledgeTypes = computed(() => props.options?.knowledge_types ?? [
  { value: 'model' as const, label: '模型' },
  { value: 'decision' as const, label: '决策' },
  { value: 'guideline' as const, label: '指南' },
  { value: 'pitfall' as const, label: '陷阱' },
  { value: 'process' as const, label: '流程' },
])

const knowledgeTypeUsage: Record<KnowledgeType, string> = {
  model: '需要说明实体、字段、数据结构或关系时',
  decision: '需要记录技术选型、架构决定及理由时',
  guideline: '需要沉淀推荐做法、禁止做法或检查标准时',
  pitfall: '需要记录风险、故障现象或排查经验时',
  process: '需要说明业务流程、状态流转或操作步骤时',
}

const layers = computed(() => props.options?.layers ?? [])
const technicalDirections = computed(() => props.options?.technical_directions ?? [])

const selectedLayer = computed<KnowledgeLayer>(() =>
  props.draft.scope === 'personal' ? 'layer0p' : (props.draft.layer ?? 'layer1'),
)

const activeTechnicalDirection = computed<TechnicalDirection | null>(() =>
  props.draft.scope === 'team' && props.draft.layer === 'layer1'
    ? (props.draft.technical_direction ?? null)
    : null,
)

const loadingTemplateLabel = computed(() =>
  selectedTechnicalDirection.value
    ? `${selectedTechnicalDirection.value} / ${selectedType.value}`
    : selectedType.value,
)

const templateDialogDescription = computed(() =>
  pendingTemplateSelection.value?.change === 'technical-direction'
    ? '当前正文已经被修改。切换技术立场标签会使用对应的补充模板和知识类型模板替换现有正文；不选择标签时只使用知识类型模板。此操作无法撤销。'
    : '当前正文已经被修改。切换知识类型会使用新模板替换现有正文，此操作无法撤销。',
)

const storageLocation = computed(() => {
  const base = formatLayer(selectedLayer.value)
  if (selectedLayer.value === 'layer2' && props.draft.domain) {
    return `${base} / ${props.draft.domain}`
  }
  return base
})

watch(templateLoading, (loading) => emit('template-loading', loading))

watch(editorFullscreen, (fullscreen) => {
  document.body.classList.toggle('editor-fullscreen-open', fullscreen)
  void nextTick(() => editor.value?.focus())
})

watch(
  () => [props.draft.type, props.draft.technical_direction] as const,
  ([type, technicalDirection]) => {
    if (templateLoading.value || pendingTemplateSelection.value !== null) return
    selectedType.value = type
    selectedTechnicalDirection.value = technicalDirection ?? ''
  },
)

watch(
  () => [props.draft.scope, props.draft.layer, props.options] as const,
  ([scope]) => {
    if (scope === 'personal') {
      delete props.draft.layer
      delete props.draft.technical_direction
      delete props.draft.domain
    } else {
      const allowedLayers = props.options?.layers.map((item) => item.value) ?? []
      if (!props.draft.layer || !allowedLayers.includes(props.draft.layer)) {
        props.draft.layer = props.options?.layers[0]?.value
      }
      if (props.draft.layer === 'layer1') {
        const allowedDirections = props.options?.technical_directions.map((item) => item.value) ?? []
        if (
          props.draft.technical_direction
          && !allowedDirections.includes(props.draft.technical_direction)
        ) {
          delete props.draft.technical_direction
        }
      } else {
        delete props.draft.technical_direction
      }
      if (props.draft.layer !== 'layer2') delete props.draft.domain
      if (
        props.draft.layer === 'layer2'
        && props.draft.domain
        && !props.options?.business_domains.some((domain) => domain.id === props.draft.domain)
      ) {
        delete props.draft.domain
      }
    }
  },
  { immediate: true },
)

function addTag() {
  const value = tagInput.value.trim().replace(/^#/, '')
  if (value && !props.draft.tags.includes(value)) props.draft.tags.push(value)
  tagInput.value = ''
}

function onTagKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' || event.key === ',') {
    event.preventDefault()
    addTag()
  }
  if (event.key === 'Backspace' && !tagInput.value && props.draft.tags.length) props.draft.tags.pop()
}

function removeTag(index: number) {
  props.draft.tags.splice(index, 1)
}

function addSource() {
  props.draft.source_references.push('')
}

function removeSource(index: number) {
  if (props.draft.source_references.length === 1) {
    props.draft.source_references[0] = ''
    return
  }
  props.draft.source_references.splice(index, 1)
}

function toggleEditorFullscreen() {
  editorFullscreen.value = !editorFullscreen.value
}

function onEditorKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && editorFullscreen.value) editorFullscreen.value = false
}

function templateSelectionKey(
  type: KnowledgeType,
  technicalDirection: TechnicalDirection | null,
): string {
  return `${type}:${technicalDirection ?? 'base'}`
}

function currentTemplateSelection(change: TemplateSelection['change']): TemplateSelection {
  return {
    type: props.draft.type,
    technicalDirection: activeTechnicalDirection.value,
    change,
  }
}

function syncTemplateSelectors() {
  selectedType.value = props.draft.type
  selectedTechnicalDirection.value = activeTechnicalDirection.value ?? ''
}

async function templateContent(selection: TemplateSelection): Promise<string> {
  const key = templateSelectionKey(selection.type, selection.technicalDirection)
  const cached = templateCache.get(key)
  if (cached !== undefined) return cached
  const response = await getKnowledgeTemplate(
    selection.type,
    selection.technicalDirection ?? undefined,
  )
  if (
    response.type !== selection.type
    || response.technical_direction !== selection.technicalDirection
    || !response.content.trim()
  ) {
    throw new Error('后端返回的知识模板无效')
  }
  templateCache.set(key, response.content)
  return response.content
}

function templateErrorMessage(reason: unknown): string {
  return reason instanceof ApiError
    ? reason.message
    : reason instanceof Error
      ? reason.message
      : '知识模板加载失败，请稍后重试'
}

async function loadTemplate(selection: TemplateSelection) {
  const requestId = ++templateRequestId
  const contextBeforeRequest = `${props.draft.scope}:${props.draft.layer ?? 'layer0p'}`
  templateLoading.value = true
  templateError.value = ''
  retryTemplateSelection.value = null

  try {
    const content = await templateContent(selection)
    if (requestId !== templateRequestId) return
    if (`${props.draft.scope}:${props.draft.layer ?? 'layer0p'}` !== contextBeforeRequest) {
      syncTemplateSelectors()
      return
    }

    props.draft.type = selection.type
    if (props.draft.scope === 'team' && props.draft.layer === 'layer1') {
      if (selection.technicalDirection) {
        props.draft.technical_direction = selection.technicalDirection
      } else {
        delete props.draft.technical_direction
      }
    }
    props.draft.content = content
    selectedType.value = selection.type
    selectedTechnicalDirection.value = selection.technicalDirection ?? ''
    loadedTemplateKey.value = templateSelectionKey(
      selection.type,
      selection.technicalDirection,
    )
    loadedTemplateContent.value = content
  } catch (reason) {
    if (requestId !== templateRequestId) return
    syncTemplateSelectors()
    retryTemplateSelection.value = selection
    templateError.value = `${templateErrorMessage(reason)}，已保留原有类型和正文`
  } finally {
    if (requestId === templateRequestId) templateLoading.value = false
  }
}

function requestTemplateChange(selection: TemplateSelection) {
  const currentSelection = currentTemplateSelection(selection.change)
  const currentKey = templateSelectionKey(
    currentSelection.type,
    currentSelection.technicalDirection,
  )
  const nextKey = templateSelectionKey(selection.type, selection.technicalDirection)
  if (nextKey === currentKey) {
    templateRequestId += 1
    templateLoading.value = false
    templateError.value = ''
    retryTemplateSelection.value = null
    syncTemplateSelectors()
    return
  }
  const currentTemplate = loadedTemplateKey.value === currentKey
    ? loadedTemplateContent.value
    : null
  if (shouldConfirmTemplateReplacement(props.draft.content, currentTemplate)) {
    pendingTemplateSelection.value = selection
    syncTemplateSelectors()
    return
  }
  void loadTemplate(selection)
}

function onTypeChange() {
  requestTemplateChange({
    type: selectedType.value,
    technicalDirection: activeTechnicalDirection.value,
    change: 'type',
  })
}

function onTechnicalDirectionChange() {
  requestTemplateChange({
    type: props.draft.type,
    technicalDirection: selectedTechnicalDirection.value || null,
    change: 'technical-direction',
  })
}

function cancelTemplateSwitch() {
  pendingTemplateSelection.value = null
  syncTemplateSelectors()
}

function confirmTemplateSwitch() {
  const selection = pendingTemplateSelection.value
  pendingTemplateSelection.value = null
  if (!selection) return
  selectedType.value = selection.type
  selectedTechnicalDirection.value = selection.technicalDirection ?? ''
  void loadTemplate(selection)
}

function retryTemplate() {
  const selection = retryTemplateSelection.value
  templateError.value = ''
  if (!selection) return
  selectedType.value = selection.type
  selectedTechnicalDirection.value = selection.technicalDirection ?? ''
  void loadTemplate(selection)
}

async function wrapSelection(prefix: string, suffix = prefix, placeholder = '文本') {
  const input = editor.value
  if (!input) return
  const start = input.selectionStart
  const end = input.selectionEnd
  const selected = props.draft.content.slice(start, end) || placeholder
  props.draft.content = `${props.draft.content.slice(0, start)}${prefix}${selected}${suffix}${props.draft.content.slice(end)}`
  await nextTick()
  input.focus()
  input.setSelectionRange(start + prefix.length, start + prefix.length + selected.length)
}

async function prefixLines(prefix: string) {
  const input = editor.value
  if (!input) return
  const start = input.selectionStart
  const end = input.selectionEnd
  const before = props.draft.content.lastIndexOf('\n', start - 1) + 1
  const afterIndex = props.draft.content.indexOf('\n', end)
  const after = afterIndex === -1 ? props.draft.content.length : afterIndex
  const selected = props.draft.content.slice(before, after)
  const replaced = selected.split('\n').map((line) => `${prefix}${line}`).join('\n')
  props.draft.content = `${props.draft.content.slice(0, before)}${replaced}${props.draft.content.slice(after)}`
  await nextTick()
  input.focus()
  input.setSelectionRange(before, before + replaced.length)
}

</script>

<template>
  <section class="knowledge-form-card">
    <div class="form-row form-row-top">
      <label id="scope-label">知识范围</label>
      <div class="form-control-stack">
        <div class="segmented-control scope-control" role="radiogroup" aria-labelledby="scope-label">
          <button
            type="button"
            :class="{ selected: draft.scope === 'personal' }"
            role="radio"
            :aria-checked="draft.scope === 'personal'"
            @click="draft.scope = 'personal'"
          >个人知识</button>
          <button
            type="button"
            :class="{ selected: draft.scope === 'team' }"
            role="radio"
            :aria-checked="draft.scope === 'team'"
            @click="draft.scope = 'team'"
          >团队知识</button>
        </div>
        <p class="field-help"><Info :size="16" />{{ draft.scope === 'personal' ? '个人知识仅允许所有者注入和调用' : '团队知识按成员角色授权，并由团队共同消费' }}</p>
      </div>
    </div>

    <div v-if="draft.scope === 'personal'" class="form-row">
      <label for="owner">当前所有者</label>
      <div class="input-with-icon read-only-input">
        <input id="owner" :value="ownerId" readonly />
        <LockKeyhole :size="17" />
      </div>
    </div>

    <div class="form-row">
      <label for="title">标题 <em>*</em></label>
      <div>
        <input id="title" v-model="draft.title" :class="{ invalid: errors.title }" maxlength="120" />
        <p v-if="errors.title" class="field-error">{{ errors.title }}</p>
      </div>
    </div>

    <div class="form-row">
      <label for="type">知识类型 <em>*</em></label>
      <div class="select-shell">
        <select id="type" v-model="selectedType" :aria-busy="templateLoading" @change="onTypeChange">
          <option v-for="item in knowledgeTypes" :key="item.value" :value="item.value">
            {{ item.label }} — {{ knowledgeTypeUsage[item.value] }}
          </option>
        </select>
        <ChevronDown :size="17" />
      </div>
    </div>

    <div class="form-row">
      <label for="tag-input">标签</label>
      <div class="tag-editor" :class="{ invalid: errors.tags }" @click="tagField?.focus()">
        <span v-for="(tag, index) in draft.tags" :key="`${tag}-${index}`" class="tag-chip">
          {{ tag }}
          <button type="button" :aria-label="`移除标签 ${tag}`" @click.stop="removeTag(index)"><X :size="14" /></button>
        </span>
        <input
          id="tag-input"
          ref="tagField"
          v-model="tagInput"
          aria-label="新增标签"
          placeholder="输入标签后按 Enter"
          @blur="addTag"
          @keydown="onTagKeydown"
        />
      </div>
    </div>

    <div class="form-row form-row-sources">
      <label for="source-0">来源 <em>*</em></label>
      <div class="source-list">
        <div v-for="(_, index) in draft.source_references" :key="index" class="source-input-row">
          <input
            :id="`source-${index}`"
            v-model="draft.source_references[index]"
            :class="{ invalid: errors.source }"
            placeholder="例如：项目复盘、架构评审或工作流产物"
          />
          <button v-if="draft.source_references.length > 1" type="button" aria-label="移除来源" @click="removeSource(index)"><X :size="17" /></button>
        </div>
        <button class="text-button compact-add" type="button" @click="addSource">+ 添加来源</button>
        <p v-if="errors.source" class="field-error">{{ errors.source }}</p>
      </div>
    </div>

    <template v-if="draft.scope === 'team'">
      <div class="form-row">
        <label for="layer">知识层级 <em>*</em></label>
        <div class="select-shell">
          <select id="layer" v-model="draft.layer">
            <option v-for="item in layers" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
          <ChevronDown :size="17" />
        </div>
      </div>
      <div v-if="draft.layer === 'layer1'" class="form-row">
        <label for="technical-direction">技术立场标签 <span class="optional-label">（可选）</span></label>
        <div class="form-control-stack">
          <div class="select-shell">
            <select
              id="technical-direction"
              v-model="selectedTechnicalDirection"
              :aria-busy="templateLoading"
              @change="onTechnicalDirectionChange"
            >
              <option value="">不选择（中性知识）</option>
              <option
                v-for="item in technicalDirections"
                :key="item.value"
                :value="item.value"
              >{{ item.label }} · {{ item.value }}</option>
            </select>
            <ChevronDown :size="17" />
          </div>
          <p class="field-help">
            <Info :size="16" />主要推荐正确方案时选择正向模式；主要警告错误做法时选择反模式；中性知识保持不选择。
          </p>
        </div>
      </div>
      <div v-if="draft.layer === 'layer2'" class="form-row">
        <label for="domain">业务领域 <em>*</em></label>
        <div class="domain-control-stack">
          <div class="domain-control-row">
            <div class="select-shell">
              <select id="domain" v-model="draft.domain" :class="{ invalid: errors.domain }">
                <option value="" disabled>请选择业务领域</option>
                <option
                  v-for="domain in options?.business_domains ?? []"
                  :key="domain.id"
                  :value="domain.id"
                >{{ domain.name }} · {{ domain.id }}</option>
              </select>
              <ChevronDown :size="17" />
            </div>
            <button
              v-if="canManageBusinessDomains"
              class="domain-add-button"
              type="button"
              @click="emit('add-business-domain')"
            >+ 新增业务领域</button>
          </div>
          <p v-if="errors.domain" class="field-error">{{ errors.domain }}</p>
          <p v-if="!options?.business_domains.length" class="domain-empty-help">
            {{ canManageBusinessDomains ? '尚未配置业务领域，请先新增后再选择。' : '尚未配置业务领域，请联系 Maintainer 新增。' }}
          </p>
        </div>
      </div>
    </template>

    <div class="form-row">
      <label for="storage">存储位置</label>
      <div class="input-with-icon read-only-input">
        <input id="storage" :value="storageLocation" readonly />
        <LockKeyhole :size="17" />
      </div>
    </div>

    <div class="form-row form-row-editor">
      <label for="knowledge-content">知识正文 <em>*</em></label>
      <div>
        <div
          class="template-guidance"
          :class="{ 'template-guidance-error': templateError }"
          aria-live="polite"
        >
          <template v-if="templateLoading">
            <span class="template-spinner" aria-hidden="true" />
            <span>正在加载 {{ loadingTemplateLabel }} 模板…</span>
          </template>
          <template v-else-if="templateError">
            <span>{{ templateError }}</span>
            <button class="text-button template-retry" type="button" @click="retryTemplate">
              <RefreshCw :size="14" />重新加载
            </button>
          </template>
          <template v-else>
            <Info :size="16" />
            <span>首次打开保持为空；切换知识类型或 Layer 1 技术立场标签时可载入对应填写模板。</span>
          </template>
        </div>
        <div
          class="editor-shell"
          :class="{
            invalid: errors.content,
            'template-is-loading': templateLoading,
            'editor-fullscreen': editorFullscreen,
          }"
        >
          <div class="editor-toolbar" aria-label="Markdown 编辑工具">
            <button type="button" title="二级标题" @click="prefixLines('## ')"><Heading2 :size="18" /></button>
            <span class="toolbar-divider" />
            <button type="button" title="加粗" @click="wrapSelection('**')"><Bold :size="17" /></button>
            <button type="button" title="斜体" @click="wrapSelection('_')"><Italic :size="17" /></button>
            <button type="button" title="删除线" @click="wrapSelection('~~')"><Strikethrough :size="17" /></button>
            <button type="button" title="行内代码" @click="wrapSelection('`')"><Code2 :size="17" /></button>
            <button type="button" title="链接" @click="wrapSelection('[', '](https://)', '链接文字')"><Link2 :size="17" /></button>
            <button type="button" title="无序列表" @click="prefixLines('- ')"><List :size="18" /></button>
            <button type="button" title="有序列表" @click="prefixLines('1. ')"><ListOrdered :size="18" /></button>
            <button type="button" title="任务项" @click="prefixLines('- [ ] ')"><CheckSquare :size="17" /></button>
            <button type="button" title="引用" @click="prefixLines('> ')"><Quote :size="17" /></button>
            <button type="button" title="表格" @click="wrapSelection('| 列 1 | 列 2 |\n| --- | --- |\n| ', ' | 内容 |', '内容')"><Table2 :size="17" /></button>
            <span class="toolbar-spacer" />
            <button type="button" title="预览将在下一步显示"><Eye :size="18" /></button>
            <button
              type="button"
              :title="editorFullscreen ? '退出全屏编辑' : '全屏编辑'"
              :aria-label="editorFullscreen ? '退出全屏编辑' : '全屏编辑'"
              :aria-pressed="editorFullscreen"
              @click="toggleEditorFullscreen"
            >
              <Minimize2 v-if="editorFullscreen" :size="17" />
              <Maximize2 v-else :size="17" />
            </button>
          </div>
          <div class="editor-textarea-grow" :data-replicated-value="draft.content">
            <textarea
              id="knowledge-content"
              ref="editor"
              v-model="draft.content"
              :disabled="templateLoading"
              spellcheck="false"
              aria-label="Markdown 知识正文"
            />
          </div>
        </div>
      </div>
      <p v-if="errors.content" class="field-error editor-error">{{ errors.content }}</p>
    </div>
    <ConfirmDialog
      :open="pendingTemplateSelection !== null"
      title="替换知识正文？"
      :description="templateDialogDescription"
      confirm-text="替换正文"
      danger
      @cancel="cancelTemplateSwitch"
      @confirm="confirmTemplateSwitch"
    />
  </section>
</template>
