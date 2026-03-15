import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail
    let message: string
    if (Array.isArray(detail)) {
      message = detail.map((e: { msg?: string }) => e.msg || String(e)).join('; ')
    } else if (detail && typeof detail === 'object') {
      message = JSON.stringify(detail)
    } else {
      message = detail || error.response?.data?.message || error.message || 'Произошла ошибка'
    }
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default client
