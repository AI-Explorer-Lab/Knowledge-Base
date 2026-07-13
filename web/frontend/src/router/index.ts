import { createRouter, createWebHistory } from 'vue-router'
import { identity, loadSession, sessionFailureKind } from '@/composables/useSession'
import { routeRequiresForbidden } from '@/utils/recovery'

declare module 'vue-router' {
  interface RouteMeta {
    breadcrumb?: string
    allowedRoles?: Array<'reader' | 'contributor' | 'maintainer'>
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      redirect: '/knowledge/create',
    },
    {
      path: '/knowledge/create',
      name: 'knowledge-create',
      component: () => import('@/views/KnowledgeCreateView.vue'),
      meta: {
        breadcrumb: '知识治理 / 人工注入',
        allowedRoles: ['contributor', 'maintainer'],
      },
    },
    {
      path: '/knowledge/preview',
      name: 'knowledge-preview',
      component: () => import('@/views/KnowledgePreviewView.vue'),
      meta: {
        breadcrumb: '知识治理 / 预览校验',
        allowedRoles: ['contributor', 'maintainer'],
      },
    },
    {
      path: '/knowledge/completed',
      name: 'knowledge-completed',
      component: () => import('@/views/KnowledgeCompleteView.vue'),
      meta: {
        breadcrumb: '知识治理 / 完成注入',
        allowedRoles: ['contributor', 'maintainer'],
      },
    },
    {
      path: '/permissions',
      name: 'permissions',
      component: () => import('@/views/PermissionView.vue'),
      meta: {
        breadcrumb: '团队设置 / 权限管理',
        allowedRoles: ['maintainer'],
      },
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('@/views/ForbiddenView.vue'),
      meta: { breadcrumb: '访问受限' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/knowledge/create',
    },
  ],
})

router.beforeEach(async (to) => {
  await loadSession()
  const allowed = to.meta.allowedRoles
  if (routeRequiresForbidden({
    routeName: to.name,
    allowedRoles: allowed,
    identity: identity.value,
    failureKind: sessionFailureKind.value,
  })) {
    return { name: 'forbidden', query: { from: to.fullPath } }
  }
  if (to.name === 'knowledge-preview') {
    const { previewIsCurrent } = (await import('@/composables/useKnowledgeFlow')).useKnowledgeFlow()
    if (!previewIsCurrent.value) return { name: 'knowledge-create' }
  }
  if (to.name === 'knowledge-completed') {
    const { result } = (await import('@/composables/useKnowledgeFlow')).useKnowledgeFlow()
    if (!result.value) return { name: 'knowledge-create' }
  }
  return true
})

router.afterEach((to) => {
  document.title = `${String(to.meta.breadcrumb ?? '团队知识库').split(' / ').at(-1)} · 团队知识库`
})

export default router
