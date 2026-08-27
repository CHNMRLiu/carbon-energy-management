<script setup>
import { onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const exportingReport = ref(false)
const data = ref({})

const pieRef = ref(null)
const trendRef = ref(null)

const columns = [
  { prop: 'period', label: '月份', width: 140 },
  { prop: 'emission', label: '排放量 (tCO₂)', minWidth: 150, align: 'right', sortable: true, formatter: (r) => Number(r.emission || 0).toLocaleString('zh-CN') }
]

function renderCharts() {
  const d = data.value
  if (d.bySource?.length && pieRef.value) {
    pieRef.value.setOption({
      color: PALETTE,
      tooltip: {
        ...tooltipBase,
        trigger: 'item',
        formatter: (p) => `${p.name}<br/><b>${Number(p.value).toLocaleString('zh-CN')} tCO₂</b> (${p.percent}%)`
      },
      legend: { bottom: 0, textStyle: { color: '#55655f', fontSize: 12 } },
      series: [
        {
          type: 'pie',
          radius: ['44%', '68%'],
          center: ['50%', '44%'],
          itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 6 },
          label: { formatter: '{b}\n{d}%', fontSize: 11, color: '#55655f' },
          data: d.bySource
        }
      ]
    })
  }
  if (d.trend?.axis?.length && trendRef.value) {
    trendRef.value.setOption({
      color: [PALETTE[3]],
      tooltip: { ...tooltipBase, trigger: 'axis' },
      grid: { left: 12, right: 20, top: 30, bottom: 8, containLabel: true },
      xAxis: { type: 'category', data: d.trend.axis, axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
      yAxis: { type: 'value', name: 'tCO₂', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
      series: [
        {
          name: '碳排放量',
          type: 'bar',
          barWidth: 14,
          itemStyle: {
            borderRadius: [5, 5, 0, 0],
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#d64545' },
                { offset: 1, color: 'rgba(214,69,69,0.25)' }
              ]
            }
          },
          data: d.trend.data
        }
      ]
    })
  }
}

