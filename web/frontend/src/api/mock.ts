import type {
  CreateKnowledgeResponse,
  CurrentUserResponse,
  KnowledgeDraft,
  KnowledgeFile,
  KnowledgeOptions,
  Member,
  MembersResponse,
  PreviewResponse,
  Role,
} from '@/types'
import { ApiError } from '@/types'

const wait = (milliseconds = 180) => new Promise((resolve) => window.setTimeout(resolve, milliseconds))

const members: Member[] = [
  { id: 'zhangsan', display_name: '张三', role: 'maintainer', status: 'active' },
  { id: 'lisi', display_name: '李四', role: 'contributor', status: 'active' },
  { id: 'wangwu', display_name: '王五', role: 'reader', status: 'active' },
]

const previewTokens = new Map<string, KnowledgeDraft>()
const createdFiles = new Map<string, KnowledgeFile>()

const options: KnowledgeOptions = {
  scopes: [
    { value: 'personal', label: '个人知识' },
    { value: 'team', label: '团队知识' },
  ],
  knowledge_types: [
    { value: 'model', label: 'model' },
    { value: 'decision', label: 'decision' },
    { value: 'guideline', label: 'guideline' },
    { value: 'pitfall', label: 'pitfall' },
    { value: 'process', label: 'process' },
  ],
  layers: [
    { value: 'layer1', label: 'Layer 1 · 技术知识' },
    { value: 'layer2', label: 'Layer 2 · 业务知识' },
    { value: 'layer3', label: 'Layer 3 · 项目知识' },
  ],
  categories: {
    layer0p: ['guidelines', 'decisions', 'models', 'pitfalls', 'processes'],
    layer1: ['patterns', 'guidelines', 'pitfalls'],
    layer2: ['models', 'decisions', 'processes'],
    layer3: ['decisions', 'guidelines', 'processes'],
  },
  business_domains: ['order', 'customer', 'billing'],
  preview_ttl_seconds: 600,
}

const typeCodes = {
  model: 'MDL',
  decision: 'DEC',
  guideline: 'GDL',
  pitfall: 'PTF',
  process: 'PRC',
} as const

const typeCategories = {
  model: 'models',
  decision: 'decisions',
  guideline: 'guidelines',
  pitfall: 'pitfalls',
  process: 'processes',
} as const

function makePreview(draft: KnowledgeDraft): PreviewResponse {
  const personal = draft.scope === 'personal'
  const id = `${personal ? 'PK-ZS' : 'TK'}-${typeCodes[draft.type]}-001`
  const layer = personal ? 'layer0p' : (draft.layer ?? 'layer1')
  const category = draft.category || (personal ? typeCategories[draft.type] : 'patterns')
  const base = personal
    ? 'personal-prefernece/zhangsan/knowledge'
    : layer === 'layer1'
      ? 'tech-wiki'
      : layer === 'layer2'
        ? `biz-wiki/${draft.domain || 'order'}`
        : 'docs/knowledge'
  const relativePath = `${base}/${category}/${id}.md`
  const createdAt = new Date().toISOString()
  const token = `preview_${crypto.randomUUID()}`

  previewTokens.set(token, structuredClone(draft))

  return {
    preview: {
      id,
      title: draft.title,
      type: draft.type,
      tags: [...draft.tags],
      source_references: [...draft.source_references],
      scope: draft.scope,
      owner_id: personal ? 'zhangsan' : null,
      layer,
      maturity: 'draft',
      created_at: createdAt,
      relative_path: relativePath,
      content: draft.content,
      metadata: {
        id,
        title: draft.title,
        type: draft.type,
        tags: [...draft.tags],
        source_references: [...draft.source_references],
        scope: draft.scope,
        ...(personal ? { owner_id: 'zhangsan' } : {}),
        layer,
        maturity: 'draft',
        created_at: createdAt,
        evidence: { contributors: ['zhangsan'], references: [], validations: [] },
        promotion: { candidate: false, target_layer: null, target_path: null, previous_layers: [] },
        conflict_status: 'none',
      },
    },
    checks: [
      { key: 'permission', label: '身份与角色权限', status: 'passed', detail: '当前成员可人工注入知识' },
      { key: 'metadata', label: '元数据字段完整', status: 'passed', detail: '所有必填元数据已通过校验' },
      { key: 'id_unique', label: '知识 ID 全库唯一', status: 'passed', detail: '未发现重复知识 ID' },
      { key: 'path_available', label: '存储路径合法且可用', status: 'passed', detail: '目标路径未被占用且未越界' },
      { key: 'catalog_writable', label: '目录索引可更新', status: 'passed', detail: 'Layer A 与 Layer B 索引可写' },
      { key: 'audit_log_writable', label: '审计日志可更新', status: 'passed', detail: '追加式审计日志可写' },
    ],
    preview_token: token,
    expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
  }
}

