<script setup>
import { computed, onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'
import { ElMessage, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElDialog, ElButton } from 'element-plus'

const loading = ref(false)
const data = ref({})
const activeTab = ref('process')

// 自定义指标相关状态
const showCustomDialog = ref(false)
const customForm = ref({
  name: '',
  energy_code: '',
  output: '',
  energy_consumption: ''
})
const customIndicators = ref([])

const TAB_META = {
  process: { label: '工序对标', unit: 'kgce/t' },
  product: { label: '产品对标', unit: 'kgce/t' },
  equipment: { label: '设备对标', unit: '比功率/效率' },
  custom: { label: '自定义指标', unit: 'kgce/t' }
}

const chartRef = ref(null)

const rows = computed(() => {
  if (activeTab.value === 'custom') {
    return customIndicators.value
  }
  return data.value[activeTab.value] || []
})
const passCount = computed(() => rows.value.filter((r) => r.pass).length)
const passRate = computed(() => (rows.value.length ? (passCount.value / rows.value.length) * 100 : 0))
const worst = computed(() => rows.value.filter((r) => !r.pass).sort((a, b) => Math.abs(b.gap) - Math.abs(a.gap))[0])

const columns = [
  { prop: 'name', label: '对标项', minWidth: 160 },
  { prop: 'actual', label: '实际值', width: 110, align: 'right', formatter: (r) => Number(r.actual || 0).toLocaleString('zh-CN') },
  { prop: 'limit', label: '限额值', width: 110, align: 'right', formatter: (r) => Number(r.limit || 0).toLocaleString('zh-CN') },
  { prop: 'unit', label: '单位', width: 100 },
  { prop: 'gap', label: '偏差', width: 110, align: 'right', slot: true },
  { prop: 'pass', label: '达标状态', width: 100, align: 'center', slot: true },
  { prop: 'advice', label: '处置建议', minWidth: 200 }
]

// 能源类型选项
const ENERGY_OPTIONS = [
  { value: 'electricity', label: '电力' },
  { value: 'steam', label: '蒸汽' },
  { value: 'gas', label: '天然气' },
  { value: 'coal', label: '煤炭' },
  { value: 'oil', label: '石油' }
]

// 打开自定义指标对话框
function openCustomDialog() {
  showCustomDialog.value = true
  customForm.value = {
    name: '',
    energy_code: '',
    output: '',
    energy_consumption: ''
  }
}

// 提交自定义指标
function submitCustomIndicator() {
  if (!customForm.value.name || !customForm.value.energy_code || !customForm.value.output || !customForm.value.energy_consumption) {
    ElMessage.warning('请填写所有字段')
    return
  }
  
  const output = parseFloat(customForm.value.output)
  const consumption = parseFloat(customForm.value.energy_consumption)
  const actual = consumption / output // 单位产品能耗
  
  // 模拟限额值（实际应从标准库获取）
  const limit = actual * 1.1 // 假设限额为实际值的110%
  const gap = ((actual - limit) / limit * 100).toFixed(2)
  const pass = actual <= limit
  
  const newIndicator = {
    name: customForm.value.name,
    energy_code: customForm.value.energy_code,
    actual: parseFloat(actual.toFixed(2)),
    limit: parseFloat(limit.toFixed(2)),
    unit: 'kgce/t',
    gap: parseFloat(gap),
    pass,
    advice: pass ? '符合标准，继续保持' : `超标${Math.abs(gap)}%，建议优化用能效率`
  }
  
  customIndicators.value.push(newIndicator)
  showCustomDialog.value = false
  ElMessage.success('自定义指标添加成功')
  renderChart()
}

function renderChart() {
  const list = rows.value
  if (!list.length || !chartRef.value) return
  chartRef.value.setOption({
    color: [PALETTE[0], PALETTE[2]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, textStyle: { color: '#55655f', fontSize: 12 } },
    grid: { left: 12, right: 24, top: 36, bottom: 8, containLabel: true },
    xAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    yAxis: { type: 'category', data: list.map((r) => r.name), axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    series: [
      { name: '实际值', type: 'bar', barWidth: 10, itemStyle: { borderRadius: [0, 4, 4, 0] }, data: list.map((r) => r.actual) },
      { name: '限额值', type: 'bar', barWidth: 10, itemStyle: { borderRadius: [0, 4, 4, 0], opacity: 0.55 }, data: list.map((r) => r.limit) }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.energyBenchmark()
    renderChart()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
  renderChart()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>能效对标</h2>
        <p>工序、产品、设备三级对标 · 限额依据国家单位产品能耗限额标准与设备能效标准</p>
      </div>
      <div style="display: flex; gap: 12px; align-items: center;">
        <el-radio-group :model-value="activeTab" @update:model-value="switchTab">
          <el-radio-button v-for="(m, k) in TAB_META" :key="k" :value="k">{{ m.label }}</el-radio-button>
        </el-radio-group>
        <el-button v-if="activeTab === 'custom'" type="primary" size="small" @click="openCustomDialog">
          + 添加自定义指标
        </el-button>
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="对标项总数" :value="rows.length" unit="项" :decimals="0" accent="blue" />
      <KpiCard label="达标项" :value="passCount" unit="项" :decimals="0" accent="brand" />
      <KpiCard label="达标率" :value="passRate.toFixed(1)" unit="%" accent="violet" :good-when-down="false" />
      <KpiCard
        label="最大超标项"
        :value="worst ? worst.name : '无'"
        :decimals="0"
        :sub="worst ? `偏差 ${worst.gap > 0 ? '+' : ''}${worst.gap}%` : '全部达标'"
        :accent="worst ? 'danger' : 'brand'"
      />
    </div>

    <ChartCard ref="chartRef" :title="`${TAB_META[activeTab].label} · 实际值与限额对比`" :desc="`单位：${TAB_META[activeTab].unit}`" :loading="loading" height="330px" />

    <DataTable :title="`${TAB_META[activeTab].label}明细`" :columns="columns" :data="rows" :loading="loading" show-index>
      <template #col-gap="{ row }">
        <span class="num" :style="{ color: row.pass ? 'var(--brand-deep)' : 'var(--danger)' }">
          {{ row.gap > 0 ? '+' : '' }}{{ row.gap }}%
        </span>
      </template>
      <template #col-pass="{ row }">
        <span class="tag-dot" :style="{ color: row.pass ? 'var(--brand-deep)' : 'var(--danger)' }">
          {{ row.pass ? '达标' : '超标' }}
        </span>
      </template>
    </DataTable>

    <!-- 自定义指标对话框 -->
    <el-dialog v-model="showCustomDialog" title="添加自定义测评指标" width="500px">
      <el-form :model="customForm" label-width="120px">
        <el-form-item label="指标名称" required>
          <el-input v-model="customForm.name" placeholder="例如：车间A单位产品能耗" />
        </el-form-item>
        <el-form-item label="能源类型" required>
          <el-select v-model="customForm.energy_code" placeholder="选择能源类型" style="width: 100%;">
            <el-option v-for="opt in ENERGY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="产量 (t)" required>
          <el-input v-model="customForm.output" type="number" placeholder="输入产量" />
        </el-form-item>
        <el-form-item label="能耗量 (kgce)" required>
          <el-input v-model="customForm.energy_consumption" type="number" placeholder="输入能耗量" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCustomDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCustomIndicator">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
