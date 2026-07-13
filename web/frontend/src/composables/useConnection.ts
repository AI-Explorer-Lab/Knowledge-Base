import { readonly, ref } from 'vue'

const connected = ref(false)

export function markConnected(value: boolean) {
  connected.value = value
}

export function useConnection() {
  return { connected: readonly(connected) }
}

export { connected }
