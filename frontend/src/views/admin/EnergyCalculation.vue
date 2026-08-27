<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import FilterBar from '@/components/FilterBar.vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, gridBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'

const loading = ref(false)
const filter = reactive({ period: 'month' })

const data = ref({})
const chartRef = ref(null)

const columns = [
  { prop: 'name', label: '指标', minWidth: 160 },
  { prop: 'value', label: '本期值', minWidth: 130, align: 'right', formatter: (r) => Number(r.value || 0).toLocaleString('zh-CN') },
  { prop: 'unit', label: '单位', width: 110 },
  { prop: 'yoy', label: '同比 (%)', width: 120, align: 'right', formatter: (r) => (r.yoy === null ? '--' : `${r.yoy > 0 ? '+' : ''}${r.yoy.toFixed(2)}`) },
  { prop: 'mom', label: '环比 (%)', width: 120, align: 'right', formatter: (r) => (r.mom === null ? '--' : `${r.mom > 0 ? '+' : ''}${r.mom.toFixed(2)}`) }
]

const rows = computed(() => {
  const d = data.value
  return [
    { name: '综合能耗', ...(d.comprehensive || {}) },
    { name: '单位产品能耗', ...(d.unitProduct || {}) },
    { name: '单位产值能耗', ...(d.unitOutput || {}) }
  ].map((r) => ({ value: r.value ?? 0, unit: '', yoy: null, mom: null, ...r }))
})

/** 由同比/环比反推上期值，绘制本期/上期/同期对比柱状图 */
const compare = computed(() => {
  const c = data.value.comprehensive
  if (!c) return { axis: [], data: [] }
  const axis = []
  const vals = []
  if (c.yoy !== null && c.yoy !== undefined && data.value.compare_labels?.yoy) {
    axis.push(`同期 ${data.value.compare_labels.yoy}`)
    vals.push(+(c.value / (1 + c.yoy / 100)).toFixed(2))
  }
  if (c.mom !== null && c.mom !== undefined && data.value.compare_labels?.mom) {
    axis.push(`上期 ${data.value.compare_labels.mom}`)
    vals.push(+(c.value / (1 + c.mom / 100)).toFixed(2))
  }
  axis.push(`本期 ${data.value.current_period || ''}`)
  vals.push(c.value)
  return { axis, data: vals }
})

function renderChart() {
  const cmp = compare.value
  if (!cmp.axis.length || !chartRef.value) return
  chartRef.value.setOption({
    color: [PALETTE[0]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: gridBase,
    xAxis: { type: 'category', data: cmp.axis, axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    yAxis: { type: 'value', name: 'tce', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      {
        name: '综合能耗',
        type: 'bar',
        barWidth: 40,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#0c8f7a' },
              { offset: 1, color: 'rgba(12,143,122,0.18)' }
            ]
          }
        },
        label: { show: true, position: 'top', color: '#55655f', fontSize: 12 },
        data: cmp.data
      }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.energyCalculation({ period: filter.period })
    renderChart()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function reset() {
  filter.period = 'month'
  load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>能耗计算</h2>
        <p>综合能耗、单位产品能耗、单位产值能耗 · 严格遵循 GB/T 2589《综合能耗计算通则》</p>
      </div>
    </div>

    <FilterBar @query="load" @reset="reset">
      <span class="field-label">统计周期</span>
      <el-select v-model="filter.period">
        <el-option label="月度" value="month" />
        <el-option label="年度" value="year" />
      </el-select>
    </FilterBar>

    <div class="kpi-grid">
      <KpiCard
        label="综合能耗"
        :value="data.comprehensive?.value ?? '--'"
        :unit="data.comprehensive?.unit || 'tce'"
        :trend="data.comprehensive?.yoy ?? null"
        :sub="`环比 ${data.comprehensive?.mom ?? '--'}%`"
        accent="brand"
      />
      <KpiCard
        label="单位产品能耗"
        :value="data.unitProduct?.value ?? '--'"
        :unit="data.unitProduct?.unit || 'kgce/t'"
        :decimals="2"
        :trend="data.unitProduct?.yoy ?? null"
        :sub="`环比 ${data.unitProduct?.mom ?? '--'}%`"
        accent="blue"
      />
      <KpiCard
        label="单位产值能耗"
        :value="data.unitOutput?.value ?? '--'"
        :unit="data.unitOutput?.unit || 'tce/万元'"
        :decimals="4"
        :trend="data.unitOutput?.yoy ?? null"
        :sub="`环比 ${data.unitOutput?.mom ?? '--'}%`"
        accent="amber"
      />
      <KpiCard label="本期产量" :value="data.output?.output_t ?? '--'" unit="t" accent="violet" :sub="`期次 ${data.current_period || '--'}`" />
      <KpiCard label="本期产值" :value="data.output?.output_value_wan ?? '--'" unit="万元" accent="danger" />
    </div>
    
    <ChartCard ref="chartRef" title="综合能耗对比" desc="本期与同期/上期对比（同比环比反推）· 单位 tce" :loading="loading" height="320px" />
    
    <DataTable
      title="核算指标对比明细"
      :columns="columns"
      :data="rows"
      :loading="loading"
      show-index
    >
      <template #footer>
        折标煤 = Σ(各能源实物量 × 折标系数)，系数执行 GB/T 2589-2020 当量值口径；同比/环比由后端基于月度汇总数据计算。
      </template>
    </DataTable>
  </div>
</template>
