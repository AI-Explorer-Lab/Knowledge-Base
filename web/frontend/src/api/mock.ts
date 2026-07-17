import type {
  CreateKnowledgeResponse,
  BusinessDomain,
  CurrentUserResponse,
  KnowledgeDraft,
  KnowledgeFile,
  KnowledgeLayer,
  KnowledgeMaturity,
  KnowledgeListResponse,
  KnowledgeOptions,
  KnowledgeReview,
  KnowledgeTemplate,
  KnowledgeType,
  Member,
  MembersResponse,
  PreviewResponse,
  Role,
  AssignableRole,
  AuditListResponse,
  AuditRecord,
  SuperAdminAction,
  SuperAdminCommitResponse,
  SuperAdminKnowledge,
  SuperAdminKnowledgeInput,
  SuperAdminKnowledgeListResponse,
  SuperAdminPreviewResponse,
  TechnicalDirection,
} from '@/types'
import { ApiError } from '@/types'

const wait = (milliseconds = 180) => new Promise((resolve) => globalThis.setTimeout(resolve, milliseconds))

function mockKnowledgeReview(baseAt: string, maturity: KnowledgeMaturity): KnowledgeReview {
  const reviewDays = maturity === 'proven' ? 60 : 30
  const nextReview = new Date(Date.parse(baseAt) + reviewDays * 24 * 60 * 60 * 1000)
  const beijingTime = new Date(nextReview.getTime() + 8 * 60 * 60 * 1000)
    .toISOString()
    .replace('Z', '+08:00')
  return {
    next_review_at: beijingTime,
    overdue: Date.now() >= nextReview.getTime(),
  }
}

const members: Member[] = [
  { id: 'zhangsan', display_name: '张三', role: 'super_admin', status: 'active' },
  { id: 'lisi', display_name: '李四', role: 'contributor', status: 'active' },
  { id: 'wangwu', display_name: '王五', role: 'reader', status: 'active' },
]

const previewTokens = new Map<string, KnowledgeDraft>()
const seededFiles: KnowledgeFile[] = [
  {
    id: 'PK-ZS-GDL-001',
    title: '调试 API 前先检查端口',
    type: 'guideline',
    scope: 'personal',
    owner_id: 'zhangsan',
    layer: 'layer0p',
    technical_direction: null,
    maturity: 'draft',
    created_at: '2026-07-12T10:20:00Z',
    tags: ['debug', 'api'],
    source_references: ['个人调试复盘'],
    relative_path: 'personal-prefernece/zhangsan/knowledge/guidelines/PK-ZS-GDL-001.md',
    content: '启动服务前，先确认目标端口没有被占用，并检查服务监听地址。',
    review: mockKnowledgeReview('2026-07-12T10:20:00Z', 'draft'),
  },
  {
    id: 'TC-GDL-001',
    title: '团队提交信息约定',
    type: 'guideline',
    scope: 'team',
    owner_id: null,
    layer: 'layer0t',
    technical_direction: null,
    maturity: 'verified',
    created_at: '2026-07-12T09:10:00Z',
    tags: ['team', 'commit'],
    source_references: ['团队协作约定'],
    relative_path: 'team-conventions/guidelines/TC-GDL-001.md',
    content: '提交信息需要说明变更目的，并保持一次提交只处理一个清晰主题。',
    review: mockKnowledgeReview('2026-07-12T09:10:00Z', 'verified'),
  },
  {
    id: 'TK-GDL-001',
    title: '知识治理协作约定',
    type: 'guideline',
    scope: 'team',
    owner_id: null,
    layer: 'layer1',
    technical_direction: 'patterns',
    maturity: 'verified',
    created_at: '2026-07-11T08:40:00Z',
    tags: ['governance', 'team'],
    source_references: ['团队架构评审'],
    relative_path: 'tech-wiki/patterns/TK-GDL-001.md',
    content: '所有人工知识在写入前都必须经过元数据、路径、权限和索引校验。',
    review: mockKnowledgeReview('2026-07-11T08:40:00Z', 'verified'),
  },
  {
    id: 'PJ-DEC-001',
    title: '项目文档分层决策',
    type: 'decision',
    scope: 'team',
    owner_id: null,
    layer: 'layer3',
    technical_direction: null,
    maturity: 'proven',
    created_at: '2026-07-09T03:15:00Z',
    tags: ['project', 'architecture'],
    source_references: ['项目复盘'],
    relative_path: 'docs/knowledge/decisions/PJ-DEC-001.md',
    content: '项目知识按决策、指南和流程拆分，避免把阶段性信息混入稳定技术规范。',
    review: mockKnowledgeReview('2026-07-09T03:15:00Z', 'proven'),
  },
]
const createdFiles = new Map<string, KnowledgeFile>(
  seededFiles.map((knowledge) => [knowledge.id, knowledge]),
)

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
    { value: 'layer0t', label: 'Layer 0-T · 团队约定' },
    { value: 'layer1', label: 'Layer 1 · 技术知识' },
    { value: 'layer2', label: 'Layer 2 · 业务知识' },
    { value: 'layer3', label: 'Layer 3 · 项目知识' },
  ],
  technical_directions: [
    { value: 'patterns', label: '正向模式' },
    { value: 'anti-patterns', label: '反模式' },
  ],
  business_domains: [
    { id: 'order', name: '订单', description: '订单履约与交易过程', status: 'active' },
    { id: 'customer', name: '客户', description: '客户关系与客户服务', status: 'active' },
    { id: 'billing', name: '结算', description: '计费、对账与结算', status: 'active' },
  ],
  preview_ttl_seconds: 600,
}

