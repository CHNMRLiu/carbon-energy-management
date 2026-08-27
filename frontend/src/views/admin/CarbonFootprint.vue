<script setup>
import { computed, onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'

const loading = ref(false)
const data = ref({})
const chartRef = ref(null)

const columns = [
  { prop: 'stage', label: '生命周期阶段', minWidth: 160 },
  { prop: 'value', label: '排放量 (tCO₂e)', minWidth: 150, align: 'right', formatter: (r) => Number(r.value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) },
  { prop: 'share', label: '占比', width: 180, slot: true }
]

const total = computed(() => Number(data.value.total || 0))

const rows = computed(() =>
  (data.value.stages || []).map((s) => ({
    ...s,
    pct: Number.isFinite(Number(s.share)) && s.share > 0
      ? Number(s.share)
      : (total.value ? (Number(s.value || 0) / total.value) * 100 : 0)
  }))
)

function renderChart(stages) {
  if (!stages?.length || !chartRef.value) return
  chartRef.value.setOption({
    color: PALETTE,
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 12, right: 20, top: 30, bottom: 8, containLabel: true },
    xAxis: { type: 'category', data: stages.map((s) => s.stage), axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    yAxis: { type: 'value', name: 'tCO₂e', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      {
        name: '阶段排放',
        type: 'bar',
        barWidth: 34,
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
        data: stages.map((s) => Number(s.value || 0))
      }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.carbonFootprint()
    renderChart(data.value.stages)
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
        <h2>产品碳足迹</h2>
        <p>{{ data.product || '--' }} 全生命周期碳足迹 · 依据 {{ data.standard || 'GB/T 24067' }} · 统计区间 {{ (data.range || []).join(' ~ ') }}</p>
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="单位产品碳足迹" :value="data.unitFootprint ?? '--'" :unit="data.unit || 'kgCO₂e/t'" :decimals="3" accent="brand" />
      <KpiCard label="全生命周期总排放" :value="total || '--'" unit="tCO₂e" accent="blue" />
      <KpiCard label="碳标识等级" :value="data.label?.grade ?? '--'" :decimals="0" accent="violet" :sub="data.label?.description || ''" />
      <KpiCard label="行业基准值" :value="data.label?.benchmark ?? '--'" :unit="data.unit || 'kgCO₂e/t'" accent="amber" :sub="`产量 ${Number(data.total_output || 0).toLocaleString('zh-CN')} t`" />
    </div>

    <ChartCard ref="chartRef" title="生命周期五阶段排放" desc="原材料获取 → 运输 → 生产制造 → 使用阶段 → 回收处置" :loading="loading" height="330px" />

    <DataTable title="阶段排放明细" :columns="columns" :data="rows" :loading="loading" show-index>
      <template #col-share="{ row }">
        <div class="share-bar">
          <div class="share-fill" :style="{ width: row.pct.toFixed(1) + '%' }"></div>
          <span class="num">{{ row.pct.toFixed(1) }}%</span>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
.share-bar {
  position: relative; height: 18px; border-radius: 9px;
  background: var(--surface-2); overflow: hidden; min-width: 140px;
}
.share-fill {
  position: absolute; inset: 0 auto 0 0;
  background: linear-gradient(90deg, rgba(12, 143, 122, 0.25), var(--brand));
  border-radius: 9px;
}
.share-bar .num {
  position: relative; font-size: 11px; color: var(--ink);
  display: block; text-align: right; padding-right: 8px; line-height: 18px;
}
</style>
