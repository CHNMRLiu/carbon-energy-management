<script setup>
import { computed, onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'

const loading = ref(false)
const data = ref({})
const direction = ref('upstream')
const chartRef = ref(null)

const rows = computed(() => data.value[direction.value] || [])
const allPartners = computed(() => [...(data.value.upstream || []), ...(data.value.downstream || [])])
const totalChainEmission = computed(() => allPartners.value.reduce((s, r) => s + r.emission, 0))

const columns = [
  { prop: 'name', label: '企业名称', minWidth: 170 },
  { prop: 'scope', label: '业务环节', width: 160 },
  { prop: 'product', label: '产品/服务', width: 130 },
  { prop: 'emission', label: '碳排放 (tCO₂)', minWidth: 150, align: 'right', sortable: true, formatter: (r) => Number(r.emission || 0).toLocaleString('zh-CN') },
  { prop: 'period', label: '数据期间', width: 110 },
  { prop: 'dataQuality', label: '数据状态', width: 110, align: 'center', slot: true }
]

const QUALITY_TYPE = { 已核查: 'success', 已上报: 'primary', 待上报: 'info' }

function renderChart(top) {
  if (!top?.length || !chartRef.value) return
  chartRef.value.setOption({
    color: [PALETTE[4]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 12, right: 40, top: 20, bottom: 8, containLabel: true },
    xAxis: { type: 'value', name: 'tCO₂', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    yAxis: { type: 'category', data: [...top].reverse().map((t) => t.name), axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    series: [
      {
        name: '排放量',
        type: 'bar',
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: {
            type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: 'rgba(124,92,255,0.3)' },
              { offset: 1, color: '#7c5cff' }
            ]
          }
        },
        label: { show: true, position: 'right', formatter: '{c}', color: '#55655f', fontSize: 11 },
        data: [...top].reverse().map((t) => Number(t.value || 0))
      }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.carbonSupplyChain()
    renderChart(data.value.topEmitters)
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
        <h2>供应链碳管理</h2>
        <p>上下游企业碳数据采集、核算与足迹共享，支撑范围三排放管理</p>
      </div>
      <el-radio-group v-model="direction">
        <el-radio-button value="upstream">上游供应商</el-radio-button>
        <el-radio-button value="downstream">下游客户</el-radio-button>
      </el-radio-group>
    </div>

    <div class="kpi-grid">
      <KpiCard label="链上企业数" :value="data.summary?.total ?? allPartners.length" unit="家" :decimals="0" accent="brand" />
      <KpiCard label="供应链总排放" :value="totalChainEmission.toFixed(0)" unit="tCO₂" :decimals="0" accent="danger" />
      <KpiCard label="上游排放小计" :value="data.summary?.upstream_total ?? 0" unit="tCO₂" :decimals="0" accent="blue" :sub="`上游企业 ${data.upstream?.length ?? 0} 家`" />
      <KpiCard label="已核查数据" :value="data.summary?.verified_count ?? 0" unit="家" :decimals="0" accent="violet" :sub="`下游企业 ${data.downstream?.length ?? 0} 家`" />
    </div>

    <ChartCard ref="chartRef" title="链上企业排放 TOP5" desc="单位 tCO₂" :loading="loading" height="300px" />

    <DataTable :title="direction === 'upstream' ? '上游供应商碳数据' : '下游客户碳数据'" :columns="columns" :data="rows" :loading="loading" show-index>
      <template #col-dataQuality="{ row }">
        <el-tag :type="QUALITY_TYPE[row.dataQuality] || 'info'" size="small" effect="light">{{ row.dataQuality }}</el-tag>
      </template>
    </DataTable>
  </div>
</template>