const knowledgeTemplates: Record<KnowledgeType, string> = {
  model: `## 定义

请说明这个模型表示什么，以及它解决什么问题。

## 组成或字段

请列出主要组成部分或字段，并说明各自含义。

## 关系

请说明它与其他模型、对象或概念之间的关系。

## 约束

请记录必须遵守的规则、边界条件和不变量。

## 示例

请提供一个能够帮助读者理解该模型的具体示例。
`,
  decision: `## 背景

请说明需要作出这项决策的背景和要解决的问题。

## 最终决策

请清楚写出最终选择及其适用范围。

## 选择原因

请说明作出该选择的主要依据。

## 备选方案

请列出评估过但未采用的方案，以及未采用的原因。

## 影响

请记录这项决策带来的收益、代价、风险和后续工作。
`,
  guideline: `## 适用场景

请说明这条指南适用于哪些任务、系统或团队场景。

## 推荐做法

请列出建议遵循的具体做法。

## 禁止做法

请列出应避免的做法，并说明原因。

## 示例

请提供正确示例；如有必要，也可补充错误示例用于对照。

## 检查方式

请说明如何确认这条指南已经被正确执行。
`,
  pitfall: `## 问题现象

请描述问题发生时可以观察到的现象或错误信息。

## 影响

请说明问题会影响哪些用户、系统或工作流程。

## 原因

请记录已经确认的根本原因和常见触发条件。

## 排查步骤

请按顺序列出定位问题的方法。

## 解决与预防

请说明解决方法，以及以后如何避免再次发生。
`,
  process: `## 流程目标

请说明这套流程要完成的目标。

## 适用范围

请说明哪些角色、任务或场景需要执行这套流程。

## 前置条件

请列出开始流程前必须具备的条件和输入。

## 执行步骤

1. 请填写第一步。
2. 请填写第二步。
3. 请根据实际情况继续补充。

## 异常处理

请说明执行失败、中断或出现例外时如何处理。

## 完成标准

请列出能够判断流程已经完成的结果或检查项。
`,
}

