<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import FilterBar from '@/components/FilterBar.vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { ENERGY_OPTIONS } from '@/api/adapters'
import { PALETTE, tooltipBase, gridBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'

const loading = ref(false)
const filter = reactive({ energy_type: 'all', period: 'month', start: '', end: '' })

const data = ref({ details: [], total_tce: 0, trend: { axis: [], totals: [], series: [] } })
const chartRef = ref(null)

const lastMom = computed(() => {
  const t = data.value.trend?.totals || []
  if (t.length < 2 || !t[t.length - 2]) return null
  return +(((t[t.length - 1] - t[t.length - 2]) / t[t.length - 2]) * 100).toFixed(1)
})

const columns = [
  { prop: 'energy_name', label: '能源类型', width: 120 },
  { prop: 'quantity', label: '实物量', minWidth: 140, align: 'right', formatter: (r) => Number(r.quantity || 0).toLocaleString('zh-CN') },
  { prop: 'unit', label: '单位', width: 90 },
  { prop: 'ce_tce', label: '折标煤 (tce)', minWidth: 130, align: 'right', sortable: true, formatter: (r) => Number(r.ce_tce || 0).toLocaleString('zh-CN') },
  { prop: 'share', label: '占比', minWidth: 110, align: 'right', formatter: (r) => `${Number(r.share || 0).toFixed(2)}%` }
]

function renderChart(trend) {
  if (!trend?.axis?.length || !chartRef.value) return
  chartRef.value.setOption({
    color: PALETTE,
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, textStyle: { color: '#55655f', fontSize: 12 } },
    grid: gridBase,
    xAxis: { type: 'category', data: trend.axis, axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    yAxis: { type: 'value', name: 'tce', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: trend.series.map((s) => ({
      name: s.name,
      type: 'bar',
      stack: 'total',
      barWidth: '46%',
      emphasis: { focus: 'series' },
      data: s.data
    }))
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.energyConsumption({ ...filter })
    renderChart(data.value.trend)
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(filter, { energy_type: 'all', period: 'month', start: '', end: '' })
  load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>能耗查询</h2>
        <p>煤炭、电力、天然气、蒸汽等多能源实时查询与历史追溯 · 折标依据 GB/T 2589</p>
      </div>
    </div>

    <FilterBar @query="load" @reset="reset">
      <span class="field-label">能源类型</span>
      <el-select v-model="filter.energy_type" placeholder="全部" style="width: 130px">
        <el-option v-for="t in ENERGY_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <span class="field-label">统计周期</span>
      <el-select v-model="filter.period">
        <el-option label="月度" value="month" />
        <el-option label="年度" value="year" />
      </el-select>
      <span class="field-label">起止</span>
      <el-date-picker
        v-model="filter.start"
        :type="filter.period === 'year' ? 'year' : 'month'"
        placeholder="开始"
        value-format="YYYY-MM"
        style="width: 130px"
      />
      <span style="color: var(--ink-3)">—</span>
      <el-date-picker
        v-model="filter.end"
        :type="filter.period === 'year' ? 'year' : 'month'"
        placeholder="结束"
        value-format="YYYY-MM"
        style="width: 130px"
      />
    </FilterBar>

    <div class="kpi-grid">
      <KpiCard label="折标煤合计" :value="data.total_tce" unit="tce" :decimals="2" accent="brand" sub="各能源折标合计" />
      <KpiCard label="能源品类数" :value="data.details.length" unit="种" :decimals="0" accent="blue" />
      <KpiCard
        label="最大能耗能源"
        :value="data.details[0]?.energy_name || '--'"
        :decimals="0"
        accent="amber"
        :sub="data.details[0] ? `${data.details[0].ce_tce.toLocaleString('zh-CN')} tce` : ''"
      />
      <KpiCard
        label="最新一期折标煤"
        :value="data.trend.totals.length ? data.trend.totals[data.trend.totals.length - 1] : '--'"
        unit="tce"
        :decimals="2"
        accent="violet"
        :trend="lastMom"
        :sub="data.trend.axis.length ? `期次 ${data.trend.axis[data.trend.axis.length - 1]}` : ''"
      />
    </div>

    <ChartCard ref="chartRef" title="能耗趋势" desc="分能源折标煤堆叠 · 单位 tce" :loading="loading" height="330px" />

    <DataTable
      title="分能源用量明细"
      :columns="columns"
      :data="data.details"
      :loading="loading"
      max-height="420"
      show-index
    >
      <template #extra>
        <span style="font-size: 12px; color: var(--ink-3)">共 {{ data.details.length }} 条记录</span>
      </template>
    </DataTable>
  </div>
</template>
