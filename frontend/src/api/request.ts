import axios from 'axios'
import { getToken, clearSession } from '../auth'

const api = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器：自动附加 JWT Bearer Token（SEC-001 前端配套）
api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token 缺失或失效：清除会话并跳转到登录页
      clearSession()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (!error.response || error.response.status === 502) {
      // 后端不可用时静默处理
      console.warn('[API] Backend service unavailable')
    }
    return Promise.reject(error)
  }
)

// Type-safe wrapper: interceptor unwraps AxiosResponse, so .get/.post return data directly
const typedApi = {
  get: <T = any>(url: string, config?: any): Promise<T> => api.get(url, config),
  post: <T = any>(url: string, data?: any, config?: any): Promise<T> => api.post(url, data, config),
  put: <T = any>(url: string, data?: any, config?: any): Promise<T> => api.put(url, data, config),
  delete: <T = any>(url: string, config?: any): Promise<T> => api.delete(url, config)
}

export default typedApi