const technicalDirectionTemplates: Record<TechnicalDirection, string> = {
  patterns: `## 模式摘要

请概括这个正向技术模式解决的问题和核心做法。

## 复用条件

请说明采用这个模式前需要满足的技术条件和适用边界。

## 收益与代价

请记录采用这个模式能够获得的收益，以及需要承担的复杂度或成本。

## 验证案例

请提供已经验证该模式有效的项目、场景或结果。

---

以下内容请继续按照所选知识类型填写。
`,
  'anti-patterns': `## 反模式摘要

请概括这个反模式中的错误做法，以及它通常出现在哪些场景。

## 识别信号与危害

请记录能够识别该反模式的现象、风险和实际影响。

## 产生原因

请说明团队为什么容易采用这种做法。

## 推荐替代方案

请说明应该改用什么方案，以及替代方案解决问题的方式。

## 迁移方式

请列出从反模式迁移到推荐方案的步骤和注意事项。

---

以下内容请继续按照所选知识类型填写。
`,
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
  const layer = personal ? 'layer0p' : (draft.layer ?? 'layer0t')
  const prefix = personal
    ? 'PK-ZS'
    : layer === 'layer0t'
      ? 'TC'
      : layer === 'layer2'
        ? 'BK'
        : layer === 'layer3'
          ? 'PJ'
          : 'TK'
  const code = typeCodes[draft.type]
  const id = `${prefix}-${code}-001`
  const category = typeCategories[draft.type]
  const base = personal
    ? 'personal-prefernece/zhangsan/knowledge'
    : layer === 'layer0t'
      ? 'team-conventions'
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
      technical_direction: layer === 'layer1' ? (draft.technical_direction ?? null) : null,
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
        ...(layer === 'layer1' && draft.technical_direction
          ? { technical_direction: draft.technical_direction }
          : {}),
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
      can_browse_knowledge: true,
      can_create_knowledge: ['contributor', 'maintainer', 'super_admin'].includes(member.role),
      can_manage_members: ['maintainer', 'super_admin'].includes(member.role),
      can_manage_business_domains: ['maintainer', 'super_admin'].includes(member.role),
      can_super_admin: member.role === 'super_admin',
    },
    environment: 'development',
  }
}

export async function mockGetKnowledgeOptions(): Promise<KnowledgeOptions> {
  await wait(80)
  return structuredClone(options)
}

export async function mockCreateBusinessDomain(payload: {
  id: string
  name: string
  description: string
}): Promise<{ business_domain: BusinessDomain }> {
  await wait()
  if (options.business_domains.some((domain) => domain.id === payload.id)) {
    throw new ApiError('业务领域标识已存在', {
      status: 409,
      code: 'business_domain_exists',
      fieldErrors: [{ field: 'id', message: '请使用其他领域标识' }],
    })
  }
  const businessDomain: BusinessDomain = { ...payload, status: 'active' }
  options.business_domains.push(businessDomain)
  return { business_domain: structuredClone(businessDomain) }
}

