export type Role = 'reader' | 'contributor' | 'maintainer'
export type MemberStatus = 'active' | 'disabled'
export type KnowledgeScope = 'personal' | 'team'
export type KnowledgeLayer = 'layer0p' | 'layer1' | 'layer2' | 'layer3'
export type KnowledgeType = 'model' | 'decision' | 'guideline' | 'pitfall' | 'process'
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
  }
  environment?: string
}

export interface SelectOption<T extends string = string> {
  value: T
  label: string
}

export interface KnowledgeOptions {
  scopes: SelectOption<KnowledgeScope>[]
  knowledge_types: SelectOption<KnowledgeType>[]
  layers: SelectOption<Exclude<KnowledgeLayer, 'layer0p'>>[]
  categories: Record<KnowledgeLayer, string[]>
  business_domains: string[]
  preview_ttl_seconds: number
}

export interface KnowledgeDraft {
  scope: KnowledgeScope
  title: string
  type: KnowledgeType
  tags: string[]
  source_references: string[]
  layer?: Exclude<KnowledgeLayer, 'layer0p'>
  category?: string
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