export async function mockGetCurrentUser(): Promise<CurrentUserResponse> {
  await wait(80)
  const member = members[0]
  if (member.status === 'disabled') {
    throw new ApiError('当前成员已停用', { status: 403, code: 'member_disabled' })
  }
  return {
    member,
    permissions: {
      can_create_knowledge: member.role === 'contributor' || member.role === 'maintainer',
      can_manage_members: member.role === 'maintainer',
    },
    environment: 'development',
  }
}

export async function mockGetKnowledgeOptions(): Promise<KnowledgeOptions> {
  await wait(80)
  return structuredClone(options)
}

export async function mockPreviewKnowledge(draft: KnowledgeDraft): Promise<PreviewResponse> {
  await wait()
  if (!draft.title.trim() || !draft.content.trim() || draft.source_references.every((source) => !source.trim())) {
    throw new ApiError('请完成所有必填内容', { status: 422, code: 'VALIDATION_ERROR' })
  }
  return makePreview(draft)
}

export async function mockCreateKnowledge(
  draft: KnowledgeDraft,
  previewToken: string,
): Promise<CreateKnowledgeResponse> {
  await wait(360)
  const tokenDraft = previewTokens.get(previewToken)
  if (!tokenDraft || JSON.stringify(tokenDraft) !== JSON.stringify(draft)) {
    throw new ApiError('预览凭证已失效，请重新预览校验', {
      status: 409,
      code: 'preview_form_changed',
    })
  }
  const response = makePreview(draft)
  previewTokens.delete(previewToken)
  createdFiles.set(response.preview.id, {
    id: response.preview.id,
    title: response.preview.title,
    type: response.preview.type,
    scope: response.preview.scope,
    owner_id: response.preview.owner_id,
    layer: response.preview.layer,
    maturity: response.preview.maturity,
    created_at: response.preview.created_at,
    tags: response.preview.tags,
    source_references: response.preview.source_references,
    relative_path: response.preview.relative_path,
    content: draft.content,
  })
  return {
    knowledge: {
      id: response.preview.id,
      title: response.preview.title,
      type: response.preview.type,
      scope: response.preview.scope,
      owner_id: response.preview.owner_id,
      layer: response.preview.layer,
      maturity: response.preview.maturity,
      created_at: response.preview.created_at,
      tags: response.preview.tags,
      source_references: response.preview.source_references,
      relative_path: response.preview.relative_path,
    },
    actor: { id: 'zhangsan', display_name: '张三', role: 'maintainer' },
    writes: [
      { key: 'knowledge_file', label: 'Markdown 知识文件已写入', status: 'completed', detail: response.preview.relative_path },
      { key: 'layer_catalog', label: 'Layer B 分类索引已更新', status: 'completed', detail: '分类目录已同步' },
      { key: 'global_catalog', label: 'Layer A 全景目录已更新', status: 'completed', detail: '全景目录已同步' },
      { key: 'audit_log', label: '审计日志已记录', status: 'completed', detail: '创建操作已追加至 log.md' },
    ],
    catalog_updated: true,
    audit_logged: true,
  }
}

export async function mockGetKnowledgeById(knowledgeId: string): Promise<{ knowledge: KnowledgeFile }> {
  await wait(100)
  const knowledge = createdFiles.get(knowledgeId)
  if (!knowledge) throw new ApiError('知识文件不存在或当前成员无权查看', { status: 404, code: 'NOT_FOUND' })
  return { knowledge: structuredClone(knowledge) }
}

export async function mockGetMembers(): Promise<MembersResponse> {
  await wait(100)
  return { members: structuredClone(members) }
}

export async function mockCreateMember(payload: {
  id: string
  display_name: string
  role: Role
}): Promise<{ member: Member }> {
  await wait()
  if (members.some((member) => member.id === payload.id)) {
    throw new ApiError('成员 ID 已存在', { status: 409, code: 'MEMBER_EXISTS' })
  }
  const member: Member = { ...payload, status: 'active' }
  members.push(member)
  return { member: structuredClone(member) }
}

export async function mockUpdateMember(
  memberId: string,
  payload: Partial<Pick<Member, 'display_name' | 'role' | 'status'>>,
): Promise<{ member: Member }> {
  await wait()
  const member = members.find((candidate) => candidate.id === memberId)
  if (!member) throw new ApiError('成员不存在', { status: 404, code: 'MEMBER_NOT_FOUND' })
  const activeMaintainers = members.filter(
    (candidate) => candidate.role === 'maintainer' && candidate.status === 'active',
  )
  if (
    member.role === 'maintainer' &&
    member.status === 'active' &&
    activeMaintainers.length === 1 &&
    (payload.role && payload.role !== 'maintainer' || payload.status === 'disabled')
  ) {
    throw new ApiError('不能停用或降级最后一名 Maintainer', {
      status: 409,
      code: 'LAST_MAINTAINER',
    })
  }
  Object.assign(member, payload)
  return { member: structuredClone(member) }
}
