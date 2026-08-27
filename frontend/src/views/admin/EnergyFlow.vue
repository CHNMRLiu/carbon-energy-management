<script setup>
import { computed, onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import SankeyChart from '@/components/SankeyChart.vue'
import { api } from '@/api'

const loading = ref(false)
const flow = ref({ nodes: [], links: [] })

const columns = [
  { prop: 'source', label: '来源节点', minWidth: 150 },
  { prop: 'target', label: '去向节点', minWidth: 150 },
  { prop: 'value', label: '流量 (tce)', minWidth: 130, align: 'right', sortable: true, formatter: (r) => Number(r.value).toLocaleString('zh-CN') }
]

const stats = computed(() => {
  const links = flow.value.links || []
  const targets = new Set(links.map((l) => l.target))
  const sources = new Set(links.map((l) => l.source))
  // 输入：不出现在任何 link 目标中的节点
  const input = links.filter((l) => !targets.has(l.source)).reduce((s, l) => s + l.value, 0)
  const loss = links.filter((l) => /损/.test(l.target)).reduce((s, l) => s + l.value, 0)
  const used = links.filter((l) => /有效|利用/.test(l.target)).reduce((s, l) => s + l.value, 0)
  const efficiency = input > 0 ? ((input - loss) / input) * 100 : 0
  return { input, loss, used, efficiency }
})

async function load() {
  loading.value = true
  try {
    flow.value = await api.energyFlow()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>能流分析</h2>
        <p>能源输入 → 转换 → 分配 → 利用全过程桑基图展示 · 单位 tce</p>
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="能源输入总量" :value="stats.input" unit="tce" accent="brand" />
      <KpiCard label="有效利用量" :value="stats.used" unit="tce" accent="blue" />
      <KpiCard label="损耗量" :value="stats.loss" unit="tce" accent="danger" />
      <KpiCard label="综合能源效率" :value="stats.efficiency.toFixed(1)" unit="%" accent="amber" :good-when-down="false" />
    </div>

    <ChartCard title="全厂能流桑基图" desc="悬停节点可高亮关联路径" :loading="loading" height="520px">
      <SankeyChart :nodes="flow.nodes" :links="flow.links" :loading="loading" height="470px" unit="tce" />
    </ChartCard>

    <DataTable title="能流明细（支路流量）" :columns="columns" :data="flow.links || []" :loading="loading" max-height="400" show-index />
  </div>
</template>
