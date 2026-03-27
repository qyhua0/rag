import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

http.interceptors.response.use(
  res => res.data,
  err => {
    const msg = err.response?.data?.detail || err.response?.data?.message || err.message
    return Promise.reject(new Error(msg))
  }
)

// Knowledge Base
export const kbApi = {
  list: (p) => http.get('/kb', { params: p }),
  get:  (id) => http.get(`/kb/${id}`),
  create: (d) => http.post('/kb', d),
  update: (id, d) => http.put(`/kb/${id}`, d),
  delete: (id) => http.delete(`/kb/${id}`),
}

// Document
export const docApi = {
  list:   (p) => http.get('/doc', { params: p }),
  get:    (id) => http.get(`/doc/${id}`),
  delete: (id) => http.delete(`/doc/${id}`),
  reprocess: (id) => http.post(`/doc/${id}/reprocess`),
  upload: (formData, onProgress) => http.post('/doc/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => onProgress && onProgress(Math.round(e.loaded / e.total * 100)),
  }),
  importPath: (d) => http.post('/doc/import-path', d),
}

// Chat
export const chatApi = {
  listConvs:  (p) => http.get('/chat/conversations', { params: p }),
  getMessages: (id) => http.get(`/chat/conversations/${id}/messages`),
  deleteConv: (id) => http.delete(`/chat/conversations/${id}`),
  send: (d) => http.post('/chat/send', d),
}

// System
export const sysApi = {
  health: () => http.get('/system/health'),
  models: () => http.get('/system/models'),
}

export default http
