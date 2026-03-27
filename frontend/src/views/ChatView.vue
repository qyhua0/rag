<template>
  <div class="flex h-full overflow-hidden">
    <!-- Conversation sidebar -->
    <div class="w-56 flex-shrink-0 flex flex-col border-r border-gray-100 bg-white">
      <div class="flex items-center justify-between px-3 py-3 border-b border-gray-100">
        <div class="flex items-center gap-2">
          <button class="btn-ghost p-1" @click="$router.push(`/kb/${id}`)">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <span class="text-xs font-medium text-gray-700">对话列表</span>
        </div>
        <button class="btn-ghost p-1" title="新对话" @click="newConversation">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-2 space-y-0.5">
        <div v-for="conv in convs" :key="conv.id"
          class="group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer text-xs transition-colors"
          :class="activeConvId === conv.id ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50'"
          @click="loadConversation(conv.id)">
          <svg class="w-3 h-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <span class="flex-1 truncate">{{ conv.title }}</span>
          <button class="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-red-500 transition-all"
            @click.stop="deleteConv(conv.id)">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div v-if="!convs.length" class="py-8 text-center text-xs text-gray-400">暂无对话记录</div>
      </div>
    </div>

    <!-- Chat area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Chat header -->
      <div class="flex-shrink-0 flex items-center justify-between px-5 py-3 border-b border-gray-100 bg-white">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-lg bg-primary-600 flex items-center justify-center">
            <svg class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
          </div>
          <span class="text-sm font-medium text-gray-700">知识库问答</span>
        </div>
        <span class="text-xs text-gray-400">基于 {{ kbName }} 知识库</span>
      </div>

      <!-- Messages -->
      <div ref="msgContainer" class="flex-1 overflow-y-auto px-6 py-4 space-y-5">
        <!-- Welcome -->
        <div v-if="!messages.length" class="flex flex-col items-center justify-center h-full text-center">
          <div class="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center mb-4">
            <svg class="w-7 h-7 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
          </div>
          <h3 class="text-base font-semibold text-gray-800 mb-1">开始与知识库对话</h3>
          <p class="text-sm text-gray-500 max-w-xs">我会基于知识库中的文档内容来回答您的问题，并注明引用来源</p>
        </div>

        <!-- Message list -->
        <template v-for="msg in messages" :key="msg.id || msg._tmpId">
          <!-- User message -->
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="max-w-[75%] px-4 py-3 rounded-2xl rounded-tr-sm bg-primary-600 text-white text-sm leading-relaxed">
              {{ msg.content }}
            </div>
          </div>

          <!-- Assistant message -->
          <div v-else class="flex gap-3">
            <div class="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0 mt-0.5">
              <svg class="w-4 h-4 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="card px-4 py-3 rounded-tl-sm">
                <div v-if="msg._streaming" class="prose-rag">
                  <span>{{ msg.content }}</span><span class="cursor-blink text-primary-500 ml-0.5">▋</span>
                </div>
                <div v-else class="prose-rag" v-html="renderMd(msg.content)"></div>
              </div>
              <!-- Sources -->
              <div v-if="msg.sources && msg.sources.length" class="mt-2">
                <button class="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                  @click="msg._showSrc = !msg._showSrc">
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                  </svg>
                  {{ msg.sources.length }} 个引用来源 {{ msg._showSrc ? '▲' : '▼' }}
                </button>
                <div v-if="msg._showSrc" class="mt-2 space-y-1.5">
                  <div v-for="src in msg.sources" :key="src.index"
                    class="flex gap-2 p-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs">
                    <span class="w-5 h-5 rounded bg-primary-100 text-primary-600 flex items-center justify-center flex-shrink-0 font-medium">
                      {{ src.index }}
                    </span>
                    <div class="min-w-0">
                      <p class="font-medium text-gray-700 truncate">{{ src.filename }}{{ src.page ? ` · 第${src.page}页` : '' }}</p>
                      <p class="text-gray-500 mt-0.5 line-clamp-2">{{ src.content }}</p>
                    </div>
                    <span class="text-gray-400 flex-shrink-0 self-start">{{ (src.score * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- Loading indicator -->
        <div v-if="thinking && !streamingMsg" class="flex gap-3">
          <div class="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <svg class="w-4 h-4 text-primary-600 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          </div>
          <div class="card px-4 py-3 text-sm text-gray-400 rounded-tl-sm">正在检索知识库...</div>
        </div>
      </div>

      <!-- Input area -->
      <div class="flex-shrink-0 border-t border-gray-100 bg-white px-4 py-3">
        <div class="flex gap-2 items-end">
          <div class="flex-1 relative">
            <textarea
              ref="inputRef"
              v-model="input"
              @keydown.enter.exact.prevent="sendMessage"
              @keydown.enter.shift.exact="() => {}"
              @input="autoResize"
              rows="1"
              placeholder="输入问题，Enter 发送，Shift+Enter 换行..."
              class="input resize-none overflow-hidden py-2.5 pr-4 text-sm leading-relaxed"
              style="min-height: 42px; max-height: 120px;"
              :disabled="thinking"
            ></textarea>
          </div>
          <button class="btn-primary h-10 px-4 flex-shrink-0" @click="sendMessage" :disabled="!input.trim() || thinking">
            <svg v-if="!thinking" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          </button>
        </div>
        <p class="text-xs text-gray-400 mt-1.5 px-1">基于知识库内容回答，答案仅供参考</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { chatApi, kbApi } from '@/api'
import { useAppStore } from '@/stores/app'
import { marked } from 'marked'

const route = useRoute()
const appStore = useAppStore()
const id = parseInt(route.params.id)

const messages = ref([])
const convs = ref([])
const activeConvId = ref(null)
const input = ref('')
const thinking = ref(false)
const streamingMsg = ref(null)
const msgContainer = ref(null)
const inputRef = ref(null)
const kbName = ref('')

marked.setOptions({ breaks: true, gfm: true })
const renderMd = (text) => marked.parse(text || '')

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

async function scrollToBottom(smooth = true) {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTo({ top: msgContainer.value.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
  }
}

function newConversation() {
  activeConvId.value = null
  messages.value = []
}

async function loadConvList() {
  try {
    const res = await chatApi.listConvs({ kb_id: id, page_size: 50 })
    convs.value = res.data.items
  } catch {}
}

async function loadConversation(convId) {
  activeConvId.value = convId
  try {
    const res = await chatApi.getMessages(convId)
    messages.value = res.data.map(m => ({ ...m, _showSrc: false }))
    await scrollToBottom(false)
  } catch {}
}

async function deleteConv(convId) {
  try {
    await chatApi.deleteConv(convId)
    if (activeConvId.value === convId) { activeConvId.value = null; messages.value = [] }
    await loadConvList()
  } catch (e) { appStore.showToast(e.message, 'error') }
}

async function sendMessage() {
  const q = input.value.trim()
  if (!q || thinking.value) return

  input.value = ''
  if (inputRef.value) { inputRef.value.style.height = '42px' }
  thinking.value = true

  // Add user message
  const tmpId = Date.now()
  messages.value.push({ _tmpId: tmpId, role: 'user', content: q })
  await scrollToBottom()

  // Add streaming placeholder
  const aiMsg = reactive({ _tmpId: tmpId + 1, role: 'assistant', content: '', sources: [], _streaming: true, _showSrc: false })
  messages.value.push(aiMsg)
  streamingMsg.value = aiMsg

  try {
    // SSE streaming
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kb_id: id, conv_id: activeConvId.value, question: q }),
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'token') {
            aiMsg.content += data.data
            await scrollToBottom()
          } else if (data.type === 'sources') {
            aiMsg.sources = data.data
          } else if (data.type === 'conv_id') {
            activeConvId.value = data.data
            await loadConvList()
          } else if (data.type === 'done') {
            aiMsg._streaming = false
            streamingMsg.value = null
          } else if (data.type === 'error') {
            aiMsg.content = `❌ ${data.data}`
            aiMsg._streaming = false
          }
        } catch {}
      }
    }
  } catch (e) {
    aiMsg.content = `❌ 请求失败: ${e.message}`
    aiMsg._streaming = false
    streamingMsg.value = null
  } finally {
    thinking.value = false
    streamingMsg.value = null
    await scrollToBottom()
  }
}

onMounted(async () => {
  try {
    const res = await kbApi.get(id)
    kbName.value = res.data.name
  } catch {}
  await loadConvList()
})
</script>
