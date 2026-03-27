<template>
  <div class="flex flex-col h-full overflow-auto">
    <!-- Header -->
    <div class="flex-shrink-0 flex items-center justify-between px-8 py-5 border-b border-gray-100 bg-white">
      <div>
        <h1 class="text-lg font-semibold text-gray-900">知识库</h1>
        <p class="text-xs text-gray-500 mt-0.5">管理企业文档，构建智能知识检索</p>
      </div>
      <button class="btn-primary" @click="showCreate = true">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
        </svg>
        新建知识库
      </button>
    </div>

    <!-- Search -->
    <div class="flex-shrink-0 px-8 py-4">
      <div class="relative max-w-xs">
        <svg class="absolute left-2.5 top-2.5 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z"/>
        </svg>
        <input v-model="keyword" @input="onSearch" placeholder="搜索知识库..."
          class="input pl-8 text-sm h-9" />
      </div>
    </div>

    <!-- Grid -->
    <div class="flex-1 px-8 pb-8">
      <div v-if="loading" class="flex items-center justify-center h-48">
        <Spinner />
      </div>

      <div v-else-if="!kbs.length" class="flex flex-col items-center justify-center h-48 text-gray-400">
        <svg class="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
        </svg>
        <p class="text-sm">还没有知识库，点击右上角新建</p>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div v-for="kb in kbs" :key="kb.id"
          class="card p-4 hover:shadow-md hover:border-primary-100 transition-all cursor-pointer group"
          @click="$router.push(`/kb/${kb.id}`)">

          <div class="flex items-start justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center text-xl flex-shrink-0">
              {{ kb.icon }}
            </div>
            <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1" @click.stop>
              <button class="btn-ghost p-1.5" @click.stop="openEdit(kb)">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
                </svg>
              </button>
              <button class="btn-danger p-1.5" @click.stop="onDelete(kb)">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>

          <h3 class="font-medium text-gray-900 text-sm mb-1 line-clamp-1">{{ kb.name }}</h3>
          <p class="text-xs text-gray-500 line-clamp-2 min-h-[32px]">{{ kb.description || '暂无描述' }}</p>

          <div class="mt-3 pt-3 border-t border-gray-50 flex items-center justify-between">
            <span class="text-xs text-gray-400">{{ kb.doc_count }} 篇文档</span>
            <span :class="kb.status === 'active' ? 'badge-green' : 'badge-gray'">
              {{ kb.status === 'active' ? '正常' : '停用' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="flex justify-center mt-6">
        <div class="flex gap-1">
          <button class="btn-ghost px-2.5 py-1.5 text-xs" :disabled="page === 1" @click="page--; load()">上一页</button>
          <span class="flex items-center px-3 text-xs text-gray-500">{{ page }} / {{ Math.ceil(total/pageSize) }}</span>
          <button class="btn-ghost px-2.5 py-1.5 text-xs" :disabled="page >= Math.ceil(total/pageSize)" @click="page++; load()">下一页</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <Modal v-if="showCreate || editKb" @close="showCreate=false; editKb=null">
      <template #title>{{ editKb ? '编辑知识库' : '新建知识库' }}</template>
      <form @submit.prevent="onSubmit" class="space-y-4">
        <div>
          <label class="text-xs font-medium text-gray-700 mb-1.5 block">图标</label>
          <div class="flex gap-2 flex-wrap">
            <button type="button" v-for="e in icons" :key="e"
              class="w-8 h-8 rounded-lg text-lg transition-all"
              :class="form.icon === e ? 'bg-primary-100 ring-2 ring-primary-400' : 'hover:bg-gray-100'"
              @click="form.icon = e">{{ e }}</button>
          </div>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700 mb-1.5 block">名称 <span class="text-red-500">*</span></label>
          <input v-model="form.name" required class="input" placeholder="输入知识库名称" />
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700 mb-1.5 block">描述</label>
          <textarea v-model="form.description" class="input resize-none h-20" placeholder="简要描述此知识库的用途" />
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button type="button" class="btn-ghost" @click="showCreate=false; editKb=null">取消</button>
          <button type="submit" class="btn-primary" :disabled="submitting">
            <Spinner v-if="submitting" class="w-3.5 h-3.5" />
            {{ editKb ? '保存' : '创建' }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { kbApi } from '@/api'
import { useAppStore } from '@/stores/app'
import Modal from '@/components/Modal.vue'
import Spinner from '@/components/Spinner.vue'

const appStore = useAppStore()
const kbs = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const keyword = ref('')
const showCreate = ref(false)
const editKb = ref(null)
const submitting = ref(false)
const icons = ['📚', '📝', '💡', '🔬', '📊', '🏢', '⚙️', '🎯', '📋', '🗂️', '💼', '🔧']

const form = reactive({ name: '', description: '', icon: '📚' })

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; load() }, 400)
}

async function load() {
  loading.value = true
  try {
    const res = await kbApi.list({ page: page.value, page_size: pageSize, keyword: keyword.value || undefined })
    kbs.value = res.data.items
    total.value = res.data.total
  } catch (e) { appStore.showToast(e.message, 'error') }
  finally { loading.value = false }
}

function openEdit(kb) {
  editKb.value = kb
  Object.assign(form, { name: kb.name, description: kb.description || '', icon: kb.icon })
}

async function onSubmit() {
  submitting.value = true
  try {
    if (editKb.value) {
      await kbApi.update(editKb.value.id, form)
      appStore.showToast('更新成功', 'success')
    } else {
      await kbApi.create(form)
      appStore.showToast('创建成功', 'success')
    }
    showCreate.value = false; editKb.value = null
    Object.assign(form, { name: '', description: '', icon: '📚' })
    await load()
  } catch (e) { appStore.showToast(e.message, 'error') }
  finally { submitting.value = false }
}

async function onDelete(kb) {
  if (!confirm(`确认删除知识库「${kb.name}」？此操作将删除所有文档和向量数据。`)) return
  try {
    await kbApi.delete(kb.id)
    appStore.showToast('删除成功', 'success')
    await load()
  } catch (e) { appStore.showToast(e.message, 'error') }
}

onMounted(load)
</script>
