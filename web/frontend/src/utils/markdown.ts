function escapeHtml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function safeLinkTarget(value: string): string | null {
  const target = value.trim()
  if (!target || /[\u0000-\u001f\u007f]/.test(target)) return null
  if (/^(https?:|mailto:)/i.test(target)) return target
  if (target.startsWith('//')) return null
  if (/^(\/|\.\/|\.\.\/|#|\?)/.test(target)) return target
  if (/^[a-z][a-z0-9+.-]*:/i.test(target)) return null
  return target
}

function renderEmphasis(value: string) {
  return escapeHtml(value)
    .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
    .replace(/~~([^~\n]+)~~/g, '<del>$1</del>')
    .replace(/_([^_\n]+)_/g, '<em>$1</em>')
    .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
}

function inlineMarkdown(value: string) {
  const tokens: string[] = []
  const token = (html: string) => {
    const index = tokens.push(html) - 1
    return `\uE000${index}\uE001`
  }

  let protectedText = value.replace(/`([^`\n]+)`/g, (_match, code: string) =>
    token(`<code>${escapeHtml(code)}</code>`),
  )

  protectedText = protectedText.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, (_match, label: string, href: string) => {
    const safeTarget = safeLinkTarget(href)
    if (!safeTarget) return token(`${renderEmphasis(label)} (${escapeHtml(href)})`)
    const external = /^(https?:|mailto:)/i.test(safeTarget)
    const attributes = external ? ' target="_blank" rel="noopener noreferrer"' : ''
    return token(`<a href="${escapeHtml(safeTarget)}"${attributes}>${renderEmphasis(label)}</a>`)
  })

  let rendered = renderEmphasis(protectedText)
  rendered = rendered.replace(/\uE000(\d+)\uE001/g, (_match, index: string) => tokens[Number(index)] ?? '')
  return rendered
}

function splitTableRow(line: string) {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim())
}

function isTableDivider(line: string) {
  const cells = splitTableRow(line)
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell))
}

export function renderMarkdown(source: string): string {
  const lines = source.replace(/\r\n/g, '\n').split('\n')
  const output: string[] = []
  let listType: 'ul' | 'ol' | 'task' | null = null
  let codeOpen = false

  const closeList = () => {
    if (listType === 'ol') output.push('</ol>')
    if (listType === 'ul' || listType === 'task') output.push('</ul>')
    listType = null
  }

  const openList = (nextType: 'ul' | 'ol' | 'task') => {
    if (listType === nextType) return
    closeList()
    output.push(nextType === 'ol' ? '<ol>' : `<ul${nextType === 'task' ? ' class="task-list"' : ''}>`)
    listType = nextType
  }

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]

    if (line.startsWith('```')) {
      closeList()
      if (codeOpen) {
        output.push('</code></pre>')
        codeOpen = false
      } else {
        const rawLanguage = line.slice(3).trim().toLowerCase()
        const language = /^[a-z0-9_-]{1,30}$/.test(rawLanguage) ? rawLanguage : ''
        output.push(`<pre><code${language ? ` data-language="${language}"` : ''}>`)
        codeOpen = true
      }
      continue
    }

    if (codeOpen) {
      output.push(`${escapeHtml(line)}\n`)
      continue
    }

    if (line.includes('|') && index + 1 < lines.length && isTableDivider(lines[index + 1])) {
      closeList()
      const headers = splitTableRow(line)
      output.push('<div class="markdown-table-wrap"><table><thead><tr>')
      headers.forEach((header) => output.push(`<th>${inlineMarkdown(header)}</th>`))
      output.push('</tr></thead><tbody>')
      index += 2
      while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
        output.push('<tr>')
        splitTableRow(lines[index]).forEach((cell) => output.push(`<td>${inlineMarkdown(cell)}</td>`))
        output.push('</tr>')
        index += 1
      }
      output.push('</tbody></table></div>')
      index -= 1
      continue
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/)
    if (heading) {
      closeList()
      const level = heading[1].length
      output.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`)
      continue
    }

    const task = line.match(/^[-*]\s+\[([ xX])\]\s+(.+)$/)
    if (task) {
      openList('task')
      output.push(`<li><input type="checkbox" disabled${task[1].toLowerCase() === 'x' ? ' checked' : ''}><span>${inlineMarkdown(task[2])}</span></li>`)
      continue
    }

    const bullet = line.match(/^[-*]\s+(.+)$/)
    if (bullet) {
      openList('ul')
      output.push(`<li>${inlineMarkdown(bullet[1])}</li>`)
      continue
    }

    const ordered = line.match(/^\d+\.\s+(.+)$/)
    if (ordered) {
      openList('ol')
      output.push(`<li>${inlineMarkdown(ordered[1])}</li>`)
      continue
    }

    const quote = line.match(/^>\s?(.*)$/)
    if (quote) {
      closeList()
      output.push(`<blockquote><p>${inlineMarkdown(quote[1])}</p></blockquote>`)
      continue
    }

    closeList()
    if (line.trim()) output.push(`<p>${inlineMarkdown(line)}</p>`)
  }

  closeList()
  if (codeOpen) output.push('</code></pre>')
  return output.join('')
}
