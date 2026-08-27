import { ref, onUnmounted } from 'vue'

/**
 * 通用轮询组合式函数
 * - interval 轮询间隔（ms）
 * - 页面隐藏（document.visibilitychange）时暂停，可见时立即恢复
 * - 任务失败按指数退避重试：interval * 2^n，上限 backoffCap
 * - onUnmounted 自动清理
 *
 * @param {() => Promise<any>} task 轮询任务
 * @param {{interval?: number, immediate?: boolean, backoffCap?: number}} options
 */
export function usePolling(task, options = {}) {
  const { interval = 10000, immediate = true, backoffCap = 120000 } = options

  const loading = ref(false)
  let timer = null
  let running = false
  let stopped = false
  let failures = 0

  function nextDelay() {
    if (failures === 0) return interval
    return Math.min(interval * 2 ** (failures - 1), backoffCap)
  }

  function schedule(delay) {
    if (stopped || timer !== null) return
    timer = setTimeout(() => {
      timer = null
      tick()
    }, delay)
  }

  async function tick() {
    if (stopped || running || document.hidden) return
    running = true
    loading.value = true
    try {
      await task()
      failures = 0
    } catch (e) {
      failures += 1
    } finally {
      running = false
      loading.value = false
      schedule(nextDelay())
    }
  }

  function onVisibility() {
    if (stopped) return
    if (document.hidden) {
      // 隐藏：取消未触发的定时器，暂停轮询
      if (timer !== null) {
        clearTimeout(timer)
        timer = null
      }
    } else {
      // 恢复可见：立即执行一次
      tick()
    }
  }

  function start() {
    stopped = false
    // 先移除再添加，避免重复调用 start()/restart 时重复注册监听器
    document.removeEventListener('visibilitychange', onVisibility)
    document.addEventListener('visibilitychange', onVisibility)
    if (immediate) {
      tick()
    } else {
      schedule(interval)
    }
  }

  function stop() {
    stopped = true
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
    document.removeEventListener('visibilitychange', onVisibility)
  }

  onUnmounted(stop)
  start()

  return { loading, stop, restart: start }
}
