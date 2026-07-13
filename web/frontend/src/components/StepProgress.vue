<script setup lang="ts">
import { Check } from 'lucide-vue-next'

defineProps<{ current: 1 | 2 | 3 }>()

const steps = [
  { number: 1, label: '填写内容' },
  { number: 2, label: '预览校验' },
  { number: 3, label: '完成注入' },
] as const
</script>

<template>
  <ol class="step-progress" :aria-label="`当前为第 ${current} 步`">
    <li
      v-for="(step, index) in steps"
      :key="step.number"
      class="step-item"
      :class="{ active: step.number === current, complete: step.number < current }"
    >
      <div class="step-topline">
        <span v-if="index" class="step-connector" />
        <span class="step-circle">
          <Check v-if="step.number < current" :size="19" stroke-width="2.7" />
          <template v-else>0{{ step.number }}</template>
        </span>
      </div>
      <span class="step-label">{{ step.label }}</span>
    </li>
  </ol>
</template>
