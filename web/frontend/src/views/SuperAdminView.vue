<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  Archive,
  BookOpenCheck,
  FileClock,
  FolderCog,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  UsersRound,
} from 'lucide-vue-next'
import AdminChangePreview from '@/components/AdminChangePreview.vue'
import AuditLogPanel from '@/components/AuditLogPanel.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import MemberDrawer, { type MemberFormValue } from '@/components/MemberDrawer.vue'
import SuperAdminKnowledgeDrawer from '@/components/SuperAdminKnowledgeDrawer.vue'
import {
  commitSuperAdminKnowledge,
  createBusinessDomain,
  createMember,
  executeSuperAdminAction,
  getAuditRecords,
  getMembers,
  getSuperAdminKnowledge,
  listSuperAdminKnowledge,
  previewSuperAdminKnowledge,
  updateBusinessDomain,
  updateMember,
} from '@/api'
import { options as sessionOptions, reloadKnowledgeOptions } from '@/composables/useSession'
import { pushToast } from '@/composables/useToast'
import type {
  AuditRecord,
  BusinessDomain,
  Member,
  SuperAdminAction,
  SuperAdminKnowledge,
  SuperAdminKnowledgeInput,
  SuperAdminKnowledgeListItem,
  SuperAdminPreviewResponse,
} from '@/types'

type Tab = 'knowledge' | 'members' | 'domains' | 'audit'
const tab = ref<Tab>('knowledge')
const tabs = [
  { value: 'knowledge' as const, label: '知识管理', icon: BookOpenCheck },
  { value: 'members' as const, label: '成员管理', icon: UsersRound },
  { value: 'domains' as const, label: '业务领域', icon: FolderCog },
  { value: 'audit' as const, label: '审计记录', icon: FileClock },
]

const knowledgeState = ref<'active' | 'archived' | 'all'>('active')
const knowledgeQuery = ref('')
const knowledgeLayer = ref<'' | SuperAdminKnowledgeListItem['layer']>('')
const knowledgeScope = ref<'' | 'personal' | 'team'>('')
const knowledgeMaturity = ref<'' | SuperAdminKnowledgeListItem['maturity']>('')
const knowledgeItems = ref<SuperAdminKnowledgeListItem[]>([])
const knowledgeCounts = reactive({ active: 0, archived: 0 })
const knowledgeLoading = ref(false)
const selectedKnowledge = ref<SuperAdminKnowledge | null>(null)
const editorOpen = ref(false)
const previewOpen = ref(false)
const previewBusy = ref(false)
const previewPayload = ref<SuperAdminKnowledgeInput | null>(null)
const updatePreview = ref<SuperAdminPreviewResponse | null>(null)
const actionForm = reactive({
  action: 'archive' as SuperAdminAction,
  reason: '',
  target_layer: 'layer1' as 'layer1' | 'layer2',
  domain: '',
  owner_confirmed_by: '',
  confirm_id: '',
})
const actionBusy = ref(false)

const members = ref<Member[]>([])
const membersLoading = ref(false)
const memberDrawerOpen = ref(false)
const selectedMember = ref<Member | null>(null)
const memberSaving = ref(false)
const memberConfirmOpen = ref(false)
const pendingMemberForm = ref<MemberFormValue | null>(null)

const domains = computed(() => sessionOptions.value?.business_domains ?? [])
const domainDrafts = reactive<Record<string, { name: string; description: string }>>({})
const newDomain = reactive({ id: '', name: '', description: '' })
const domainSaving = ref('')

const auditItems = ref<AuditRecord[]>([])
const auditTotal = ref(0)
const auditQuery = ref('')
const auditLoading = ref(false)

