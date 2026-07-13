<script setup lang="ts">
import { X } from 'lucide-vue-next'

withDefaults(defineProps<{
  open: boolean
  title: string
  description: string
  confirmText?: string
  busy?: boolean
  danger?: boolean
}>(), {
  confirmText: '确认修改',
  busy: false,
  danger: false,
})

const emit = defineEmits<{ cancel: []; confirm: [] }>()
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-backdrop" @click.self="emit('cancel')">
        <section class="confirm-dialog" role="dialog" aria-modal="true" :aria-label="title">
          <button class="dialog-close" type="button" aria-label="关闭" @click="emit('cancel')"><X :size="20" /></button>
          <h2>{{ title }}</h2>
          <p>{{ description }}</p>
          <div class="dialog-actions">
            <button class="button button-secondary" type="button" :disabled="busy" @click="emit('cancel')">取消</button>
            <button
              class="button"
              :class="danger ? 'button-danger' : 'button-primary'"
              type="button"
              :disabled="busy"
              @click="emit('confirm')"
            >
              <span v-if="busy" class="button-spinner" />
              {{ busy ? '正在保存…' : confirmText }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>
