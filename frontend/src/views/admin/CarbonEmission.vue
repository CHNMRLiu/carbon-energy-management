<script setup>
import { onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'

const loading = ref(false)
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

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>碳排放核算</h2>
        <p>总量与强度核算、来源拆分、月度趋势与预警 · 依据 GB/T 32151 系列及行业核算标准</p>
      </div>
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
