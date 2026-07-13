<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
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
  Quote,
  RefreshCw,
  Strikethrough,
  Table2,
  X,
} from 'lucide-vue-next'
import { getKnowledgeTemplate } from '@/api'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import type { KnowledgeDraft, KnowledgeLayer, KnowledgeOptions, KnowledgeType } from '@/types'
import { ApiError } from '@/types'
import type { KnowledgeErrors } from '@/utils/knowledge'
import {
  categoryForType,
  formatLayer,
  shouldConfirmTemplateReplacement,
} from '@/utils/knowledge'

const props = defineProps<{
  draft: KnowledgeDraft
  ownerId: string
  options: KnowledgeOptions | null
  errors: KnowledgeErrors
}>()

const emit = defineEmits<{
  'template-loading': [loading: boolean]
}>()

const editor = ref<HTMLTextAreaElement | null>(null)
const tagField = ref<HTMLInputElement | null>(null)
const tagInput = ref('')
const selectedType = ref<KnowledgeType>(props.draft.type)
const templateLoading = ref(false)
const templateError = ref('')
const loadedTemplateType = ref<KnowledgeType | null>(null)
const loadedTemplateContent = ref<string | null>(null)
const pendingTemplateType = ref<KnowledgeType | null>(null)
const retryTemplateType = ref<KnowledgeType | null>(null)
const templateCache = new Map<KnowledgeType, string>()
let initialTemplateRequested = false
let templateRequestId = 0

onBeforeUnmount(() => {
  templateRequestId += 1
  templateLoading.value = false
})

const knowledgeTypes = computed(() => props.options?.knowledge_types ?? [
  { value: 'model' as const, label: 'model' },
  { value: 'decision' as const, label: 'decision' },
  { value: 'guideline' as const, label: 'guideline' },
  { value: 'pitfall' as const, label: 'pitfall' },
  { value: 'process' as const, label: 'process' },
])

const layers = computed(() => props.options?.layers ?? [])

const selectedLayer = computed<KnowledgeLayer>(() =>
  props.draft.scope === 'personal' ? 'layer0p' : (props.draft.layer ?? 'layer1'),
)

const categories = computed(() => props.options?.categories[selectedLayer.value] ?? [])

watch(templateLoading, (loading) => emit('template-loading', loading))

watch(
  () => props.draft.type,
  (type) => {
    if (!templateLoading.value && pendingTemplateType.value === null) selectedType.value = type
  },
)

watch(
  () => props.options,
  (availableOptions) => {
    if (!availableOptions || initialTemplateRequested) return
    initialTemplateRequested = true
    if (!props.draft.content.trim()) void loadTemplate(props.draft.type, 'initial')
  },
  { immediate: true },
)

