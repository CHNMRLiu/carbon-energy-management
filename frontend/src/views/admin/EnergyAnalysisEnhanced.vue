<script setup>
import { onMounted, reactive, ref } from 'vue'
import ChartCard from '@/components/ChartCard.vue'
import KpiCard from '@/components/KpiCard.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, gridBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'
import { ElMessage, ElSelect, ElOption } from 'element-plus'

const loading = ref(false)
const activeTab = ref('meter-comparison') // meter-comparison | meter-trend | unit-comparison

// 计量对标状态
const meterComparisonFilter = reactive({
  meter1_id: '',
  meter2_id: '',
  period: 'month'
})
const meterComparisonData = ref(null)
const meterComparisonChartRef = ref(null)

// 计量环比状态
const meterTrendFilter = reactive({
  meter_id: '',
  period_type: 'month-over-month'
})
const meterTrendData = ref(null)

// 单元对标状态
const unitComparisonFilter = reactive({
  unit1_code: '',
  unit2_code: '',
  period: 'month'
})
const unitComparisonData = ref(null)
const unitComparisonChartRef = ref(null)

// 模拟计量点列表（实际应从 API 获取）
const meterPoints = ref([
  { id: 1, code: 'M001', name: '总进线电表', energy_code: 'electricity' },
  { id: 2, code: 'M002', name: '车间A电表', energy_code: 'electricity' },
  { id: 3, code: 'M003', name: '蒸汽流量计', energy_code: 'steam' },
  { id: 4, code: 'M004', name: '天然气表', energy_code: 'gas' }
])

// 用能单元列表
const units = ref([
  { code: 'ORG001', name: '生产车间A' },
  { code: 'ORG002', name: '生产车间B' },
  { code: 'ORG003', name: '办公楼' }
])

const PERIOD_OPTIONS = [
  { value: 'day', label: '日' },
  { value: 'week', label: '周' },
  { value: 'month', label: '月' },
  { value: 'year', label: '年' }
]

const TREND_TYPE_OPTIONS = [
  { value: 'month-over-month', label: '环比（本月 vs 上月）' },
  { value: 'year-over-year', label: '同比（今年 vs 去年）' }
]

// 渲染计量对标图表
function renderMeterComparisonChart() {
  const d = meterComparisonData.value
  if (!d || !meterComparisonChartRef.value) return
  
  const chart = meterComparisonChartRef.value
  chart.setOption({
    color: [PALETTE[0], PALETTE[1]],
    tooltip: { ...tooltipBase, trigger: 'axis' },
    legend: { top: 0, textStyle: { color: '#55655f' } },
    grid: { left: 12, right: 20, top: 40, bottom: 8, containLabel: true },
    xAxis: { 
      type: 'category', 
      data: d.comparison.time_labels,
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
      axisTick: { show: false }
    },
    yAxis: { 
      type: 'value',
      name: d.meter1.unit,
      axisLabel: axisLabelStyle,
      splitLine: splitLineStyle
    },
    series: [
      {
        name: d.meter1.name,
        type: 'line',
        smooth: true,
        symbolSize: 6,
        data: d.meter1.series
      },
      {
        name: d.meter2.name,
        type: 'line',
        smooth: true,
        symbolSize: 6,
        data: d.meter2.series
      }
    ]
  })
}

// 渲染单元对标图表
function renderUnitComparisonChart() {
  const d = unitComparisonData.value
  if (!d || !unitComparisonChartRef.value) return
  
  const allEnergies = new Set()
  d.unit1.details.forEach(x => allEnergies.add(x.energy_code))
  d.unit2.details.forEach(x => allEnergies.add(x.energy_code))
  
  const chart = unitComparisonChartRef.value
  chart.setOption({
    color: [PALETTE[0], PALETTE[1]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, textStyle: { color: '#55655f' } },
    grid: { left: 12, right: 20, top: 40, bottom: 8, containLabel: true },
    xAxis: { 
      type: 'category',
      data: Array.from(allEnergies).map(code => {
        const e1 = d.unit1.details.find(x => x.energy_code === code)
        return e1 ? e1.energy_name : code
      }),
      axisLabel: { ...axisLabelStyle, rotate: 30 },
      axisLine: axisLineStyle,
      axisTick: { show: false }
    },
    yAxis: { 
      type: 'value',
      name: 'tce',
      axisLabel: axisLabelStyle,
      splitLine: splitLineStyle
    },
    series: [
      {
        name: d.unit1.name,
        type: 'bar',
        barMaxWidth: 40,
        data: Array.from(allEnergies).map(code => {
          const e = d.unit1.details.find(x => x.energy_code === code)
          return e ? e.ce_tce : 0
        })
      },
      {
        name: d.unit2.name,
        type: 'bar',
        barMaxWidth: 40,
        data: Array.from(allEnergies).map(code => {
          const e = d.unit2.details.find(x => x.energy_code === code)
          return e ? e.ce_tce : 0
        })
      }
    ]
  })
}