const actionOptions = computed(() => {
  if (!selectedKnowledge.value) return []
  return [
    ...(selectedKnowledge.value.archived
      ? [{ value: 'restore' as const, label: '恢复知识' }]
      : [{ value: 'archive' as const, label: '归档知识' }]),
    { value: 'approve_proven' as const, label: '审批为 proven' },
    { value: 'propose_promotion' as const, label: '发起层级提升' },
    { value: 'approve_promotion' as const, label: '批准层级提升' },
    { value: 'rollback_layer' as const, label: '退回 Layer 3' },
    { value: 'mark_conflict' as const, label: '标记冲突' },
    { value: 'resolve_conflict' as const, label: '解决冲突' },
  ]
})

onMounted(async () => {
  await Promise.all([loadKnowledge(), loadMembers(), loadDomains(), loadAudit()])
})
watch(knowledgeState, loadKnowledge)
watch(
  domains,
  (items) => {
    for (const domain of items) {
      domainDrafts[domain.id] ??= { name: domain.name, description: domain.description }
    }
  },
  { immediate: true },
)
watch(selectedKnowledge, (knowledge) => {
  actionForm.action = knowledge?.archived ? 'restore' : 'archive'
  actionForm.reason = ''
  actionForm.confirm_id = ''
  actionForm.owner_confirmed_by = ''
})

async function loadKnowledge() {
  knowledgeLoading.value = true
  try {
    const response = await listSuperAdminKnowledge(
      knowledgeState.value,
      knowledgeQuery.value,
      {
        layer: knowledgeLayer.value || undefined,
        scope: knowledgeScope.value || undefined,
        maturity: knowledgeMaturity.value || undefined,
      },
    )
    knowledgeItems.value = response.items
    Object.assign(knowledgeCounts, response.counts)
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '超级管理知识列表加载失败', 'error')
  } finally {
    knowledgeLoading.value = false
  }
}

async function selectKnowledge(item: SuperAdminKnowledgeListItem) {
  try {
    selectedKnowledge.value = (await getSuperAdminKnowledge(item.id)).knowledge
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '知识详情加载失败', 'error')
  }
}

function openEditor() {
  if (!selectedKnowledge.value || selectedKnowledge.value.archived) return
  editorOpen.value = true
}

async function previewChange(payload: SuperAdminKnowledgeInput) {
  if (!selectedKnowledge.value) return
  previewBusy.value = true
  try {
    previewPayload.value = payload
    updatePreview.value = await previewSuperAdminKnowledge(selectedKnowledge.value.id, payload)
    editorOpen.value = false
    previewOpen.value = true
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '修改预览失败', 'error')
  } finally {
    previewBusy.value = false
  }
}

async function commitChange() {
  if (!selectedKnowledge.value || !previewPayload.value || !updatePreview.value) return
  previewBusy.value = true
  try {
    const result = await commitSuperAdminKnowledge(
      selectedKnowledge.value.id,
      previewPayload.value,
      updatePreview.value.preview_token,
    )
    selectedKnowledge.value = result.knowledge
    previewOpen.value = false
    updatePreview.value = null
    previewPayload.value = null
    await Promise.all([loadKnowledge(), loadAudit()])
    pushToast(`知识 ${result.knowledge.id} 已更新到 revision ${result.knowledge.revision}`, 'success')
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '知识修改提交失败', 'error')
  } finally {
    previewBusy.value = false
  }
}

async function runGovernanceAction() {
  const knowledge = selectedKnowledge.value
  if (!knowledge) return
  if (actionForm.reason.trim().length < 3) {
    pushToast('请填写至少 3 个字的操作原因', 'error')
    return
  }
  if (actionForm.confirm_id !== knowledge.id) {
    pushToast('请输入目标知识 ID 进行确认', 'error')
    return
  }
  actionBusy.value = true
  try {
    const payload: {
      action: SuperAdminAction
      reason: string
      target_layer?: 'layer1' | 'layer2'
      domain?: string
      owner_confirmed_by?: string
    } = { action: actionForm.action, reason: actionForm.reason.trim() }
    if (actionForm.action === 'propose_promotion') {
      payload.target_layer = actionForm.target_layer
      if (actionForm.target_layer === 'layer2') payload.domain = actionForm.domain
    }
    if (actionForm.owner_confirmed_by.trim()) payload.owner_confirmed_by = actionForm.owner_confirmed_by.trim()
    const result = await executeSuperAdminAction(knowledge.id, payload)
    selectedKnowledge.value = result.knowledge
    await Promise.all([loadKnowledge(), loadAudit()])
    pushToast(`治理动作 ${result.action} 已完成`, 'success')
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '治理动作执行失败', 'error')
  } finally {
    actionBusy.value = false
  }
}

