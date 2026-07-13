import { readonly, reactive, ref } from 'vue'
import { getCurrentUser, getKnowledgeOptions } from '@/api'
import type { CurrentUserResponse, KnowledgeOptions, Member } from '@/types'
import { markConnected } from '@/composables/useConnection'
import { classifySessionFailure, type SessionFailureKind } from '@/utils/recovery'

const identity = ref<CurrentUserResponse | null>(null)
const options = ref<KnowledgeOptions | null>(null)
const loading = ref(false)
const error = ref('')
const optionsError = ref('')
const failureKind = ref<SessionFailureKind>('none')
const blockedMember = ref<Member | null>(null)
let loadPromise: Promise<void> | null = null

async function loadSession(force = false): Promise<void> {
  if (loadPromise && !force) return loadPromise
  if (identity.value && !force) return
  if (!force && ['disabled', 'unauthenticated', 'forbidden'].includes(failureKind.value)) return

  if (force) {
    identity.value = null
    options.value = null
    blockedMember.value = null
  }

  loading.value = true
  error.value = ''
  optionsError.value = ''
  failureKind.value = 'none'
  loadPromise = getCurrentUser()
    .then(async (nextIdentity) => {
      identity.value = nextIdentity
      blockedMember.value = null
      failureKind.value = 'none'
      markConnected(true)
      if (nextIdentity.permissions.can_create_knowledge) {
        try {
          options.value = await getKnowledgeOptions()
        } catch (reason) {
          options.value = null
          optionsError.value = reason instanceof Error ? reason.message : '无法加载知识治理选项'
        }
      } else {
        options.value = null
      }
    })
    .catch((reason: unknown) => {
      identity.value = null
      options.value = null
      failureKind.value = classifySessionFailure(reason)
      if (failureKind.value !== 'disabled') blockedMember.value = null
      markConnected(failureKind.value !== 'network')
      error.value = reason instanceof Error ? reason.message : '无法加载当前身份'
    })
    .finally(() => {
      loading.value = false
      loadPromise = null
    })

  return loadPromise
}

function setBlockedSession(kind: Extract<SessionFailureKind, 'disabled' | 'forbidden' | 'unauthenticated'>, message: string, member?: Member) {
  identity.value = null
  options.value = null
  optionsError.value = ''
  failureKind.value = kind
  error.value = message
  blockedMember.value = member ? { ...member } : null
  markConnected(true)
}

export function useSession() {
  return reactive({
    identity: readonly(identity),
    options: readonly(options),
    optionsError: readonly(optionsError),
    loading: readonly(loading),
    error: readonly(error),
    failureKind: readonly(failureKind),
    blockedMember: readonly(blockedMember),
    loadSession,
  })
}

export {
  identity,
  options,
  optionsError as sessionOptionsError,
  loading as sessionLoading,
  error as sessionError,
  failureKind as sessionFailureKind,
  blockedMember as sessionBlockedMember,
  loadSession,
  setBlockedSession,
}