// 加载计量对标数据
async function loadMeterComparison() {
  if (!meterComparisonFilter.meter1_id || !meterComparisonFilter.meter2_id) {
    ElMessage.warning('请选择两个计量点')
    return
  }
  
  loading.value = true
  try {
    meterComparisonData.value = await api.meterComparison({
      meter1_id: meterComparisonFilter.meter1_id,
      meter2_id: meterComparisonFilter.meter2_id,
      period: meterComparisonFilter.period
    })
    setTimeout(renderMeterComparisonChart, 100)
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 加载计量环比数据
async function loadMeterTrend() {
  if (!meterTrendFilter.meter_id) {
    ElMessage.warning('请选择计量点')
    return
  }
  
  loading.value = true
  try {
    meterTrendData.value = await api.meterTrend({
      meter_id: meterTrendFilter.meter_id,
      period: meterTrendFilter.period_type
    })
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 加载单元对标数据
async function loadUnitComparison() {
  if (!unitComparisonFilter.unit1_code || !unitComparisonFilter.unit2_code) {
    ElMessage.warning('请选择两个用能单元')
    return
  }
  
  loading.value = true
  try {
    unitComparisonData.value = await api.unitComparison({
      unit1_code: unitComparisonFilter.unit1_code,
      unit2_code: unitComparisonFilter.unit2_code,
      period: unitComparisonFilter.period
    })
    setTimeout(renderUnitComparisonChart, 100)
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 默认加载一次
})
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>能源分析增强</h2>
        <p>计量对标、计量环比、单元对标三维对比分析</p>
      </div>
    </div>

    <!-- 标签切换 -->
    <div class="tabs" style="margin-bottom: 20px;">
      <el-radio-group v-model="activeTab" size="large">
        <el-radio-button value="meter-comparison">计量对标</el-radio-button>
        <el-radio-button value="meter-trend">计量环比</el-radio-button>
        <el-radio-button value="unit-comparison">单元对标</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 计量对标 -->
    <div v-if="activeTab === 'meter-comparison'" class="section">
      <div class="filter-bar" style="margin-bottom: 16px;">
        <el-select v-model="meterComparisonFilter.meter1_id" placeholder="选择计量点1" style="width: 200px; margin-right: 12px;">
          <el-option v-for="m in meterPoints" :key="m.id" :label="m.name" :value="m.id" />
        </el-select>
        <el-select v-model="meterComparisonFilter.meter2_id" placeholder="选择计量点2" style="width: 200px; margin-right: 12px;">
          <el-option v-for="m in meterPoints" :key="m.id" :label="m.name" :value="m.id" />
        </el-select>
        <el-select v-model="meterComparisonFilter.period" placeholder="周期" style="width: 120px; margin-right: 12px;">
          <el-option v-for="p in PERIOD_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
        </el-select>
        <el-button type="primary" @click="loadMeterComparison" :loading="loading">查询</el-button>
      </div>

      <div v-if="meterComparisonData" class="kpi-grid">
        <KpiCard 
          :label="meterComparisonData.meter1.name" 
          :value="meterComparisonData.meter1.total" 
          :unit="meterComparisonData.meter1.unit" 
          :decimals="2" 
          accent="brand" 
        />
        <KpiCard 
          :label="meterComparisonData.meter2.name" 
          :value="meterComparisonData.meter2.total" 
          :unit="meterComparisonData.meter2.unit" 
          :decimals="2" 
          accent="amber" 
        />
        <KpiCard 
          label="差值" 
          :value="Math.abs(meterComparisonData.comparison.difference)" 
          :unit="meterComparisonData.meter1.unit" 
          :decimals="2" 
          accent="blue" 
        />
        <KpiCard 
          label="差异比例" 
          :value="meterComparisonData.comparison.diff_percent" 
          unit="%" 
          :decimals="2" 
          accent="violet" 
        />
      </div>

      <ChartCard 
        ref="meterComparisonChartRef" 
        title="计量对标趋势对比" 
        desc="两计量器具同时段用量对比" 
        :loading="loading" 
        height="350px" 
      />
    </div>

    <!-- 计量环比 -->
    <div v-if="activeTab === 'meter-trend'" class="section">
      <div class="filter-bar" style="margin-bottom: 16px;">
        <el-select v-model="meterTrendFilter.meter_id" placeholder="选择计量点" style="width: 200px; margin-right: 12px;">
          <el-option v-for="m in meterPoints" :key="m.id" :label="m.name" :value="m.id" />
        </el-select>
        <el-select v-model="meterTrendFilter.period_type" placeholder="对比类型" style="width: 200px; margin-right: 12px;">
          <el-option v-for="p in TREND_TYPE_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
        </el-select>
        <el-button type="primary" @click="loadMeterTrend" :loading="loading">查询</el-button>
      </div>

      <div v-if="meterTrendData" class="kpi-grid">
        <KpiCard 
          :label="meterTrendData.trend.period_names[0]" 
          :value="meterTrendData.trend.values[0]" 
          :unit="meterTrendData.meter.unit" 
          :decimals="2" 
          accent="brand" 
        />
        <KpiCard 
          :label="meterTrendData.trend.period_names[1]" 
          :value="meterTrendData.trend.values[1]" 
          :unit="meterTrendData.meter.unit" 
          :decimals="2" 
          accent="amber" 
        />
        <KpiCard 
          label="变化量" 
          :value="meterTrendData.trend.change" 
          :unit="meterTrendData.meter.unit" 
          :decimals="2" 
          :accent="meterTrendData.trend.change >= 0 ? 'danger' : 'success'" 
        />
        <KpiCard 
          label="变化率" 
          :value="meterTrendData.trend.change_percent" 
          unit="%" 
          :decimals="2" 
          :accent="meterTrendData.trend.change_percent >= 0 ? 'danger' : 'success'" 
        />
      </div>

      <div v-if="meterTrendData" class="info-card" style="margin-top: 20px; padding: 20px; background: #f5f7fa; border-radius: 8px;">
        <h3 style="margin: 0 0 12px 0; font-size: 16px;">{{ meterTrendData.meter.name }}</h3>
        <p style="margin: 0; color: #666;">
          {{ meterTrendData.trend.period_names[0] }}: {{ meterTrendData.trend.values[0] }} {{ meterTrendData.meter.unit }}<br/>
          {{ meterTrendData.trend.period_names[1] }}: {{ meterTrendData.trend.values[1] }} {{ meterTrendData.meter.unit }}<br/>
          变化: {{ meterTrendData.trend.change >= 0 ? '+' : '' }}{{ meterTrendData.trend.change }} {{ meterTrendData.meter.unit }} 
          ({{ meterTrendData.trend.change_percent >= 0 ? '+' : '' }}{{ meterTrendData.trend.change_percent }}%)
        </p>
      </div>
    </div>

    <!-- 单元对标 -->
    <div v-if="activeTab === 'unit-comparison'" class="section">
      <div class="filter-bar" style="margin-bottom: 16px;">
        <el-select v-model="unitComparisonFilter.unit1_code" placeholder="选择用能单元1" style="width: 200px; margin-right: 12px;">
          <el-option v-for="u in units" :key="u.code" :label="u.name" :value="u.code" />
        </el-select>
        <el-select v-model="unitComparisonFilter.unit2_code" placeholder="选择用能单元2" style="width: 200px; margin-right: 12px;">
          <el-option v-for="u in units" :key="u.code" :label="u.name" :value="u.code" />
        </el-select>
        <el-select v-model="unitComparisonFilter.period" placeholder="周期" style="width: 120px; margin-right: 12px;">
          <el-option v-for="p in PERIOD_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
        </el-select>
        <el-button type="primary" @click="loadUnitComparison" :loading="loading">查询</el-button>
      </div>

      <div v-if="unitComparisonData" class="kpi-grid">
        <KpiCard 
          :label="unitComparisonData.unit1.name" 
          :value="unitComparisonData.unit1.total_ce_tce" 
          unit="tce" 
          :decimals="2" 
          accent="brand" 
        />
        <KpiCard 
          :label="unitComparisonData.unit2.name" 
          :value="unitComparisonData.unit2.total_ce_tce" 
          unit="tce" 
          :decimals="2" 
          accent="amber" 
        />
        <KpiCard 
          label="差值" 
          :value="Math.abs(unitComparisonData.comparison.difference)" 
          unit="tce" 
          :decimals="2" 
          accent="blue" 
        />
        <KpiCard 
          label="差异比例" 
          :value="unitComparisonData.comparison.diff_percent" 
          unit="%" 
          :decimals="2" 
          accent="violet" 
        />
      </div>

      <ChartCard 
        ref="unitComparisonChartRef" 
        title="用能单元能耗对比" 
        desc="分能源类型折标煤对比" 
        :loading="loading" 
        height="350px" 
      />
    </div>
  </div>
</template>

<style scoped>
.section {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
