<script setup>
import { computed, onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api, AUDIT_EXPORT_URL, AUDIT_REPORT_URL } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const exporting = ref(false)
const exportingReport = ref(false)
const data = ref({ records: [], standards: [], dataBasis: { meter_readings: 0, manual_reports: 0, methods: [] } })
const chartRef = ref(null)

const columns = [
  { prop: 'energy_name', label: '能源类型', width: 120 },
  { prop: 'quantity', label: '活动水平（实物量）', minWidth: 170, align: 'right', formatter: (r) => Number(r.quantity || 0).toLocaleString('zh-CN', { maximumFractionDigits: 1 }) },
  { prop: 'unit', label: '单位', width: 90 },
  { prop: 'factor', label: '排放因子', width: 120, align: 'right', formatter: (r) => Number(r.factor || 0).toFixed(7) },
  { prop: 'emission', label: '排放量 (tCO₂)', minWidth: 150, align: 'right', sortable: true, formatter: (r) => Number(r.emission || 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 }) },
  { prop: 'collect_method', label: '采集方式', width: 120, align: 'center', slot: true },
  { prop: 'source', label: '核算依据', width: 130 }
]

const stdColumns = [
  { prop: 'code', label: '标准编号', width: 180 },
  { prop: 'name', label: '标准名称', minWidth: 260 },
  { prop: 'scope', label: '适用范围', minWidth: 180 }
]

const records = computed(() => data.value.records || [])

const METHOD_TYPE = { 仪表采集: 'success', 系统对接: 'primary', 手工填报: 'warning', 烟感实测: 'danger' }

function renderChart() {
  const recs = records.value
  if (!recs.length || !chartRef.value) return
  chartRef.value.setOption({
    color: [PALETTE[0]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 12, right: 20, top: 30, bottom: 8, containLabel: true },
    xAxis: { type: 'category', data: recs.map((r) => r.energy_name), axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    yAxis: { type: 'value', name: 'tCO₂', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      {
        name: '核算排放量',
        type: 'bar',
        barWidth: 36,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#0c8f7a' },
              { offset: 1, color: 'rgba(12,143,122,0.15)' }
            ]
          }
        },
        label: { show: true, position: 'top', formatter: (p) => Number(p.value || 0).toFixed(1), color: '#55655f', fontSize: 11 },
        data: recs.map((r) => Number(r.emission || 0))
      }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.carbonAudit()
    renderChart()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

/** fetch + Blob + <a download> 下载，避免 window.open 被弹窗拦截 */
async function downloadFile(url, fallbackName) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const blob = await res.blob()
  let filename = fallbackName
  const disposition = res.headers.get('Content-Disposition') || ''
  const m = disposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i)
  if (m && m[1]) filename = decodeURIComponent(m[1])
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(objectUrl)
}

async function exportCsv() {
  exporting.value = true
  try {
    await downloadFile(AUDIT_EXPORT_URL, `carbon_audit_${new Date().getFullYear()}.csv`)
    ElMessage.success('核查数据已导出')
  } catch (e) {
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

async function exportReport() {
  exportingReport.value = true
  try {
    await downloadFile(AUDIT_REPORT_URL, `carbon_audit_report_${new Date().getFullYear()}.txt`)
    ElMessage.success('核查报告已导出')
  } catch (e) {
    ElMessage.error('报告导出失败，请稍后重试')
  } finally {
    exportingReport.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>碳核查支撑</h2>
        <p>排放数据全链路溯源 · 核算区间 {{ data.period_label || '--' }} · 核查材料一键导出</p>
      </div>
      <el-button type="primary" :loading="exporting" @click="exportCsv">
        导出核查数据 (CSV)
      </el-button>
      <el-button :loading="exportingReport" @click="exportReport">
        导出核查报告 (TXT)
      </el-button>
    </div>

    <div class="kpi-grid">
      <KpiCard label="核算总排放" :value="data.total ?? '--'" unit="tCO₂" accent="danger" />
      <KpiCard label="溯源记录数" :value="records.length" unit="条" :decimals="0" accent="blue" />
      <KpiCard label="仪表采集记录" :value="data.dataBasis?.meter_readings ?? 0" unit="条" :decimals="0" accent="brand" sub="自动采集数据" />
      <KpiCard label="手工填报记录" :value="data.dataBasis?.manual_reports ?? 0" unit="条" :decimals="0" accent="amber" :sub="`采集方式：${(data.dataBasis?.methods || []).join(' / ') || '--'}`" />
    </div>

    <ChartCard ref="chartRef" title="分能源核算排放" desc="单位 tCO₂" :loading="loading" height="280px" />

    <DataTable title="溯源清单" :columns="columns" :data="records" :loading="loading" max-height="460" show-index>
      <template #col-collect_method="{ row }">
        <el-tag :type="METHOD_TYPE[row.collect_method] || 'info'" size="small" effect="plain">{{ row.collect_method }}</el-tag>
      </template>
    </DataTable>

    <DataTable title="采用核算标准" :columns="stdColumns" :data="data.standards || []" :loading="loading" show-index />
  </div>
</template>
