<script setup lang="ts">
import { AlertTriangle, ArrowRight, CheckCircle2, X } from 'lucide-vue-next'
import type { SuperAdminPreviewResponse } from '@/types'

defineProps<{ open: boolean; preview: SuperAdminPreviewResponse | null; busy?: boolean }>()
const emit = defineEmits<{ cancel: []; confirm: [] }>()
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-backdrop admin-preview-backdrop" @click.self="emit('cancel')">
        <section class="admin-preview-modal" role="dialog" aria-modal="true" aria-label="确认知识修改">
          <header><div><span class="eyebrow">修改预览</span><h2>确认前后差异</h2></div><button type="button" aria-label="关闭" @click="emit('cancel')"><X :size="23" /></button></header>
          <template v-if="preview">
            <div class="admin-preview-warning"><AlertTriangle :size="21" /><span>此操作会创建新 revision，并使当前知识回到 draft。</span></div>
            <div class="admin-diff-grid">
              <article><span>修改前 · revision {{ preview.before.revision }}</span><h3>{{ preview.before.title }}</h3><code>{{ preview.before.relative_path }}</code><p>{{ preview.before.scope }} · {{ preview.before.layer }} · {{ preview.before.maturity }}</p></article>
              <ArrowRight class="admin-diff-arrow" :size="24" />
              <article><span>修改后 · revision {{ preview.after.revision }}</span><h3>{{ preview.after.title }}</h3><code>{{ preview.after.relative_path }}</code><p>{{ preview.after.scope }} · {{ preview.after.layer }} · {{ preview.after.maturity }}</p></article>
            </div>
            <div class="admin-preview-section"><h3>变更字段</h3><div class="admin-chip-list"><span v-for="field in preview.changed_fields" :key="field">{{ field }}</span></div></div>
            <div class="admin-preview-section"><h3>治理影响</h3><ul><li v-for="item in preview.consequences" :key="item"><CheckCircle2 :size="17" />{{ item }}</li></ul></div>
            <footer><button class="button button-secondary" type="button" :disabled="busy" @click="emit('cancel')">返回修改</button><button class="button button-primary" type="button" :disabled="busy" @click="emit('confirm')">{{ busy ? '正在提交…' : '确认并写入' }}</button></footer>
          </template>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>
