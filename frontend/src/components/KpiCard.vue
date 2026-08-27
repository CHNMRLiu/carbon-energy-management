<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  unit: { type: String, default: '' },
  decimals: { type: Number, default: 1 },
  /** 趋势百分比，如 -3.6 表示同比下降 3.6% */
  trend: { type: Number, default: null },
  /** 数值下降是否为利好（能耗/碳排类指标为 true） */
  goodWhenDown: { type: Boolean, default: true },
  /** 左侧强调色 */
  accent: { type: String, default: 'brand' },
  sub: { type: String, default: '' }
})

const display = computed(() => {
  const n = Number(props.value)
  if (Number.isFinite(n)) {
    return n.toLocaleString('zh-CN', { minimumFractionDigits: props.decimals, maximumFractionDigits: props.decimals })
  }
  return String(props.value ?? '--')
})

const trendInfo = computed(() => {
  if (props.trend === null || props.trend === undefined || Number.isNaN(props.trend)) return null
  const up = props.trend >= 0
  const good = props.goodWhenDown ? !up : up
  return { up, good, text: `${up ? '+' : ''}${props.trend.toFixed(1)}%` }
})
</script>

<template>
  <div class="kpi-card card" :data-accent="accent">
    <div class="kpi-label">{{ label }}</div>
    <div class="kpi-value">
      <span class="num">{{ display }}</span>
      <span v-if="unit" class="kpi-unit">{{ unit }}</span>
    </div>
    <div class="kpi-foot">
      <span v-if="trendInfo" class="kpi-trend" :class="trendInfo.good ? 'good' : 'bad'">
        <svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true">
          <path v-if="trendInfo.up" d="M6 1.5 11 9.5H1z" fill="currentColor" />
          <path v-else d="M6 10.5 1 2.5h10z" fill="currentColor" />
        </svg>
        {{ trendInfo.text }}
      </span>
      <span v-if="sub" class="kpi-sub">{{ sub }}</span>
    </div>
  </div>
</template>

<style scoped>
.kpi-card {
  position: relative;
  padding: 16px 18px 14px;
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.kpi-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--accent-c, var(--brand));
  border-radius: 4px 0 0 4px;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 10px 28px -14px rgba(22, 36, 31, 0.25); }
.kpi-card[data-accent='brand'] { --accent-c: linear-gradient(180deg, var(--brand), var(--brand-deep)); }
.kpi-card[data-accent='blue'] { --accent-c: var(--blue); }
.kpi-card[data-accent='amber'] { --accent-c: var(--amber); }
.kpi-card[data-accent='violet'] { --accent-c: var(--violet); }
.kpi-card[data-accent='danger'] { --accent-c: var(--danger); }

.kpi-label { font-size: 13px; color: var(--ink-2); letter-spacing: 0.04em; }
.kpi-value { margin-top: 8px; display: flex; align-items: baseline; gap: 6px; }
.kpi-value .num { font-size: 30px; font-weight: 700; line-height: 1.1; color: var(--ink); }
.kpi-unit { font-size: 12px; color: var(--ink-3); }
.kpi-foot { margin-top: 10px; display: flex; align-items: center; gap: 10px; min-height: 18px; }
.kpi-trend {
  display: inline-flex; align-items: center; gap: 4px;
  font-family: var(--font-num); font-size: 12px; font-weight: 600;
  padding: 1px 8px; border-radius: 999px;
}
.kpi-trend.good { color: var(--brand-deep); background: var(--brand-soft); }
.kpi-trend.bad { color: var(--danger); background: var(--danger-soft); }
.kpi-sub { font-size: 12px; color: var(--ink-3); }
</style>
