import { readonly, ref } from 'vue'

export type ToastTone = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  message: string
  tone: ToastTone
}

const toasts = ref<ToastItem[]>([])
let nextId = 1

export function pushToast(message: string, tone: ToastTone = 'info', duration = 3200) {
  const id = nextId++
  toasts.value.push({ id, message, tone })
  window.setTimeout(() => dismissToast(id), duration)
}

export function dismissToast(id: number) {
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

export function useToast() {
  return {
    toasts: readonly(toasts),
    pushToast,
    dismissToast,
  }
}
