import axios from 'axios'
import { ElMessage } from 'element-plus'
import { isMockEnabled, handleMock } from './mock'

/**
 * 统一响应体：{ code: 0, message: "ok", data: ... }
 * 拦截器统一解包；code != 0 时弹出 ElMessage 错误并 reject。
 */
const client = axios.create({
  baseURL: '/api/v1',
  timeout: 15000
})

const xhrAdapter = axios.getAdapter('xhr')

// mock 模式：命中 mock 路由时直接返回模拟响应，未命中仍走真实请求，
// 不影响真实请求路径（开关见 ./mock，localStorage['ecms.mock'] = '1' 开启）。
client.defaults.adapter = async (config) => {
  if (isMockEnabled()) {
    const mocked = await handleMock(config)
    if (mocked) return mocked
  }
  return xhrAdapter(config)
}

client.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) {
        return body.data
      }
      ElMessage.error(body.message || '服务返回异常')
      return Promise.reject(new Error(body.message || `biz error: code=${body.code}`))
    }
    return body
  },
  (error) => {
    const msg =
      error?.response?.data?.message ||
      (error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络请求失败，请检查后端服务')
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default client
