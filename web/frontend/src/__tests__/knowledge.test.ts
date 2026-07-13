import { describe, expect, it } from 'vitest'
import { renderMarkdown } from '@/utils/markdown'
import {
  buildKnowledgePayload,
  categoryForType,
  initialKnowledgeDraft,
  shouldConfirmTemplateReplacement,
  validateKnowledgeDraft,
} from '@/utils/knowledge'
import type { KnowledgeOptions } from '@/types'

const options: KnowledgeOptions = {
  scopes: [
    { value: 'personal', label: '个人知识' },
    { value: 'team', label: '团队知识' },
  ],
  knowledge_types: [{ value: 'guideline', label: 'guideline' }],
  layers: [
    { value: 'layer1', label: 'Layer 1' },
    { value: 'layer2', label: 'Layer 2' },
    { value: 'layer3', label: 'Layer 3' },
  ],
  categories: {
    layer0p: ['guidelines'],
    layer1: ['patterns'],
    layer2: ['models'],
    layer3: ['decisions'],
  },
  business_domains: ['order'],
  preview_ttl_seconds: 600,
}

describe('knowledge request shaping', () => {
  it('opens a new injection flow without example content', () => {
    const draft = initialKnowledgeDraft()

    expect(draft).toMatchObject({
      title: '',
      tags: [],
      source_references: [''],
      content: '',
    })
  })

  it('omits all backend-derived and hidden fields for personal knowledge', () => {
    const draft = initialKnowledgeDraft()
    draft.layer = 'layer2'
    draft.domain = 'order'
    draft.category = 'models'

    const payload = buildKnowledgePayload(draft)

    expect(payload.scope).toBe('personal')
    expect(payload).not.toHaveProperty('layer')
    expect(payload).not.toHaveProperty('domain')
    expect(payload).not.toHaveProperty('category')
    expect(payload).not.toHaveProperty('owner_id')
    expect(payload).not.toHaveProperty('maturity')
  })

  it('keeps only the selected controlled team location fields', () => {
    const draft = initialKnowledgeDraft()
    Object.assign(draft, {
      scope: 'team',
      layer: 'layer2',
      domain: 'order',
      category: 'models',
    })

    expect(buildKnowledgePayload(draft)).toMatchObject({
      scope: 'team',
      layer: 'layer2',
      domain: 'order',
      category: 'models',
    })
  })

  it('requires a domain only for Layer 2 team knowledge', () => {
    const draft = initialKnowledgeDraft()
    Object.assign(draft, { scope: 'team', layer: 'layer2', category: 'models', domain: '' })
    expect(validateKnowledgeDraft(draft).domain).toBeTruthy()

    draft.layer = 'layer1'
    draft.category = 'patterns'
    expect(validateKnowledgeDraft(draft).domain).toBeUndefined()
  })

  it('accepts any nonempty Markdown body as required by the plan', () => {
    const draft = initialKnowledgeDraft()
    draft.content = '有效'
    expect(validateKnowledgeDraft(draft).content).toBeUndefined()
  })

  it('normalizes a category to an allowed server option', () => {
    expect(categoryForType('guideline', 'layer1', options)).toBe('patterns')
  })

  it('protects edited content before replacing a knowledge template', () => {
    const originalTemplate = '## 推荐做法\n\n请填写'

    expect(shouldConfirmTemplateReplacement('', null)).toBe(false)
    expect(shouldConfirmTemplateReplacement(originalTemplate, originalTemplate)).toBe(false)
    expect(shouldConfirmTemplateReplacement(`${originalTemplate}\n用户补充`, originalTemplate)).toBe(true)
    expect(shouldConfirmTemplateReplacement('从预览页返回的正文', null)).toBe(true)
  })
})

describe('Markdown preview safety', () => {
  it('escapes raw HTML before rendering Markdown', () => {
    const html = renderMarkdown('## 标题\n<script>alert(1)</script>')
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;')
    expect(html).not.toContain('<script>')
  })

  it.each([
    ['二级标题', '## 标题', '<h2>标题</h2>'],
    ['加粗', '**重点**', '<strong>重点</strong>'],
    ['斜体', '_说明_', '<em>说明</em>'],
    ['删除线', '~~旧内容~~', '<del>旧内容</del>'],
    ['行内代码', '`npm test`', '<code>npm test</code>'],
    ['无序列表', '- 第一项', '<ul><li>第一项</li></ul>'],
    ['有序列表', '1. 第一项', '<ol><li>第一项</li></ol>'],
    ['任务项', '- [x] 已完成', '<input type="checkbox" disabled checked>'],
    ['引用', '> 评审结论', '<blockquote><p>评审结论</p></blockquote>'],
  ])('renders the %s toolbar syntax', (_name, markdown, expected) => {
    expect(renderMarkdown(markdown)).toContain(expected)
  })

  it('renders tables created by the toolbar', () => {
    const html = renderMarkdown('| 列 1 | 列 2 |\n| --- | --- |\n| 内容 | 说明 |')
    expect(html).toContain('<table>')
    expect(html).toContain('<th>列 1</th>')
    expect(html).toContain('<td>说明</td>')
  })

  it('allows only explicit safe or relative links', () => {
    expect(renderMarkdown('[官网](https://example.com)')).toContain('href="https://example.com"')
    expect(renderMarkdown('[邮件](mailto:team@example.com)')).toContain('href="mailto:team@example.com"')
    expect(renderMarkdown('[文档](../docs/guide.md)')).toContain('href="../docs/guide.md"')

    const dangerous = renderMarkdown('[危险](javascript:alert(1))')
    expect(dangerous).not.toContain('<a ')
    expect(dangerous).not.toContain('href=')
  })

  it('escapes HTML inside labels, tables, quotes, and code blocks', () => {
    const html = renderMarkdown('[<img src=x>](https://example.com)\n| <b>x</b> |\n| --- |\n> <svg>\n```html\n<script>x</script>\n```')
    expect(html).not.toContain('<img')
    expect(html).not.toContain('<b>')
    expect(html).not.toContain('<svg>')
    expect(html).not.toContain('<script>')
    expect(html).toContain('&lt;script&gt;x&lt;/script&gt;')
  })
})
