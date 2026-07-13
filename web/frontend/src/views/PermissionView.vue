<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CheckCircle2, Info, Plus, ShieldCheck, UsersRound } from 'lucide-vue-next'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import MemberDrawer, { type MemberFormValue } from '@/components/MemberDrawer.vue'
import { createMember, getMembers, updateMember } from '@/api'
import { identity, loadSession, setBlockedSession } from '@/composables/useSession'
import { pushToast } from '@/composables/useToast'
import type { Member } from '@/types'
import { defaultRouteForIdentity } from '@/utils/recovery'

const router = useRouter()
const members = ref<Member[]>([])
const loading = ref(true)
const loadError = ref('')
const drawerOpen = ref(false)
const selectedMember = ref<Member | null>(null)
const saving = ref(false)
const confirmOpen = ref(false)
const pendingForm = ref<MemberFormValue | null>(null)

const activeCount = computed(() => members.value.filter((member) => member.status === 'active').length)
const maintainerCount = computed(() => members.value.filter(
  (member) => member.status === 'active' && member.role === 'maintainer',
).length)

const stats = computed(() => [
  { label: '团队成员', value: members.value.length, icon: UsersRound, tone: 'blue' },
  { label: 'Maintainer', value: maintainerCount.value, icon: ShieldCheck, tone: 'violet' },
  { label: '已启用', value: activeCount.value, icon: CheckCircle2, tone: 'green' },
])

const roleLabels = {
  reader: 'reader',
  contributor: 'contributor',
  maintainer: 'maintainer',
}

onMounted(loadMembers)

async function loadMembers() {
  loading.value = true
  loadError.value = ''
  try {
    members.value = (await getMembers()).members
  } catch (reason) {
    loadError.value = reason instanceof Error ? reason.message : '成员列表加载失败'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  selectedMember.value = null
  drawerOpen.value = true
}

function openEdit(member: Member) {
  selectedMember.value = member
  drawerOpen.value = true
}

function requestSave(form: MemberFormValue) {
  if (!selectedMember.value) {
    void saveCreate(form)
    return
  }
  pendingForm.value = form
  confirmOpen.value = true
}

async function saveCreate(form: MemberFormValue) {
  saving.value = true
  try {
    const response = await createMember({ id: form.id, display_name: form.display_name, role: form.role })
    members.value.push(response.member)
    drawerOpen.value = false
    pushToast(`成员 ${response.member.display_name} 已新增`, 'success')
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '新增成员失败', 'error')
  } finally {
    saving.value = false
  }
}

async function confirmSave() {
  const form = pendingForm.value
  const original = selectedMember.value
  if (!form || !original) return
  saving.value = true
  try {
    const response = await updateMember(original.id, {
      display_name: form.display_name,
      role: form.role,
      status: form.status,
    })
    const index = members.value.findIndex((member) => member.id === response.member.id)
    if (index >= 0) members.value.splice(index, 1, response.member)
    confirmOpen.value = false
    drawerOpen.value = false
    pendingForm.value = null
    pushToast(`成员 ${response.member.display_name} 的权限已更新`, 'success')

    if (response.member.id === identity.value?.member.id) {
      if (response.member.status === 'disabled') {
        setBlockedSession('disabled', '当前账号已停用，无法继续操作知识库。', response.member)
        await router.replace('/forbidden')
        return
      }
      await loadSession(true)
      await router.replace(defaultRouteForIdentity(identity.value))
    }
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '成员权限修改失败', 'error')
  } finally {
    saving.value = false
  }
}

function requestDisable(member: Member) {
  selectedMember.value = member
  pendingForm.value = { ...member, status: 'disabled' }
  confirmOpen.value = true
}

function avatarColor(index: number) {
  return ['avatar-blue', 'avatar-teal', 'avatar-violet'][index % 3]
}
</script>

<template>
  <div class="permission-page">
    <div class="permission-heading">
      <div>
        <h1>权限管理</h1>
        <p>管理团队成员的知识库角色与启用状态</p>
      </div>
      <button class="button button-primary add-member-button" type="button" @click="openCreate"><Plus :size="21" />新增成员</button>
    </div>

    <div v-if="loadError" class="inline-alert error-alert"><Info :size="19" />{{ loadError }}</div>

    <div class="stats-grid">
      <section v-for="stat in stats" :key="stat.label" class="stat-card">
        <span class="stat-icon" :class="stat.tone"><component :is="stat.icon" :size="30" /></span>
        <div><p>{{ stat.label }}</p><strong>{{ loading ? '—' : stat.value }}</strong></div>
      </section>
    </div>

    <section class="member-panel">
      <header>
        <h2>成员与角色</h2>
        <p>权限由成员角色、知识范围和所有者共同决定</p>
      </header>

      <div v-if="loading" class="table-loading"><span class="loading-spinner" />正在加载成员…</div>
      <div v-else class="member-table-wrap">
        <table class="member-table">
          <thead><tr><th>成员</th><th>成员 ID</th><th>角色</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="(member, index) in members" :key="member.id" :class="{ selected: drawerOpen && selectedMember?.id === member.id }">
              <td>
                <span class="member-avatar" :class="avatarColor(index)">{{ member.display_name.slice(0, 1) }}</span>
                <span class="member-name">
                  {{ member.display_name }}
                  <small v-if="member.id === identity?.member.id">当前用户</small>
                </span>
              </td>
              <td>{{ member.id }}</td>
              <td><span class="role-pill" :class="`role-${member.role}`">{{ roleLabels[member.role] }}</span></td>
              <td><span class="member-status"><i :class="{ disabled: member.status === 'disabled' }" />{{ member.status === 'active' ? '已启用' : '已停用' }}</span></td>
              <td class="member-actions">
                <button class="text-button" type="button" @click="openEdit(member)">修改角色</button>
                <span v-if="member.status === 'active' && member.id !== identity?.member.id" class="action-divider" />
                <button
                  v-if="member.status === 'active' && member.id !== identity?.member.id"
                  class="text-button danger-text"
                  type="button"
                  @click="requestDisable(member)"
                >停用</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="audit-note"><Info :size="18" />角色变更将记录到审计日志</p>
    </section>

    <MemberDrawer
      :open="drawerOpen"
      :member="selectedMember"
      :busy="saving"
      @close="drawerOpen = false"
      @save="requestSave"
    />
    <ConfirmDialog
      :open="confirmOpen"
      title="确认权限变更"
      :description="pendingForm ? `确认将 ${pendingForm.display_name} 的角色设为 ${pendingForm.role}，状态设为${pendingForm.status === 'active' ? '已启用' : '已停用'}吗？该操作将写入审计日志。` : ''"
      :danger="pendingForm?.status === 'disabled'"
      :busy="saving"
      @cancel="confirmOpen = false"
      @confirm="confirmSave"
    />
  </div>
</template>
