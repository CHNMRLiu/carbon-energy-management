<script setup>
import { onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const data = ref({})
const chartRef = ref(null)

const STATUS_TYPE = { 待执行: 'warning', 执行中: 'primary', 已完成: 'success' }

const columns = [
  { prop: 'device', label: '设备', minWidth: 130 },
  { prop: 'org', label: '所属车间', width: 100 },
  { prop: 'param', label: '优化参数', minWidth: 130 },
  { prop: 'current', label: '现状值', width: 100, align: 'right' },
  { prop: 'suggested', label: '建议值', width: 100, align: 'right', slot: true },
  { prop: 'measure', label: '优化措施', minWidth: 220 },
  { prop: 'saving', label: '预计节能量 (tce/年)', minWidth: 150, align: 'right', sortable: true, formatter: (r) => Number(r.saving || 0).toLocaleString('zh-CN') },
  { prop: 'status', label: '状态', width: 100, align: 'center', slot: true },
  { prop: 'op', label: '操作', width: 100, align: 'center', slot: true }
]

function renderChart(items) {
  if (!items?.length || !chartRef.value) return
  const sorted = [...items].sort((a, b) => Number(b.saving || 0) - Number(a.saving || 0))
  chartRef.value.setOption({
    color: [PALETTE[0]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 12, right: 40, top: 30, bottom: 8, containLabel: true },
    xAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    yAxis: { type: 'category', data: sorted.map((r) => r.device), axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    series: [
      {
        name: '预计节能量',
        type: 'bar',
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: {
            type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: 'rgba(12,143,122,0.35)' },
              { offset: 1, color: '#0c8f7a' }
            ]
          }
        },
        label: { show: true, position: 'right', formatter: '{c}', color: '#55655f', fontSize: 11 },
        data: sorted.map((r) => r.saving)
      }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.energyOptimization()
    renderChart(data.value.items)
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function apply(row) {
  ElMessage.success(`「${row.device} · ${row.param}」建议值已下发至设备侧`)
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>能效平衡与优化</h2>
        <p>AI 模型分析工艺与设备运行参数，输出最优设定与预计节能量</p>
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="预计总节能量" :value="data.totalSaving ?? '--'" unit="tce/年" accent="brand" />
      <KpiCard label="预计总节电量" :value="data.totalSavingKwh ? (data.totalSavingKwh / 10000).toFixed(1) : '--'" unit="万kWh" accent="amber" />
      <KpiCard label="优化建议数" :value="data.items?.length ?? 0" unit="项" :decimals="0" accent="blue" :sub="`评估设备共 ${data.equipmentCount ?? 0} 台`" />
      <KpiCard
        label="待执行项"
        :value="data.items?.filter((i) => i.status === '待执行').length ?? 0"
        unit="项"
        :decimals="0"
        accent="danger"
        sub="建议尽快落地"
      />
    </div>

    <ChartCard ref="chartRef" title="各设备预计节能量" desc="单位 tce/年，按节能潜力排序" :loading="loading" height="300px" />

    <DataTable title="设备参数优化清单" :columns="columns" :data="data.items || []" :loading="loading" show-index>
      <template #col-suggested="{ row }">
        <span class="num" style="color: var(--brand-deep); font-weight: 700">{{ row.suggested }}</span>
      </template>
      <template #col-status="{ row }">
        <el-tag :type="STATUS_TYPE[row.status] || 'info'" size="small" effect="light">{{ row.status }}</el-tag>
      </template>
      <template #col-op="{ row }">
        <el-button v-if="row.status === '待执行'" size="small" type="primary" link @click="apply(row)">下发</el-button>
        <span v-else style="color: var(--ink-3)">—</span>
      </template>
    </DataTable>
  </div>
</template>
