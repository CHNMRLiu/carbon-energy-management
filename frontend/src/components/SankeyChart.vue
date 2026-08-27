<script setup>
import { ref, watch } from 'vue'
import { useEChart } from '@/composables/useEChart'
import { tooltipBase, PALETTE } from '@/utils/charts'

const props = defineProps({
  /** [{ name }] */
  nodes: { type: Array, default: () => [] },
  /** [{ source, target, value }] */
  links: { type: Array, default: () => [] },
  height: { type: String, default: '460px' },
  unit: { type: String, default: 'tce' },
  loading: { type: Boolean, default: false }
})

const boxRef = ref(null)
const { setOption } = useEChart(boxRef)

function render() {
  if (!props.nodes?.length) return
  setOption({
    color: PALETTE,
    tooltip: {
      ...tooltipBase,
      trigger: 'item',
      formatter: (p) =>
        p.dataType === 'edge'
          ? `${p.data.source} → ${p.data.target}<br/><b>${Number(p.data.value).toLocaleString('zh-CN')} ${props.unit}</b>`
          : `${p.name}<br/><b>${Number(p.value).toLocaleString('zh-CN')} ${props.unit}</b>`
    },
    series: [
      {
        type: 'sankey',
        data: props.nodes.map((n) => ({ ...n })),
        links: props.links.map((l) => ({ ...l })),
        nodeAlign: 'justify',
        nodeWidth: 14,
        nodeGap: 12,
        left: 12,
        right: 120,
        top: 12,
        bottom: 12,
        emphasis: { focus: 'adjacency' },
        lineStyle: { color: 'gradient', curveness: 0.55, opacity: 0.42 },
        itemStyle: { borderWidth: 0, borderRadius: 3 },
        label: { color: '#16241f', fontSize: 12, fontWeight: 600 },
        levels: [
          { depth: 0, itemStyle: { color: '#0c8f7a' }, lineStyle: { opacity: 0.35 } },
          { depth: 1, itemStyle: { color: '#2f6fed' }, lineStyle: { opacity: 0.35 } },
          { depth: 2, itemStyle: { color: '#d9912b' }, lineStyle: { opacity: 0.35 } },
          { depth: 3, itemStyle: { color: '#37b26a' }, lineStyle: { opacity: 0.35 } },
          { depth: 4, itemStyle: { color: '#8b988f' }, lineStyle: { opacity: 0.35 } }
        ]
      }
    ]
  })
}

watch(() => [props.nodes, props.links], render, { immediate: true, deep: false })
</script>

<template>
  <div class="sankey-wrap" v-loading="loading">
    <div ref="boxRef" class="sankey-box" :style="{ height }"></div>
    <div v-if="!nodes?.length && !loading" class="sankey-empty">暂无能流数据</div>
  </div>
</template>

<style scoped>
.sankey-wrap { position: relative; }
.sankey-box { width: 100%; }
.sankey-empty {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  color: var(--ink-3); font-size: 13px;
}
</style>