watch(
  () => [props.draft.scope, props.draft.type, props.draft.layer, props.options] as const,
  ([scope, type]) => {
    if (scope === 'personal') {
      delete props.draft.layer
      delete props.draft.domain
      delete props.draft.category
    } else {
      const allowedLayers = props.options?.layers.map((item) => item.value) ?? []
      if (!props.draft.layer || !allowedLayers.includes(props.draft.layer)) {
        props.draft.layer = props.options?.layers[0]?.value
      }
      if (props.draft.layer !== 'layer2') delete props.draft.domain
      if (props.draft.layer) {
        props.draft.category = categoryForType(type, props.draft.layer, props.options)
      } else {
        delete props.draft.category
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

async function templateContent(type: KnowledgeType): Promise<string> {
  const cached = templateCache.get(type)
  if (cached !== undefined) return cached
  const response = await getKnowledgeTemplate(type)
  if (response.type !== type || !response.content.trim()) {
    throw new Error('后端返回的知识模板无效')
  }
  templateCache.set(type, response.content)
  return response.content
}

function templateErrorMessage(reason: unknown): string {
  return reason instanceof ApiError
    ? reason.message
    : reason instanceof Error
      ? reason.message
      : '知识模板加载失败，请稍后重试'
}

async function loadTemplate(type: KnowledgeType, mode: 'initial' | 'switch') {
  const requestId = ++templateRequestId
  const contentBeforeRequest = props.draft.content
  templateLoading.value = true
  templateError.value = ''
  retryTemplateType.value = null

  try {
    const content = await templateContent(type)
    if (requestId !== templateRequestId) return

    if (mode === 'initial') {
      if (props.draft.type !== type || props.draft.content !== contentBeforeRequest) return
    } else {
      props.draft.type = type
      if (props.draft.scope === 'team') {
        props.draft.category = categoryForType(type, selectedLayer.value, props.options)
      }
    }

    props.draft.content = content
    selectedType.value = type
    loadedTemplateType.value = type
    loadedTemplateContent.value = content
  } catch (reason) {
    if (requestId !== templateRequestId) return
    selectedType.value = props.draft.type
    retryTemplateType.value = type
    templateError.value = mode === 'switch'
      ? `${templateErrorMessage(reason)}，已保留原有类型和正文`
      : templateErrorMessage(reason)
  } finally {
    if (requestId === templateRequestId) templateLoading.value = false
  }
}

function requestTypeChange(type: KnowledgeType) {
  if (type === props.draft.type) {
    templateRequestId += 1
    templateLoading.value = false
    templateError.value = ''
    retryTemplateType.value = null
    selectedType.value = props.draft.type
    return
  }
  const currentTemplate = loadedTemplateType.value === props.draft.type
    ? loadedTemplateContent.value
    : null
  if (shouldConfirmTemplateReplacement(props.draft.content, currentTemplate)) {
    pendingTemplateType.value = type
    selectedType.value = props.draft.type
    return
  }
  void loadTemplate(type, 'switch')
}

function onTypeChange() {
  requestTypeChange(selectedType.value)
}

function cancelTemplateSwitch() {
  pendingTemplateType.value = null
  selectedType.value = props.draft.type
}

function confirmTemplateSwitch() {
  const type = pendingTemplateType.value
  pendingTemplateType.value = null
  if (!type) return
  selectedType.value = type
  void loadTemplate(type, 'switch')
}

function retryTemplate() {
  const type = retryTemplateType.value ?? props.draft.type
  templateError.value = ''
  selectedType.value = type
  if (type === props.draft.type && !props.draft.content.trim()) {
    void loadTemplate(type, 'initial')
    return
  }
  requestTypeChange(type)
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
          <option v-for="item in knowledgeTypes" :key="item.value" :value="item.value">{{ item.label }}</option>
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
      <div v-if="draft.layer === 'layer2'" class="form-row">
        <label for="domain">业务领域 <em>*</em></label>
        <div class="select-shell">
          <select id="domain" v-model="draft.domain" :class="{ invalid: errors.domain }">
            <option value="" disabled>请选择业务领域</option>
            <option v-for="domain in options?.business_domains ?? []" :key="domain" :value="domain">{{ domain }}</option>
          </select>
          <ChevronDown :size="17" />
        </div>
      </div>
      <div class="form-row">
        <label for="category">受控分类</label>
        <div class="select-shell">
          <select id="category" v-model="draft.category">
            <option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
          </select>
          <ChevronDown :size="17" />
        </div>
      </div>
    </template>

    <div class="form-row">
      <label for="storage">存储位置</label>
      <div class="input-with-icon read-only-input">
        <input id="storage" :value="formatLayer(selectedLayer)" readonly />
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
            <span>正在加载 {{ selectedType }} 模板…</span>
          </template>
          <template v-else-if="templateError">
            <span>{{ templateError }}</span>
            <button class="text-button template-retry" type="button" @click="retryTemplate">
              <RefreshCw :size="14" />重新加载
            </button>
          </template>
          <template v-else>
            <Info :size="16" />
            <span>正文已按知识类型提供填写示例，请根据真实知识修改内容。</span>
          </template>
        </div>
        <div
          class="editor-shell"
          :class="{ invalid: errors.content, 'template-is-loading': templateLoading }"
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
            <button type="button" title="扩大编辑区" @click="editor?.focus()"><Maximize2 :size="17" /></button>
          </div>
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
      <p v-if="errors.content" class="field-error editor-error">{{ errors.content }}</p>
    </div>
    <ConfirmDialog
      :open="pendingTemplateType !== null"
      title="替换知识正文？"
      description="当前正文已经被修改。切换知识类型会使用新模板替换现有正文，此操作无法撤销。"
      confirm-text="替换正文"
      danger
      @cancel="cancelTemplateSwitch"
      @confirm="confirmTemplateSwitch"
    />
  </section>
</template>
