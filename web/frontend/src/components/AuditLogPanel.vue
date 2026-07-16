<script setup lang="ts">
import { RefreshCw, Search } from 'lucide-vue-next'
import type { AuditRecord } from '@/types'

defineProps<{ items: AuditRecord[]; total: number; loading?: boolean; query: string }>()
const emit = defineEmits<{ 'update:query': [value: string]; refresh: [] }>()

function detailText(detail: unknown) {
  return typeof detail === 'string' ? detail : JSON.stringify(detail, null, 2)
}
</script>

<template>
  <section class="admin-panel audit-panel">
    <header class="admin-panel-header"><div><h2>审计记录</h2><p>只读查看知识、成员、领域和治理操作</p></div><div class="admin-toolbar"><label><Search :size="17" /><input :value="query" placeholder="搜索操作人、目标或动作" @input="emit('update:query', ($event.target as HTMLInputElement).value)" /></label><button type="button" :disabled="loading" @click="emit('refresh')"><RefreshCw :size="18" /></button></div></header>
    <p class="admin-count">共 {{ total }} 条记录</p>
    <div v-if="loading" class="table-loading"><span class="loading-spinner" />正在加载审计记录…</div>
    <div v-else-if="!items.length" class="browse-empty"><h3>暂无匹配记录</h3></div>
    <div v-else class="audit-list">
      <article v-for="item in items" :key="`${item.timestamp}-${item.action}-${item.target_id}`">
        <div class="audit-main"><span>{{ item.action }}</span><strong>{{ item.target_id }}</strong><time>{{ item.timestamp }}</time></div>
        <p>操作人：{{ item.actor }} · 会话：{{ item.session }}</p>
        <pre>{{ detailText(item.detail) }}</pre>
      </article>
    </div>
  </section>
</template>