export async function mockGetKnowledgeTemplate(
  type: KnowledgeType,
  technicalDirection?: TechnicalDirection,
): Promise<KnowledgeTemplate> {
  await wait(80)
  const baseContent = knowledgeTemplates[type]
  const content = technicalDirection
    ? `${technicalDirectionTemplates[technicalDirection].trimEnd()}\n\n${baseContent.trimStart()}`
    : baseContent
  return { type, technical_direction: technicalDirection ?? null, content }
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
    technical_direction: response.preview.technical_direction,
    maturity: response.preview.maturity,
    created_at: response.preview.created_at,
    tags: response.preview.tags,
    source_references: response.preview.source_references,
    relative_path: response.preview.relative_path,
    content: draft.content,
    review: mockKnowledgeReview(response.preview.created_at, response.preview.maturity),
  })
  return {
    knowledge: {
      id: response.preview.id,
      title: response.preview.title,
      type: response.preview.type,
      scope: response.preview.scope,
      owner_id: response.preview.owner_id,
      layer: response.preview.layer,
      technical_direction: response.preview.technical_direction,
      maturity: response.preview.maturity,
      created_at: response.preview.created_at,
      tags: response.preview.tags,
      source_references: response.preview.source_references,
      relative_path: response.preview.relative_path,
    },
    actor: { id: 'zhangsan', display_name: '张三', role: 'super_admin' },
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

export async function mockListKnowledge(
  layer?: KnowledgeLayer,
  query = '',
): Promise<KnowledgeListResponse> {
  await wait(100)
  const all = [...createdFiles.values()]
  const normalizedQuery = query.trim().toLowerCase()
  const counts: Record<KnowledgeLayer, number> = {
    layer0p: 0,
    layer0t: 0,
    layer1: 0,
    layer2: 0,
    layer3: 0,
  }
  for (const knowledge of all) counts[knowledge.layer] += 1
  const items = all
    .filter((knowledge) => !layer || knowledge.layer === layer)
    .filter((knowledge) => !normalizedQuery || [
      knowledge.id,
      knowledge.title,
      knowledge.type,
      knowledge.technical_direction ?? '',
      knowledge.content,
      ...knowledge.tags,
    ].join(' ').toLowerCase().includes(normalizedQuery))
    .sort((left, right) => right.created_at.localeCompare(left.created_at))
    .map(({ source_references: _sources, content, ...knowledge }) => ({
      ...knowledge,
      excerpt: content.length > 180 ? `${content.slice(0, 180)}…` : content,
    }))
  return { items: structuredClone(items), counts, total: items.length }
}

export async function mockGetMembers(): Promise<MembersResponse> {
  await wait(100)
  return { members: structuredClone(members) }
}

export async function mockCreateMember(payload: {
  id: string
  display_name: string
  role: AssignableRole
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
  if (member.role === 'super_admin') {
    throw new ApiError('超级管理员只能通过系统配置修改', {
      status: 403,
      code: 'super_admin_config_only',
    })
  }
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

const archivedKnowledge = new Set<string>()
const adminPreviewTokens = new Map<string, { id: string; payload: SuperAdminKnowledgeInput }>()
const auditRecords: AuditRecord[] = []

function mockDomainFor(file: KnowledgeFile): string | null {
  if (file.layer !== 'layer2') return null
  const parts = file.relative_path.split('/')
  return parts[0] === 'biz-wiki' ? parts[1] ?? null : null
}

function mockBaseDigest(file: KnowledgeFile): string {
  const seed = `${file.id}:${file.revision ?? 1}:${file.relative_path}:${file.title}`
  return Array.from({ length: 64 }, (_, index) => seed.charCodeAt(index % seed.length).toString(16).at(-1)).join('')
}

function asSuperAdminKnowledge(file: KnowledgeFile): SuperAdminKnowledge {
  const { review: _review, ...knowledge } = structuredClone(file)
  return {
    ...knowledge,
    domain: mockDomainFor(file),
    archived: archivedKnowledge.has(file.id),
    conflict_status: 'none',
    promotion: { candidate: false, target_layer: null, target_path: null, previous_layers: [] },
    evidence: { contributors: [], references: [], validations: [] },
    revision: file.revision ?? 1,
    updated_at: file.updated_at ?? null,
    updated_by: file.updated_by ?? null,
    base_digest: mockBaseDigest(file),
  }
}

function mockAdminTargetPath(id: string, payload: SuperAdminKnowledgeInput): string {
  const category = {
    model: 'models',
    decision: 'decisions',
    guideline: 'guidelines',
    pitfall: 'pitfalls',
    process: 'processes',
  }[payload.type]
  if (payload.scope === 'personal') {
    return `personal-prefernece/${payload.owner_id}/knowledge/${category}/${id}.md`
  }
  if (payload.layer === 'layer0t') return `team-conventions/${category}/${id}.md`
  if (payload.layer === 'layer1') return `tech-wiki/${category}/${id}.md`
  if (payload.layer === 'layer2') return `biz-wiki/${payload.domain}/${category}/${id}.md`
  return `docs/knowledge/${category}/${id}.md`
}

function addMockAudit(action: string, targetId: string, detail: unknown) {
  auditRecords.unshift({
    timestamp: new Date().toISOString(),
    actor: 'zhangsan',
    action,
    target_id: targetId,
    detail,
    session: 'web:super-admin',
  })
}

export async function mockUpdateBusinessDomain(
  domainId: string,
  payload: Partial<Pick<BusinessDomain, 'name' | 'description' | 'status'>>,
): Promise<{ business_domain: BusinessDomain }> {
  await wait()
  const domain = options.business_domains.find((item) => item.id === domainId)
  if (!domain) throw new ApiError('业务领域不存在', { status: 404, code: 'business_domain_not_found' })
  const before = structuredClone(domain)
  Object.assign(domain, payload)
  addMockAudit('business-domain-update', domainId, { before, after: domain })
  return { business_domain: structuredClone(domain) }
}

export async function mockListSuperAdminKnowledge(
  state: 'active' | 'archived' | 'all' = 'active',
  query = '',
  filters: {
    layer?: KnowledgeLayer
    scope?: 'personal' | 'team'
    maturity?: 'draft' | 'verified' | 'proven'
  } = {},
): Promise<SuperAdminKnowledgeListResponse> {
  await wait(100)
  const normalized = query.trim().toLowerCase()
  const all = [...createdFiles.values()].map(asSuperAdminKnowledge)
  const items = all
    .filter((item) => state === 'all' || (state === 'archived') === item.archived)
    .filter((item) => !filters.layer || item.layer === filters.layer)
    .filter((item) => !filters.scope || item.scope === filters.scope)
    .filter((item) => !filters.maturity || item.maturity === filters.maturity)
    .filter((item) => !normalized || [item.id, item.title, item.type, ...item.tags].join(' ').toLowerCase().includes(normalized))
    .map(({ content: _content, evidence: _evidence, promotion: _promotion, ...item }) => item)
  return {
    items,
    counts: {
      active: all.filter((item) => !item.archived).length,
      archived: all.filter((item) => item.archived).length,
    },
    total: items.length,
  }
}

export async function mockGetSuperAdminKnowledge(
  knowledgeId: string,
): Promise<{ knowledge: SuperAdminKnowledge }> {
  await wait(100)
  const file = createdFiles.get(knowledgeId)
  if (!file) throw new ApiError('知识不存在', { status: 404, code: 'knowledge_not_found' })
  return { knowledge: asSuperAdminKnowledge(file) }
}

export async function mockPreviewSuperAdminKnowledge(
  knowledgeId: string,
  payload: SuperAdminKnowledgeInput,
): Promise<SuperAdminPreviewResponse> {
  await wait()
  const file = createdFiles.get(knowledgeId)
  if (!file) throw new ApiError('知识不存在', { status: 404, code: 'knowledge_not_found' })
  if (payload.base_digest !== mockBaseDigest(file)) {
    throw new ApiError('知识已被其他操作修改，请重新加载', { status: 409, code: 'knowledge_changed' })
  }
  const before = asSuperAdminKnowledge(file)
  const nextRevision = (file.revision ?? 1) + 1
  const updatedAt = new Date().toISOString()
  const next: KnowledgeFile = {
    ...file,
    title: payload.title,
    type: payload.type,
    tags: [...payload.tags],
    source_references: [...payload.source_references],
    content: payload.content,
    scope: payload.scope,
    owner_id: payload.scope === 'personal' ? payload.owner_id ?? null : null,
    layer: payload.scope === 'personal' ? 'layer0p' : payload.layer ?? 'layer3',
    technical_direction: payload.technical_direction ?? null,
    maturity: 'draft',
    relative_path: mockAdminTargetPath(knowledgeId, payload),
    revision: nextRevision,
    updated_at: updatedAt,
    updated_by: 'zhangsan',
    review: mockKnowledgeReview(updatedAt, 'draft'),
  }
  const after = asSuperAdminKnowledge(next)
  const changedFields = ['title', 'type', 'tags', 'source_references', 'content', 'relative_path']
    .filter((field) => JSON.stringify(before[field as keyof SuperAdminKnowledge]) !== JSON.stringify(after[field as keyof SuperAdminKnowledge]))
  const token = crypto.randomUUID()
  adminPreviewTokens.set(token, { id: knowledgeId, payload: structuredClone(payload) })
  return {
    before,
    after,
    changed_fields: changedFields,
    consequences: [
      `revision ${before.revision} → ${after.revision}`,
      `maturity ${before.maturity} → draft`,
      '旧版本证据保留，但不再推动当前版本成熟度',
    ],
    checks: [
      { key: 'permission', label: '超级管理员身份', status: 'passed', detail: 'zhangsan' },
      { key: 'version', label: '原版本未变化', status: 'passed', detail: payload.base_digest },
    ],
    preview_token: token,
    expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
  }
}

export async function mockCommitSuperAdminKnowledge(
  knowledgeId: string,
  payload: SuperAdminKnowledgeInput,
  previewToken: string,
): Promise<SuperAdminCommitResponse> {
  await wait()
  const preview = adminPreviewTokens.get(previewToken)
  if (!preview || preview.id !== knowledgeId || JSON.stringify(preview.payload) !== JSON.stringify(payload)) {
    throw new ApiError('修改内容已变化，请重新预览', { status: 409, code: 'preview_form_changed' })
  }
  const response = await mockPreviewSuperAdminKnowledge(knowledgeId, payload)
  const next = response.after
  createdFiles.set(knowledgeId, {
    ...structuredClone(next),
    review: mockKnowledgeReview(next.updated_at ?? next.created_at, next.maturity),
  })
  adminPreviewTokens.delete(previewToken)
  addMockAudit('admin-knowledge-update', knowledgeId, { reason: payload.reason, revision: next.revision })
  return {
    knowledge: next,
    writes: [
      { key: 'knowledge_file', label: '知识文件', status: 'completed', detail: next.relative_path },
      { key: 'layer_catalog', label: 'Layer B 分类目录', status: 'completed', detail: '受影响分类目录已更新' },
      { key: 'global_catalog', label: 'Layer A 全景目录', status: 'completed', detail: 'knowledge-catalog.md' },
      { key: 'audit_log', label: '审计日志', status: 'completed', detail: 'log.md' },
    ],
    audit_logged: true,
    idempotent_replay: false,
  }
}

export async function mockExecuteSuperAdminAction(
  knowledgeId: string,
  payload: {
    action: SuperAdminAction
    reason: string
    target_layer?: 'layer1' | 'layer2'
    domain?: string
    owner_confirmed_by?: string
  },
): Promise<{ knowledge: SuperAdminKnowledge; action: string; audit_logged: boolean }> {
  await wait()
  const file = createdFiles.get(knowledgeId)
  if (!file) throw new ApiError('知识不存在', { status: 404, code: 'knowledge_not_found' })
  if (payload.action === 'archive') archivedKnowledge.add(knowledgeId)
  if (payload.action === 'restore') archivedKnowledge.delete(knowledgeId)
  addMockAudit('admin-governance-action', knowledgeId, payload)
  return { knowledge: asSuperAdminKnowledge(file), action: payload.action, audit_logged: true }
}

export async function mockGetAuditRecords(query = ''): Promise<AuditListResponse> {
  await wait(80)
  const normalized = query.trim().toLowerCase()
  const items = auditRecords.filter((item) => !normalized || JSON.stringify(item).toLowerCase().includes(normalized))
  return { items: structuredClone(items), total: items.length }
}
