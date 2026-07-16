export type AssignableRole = 'reader' | 'contributor' | 'maintainer'
export type Role = AssignableRole | 'super_admin'
export type MemberStatus = 'active' | 'disabled'
export type KnowledgeScope = 'personal' | 'team'
export type KnowledgeLayer = 'layer0p' | 'layer0t' | 'layer1' | 'layer2' | 'layer3'
export type KnowledgeType = 'model' | 'decision' | 'guideline' | 'pitfall' | 'process'
export type TechnicalDirection = 'patterns' | 'anti-patterns'
export type KnowledgeMaturity = 'draft' | 'verified' | 'proven'

export interface Member {
  id: string
  display_name: string
  role: Role
  status: MemberStatus
}

export interface CurrentUserResponse {
  member: Member
  permissions: {
    can_browse_knowledge: boolean
    can_create_knowledge: boolean
    can_manage_members: boolean
    can_manage_business_domains: boolean
    can_super_admin: boolean
  }
  environment?: string
}

export interface SelectOption<T extends string = string> {
  value: T
  label: string
}

export interface BusinessDomain {
  id: string
  name: string
  description: string
  status: 'active' | 'disabled'
}

export interface KnowledgeOptions {
  scopes: SelectOption<KnowledgeScope>[]
  knowledge_types: SelectOption<KnowledgeType>[]
  layers: SelectOption<Exclude<KnowledgeLayer, 'layer0p'>>[]
  technical_directions: SelectOption<TechnicalDirection>[]
  business_domains: BusinessDomain[]
  preview_ttl_seconds: number
}

export interface KnowledgeTemplate {
  type: KnowledgeType
  technical_direction: TechnicalDirection | null
  content: string
}

export interface KnowledgeDraft {
  scope: KnowledgeScope
  title: string
  type: KnowledgeType
  tags: string[]
  source_references: string[]
  layer?: Exclude<KnowledgeLayer, 'layer0p'>
  technical_direction?: TechnicalDirection
  domain?: string
  content: string
}

export interface KnowledgePreview {
  id: string
  title: string
  type: KnowledgeType
  tags: string[]
  source_references: string[]
  scope: KnowledgeScope
  owner_id: string | null
  layer: KnowledgeLayer
  technical_direction: TechnicalDirection | null
  maturity: 'draft'
  created_at: string
  relative_path: string
  content: string
  metadata: Record<string, unknown>
}

export interface PreviewResponse {
  preview: KnowledgePreview
  checks: PreviewCheck[]
  preview_token: string
  expires_at: string
}

export interface PreviewCheck {
  key: string
  label: string
  status: 'passed' | 'failed'
  detail: string
}

export interface CreatedKnowledge {
  id: string
  title: string
  type: KnowledgeType
  scope: KnowledgeScope
  owner_id: string | null
  layer: KnowledgeLayer
  technical_direction: TechnicalDirection | null
  maturity: KnowledgeMaturity
  created_at: string
  tags: string[]
  source_references: string[]
  relative_path: string
  file_url?: string
}

export interface CreateKnowledgeResponse {
  knowledge: CreatedKnowledge
  actor: Pick<Member, 'id' | 'display_name' | 'role'>
  writes: Array<{
    key: string
    label: string
    status: 'completed'
    detail: string
  }>
  catalog_updated: boolean
  audit_logged: boolean
}

export interface KnowledgeFile extends CreatedKnowledge {
  content: string
  revision?: number
  updated_at?: string | null
  updated_by?: string | null
}

export interface KnowledgeListItem extends Omit<CreatedKnowledge, 'source_references'> {
  excerpt: string
}

export interface KnowledgeListResponse {
  items: KnowledgeListItem[]
  counts: Record<KnowledgeLayer, number>
  total: number
}

export interface MembersResponse {
  members: Member[]
}

export interface SuperAdminKnowledge extends KnowledgeFile {
  domain: string | null
  archived: boolean
  conflict_status: 'none' | 'suspected' | 'confirmed' | 'resolved'
  promotion: Record<string, unknown>
  evidence: Record<string, unknown>
  revision: number
  updated_at: string | null
  updated_by: string | null
  base_digest: string
}

export interface SuperAdminKnowledgeListItem extends Omit<SuperAdminKnowledge, 'content' | 'evidence' | 'promotion'> {}

export interface SuperAdminKnowledgeListResponse {
  items: SuperAdminKnowledgeListItem[]
  counts: { active: number; archived: number }
  total: number
}

export interface SuperAdminKnowledgeInput {
  scope: KnowledgeScope
  owner_id?: string
  title: string
  type: KnowledgeType
  tags: string[]
  source_references: string[]
  layer?: Exclude<KnowledgeLayer, 'layer0p'>
  technical_direction?: TechnicalDirection
  domain?: string
  content: string
  reason: string
  base_digest: string
  owner_confirmed_by?: string
}

export interface SuperAdminPreviewResponse {
  before: SuperAdminKnowledge
  after: SuperAdminKnowledge
  changed_fields: string[]
  consequences: string[]
  checks: PreviewCheck[]
  preview_token: string
  expires_at: string
}

export interface SuperAdminCommitResponse {
  knowledge: SuperAdminKnowledge
  writes: CreateKnowledgeResponse['writes']
  audit_logged: boolean
  idempotent_replay: boolean
}

export type SuperAdminAction =
  | 'approve_proven'
  | 'propose_promotion'
  | 'approve_promotion'
  | 'rollback_layer'
  | 'archive'
  | 'restore'
  | 'mark_conflict'
  | 'resolve_conflict'

export interface AuditRecord {
  timestamp: string
  actor: string
  action: string
  target_id: string
  detail: unknown
  session: string
}

export interface AuditListResponse {
  items: AuditRecord[]
  total: number
}

export interface FieldError {
  field: string
  message: string
}

export class ApiError extends Error {
  status: number
  code: string
  fieldErrors: FieldError[]

  constructor(message: string, options?: { status?: number; code?: string; fieldErrors?: FieldError[] }) {
    super(message)
    this.name = 'ApiError'
    this.status = options?.status ?? 0
    this.code = options?.code ?? 'UNKNOWN_ERROR'
    this.fieldErrors = options?.fieldErrors ?? []
  }
}
