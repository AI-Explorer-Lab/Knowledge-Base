<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
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
  Strikethrough,
  Table2,
  X,
} from 'lucide-vue-next'
import type { KnowledgeDraft, KnowledgeLayer, KnowledgeOptions, KnowledgeType } from '@/types'
import type { KnowledgeErrors } from '@/utils/knowledge'
import { categoryForType, formatLayer } from '@/utils/knowledge'

const props = defineProps<{
  draft: KnowledgeDraft
  ownerId: string
  options: KnowledgeOptions | null
  errors: KnowledgeErrors
}>()

const editor = ref<HTMLTextAreaElement | null>(null)
const tagField = ref<HTMLInputElement | null>(null)
const tagInput = ref('')

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

function onTypeChange() {
  if (props.draft.scope === 'team') {
    props.draft.category = categoryForType(props.draft.type, selectedLayer.value, props.options)
  }
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
        <select id="type" v-model="draft.type" @change="onTypeChange">
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
      <div class="editor-shell" :class="{ invalid: errors.content }">
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
          spellcheck="false"
          aria-label="Markdown 知识正文"
        />
      </div>
      <p v-if="errors.content" class="field-error editor-error">{{ errors.content }}</p>
    </div>
  </section>
</template>
