import { describe, expect, it } from 'vitest'
import { ApiError, type CurrentUserResponse } from '@/types'
import {
  classifySessionFailure,
  defaultRouteForIdentity,
  routeRequiresForbidden,
  shouldResetPreviewForError,
} from '@/utils/recovery'

const identity = (role: CurrentUserResponse['member']['role']): CurrentUserResponse => ({
  member: { id: role, display_name: role, role, status: 'active' },
  permissions: {
    can_create_knowledge: role !== 'reader',
    can_manage_members: role === 'maintainer',
  },
})

describe('preview error recovery', () => {
  it.each([
    'preview_expired',
    'preview_actor_mismatch',
    'preview_form_changed',
    'preview_context_changed',
    'preview_metadata_changed',
    'preview_replay_conflict',
    'preview_state_missing',
    'invalid_preview_token',
    'invalid_preview_state',
    'PREVIEW_EXPIRED',
  ])('clears stale preview state for %s', (code) => {
    expect(shouldResetPreviewForError(code)).toBe(true)
  })

  it('keeps the token for an in-progress submission that can be retried', () => {
    expect(shouldResetPreviewForError('preview_submission_in_progress')).toBe(false)
    expect(shouldResetPreviewForError('member_disabled')).toBe(false)
  })
})

describe('session failure classification', () => {
  it('distinguishes transport, disabled account, and HTTP authorization failures', () => {
    expect(classifySessionFailure(new ApiError('offline', { code: 'NETWORK_ERROR' }))).toBe('network')
    expect(classifySessionFailure(new ApiError('disabled', { status: 403, code: 'member_disabled' }))).toBe('disabled')
    expect(classifySessionFailure(new ApiError('login', { status: 401, code: 'not_authenticated' }))).toBe('unauthenticated')
    expect(classifySessionFailure(new ApiError('denied', { status: 403, code: 'forbidden' }))).toBe('forbidden')
    expect(classifySessionFailure(new ApiError('broken', { status: 500, code: 'internal_error' }))).toBe('server')
  })
})

describe('fail-closed routing', () => {
  it('blocks a reader from protected pages but never redirects the forbidden page into itself', () => {
    expect(routeRequiresForbidden({
      routeName: 'knowledge-create',
      allowedRoles: ['contributor', 'maintainer'],
      identity: identity('reader'),
      failureKind: 'none',
    })).toBe(true)
    expect(routeRequiresForbidden({
      routeName: 'forbidden',
      identity: identity('reader'),
      failureKind: 'none',
    })).toBe(false)
    expect(defaultRouteForIdentity(identity('reader'))).toBe('/forbidden')
  })

  it('fails closed when identity is absent while leaving network/server errors to the service error screen', () => {
    expect(routeRequiresForbidden({
      routeName: 'knowledge-create',
      allowedRoles: ['contributor', 'maintainer'],
      identity: null,
      failureKind: 'none',
    })).toBe(true)
    expect(routeRequiresForbidden({
      routeName: 'knowledge-create',
      allowedRoles: ['contributor', 'maintainer'],
      identity: null,
      failureKind: 'network',
    })).toBe(false)
  })

  it('uses refreshed permissions for the post-role-change destination', () => {
    expect(defaultRouteForIdentity(identity('maintainer'))).toBe('/knowledge/create')
    expect(defaultRouteForIdentity(identity('contributor'))).toBe('/knowledge/create')
    expect(defaultRouteForIdentity(identity('reader'))).toBe('/forbidden')
    expect(defaultRouteForIdentity(null)).toBe('/forbidden')
  })
})
