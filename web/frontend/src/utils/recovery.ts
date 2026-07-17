import { ApiError, type CurrentUserResponse } from '@/types'

export type SessionFailureKind = 'none' | 'network' | 'unauthenticated' | 'forbidden' | 'disabled' | 'server'

const RETRYABLE_PREVIEW_CODES = new Set([
  'preview_submission_in_progress',
])

export function shouldResetPreviewForError(code: string): boolean {
  const normalized = code.trim().toLowerCase()
  if (!normalized || RETRYABLE_PREVIEW_CODES.has(normalized)) return false
  return normalized.startsWith('preview_')
    || normalized === 'invalid_preview_token'
    || normalized === 'invalid_preview_state'
}

export function classifySessionFailure(reason: unknown): SessionFailureKind {
  if (!(reason instanceof ApiError)) return 'server'
  const code = reason.code.trim().toLowerCase()
  if (reason.status === 0 || code === 'network_error') return 'network'
  if (code === 'member_disabled') return 'disabled'
  if (reason.status === 401) return 'unauthenticated'
  if (reason.status === 403) return 'forbidden'
  return 'server'
}

export function defaultRouteForIdentity(identity: CurrentUserResponse | null): string {
  if (!identity || identity.member.status !== 'active') return '/forbidden'
  if (identity.permissions.can_super_admin) return '/super-admin'
  if (identity.permissions.can_create_knowledge) return '/knowledge/create'
  if (identity.permissions.can_manage_members) return '/permissions'
  if (identity.permissions.can_browse_knowledge) return '/knowledge/browse'
  return '/forbidden'
}

export function routeRequiresForbidden(options: {
  routeName: string | symbol | null | undefined
  allowedRoles?: CurrentUserResponse['member']['role'][]
  identity: CurrentUserResponse | null
  failureKind: SessionFailureKind
}): boolean {
  if (options.routeName === 'forbidden') return false
  if (!options.identity) {
    return !['network', 'server'].includes(options.failureKind)
  }
  if (options.identity.member.status !== 'active') return true
  return Boolean(options.allowedRoles && !options.allowedRoles.includes(options.identity.member.role))
}
