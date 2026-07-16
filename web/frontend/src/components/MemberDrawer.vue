<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { ChevronDown, LockKeyhole, X } from 'lucide-vue-next'
import type { AssignableRole, Member, MemberStatus } from '@/types'

export interface MemberFormValue {
  id: string
  display_name: string
  role: AssignableRole
  status: MemberStatus
}

const props = defineProps<{
  open: boolean
  member: Member | null
  busy?: boolean
}>()

const emit = defineEmits<{
  close: []
  save: [value: MemberFormValue]
}>()

const form = reactive<MemberFormValue>({
  id: '',
  display_name: '',
  role: 'reader',
  status: 'active',
})
const errors = reactive({ id: '', display_name: '' })
const isCreate = computed(() => props.member === null)

watch(
  () => [props.open, props.member] as const,
  ([open, member]) => {
    if (!open) return
    Object.assign(form, member ?? { id: '', display_name: '', role: 'reader', status: 'active' })
    errors.id = ''
    errors.display_name = ''
  },
  { immediate: true },
)

function submit() {
  errors.id = /^[a-z0-9][a-z0-9._-]{1,63}$/.test(form.id)
    ? ''
    : '成员 ID 为 2–64 位，仅包含小写字母、数字、点、_ 或 -'
  errors.display_name = !form.display_name.trim()
    ? '请输入显示名称'
    : /[\r\n\0]/.test(form.display_name)
      ? '显示名称不能包含换行或控制字符'
      : ''
  if (errors.id || errors.display_name) return
  emit('save', {
    ...form,
    display_name: form.display_name.trim(),
    status: isCreate.value ? 'active' : form.status,
  })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="drawer-layer" @click.self="emit('close')">
        <aside class="member-drawer" role="dialog" aria-modal="true" :aria-label="isCreate ? '新增成员' : '编辑成员权限'">
          <header class="drawer-header">
            <h2>{{ isCreate ? '新增成员' : '编辑成员权限' }}</h2>
            <button type="button" aria-label="关闭" @click="emit('close')"><X :size="23" /></button>
          </header>

          <form class="drawer-form" @submit.prevent="submit">
            <div class="drawer-field">
              <label for="member-id">成员 ID</label>
              <div class="input-with-icon" :class="{ 'read-only-input': !isCreate }">
                <input
                  id="member-id"
                  v-model="form.id"
                  :readonly="!isCreate"
                  :class="{ invalid: errors.id }"
                  autocomplete="off"
                  placeholder="例如：lisi"
                />
                <LockKeyhole v-if="!isCreate" :size="17" />
              </div>
              <p v-if="errors.id" class="field-error">{{ errors.id }}</p>
              <p v-else-if="isCreate" class="field-help plain-help">创建后成员 ID 不可修改</p>
            </div>

            <div class="drawer-field">
              <label for="display-name">显示名称</label>
              <input id="display-name" v-model="form.display_name" :class="{ invalid: errors.display_name }" maxlength="40" />
              <p v-if="errors.display_name" class="field-error">{{ errors.display_name }}</p>
            </div>

            <fieldset class="drawer-field role-fieldset">
              <legend>角色</legend>
              <div class="segmented-control role-control">
                <button
                  v-for="role in (['reader', 'contributor', 'maintainer'] as AssignableRole[])"
                  :key="role"
                  type="button"
                  :class="{ selected: form.role === role, [`role-${role}`]: true }"
                  @click="form.role = role"
                >{{ role }}</button>
              </div>
            </fieldset>

            <div class="drawer-field">
              <label for="member-status">状态</label>
              <div v-if="isCreate" id="member-status" class="static-status-field" aria-label="状态：已启用">
                <span class="status-dot" />
                <span>已启用</span>
                <LockKeyhole :size="17" />
              </div>
              <div v-else class="select-shell status-select">
                <span class="status-dot" :class="{ disabled: form.status === 'disabled' }" />
                <select id="member-status" v-model="form.status">
                  <option value="active">已启用</option>
                  <option value="disabled">已停用</option>
                </select>
                <ChevronDown :size="18" />
              </div>
              <p v-if="isCreate" class="field-help plain-help">新成员创建后默认启用</p>
            </div>

            <div class="drawer-footer">
              <div class="drawer-actions">
                <button class="button button-secondary" type="button" :disabled="busy" @click="emit('close')">取消</button>
                <button class="button button-primary" type="submit" :disabled="busy">
                  <span v-if="busy" class="button-spinner" />
                  {{ busy ? '保存中…' : isCreate ? '新增成员' : '保存修改' }}
                </button>
              </div>

              <div class="warning-callout">
                <LockKeyhole :size="24" />
                <span>不能停用或降级最后一名 Maintainer</span>
              </div>
            </div>
          </form>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>
