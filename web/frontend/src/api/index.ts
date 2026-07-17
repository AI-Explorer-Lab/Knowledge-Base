import { apiRequest } from './client'
import {
  mockCreateKnowledge,
  mockCreateBusinessDomain,
  mockCreateMember,
  mockGetCurrentUser,
  mockGetKnowledgeOptions,
  mockGetKnowledgeTemplate,
  mockGetKnowledgeById,
  mockListKnowledge,
  mockGetMembers,
  mockPreviewKnowledge,
  mockUpdateMember,
  mockListSuperAdminKnowledge,
  mockGetSuperAdminKnowledge,
  mockPreviewSuperAdminKnowledge,
  mockCommitSuperAdminKnowledge,
  mockExecuteSuperAdminAction,
  mockGetAuditRecords,
  mockUpdateBusinessDomain,
} from './mock'
import type {
  CreateKnowledgeResponse,
  BusinessDomain,
  CurrentUserResponse,
  KnowledgeDraft,
  KnowledgeFile,
  KnowledgeLayer,
  KnowledgeListResponse,
  KnowledgeOptions,
  KnowledgeTemplate,
  KnowledgeType,
  Member,
  MembersResponse,
  PreviewResponse,
  Role,
  AssignableRole,
  AuditListResponse,
  SuperAdminAction,
  SuperAdminCommitResponse,
  SuperAdminKnowledge,
  SuperAdminKnowledgeInput,
  SuperAdminKnowledgeListResponse,
  SuperAdminPreviewResponse,
  TechnicalDirection,
} from '@/types'

export const isMockApi = import.meta.env.DEV && (
  import.meta.env.VITE_USE_MOCK_API === 'true'
  || new URLSearchParams(window.location.search).get('demo') === '1'
)

export const getCurrentUser = (): Promise<CurrentUserResponse> =>
  isMockApi ? mockGetCurrentUser() : apiRequest('/me')

export const getKnowledgeOptions = (): Promise<KnowledgeOptions> =>
  isMockApi ? mockGetKnowledgeOptions() : apiRequest('/knowledge/options')

export const createBusinessDomain = (payload: {
  id: string
  name: string
  description: string
}): Promise<{ business_domain: BusinessDomain }> =>
  isMockApi
    ? mockCreateBusinessDomain(payload)
    : apiRequest('/business-domains', { method: 'POST', body: JSON.stringify(payload) })

export const updateBusinessDomain = (
  domainId: string,
  payload: Partial<Pick<BusinessDomain, 'name' | 'description' | 'status'>>,
): Promise<{ business_domain: BusinessDomain }> =>
  isMockApi
    ? mockUpdateBusinessDomain(domainId, payload)
    : apiRequest(`/business-domains/${encodeURIComponent(domainId)}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      })

export const getKnowledgeTemplate = (
  type: KnowledgeType,
  technicalDirection?: TechnicalDirection,
): Promise<KnowledgeTemplate> => {
  if (isMockApi) return mockGetKnowledgeTemplate(type, technicalDirection)
  const params = new URLSearchParams()
  if (technicalDirection) params.set('technical_direction', technicalDirection)
  const suffix = params.size ? `?${params.toString()}` : ''
  return apiRequest(`/knowledge/templates/${encodeURIComponent(type)}${suffix}`)
}

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
  role: AssignableRole
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

export const listSuperAdminKnowledge = (
  state: 'active' | 'archived' | 'all' = 'active',
  query = '',
  filters: {
    layer?: KnowledgeLayer
    scope?: 'personal' | 'team'
    maturity?: 'draft' | 'verified' | 'proven'
  } = {},
): Promise<SuperAdminKnowledgeListResponse> => {
  if (isMockApi) return mockListSuperAdminKnowledge(state, query, filters)
  const params = new URLSearchParams({ state })
  if (query.trim()) params.set('q', query.trim())
  if (filters.layer) params.set('layer', filters.layer)
  if (filters.scope) params.set('scope', filters.scope)
  if (filters.maturity) params.set('maturity', filters.maturity)
  return apiRequest(`/super-admin/knowledge?${params.toString()}`)
}

export const getSuperAdminKnowledge = (
  knowledgeId: string,
): Promise<{ knowledge: SuperAdminKnowledge }> =>
  isMockApi
    ? mockGetSuperAdminKnowledge(knowledgeId)
    : apiRequest(`/super-admin/knowledge/${encodeURIComponent(knowledgeId)}`)

export const previewSuperAdminKnowledge = (
  knowledgeId: string,
  payload: SuperAdminKnowledgeInput,
): Promise<SuperAdminPreviewResponse> =>
  isMockApi
    ? mockPreviewSuperAdminKnowledge(knowledgeId, payload)
    : apiRequest(`/super-admin/knowledge/${encodeURIComponent(knowledgeId)}/preview`, {
        method: 'POST',
        body: JSON.stringify(payload),
      })

export const commitSuperAdminKnowledge = (
  knowledgeId: string,
  payload: SuperAdminKnowledgeInput,
  previewToken: string,
): Promise<SuperAdminCommitResponse> =>
  isMockApi
    ? mockCommitSuperAdminKnowledge(knowledgeId, payload, previewToken)
    : apiRequest(`/super-admin/knowledge/${encodeURIComponent(knowledgeId)}/commit`, {
        method: 'POST',
        body: JSON.stringify({ ...payload, preview_token: previewToken }),
      })

export const executeSuperAdminAction = (
  knowledgeId: string,
  payload: {
    action: SuperAdminAction
    reason: string
    target_layer?: 'layer1' | 'layer2'
    domain?: string
    owner_confirmed_by?: string
  },
): Promise<{ knowledge: SuperAdminKnowledge; action: string; audit_logged: boolean }> =>
  isMockApi
    ? mockExecuteSuperAdminAction(knowledgeId, payload)
    : apiRequest(`/super-admin/knowledge/${encodeURIComponent(knowledgeId)}/actions`, {
        method: 'POST',
        body: JSON.stringify(payload),
      })

export const getAuditRecords = (query = ''): Promise<AuditListResponse> => {
  if (isMockApi) return mockGetAuditRecords(query)
  const params = new URLSearchParams()
  if (query.trim()) params.set('q', query.trim())
  const suffix = params.size ? `?${params.toString()}` : ''
  return apiRequest(`/super-admin/audit${suffix}`)
}
