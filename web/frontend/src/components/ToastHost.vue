<script setup lang="ts">
import { CheckCircle2, CircleAlert, Info, X } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'

const { toasts, dismissToast } = useToast()
</script>

<template>
  <TransitionGroup name="toast" tag="div" class="toast-host" aria-live="polite">
    <div v-for="toast in toasts" :key="toast.id" class="toast-item" :class="`toast-${toast.tone}`">
      <CheckCircle2 v-if="toast.tone === 'success'" :size="19" />
      <CircleAlert v-else-if="toast.tone === 'error'" :size="19" />
      <Info v-else :size="19" />
      <span>{{ toast.message }}</span>
      <button type="button" aria-label="关闭提示" @click="dismissToast(toast.id)"><X :size="16" /></button>
    </div>
  </TransitionGroup>
</template>
