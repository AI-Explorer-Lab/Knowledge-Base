<script setup lang="ts">
import { Copy } from 'lucide-vue-next'
import type { KnowledgeLayer, KnowledgeScope } from '@/types'
import { pushToast } from '@/composables/useToast'

const props = withDefaults(defineProps<{
  title?: string
  id: string
  scope: KnowledgeScope
  ownerId: string | null
  layer: KnowledgeLayer
  maturity: string
  relativePath: string
}>(), {
  title: '元数据预览',
})

async function copyPath() {
  try {
    await navigator.clipboard.writeText(props.relativePath)
    pushToast('仓库路径已复制', 'success')
  } catch {
    pushToast('复制失败，请手动选择路径', 'error')
  }
}
</script>

<template>
  <section class="metadata-card">
    <header class="card-heading-row">
      <h2>{{ title }}</h2>
      <span class="readonly-badge">只读</span>
    </header>
    <dl class="metadata-table">
      <div><dt>ID</dt><dd>{{ id }}</dd></div>
      <div><dt>scope</dt><dd>{{ scope }}</dd></div>
      <div v-if="ownerId"><dt>owner_id</dt><dd>{{ ownerId }}</dd></div>
      <div><dt>layer</dt><dd>{{ layer }}</dd></div>
      <div><dt>maturity</dt><dd>{{ maturity }}</dd></div>
    </dl>
    <h3 class="path-heading">仓库路径</h3>
    <div class="path-box">
      <code>{{ relativePath }}</code>
      <button type="button" aria-label="复制仓库路径" @click="copyPath"><Copy :size="18" /></button>
    </div>
  </section>
</template>
