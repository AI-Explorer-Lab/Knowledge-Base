import { apiRequest } from './client'
import {
  mockCreateKnowledge,
  mockCreateMember,
  mockGetCurrentUser,
  mockGetKnowledgeOptions,
  mockGetKnowledgeById,
  mockListKnowledge,
  mockGetMembers,
  mockPreviewKnowledge,
  mockUpdateMember,
} from './mock'
import type {
  CreateKnowledgeResponse,
  CurrentUserResponse,
  KnowledgeDraft,
  KnowledgeFile,
  KnowledgeLayer,
  KnowledgeListResponse,
  KnowledgeOptions,
  Member,
  MembersResponse,
  PreviewResponse,
  Role,
} from '@/types'

export const isMockApi = import.meta.env.DEV && (
  import.meta.env.VITE_USE_MOCK_API === 'true'
  || new URLSearchParams(window.location.search).get('demo') === '1'
)

export const getCurrentUser = (): Promise<CurrentUserResponse> =>
  isMockApi ? mockGetCurrentUser() : apiRequest('/me')

export const getKnowledgeOptions = (): Promise<KnowledgeOptions> =>
  isMockApi ? mockGetKnowledgeOptions() : apiRequest('/knowledge/options')

export const getKnowledgeById = (knowledgeId: string): Promise<{ knowledge: KnowledgeFile }> =>
  isMockApi
    ? mockGetKnowledgeById(knowledgeId)
    : apiRequest(`/knowledge/${encodeURIComponent(knowledgeId)}`)

export const listKnowledge = (
  layer?: KnowledgeLayer,
  query = '',
): Promise<KnowledgeListResponse> => {
  if (isMockApi) return mockListKnowledge(layer, query)
  const params = new URLSearchParams()
  if (layer) params.set('layer', layer)
  if (query.trim()) params.set('q', query.trim())
  const suffix = params.size ? `?${params.toString()}` : ''
  return apiRequest(`/knowledge${suffix}`)
}

export const previewKnowledge = (draft: KnowledgeDraft): Promise<PreviewResponse> =>
  isMockApi
    ? mockPreviewKnowledge(draft)
    : apiRequest('/knowledge/preview', { method: 'POST', body: JSON.stringify(draft) })

export const createKnowledge = (
  draft: KnowledgeDraft,
  previewToken: string,
): Promise<CreateKnowledgeResponse> => {
  if (isMockApi) return mockCreateKnowledge(draft, previewToken)
  return apiRequest('/knowledge/manual', {
    method: 'POST',
    body: JSON.stringify({ ...draft, preview_token: previewToken }),
  })
}

export const getMembers = (): Promise<MembersResponse> =>
  isMockApi ? mockGetMembers() : apiRequest('/members')

export const createMember = (payload: {
  id: string
  display_name: string
  role: Role
}): Promise<{ member: Member }> =>
  isMockApi
    ? mockCreateMember(payload)
    : apiRequest('/members', { method: 'POST', body: JSON.stringify(payload) })

export const updateMember = (
  memberId: string,
  payload: Partial<Pick<Member, 'display_name' | 'role' | 'status'>>,
): Promise<{ member: Member }> =>
  isMockApi
    ? mockUpdateMember(memberId, payload)
    : apiRequest(`/members/${encodeURIComponent(memberId)}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      })
