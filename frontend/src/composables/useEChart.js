import { onBeforeUnmount, onMounted } from 'vue'
import echarts from '@/utils/charts'

/**
 * 统一的 ECharts 生命周期管理：
 * - onMounted 时初始化实例
 * - ResizeObserver 监听容器尺寸变化自动 resize
 * - onBeforeUnmount 时断开观察并 dispose
 * @param {import('vue').Ref<HTMLElement|null>} elRef 容器元素 ref
 * @param {{dark?: boolean}} options dark 用于大屏深色初始化
 */
export function useEChart(elRef, options = {}) {
  let chart = null
  let observer = null

  function ensure() {
    if (!chart && elRef.value) {
      chart = echarts.init(elRef.value, undefined, { renderer: 'canvas' })
      chart.setOption({ backgroundColor: 'transparent' })
    }
    return chart
  }

  onMounted(() => {
    ensure()
    if (typeof ResizeObserver !== 'undefined' && elRef.value) {
      observer = new ResizeObserver(() => {
        chart && !chart.isDisposed() && chart.resize()
      })
      observer.observe(elRef.value)
    }
  })

  /** 全量替换式 setOption（notMerge），适合轮询刷新 */
  function setOption(option) {
    const inst = ensure()
    inst && inst.setOption(option, true)
  }

  function getInstance() {
    return ensure()
  }

  onBeforeUnmount(() => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
    if (chart) {
      chart.dispose()
      chart = null
    }
  })

  return { setOption, getInstance }
}
