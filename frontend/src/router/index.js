import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/kb' },
    { path: '/kb', component: () => import('@/views/KbList.vue'), meta: { title: '知识库' } },
    { path: '/kb/:id', component: () => import('@/views/KbDetail.vue'), meta: { title: '知识库详情' } },
    { path: '/kb/:id/chat', component: () => import('@/views/ChatView.vue'), meta: { title: '对话' } },
    { path: '/kb/:id/docs', component: () => import('@/views/DocList.vue'), meta: { title: '文档管理' } },
  ]
})
