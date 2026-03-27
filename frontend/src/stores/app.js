import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const systemOk = ref(null)
  const toast = ref(null)
  let toastTimer = null

  function showToast(msg, type = 'info', duration = 3000) {
    if (toastTimer) clearTimeout(toastTimer)
    toast.value = { msg, type }
    toastTimer = setTimeout(() => toast.value = null, duration)
  }

  return { systemOk, toast, showToast }
})