async function loadMembers() {
  membersLoading.value = true
  try {
    members.value = (await getMembers()).members
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '成员列表加载失败', 'error')
  } finally {
    membersLoading.value = false
  }
}

function openMember(member: Member | null) {
  if (member?.role === 'super_admin') {
    pushToast('超级管理员只能通过系统配置修改', 'error')
    return
  }
  selectedMember.value = member
  memberDrawerOpen.value = true
}

async function requestMemberSave(form: MemberFormValue) {
  if (!selectedMember.value) {
    memberSaving.value = true
    try {
      await createMember({ id: form.id, display_name: form.display_name, role: form.role })
      memberDrawerOpen.value = false
      await loadMembers()
      pushToast('成员已新增', 'success')
    } catch (reason) {
      pushToast(reason instanceof Error ? reason.message : '新增成员失败', 'error')
    } finally {
      memberSaving.value = false
    }
    return
  }
  pendingMemberForm.value = form
  memberConfirmOpen.value = true
}

async function confirmMemberSave() {
  if (!selectedMember.value || !pendingMemberForm.value) return
  memberSaving.value = true
  try {
    const form = pendingMemberForm.value
    await updateMember(selectedMember.value.id, {
      display_name: form.display_name,
      role: form.role,
      status: form.status,
    })
    memberConfirmOpen.value = false
    memberDrawerOpen.value = false
    await Promise.all([loadMembers(), loadAudit()])
    pushToast('成员信息已更新', 'success')
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '成员修改失败', 'error')
  } finally {
    memberSaving.value = false
  }
}

async function loadDomains() {
  try {
    const next = await reloadKnowledgeOptions()
    for (const domain of next.business_domains) {
      domainDrafts[domain.id] = { name: domain.name, description: domain.description }
    }
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '业务领域加载失败', 'error')
  }
}

async function addDomain() {
  if (!newDomain.id.trim() || !newDomain.name.trim()) {
    pushToast('请填写领域 ID 和名称', 'error')
    return
  }
  domainSaving.value = 'new'
  try {
    await createBusinessDomain({ ...newDomain })
    Object.assign(newDomain, { id: '', name: '', description: '' })
    await Promise.all([loadDomains(), loadAudit()])
    pushToast('业务领域已新增', 'success')
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '新增业务领域失败', 'error')
  } finally {
    domainSaving.value = ''
  }
}

async function saveDomain(domain: BusinessDomain, toggleStatus = false) {
  domainSaving.value = domain.id
  try {
    const draft = domainDrafts[domain.id] ?? { name: domain.name, description: domain.description }
    await updateBusinessDomain(domain.id, {
      name: draft.name.trim(),
      description: draft.description.trim(),
      status: toggleStatus ? (domain.status === 'active' ? 'disabled' : 'active') : domain.status,
    })
    await Promise.all([loadDomains(), loadAudit()])
    pushToast(`业务领域 ${domain.name} 已更新`, 'success')
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '业务领域修改失败', 'error')
  } finally {
    domainSaving.value = ''
  }
}

async function loadAudit() {
  auditLoading.value = true
  try {
    const response = await getAuditRecords(auditQuery.value)
    auditItems.value = response.items
    auditTotal.value = response.total
  } catch (reason) {
    pushToast(reason instanceof Error ? reason.message : '审计记录加载失败', 'error')
  } finally {
    auditLoading.value = false
  }
}
</script>

