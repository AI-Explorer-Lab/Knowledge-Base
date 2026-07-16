<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  BookOpen,
  ChevronLeft,
  Database,
  Crown,
  LibraryBig,
  Menu,
  PenLine,
  ShieldCheck,
  WifiOff,
} from 'lucide-vue-next'
import {
  identity,
  loadSession,
  sessionError,
  sessionFailureKind,
  sessionLoading,
} from '@/composables/useSession'
import ToastHost from '@/components/ToastHost.vue'
import { connected } from '@/composables/useConnection'

const route = useRoute()
const collapsed = ref(false)
const mobileOpen = ref(false)

const canCreate = computed(() => identity.value?.permissions.can_create_knowledge ?? false)
const canBrowse = computed(() => identity.value?.permissions.can_browse_knowledge ?? false)
const canManage = computed(() => identity.value?.permissions.can_manage_members ?? false)
const canSuperAdmin = computed(() => identity.value?.permissions.can_super_admin ?? false)
const injectionRouteNames = new Set(['knowledge-create', 'knowledge-preview', 'knowledge-completed'])
const injectionActive = computed(() => injectionRouteNames.has(String(route.name)))
const avatarText = computed(() => identity.value?.member.display_name.trim().slice(0, 1) || '用')
const breadcrumbParts = computed(() => String(route.meta.breadcrumb ?? '').split(' / '))
const showServiceFailure = computed(() =>
  !identity.value && ['network', 'server'].includes(sessionFailureKind.value),
)
const serviceFailureTitle = computed(() =>
  sessionFailureKind.value === 'network' ? '暂时无法连接服务' : '暂时无法加载当前身份',
)

function closeMobileNavigation() {
  mobileOpen.value = false
}
</script>

<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': collapsed, 'mobile-nav-open': mobileOpen }">
    <aside class="sidebar" aria-label="主导航">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true"><BookOpen :size="25" stroke-width="2.2" /></span>
        <span class="brand-name">团队知识库</span>
      </div>

      <nav class="sidebar-nav">
        <RouterLink
          v-if="canCreate"
          to="/knowledge/create"
          class="nav-item"
          :class="{ active: injectionActive }"
          title="知识注入"
          @click="closeMobileNavigation"
        >
          <PenLine :size="23" />
          <span>知识注入</span>
        </RouterLink>
        <RouterLink
          v-if="canSuperAdmin"
          to="/super-admin"
          class="nav-item"
          :class="{ active: route.name === 'super-admin' }"
          title="超级管理"
          @click="closeMobileNavigation"
        >
          <Crown :size="23" />
          <span>超级管理</span>
        </RouterLink>
        <RouterLink
          v-if="canBrowse"
          to="/knowledge/browse"
          class="nav-item"
          :class="{ active: route.name === 'knowledge-browse' }"
          title="知识浏览"
          @click="closeMobileNavigation"
        >
          <LibraryBig :size="23" />
          <span>知识浏览</span>
        </RouterLink>
        <RouterLink
          v-if="canManage"
          to="/permissions"
          class="nav-item"
          :class="{ active: route.path === '/permissions' }"
          title="权限管理"
          @click="closeMobileNavigation"
        >
          <ShieldCheck :size="23" />
          <span>权限管理</span>
        </RouterLink>
        <div v-if="!canCreate && !canBrowse && !canManage && !canSuperAdmin" class="nav-item nav-item-muted">
          <Database :size="22" />
          <span>只读访问</span>
        </div>
      </nav>

      <button class="collapse-button" type="button" @click="collapsed = !collapsed">
        <ChevronLeft :size="19" />
        <span>{{ collapsed ? '展开菜单' : '收起菜单' }}</span>
      </button>
    </aside>

    <button
      v-if="mobileOpen"
      type="button"
      class="mobile-scrim"
      aria-label="关闭导航"
      @click="mobileOpen = false"
    />

    <div class="app-stage">
      <header class="topbar">
        <div class="topbar-breadcrumb">
          <button class="mobile-menu" type="button" aria-label="打开导航" @click="mobileOpen = true">
            <Menu :size="23" />
          </button>
          <template v-for="(part, index) in breadcrumbParts" :key="part">
            <span :class="{ 'current-crumb': index === breadcrumbParts.length - 1 }">{{ part }}</span>
            <span v-if="index < breadcrumbParts.length - 1" class="breadcrumb-separator">/</span>
          </template>
        </div>

        <div v-if="identity" class="identity-area">
          <div class="service-status" :class="{ disconnected: !connected }">
            <span class="status-dot" />{{ connected ? '服务已连接' : '服务连接异常' }}
          </div>
          <div class="identity-divider" />
          <div class="avatar">{{ avatarText }}</div>
          <strong>{{ identity.member.display_name }}</strong>
          <span class="role-badge">{{ identity.member.role }}</span>
        </div>
      </header>

      <main class="app-content">
        <div v-if="sessionLoading && !identity" class="full-state" aria-live="polite">
          <span class="loading-spinner" />
          <strong>正在连接知识库服务…</strong>
        </div>
        <div v-else-if="showServiceFailure" class="full-state full-state-error">
          <WifiOff :size="38" />
          <h1>{{ serviceFailureTitle }}</h1>
          <p>{{ sessionError }}</p>
          <button class="button button-primary" type="button" @click="loadSession(true)">重新连接</button>
        </div>
        <RouterView v-else />
      </main>
    </div>

    <ToastHost />
  </div>
</template>