async function load() {
  loading.value = true
  try {
    data.value = await api.carbonEmission()
    renderCharts()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

// 导出正式年度报告
async function exportAnnualReport() {
  exportingReport.value = true
  try {
    // 模拟生成 HTML 报告内容
    const reportHtml = generateReportHtml(data.value)
    
    // 创建 Blob 并下载
    const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `碳排放核算年度报告_${new Date().getFullYear()}.html`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    
    ElMessage.success('年度报告已导出（HTML格式）')
  } catch (e) {
    ElMessage.error('报告导出失败，请稍后重试')
  } finally {
    exportingReport.value = false
  }
}

// 生成 HTML 报告内容
function generateReportHtml(d) {
  const year = new Date().getFullYear()
  const bySourceRows = (d.bySource || []).map(s => `
    <tr>
      <td>${s.name}</td>
      <td style="text-align:right;">${Number(s.value).toLocaleString('zh-CN')}</td>
      <td style="text-align:right;">${s.share}%</td>
    </tr>
  `).join('')
  
  const trendRows = (d.trend?.axis || []).map((period, i) => `
    <tr>
      <td>${period}</td>
      <td style="text-align:right;">${Number(d.trend.data[i] || 0).toLocaleString('zh-CN')}</td>
    </tr>
  `).join('')
  
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>${year}年度碳排放核算报告</title>
  <style>
    body { font-family: "Microsoft YaHei", Arial, sans-serif; padding: 40px; color: #333; }
    h1 { text-align: center; color: #16241f; border-bottom: 3px solid #0c8f7a; padding-bottom: 15px; }
    h2 { color: #0c8f7a; margin-top: 30px; border-left: 4px solid #0c8f7a; padding-left: 12px; }
    .header-info { text-align: center; margin: 20px 0; color: #666; }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th, td { border: 1px solid #ddd; padding: 10px; }
    th { background: #f5f7fa; font-weight: bold; }
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
    .kpi-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; text-align: center; }
    .kpi-label { font-size: 14px; color: #666; }
    .kpi-value { font-size: 24px; font-weight: bold; color: #16241f; margin: 8px 0; }
    .kpi-unit { font-size: 12px; color: #999; }
    .footer { margin-top: 40px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #eee; padding-top: 15px; }
  </style>
</head>
<body>
  <h1>${year}年度碳排放核算报告</h1>
  <div class="header-info">
    <p>报告生成时间：${new Date().toLocaleString('zh-CN')}</p>
    <p>核算依据：GB/T 32151 系列标准及行业核算指南</p>
  </div>

  <h2>一、核心指标概览</h2>
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">累计排放总量</div>
      <div class="kpi-value">${d.total ?? '--'}</div>
      <div class="kpi-unit">${d.unit || 'tCO₂'}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">排放强度</div>
      <div class="kpi-value">${d.intensity ?? '--'}</div>
      <div class="kpi-unit">${d.intensity_unit || ''}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">最大排放源</div>
      <div class="kpi-value" style="font-size:18px;">${d.topSource?.name || '--'}</div>
      <div class="kpi-unit">${d.topSource ? `${d.topSource.value.toLocaleString('zh-CN')} tCO₂ · ${d.topSource.share}%` : ''}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">预警信息</div>
      <div class="kpi-value">${d.warnings?.length ?? 0}</div>
      <div class="kpi-unit">条</div>
    </div>
  </div>

  <h2>二、按能源来源拆分</h2>
  <table>
    <thead>
      <tr>
        <th>能源类型</th>
        <th style="text-align:right;">排放量 (tCO₂)</th>
        <th style="text-align:right;">占比</th>
      </tr>
    </thead>
    <tbody>
      ${bySourceRows || '<tr><td colspan="3" style="text-align:center;">暂无数据</td></tr>'}
    </tbody>
  </table>

  <h2>三、月度排放趋势</h2>
  <table>
    <thead>
      <tr>
        <th>月份</th>
        <th style="text-align:right;">排放量 (tCO₂)</th>
      </tr>
    </thead>
    <tbody>
      ${trendRows || '<tr><td colspan="2" style="text-align:center;">暂无数据</td></tr>'}
    </tbody>
  </table>

  <h2>四、预警信息</h2>
  ${(d.warnings || []).length > 0 ? `
    <ul>
      ${(d.warnings || []).map(w => `<li>${w.content}</li>`).join('')}
    </ul>
  ` : '<p>当前无预警信息。</p>'}

  <div class="footer">
    <p>本报告由工业企业和园区数字化能碳管理中心自动生成</p>
    <p>© ${year} 能碳管理中心系统 v0.2.0</p>
  </div>
</body>
</html>
  `.trim()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>碳排放核算</h2>
        <p>总量与强度核算、来源拆分、月度趋势与预警 · 依据 GB/T 32151 系列及行业核算标准</p>
      </div>
      <el-button type="primary" :loading="exportingReport" @click="exportAnnualReport">
        导出年度报告 (HTML)
      </el-button>
    </div>

    <div class="kpi-grid">
      <KpiCard label="累计排放总量" :value="data.total ?? '--'" :unit="data.unit || 'tCO₂'" accent="danger" :sub="`区间 ${(data.range || []).join(' ~ ')}`" />
      <KpiCard label="排放强度" :value="data.intensity ?? '--'" :unit="data.intensity_unit || ''" :decimals="4" accent="blue" />
      <KpiCard
        label="最大排放源"
        :value="data.topSource?.name || '--'"
        :decimals="0"
        accent="brand"
        :sub="data.topSource ? `${data.topSource.value.toLocaleString('zh-CN')} tCO₂ · ${data.topSource.share}%` : ''"
      />
      <KpiCard label="预警信息" :value="data.warnings?.length ?? 0" unit="条" :decimals="0" accent="amber" />
    </div>

    <el-alert
      v-for="(w, i) in data.warnings || []"
      :key="i"
      :title="w.content"
      type="warning"
      show-icon
      :closable="false"
    />

    <div class="two-col">
      <ChartCard ref="pieRef" title="按能源来源拆分" desc="本期累计 · tCO₂" :loading="loading" height="320px" />
      <ChartCard ref="trendRef" title="月度排放趋势" desc="单位 tCO₂" :loading="loading" height="320px" />
    </div>

    <DataTable title="月度核算明细" :columns="columns" :data="data.items || []" :loading="loading" max-height="400" show-index />
  </div>
</template>
