<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldX } from 'lucide-vue-next'
import {
  identity,
  loadSession,
  sessionBlockedMember,
  sessionFailureKind,
} from '@/composables/useSession'
import { defaultRouteForIdentity } from '@/utils/recovery'

const router = useRouter()
const displayMember = computed(() => identity.value?.member ?? sessionBlockedMember.value)
const title = computed(() => {
  if (sessionFailureKind.value === 'disabled' || displayMember.value?.status === 'disabled') return '当前账号已停用'
  if (sessionFailureKind.value === 'unauthenticated') return '身份验证已失效'
  return '当前角色无权访问'
})
const explanation = computed(() => {
  if (sessionFailureKind.value === 'disabled' || displayMember.value?.status === 'disabled') return '当前成员已停用，无法继续操作知识库。请联系 Maintainer 恢复账号。'
  if (sessionFailureKind.value === 'unauthenticated') return '当前登录状态已失效，请完成身份验证后重新检查权限。'
  if (sessionFailureKind.value === 'forbidden' && !identity.value) return '当前账号没有访问此功能的权限。'
  if (identity.value?.member.role === 'reader') return 'Reader 可以查看自己的身份与权限说明，但不能人工注入知识或管理成员权限。'
  return '当前身份没有进入此页面的权限。'
})

async function retryAccess() {
  await loadSession(true)
  const target = defaultRouteForIdentity(identity.value)
  if (target !== '/forbidden') await router.replace(target)
}
</script>

<template>
  <section class="forbidden-card">
    <span><ShieldX :size="43" /></span>
    <h1>{{ title }}</h1>
    <p>{{ explanation }}</p>
    <div class="identity-summary" v-if="displayMember">
      <strong>{{ displayMember.display_name }}</strong>
      <span class="role-badge">{{ displayMember.role }}</span>
      <span>{{ displayMember.status === 'active' ? '已启用' : '已停用' }}</span>
    </div>
    <button class="button button-primary" type="button" @click="retryAccess">重新检查权限</button>
  </section>
</template>
