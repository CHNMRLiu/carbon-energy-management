<script setup>
import { onMounted, reactive, ref } from 'vue'
import FilterBar from '@/components/FilterBar.vue'
import ChartCard from '@/components/ChartCard.vue'
import KpiCard from '@/components/KpiCard.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, gridBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const filter = reactive({ 
  point_code: '', 
  period: 'day',
  dimension: 'energy'
})

const data = ref({})
const chartRef = ref(null)
const meterPoints = ref([])

const PERIOD_OPTIONS = [
  { value: 'day', label: '日' },
  { value: 'week', label: '周' },
  { value: 'month', label: '月' },
  { value: 'year', label: '年' }
]

const DIMENSION_OPTIONS = [
  { value: 'energy', label: '能耗 (折标煤)' },
  { value: 'cost', label: '成本' },
  { value: 'carbon', label: '碳排放' }
]

function renderChart() {
  const d = data.value
  if (!d.data?.length || !chartRef.value) return
  
  chartRef.value.setOption({
    color: [PALETTE[0]],
    tooltip: { ...tooltipBase, trigger: 'axis' },
    grid: gridBase,
    xAxis: { 
      type: 'category', 
      data: d.data.map(item => item.time), 
      axisLabel: axisLabelStyle, 
      axisLine: axisLineStyle, 
      axisTick: { show: false } 
    },
    yAxis: { 
      type: 'value', 
      name: d.data[0]?.unit || '',
      nameTextStyle: { color: '#8b988f' }, 
      axisLabel: axisLabelStyle, 
      splitLine: splitLineStyle 
    },
    series: [
      {
        name: d.dimension === 'energy' ? '折标煤' : (d.dimension === 'cost' ? '成本' : '碳排放'),
        type: 'line',
        smooth: true,
        symbolSize: 6,
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(12,143,122,0.25)' },
              { offset: 1, color: 'rgba(12,143,122,0)' }
            ]
          }
        },
        data: d.data.map(item => item.value)
      }
    ]
  })
}

async function loadMeterPoints() {
  try {
    const res = await api.ingestPoints()
    meterPoints.value = res.items || []
    if (meterPoints.value.length > 0) {
      filter.point_code = meterPoints.value[0].code
    }
  } catch (e) {
    /* 拦截器已提示 */
  }
}

async function load() {
  if (!filter.point_code) {
    ElMessage.warning('请选择计量点')
    return
  }
  
  loading.value = true
  try {
    data.value = await api.meterCurve({ ...filter })
    renderChart()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.assign(filter, { 
    point_code: meterPoints.value[0]?.code || '', 
    period: 'day',
    dimension: 'energy'
  })
  load()
}

onMounted(() => {
  loadMeterPoints()
  load()
})
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>单器具曲线查询</h2>
        <p>单个计量器具消耗曲线 · 支持日/周/月/年周期 · 能耗/成本/碳排三维度</p>
      </div>
    </div>

    <FilterBar @query="load" @reset="reset">
      <span class="field-label">计量点</span>
      <el-select v-model="filter.point_code" placeholder="选择计量点" filterable style="width: 200px">
        <el-option 
          v-for="p in meterPoints" 
          :key="p.code" 
          :label="`${p.code} · ${p.name}`" 
          :value="p.code" 
        />
      </el-select>
      
      <span class="field-label">统计周期</span>
      <el-select v-model="filter.period" style="width: 100px">
        <el-option v-for="opt in PERIOD_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
      
      <span class="field-label">统计维度</span>
      <el-select v-model="filter.dimension" style="width: 160px">
        <el-option v-for="opt in DIMENSION_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </FilterBar>

    <div class="kpi-grid">
      <KpiCard 
        label="计量点名称" 
        :value="data.point_name || '--'" 
        :decimals="0" 
        accent="brand" 
      />
      <KpiCard 
        label="能源类型" 
        :value="data.energy_name || '--'" 
        :decimals="0" 
        accent="blue" 
      />
      <KpiCard 
        label="最新值" 
        :value="data.data?.[data.data.length - 1]?.value ?? '--'" 
        :unit="data.data?.[0]?.unit || ''" 
        :decimals="2" 
        accent="amber" 
      />
      <KpiCard 
        label="数据点数" 
        :value="data.data?.length ?? 0" 
        unit="个" 
        :decimals="0" 
        accent="violet" 
      />
    </div>

    <ChartCard 
      ref="chartRef" 
      title="消耗趋势曲线" 
      :desc="`周期：${filter.period === 'day' ? '日' : filter.period === 'week' ? '周' : filter.period === 'month' ? '月' : '年'} · 维度：${filter.dimension === 'energy' ? '折标煤' : filter.dimension === 'cost' ? '成本' : '碳排放'}`" 
      :loading="loading" 
      height="350px" 
    />
  </div>
</template>
