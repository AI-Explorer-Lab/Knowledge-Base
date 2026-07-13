<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { BriefcaseBusiness, X } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  open: boolean
  busy?: boolean
  requestError?: string
  fieldErrors?: Partial<Record<'name' | 'id' | 'description', string>>
}>(), {
  busy: false,
  requestError: '',
  fieldErrors: () => ({}),
})

const emit = defineEmits<{
  cancel: []
  save: [payload: { id: string; name: string; description: string }]
}>()

const name = ref('')
const id = ref('')
const description = ref('')
const localErrors = ref<Partial<Record<'name' | 'id' | 'description', string>>>({})
const nameInput = ref<HTMLInputElement | null>(null)

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    name.value = ''
    id.value = ''
    description.value = ''
    localErrors.value = {}
    await nextTick()
    nameInput.value?.focus()
  },
)

function validate() {
  const errors: Partial<Record<'name' | 'id' | 'description', string>> = {}
  if (!name.value.trim()) errors.name = '请填写业务领域名称'
  if (!id.value.trim()) {
    errors.id = '请填写领域标识'
  } else if (!/^[a-z0-9][a-z0-9-]{0,47}$/.test(id.value.trim())) {
    errors.id = '仅支持小写字母、数字和连字符，且必须以字母或数字开头'
  } else if (id.value.trim() === 'archive') {
    errors.id = 'archive 是保留标识，请使用其他名称'
  }
  if (description.value.trim().length > 240) errors.description = '说明不能超过 240 个字符'
  localErrors.value = errors
  return Object.keys(errors).length === 0
}

function save() {
  if (!validate()) return
  emit('save', {
    id: id.value.trim(),
    name: name.value.trim(),
    description: description.value.trim(),
  })
}

function errorFor(field: 'name' | 'id' | 'description') {
  return props.fieldErrors[field] || localErrors.value[field]
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-backdrop" @click.self="!busy && emit('cancel')">
        <section class="business-domain-dialog" role="dialog" aria-modal="true" aria-labelledby="business-domain-title">
          <button class="dialog-close" type="button" aria-label="关闭" :disabled="busy" @click="emit('cancel')"><X :size="20" /></button>
          <header>
            <span><BriefcaseBusiness :size="24" /></span>
            <div>
              <h2 id="business-domain-title">新增业务领域</h2>
              <p>创建后将作为 Layer 2 知识的受控存储范围。</p>
            </div>
          </header>

          <div v-if="requestError" class="dialog-request-error" role="alert">{{ requestError }}</div>

          <form @submit.prevent="save">
            <label for="business-domain-name">业务领域名称 <em>*</em></label>
            <input
              id="business-domain-name"
              ref="nameInput"
              v-model="name"
              :class="{ invalid: errorFor('name') }"
              maxlength="80"
              placeholder="例如：订单"
              :disabled="busy"
            />
            <p v-if="errorFor('name')" class="field-error">{{ errorFor('name') }}</p>

            <label for="business-domain-id">领域标识 <em>*</em></label>
            <input
              id="business-domain-id"
              v-model="id"
              :class="{ invalid: errorFor('id') }"
              maxlength="48"
              placeholder="例如：order"
              autocomplete="off"
              :disabled="busy"
            />
            <p v-if="errorFor('id')" class="field-error">{{ errorFor('id') }}</p>
            <p class="dialog-field-help">用于生成安全路径：biz-wiki/<strong>{{ id.trim() || 'domain-id' }}</strong>/</p>

            <label for="business-domain-description">领域说明 <span>选填</span></label>
            <textarea
              id="business-domain-description"
              v-model="description"
              :class="{ invalid: errorFor('description') }"
              maxlength="240"
              placeholder="简要说明该领域涵盖的业务边界"
              :disabled="busy"
            />
            <div class="dialog-field-meta">
              <p v-if="errorFor('description')" class="field-error">{{ errorFor('description') }}</p>
              <span>{{ description.length }}/240</span>
            </div>

            <div class="dialog-actions">
              <button class="button button-secondary" type="button" :disabled="busy" @click="emit('cancel')">取消</button>
              <button class="button button-primary" type="submit" :disabled="busy">
                <span v-if="busy" class="button-spinner" />
                {{ busy ? '正在创建…' : '创建并选中' }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>