<template>
  <div class="super-admin-page">
    <div class="super-admin-heading">
      <div><span><ShieldCheck :size="17" />受控最高权限</span><h1>超级管理</h1><p>修正知识、执行治理动作并查看不可改写的审计记录</p></div>
      <div class="super-admin-summary"><strong>{{ knowledgeCounts.active }}</strong><span>有效知识</span><strong>{{ knowledgeCounts.archived }}</strong><span>归档知识</span></div>
    </div>

    <nav class="admin-tabs" aria-label="超级管理模块">
      <button v-for="item in tabs" :key="item.value" type="button" :class="{ active: tab === item.value }" @click="tab = item.value"><component :is="item.icon" :size="19" />{{ item.label }}</button>
    </nav>

    <section v-if="tab === 'knowledge'" class="admin-panel">
      <header class="admin-panel-header"><div><h2>知识管理</h2><p>所有修改都需要预览、确认和审计</p></div><div class="admin-toolbar"><select v-model="knowledgeState"><option value="active">有效知识</option><option value="archived">归档知识</option><option value="all">全部知识</option></select><select v-model="knowledgeLayer"><option value="">全部 Layer</option><option value="layer0p">Layer 0-P</option><option value="layer0t">Layer 0-T</option><option value="layer1">Layer 1</option><option value="layer2">Layer 2</option><option value="layer3">Layer 3</option></select><select v-model="knowledgeScope"><option value="">全部范围</option><option value="personal">个人</option><option value="team">团队</option></select><select v-model="knowledgeMaturity"><option value="">全部成熟度</option><option value="draft">draft</option><option value="verified">verified</option><option value="proven">proven</option></select><label><Search :size="17" /><input v-model="knowledgeQuery" placeholder="搜索标题、ID 或标签" @keyup.enter="loadKnowledge" /></label><button type="button" @click="loadKnowledge"><RefreshCw :size="18" /></button></div></header>
      <div v-if="knowledgeLoading" class="table-loading"><span class="loading-spinner" />正在读取知识…</div>
      <div v-else class="admin-knowledge-layout">
        <div class="admin-knowledge-table-wrap">
          <table class="admin-table"><thead><tr><th>知识</th><th>范围</th><th>版本</th><th>状态</th><th /></tr></thead><tbody><tr v-for="item in knowledgeItems" :key="item.id" :class="{ selected: selectedKnowledge?.id === item.id }"><td><strong>{{ item.title }}</strong><code>{{ item.id }}</code></td><td>{{ item.scope }} · {{ item.layer }}</td><td>revision {{ item.revision }}</td><td><span class="admin-status" :class="{ archived: item.archived }">{{ item.archived ? '已归档' : item.maturity }}</span></td><td><button class="text-button" type="button" @click="selectKnowledge(item)">管理</button></td></tr></tbody></table>
        </div>
        <aside v-if="selectedKnowledge" class="admin-knowledge-detail">
          <div><span class="eyebrow">{{ selectedKnowledge.id }}</span><h3>{{ selectedKnowledge.title }}</h3><p>{{ selectedKnowledge.relative_path }}</p></div>
          <dl><div><dt>版本</dt><dd>{{ selectedKnowledge.revision }}</dd></div><div><dt>成熟度</dt><dd>{{ selectedKnowledge.maturity }}</dd></div><div><dt>冲突</dt><dd>{{ selectedKnowledge.conflict_status }}</dd></div></dl>
          <button class="button button-primary" type="button" :disabled="selectedKnowledge.archived" @click="openEditor"><Pencil :size="17" />修改知识</button>
          <div class="admin-action-box"><h4>治理动作</h4><select v-model="actionForm.action"><option v-for="item in actionOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select><template v-if="actionForm.action === 'propose_promotion'"><select v-model="actionForm.target_layer"><option value="layer1">Layer 1</option><option value="layer2">Layer 2</option></select><select v-if="actionForm.target_layer === 'layer2'" v-model="actionForm.domain"><option value="">选择业务领域</option><option v-for="domain in domains.filter((item) => item.status === 'active')" :key="domain.id" :value="domain.id">{{ domain.name }}</option></select></template><input v-model="actionForm.owner_confirmed_by" placeholder="所有者确认 ID（需要时）" /><textarea v-model="actionForm.reason" rows="3" placeholder="操作原因" /><input v-model="actionForm.confirm_id" :placeholder="`输入 ${selectedKnowledge.id} 确认`" /><button class="button button-secondary" type="button" :disabled="actionBusy" @click="runGovernanceAction">{{ actionBusy ? '执行中…' : '执行治理动作' }}</button></div>
        </aside>
      </div>
    </section>

    <section v-else-if="tab === 'members'" class="admin-panel"><header class="admin-panel-header"><div><h2>成员管理</h2><p>超级管理员账号只能通过系统配置修改</p></div><button class="button button-primary" type="button" @click="openMember(null)"><Plus :size="18" />新增成员</button></header><div v-if="membersLoading" class="table-loading">正在加载成员…</div><table v-else class="admin-table"><thead><tr><th>成员</th><th>ID</th><th>角色</th><th>状态</th><th /></tr></thead><tbody><tr v-for="member in members" :key="member.id"><td>{{ member.display_name }}</td><td><code>{{ member.id }}</code></td><td>{{ member.role }}</td><td>{{ member.status === 'active' ? '已启用' : '已停用' }}</td><td><button class="text-button" type="button" :disabled="member.role === 'super_admin'" @click="openMember(member)">{{ member.role === 'super_admin' ? '系统配置' : '修改' }}</button></td></tr></tbody></table></section>

    <section v-else-if="tab === 'domains'" class="admin-panel"><header class="admin-panel-header"><div><h2>业务领域</h2><p>停用后既有知识仍可浏览，但不能再写入新知识</p></div></header><div class="admin-new-domain"><input v-model="newDomain.id" placeholder="领域 ID" /><input v-model="newDomain.name" placeholder="领域名称" /><input v-model="newDomain.description" placeholder="领域说明" /><button class="button button-primary" type="button" :disabled="domainSaving === 'new'" @click="addDomain"><Plus :size="17" />新增</button></div><div class="domain-admin-list"><article v-for="domain in domains" :key="domain.id"><div><code>{{ domain.id }}</code><span class="admin-status" :class="{ archived: domain.status === 'disabled' }">{{ domain.status === 'active' ? '启用' : '停用' }}</span></div><input v-model="domainDrafts[domain.id].name" /><textarea v-model="domainDrafts[domain.id].description" rows="2" /><footer><button class="button button-secondary" type="button" :disabled="domainSaving === domain.id" @click="saveDomain(domain)">保存说明</button><button class="text-button" type="button" :disabled="domainSaving === domain.id" @click="saveDomain(domain, true)">{{ domain.status === 'active' ? '停用领域' : '重新启用' }}</button></footer></article></div></section>

    <AuditLogPanel v-else :items="auditItems" :total="auditTotal" :loading="auditLoading" :query="auditQuery" @update:query="auditQuery = $event" @refresh="loadAudit" />

    <SuperAdminKnowledgeDrawer :open="editorOpen" :knowledge="selectedKnowledge" :options="sessionOptions" :busy="previewBusy" @close="editorOpen = false" @preview="previewChange" />
    <AdminChangePreview :open="previewOpen" :preview="updatePreview" :busy="previewBusy" @cancel="previewOpen = false; editorOpen = true" @confirm="commitChange" />
    <MemberDrawer :open="memberDrawerOpen" :member="selectedMember" :busy="memberSaving" @close="memberDrawerOpen = false" @save="requestMemberSave" />
    <ConfirmDialog :open="memberConfirmOpen" title="确认成员变更" description="确认保存该成员的角色和状态吗？此操作会写入审计日志。" :busy="memberSaving" @cancel="memberConfirmOpen = false" @confirm="confirmMemberSave" />
  </div>
</template>
