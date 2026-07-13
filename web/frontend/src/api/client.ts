import { ApiError, type FieldError } from '@/types'
import { markConnected } from '@/composables/useConnection'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

function normalizeFieldErrors(value: unknown): FieldError[] {
  if (Array.isArray(value)) {
    return value.flatMap((item) => {
      if (!item || typeof item !== 'object') return []
      const record = item as Record<string, unknown>
      const field = Array.isArray(record.loc)
        ? String(record.loc.at(-1) ?? '')
        : String(record.field ?? '')
      const message = String(record.message ?? record.msg ?? '字段格式不正确')
      return field ? [{ field, message }] : []
    })
  }

  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).map(([field, message]) => ({
      field,
      message: String(message),
    }))
  }

  return []
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response

  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...init.headers,
      },
    })
  } catch {
    markConnected(false)
    throw new ApiError('无法连接知识库服务，请检查服务状态后重试', {
      code: 'NETWORK_ERROR',
    })
  }

  markConnected(true)

  if (response.status === 204) return undefined as T

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    payload = undefined
  }

  if (!response.ok) {
    const record = payload && typeof payload === 'object' ? (payload as Record<string, unknown>) : {}
    const rawDetail = record.detail
    const detail = rawDetail && typeof rawDetail === 'object'
      ? (rawDetail as Record<string, unknown>)
      : record
    const message = typeof rawDetail === 'string'
      ? rawDetail
      : String(detail.message ?? (response.status === 403 ? '当前角色无权执行此操作' : '请求处理失败'))
    const fieldErrors = normalizeFieldErrors(detail.field_errors ?? rawDetail)

    throw new ApiError(message, {
      status: response.status,
      code: String(detail.code ?? `HTTP_${response.status}`),
      fieldErrors,
    })
  }

  return payload as T
}
