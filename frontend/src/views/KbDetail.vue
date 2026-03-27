<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex-shrink-0 flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-white">
      <button class="btn-ghost p-1.5" @click="$router.push('/kb')">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>
      <div class="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center text-lg flex-shrink-0">
        {{ kb?.icon || '📚' }}
      </div>
      <div class="flex-1 min-w-0">
        <h1 class="text-base font-semibold text-gray-900 truncate">{{ kb?.name }}</h1>
        <p class="text-xs text-gray-500 truncate">{{ kb?.description || '暂无描述' }}</p>
      </div>
      <div class="flex gap-2">
        <button class="btn-ghost text-xs gap-1.5" @click="$router.push(`/kb/${id}/docs`)">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          文档管理
        </button>
        <button class="btn-primary text-xs gap-1.5" @click="$router.push(`/kb/${id}/chat`)">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
          </svg>
          开始对话
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="flex-1 overflow-auto p-6">
      <div class="grid grid-cols-3 gap-4 mb-6" v-if="kb">
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">文档总数</p>
          <p class="text-2xl font-bold text-gray-900">{{ kb.doc_count }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">向量数量</p>
          <p class="text-2xl font-bold text-primary-600">{{ kb.vector_count ?? '-' }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-gray-500 mb-1">嵌入模型</p>
          <p class="text-sm font-medium text-gray-700 mt-1 truncate">{{ kb.embedding_model }}</p>
        </div>
      </div>

      <!-- Recent docs -->
      <div class="card overflow-hidden">
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-50">
          <span class="text-sm font-medium text-gray-700">最近文档</span>
          <button class="text-xs text-primary-600 hover:text-primary-700" @click="$router.push(`/kb/${id}/docs`)">
            查看全部 →
          </button>
        </div>
        <div v-if="docs.length" class="divide-y divide-gray-50">
          <div v-for="doc in docs" :key="doc.id" class="flex items-center gap-3 px-4 py-3 hover:bg-gray-50">
            <span class="text-base flex-shrink-0">{{ fileIcon(doc.file_type) }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-gray-800 truncate">{{ doc.filename }}</p>
              <p class="text-xs text-gray-400">{{ doc.chunk_count }} 块 · {{ formatSize(doc.file_size) }}</p>
            </div>
            <span :class="statusBadge(doc.status)">{{ statusLabel(doc.status) }}</span>
          </div>
        </div>
        <div v-else class="py-10 text-center text-sm text-gray-400">暂无文档，去文档管理页上传</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { kbApi, docApi } from '@/api'

const route = useRoute()
const id = parseInt(route.params.id)
const kb = ref(null)
const docs = ref([])

const fileIcon = t => ({ pdf:'📄', word:'📝', excel:'📊', text:'📃', image:'🖼️' }[t] || '📁')
const formatSize = b => b > 1048576 ? (b/1048576).toFixed(1)+'MB' : (b/1024).toFixed(1)+'KB'
const statusBadge = s => ({ completed:'badge-green', processing:'badge-blue', pending:'badge-yellow', failed:'badge-red' }[s] || 'badge-gray')
const statusLabel = s => ({ completed:'已完成', processing:'处理中', pending:'待处理', failed:'失败' }[s] || s)

onMounted(async () => {
  try {
    const res = await kbApi.get(id)
    kb.value = res.data
    const dres = await docApi.list({ kb_id: id, page: 1, page_size: 5 })
    docs.value = dres.data.items
  } catch {}
})
</script>
