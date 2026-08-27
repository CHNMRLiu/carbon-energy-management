<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useEChart } from '@/composables/useEChart'
import { usePolling } from '@/composables/usePolling'
import { useAppStore } from '@/stores/app'
import { api } from '@/api'
import Ticker from '@/components/Ticker.vue'
import { Moon, Sunny as Sun } from '@element-plus/icons-vue'

const appStore = useAppStore()

/* ---------------- 缩放适配（基准 1920×1080） ---------------- */
const scale = ref(1)
const compact = ref(false)

function onResize() {
  compact.value = window.innerWidth < 768
  scale.value = Math.min(window.innerWidth / 1920, window.innerHeight / 1080)
}

/* ---------------- 实时时钟 ---------------- */
const now = ref(new Date())
let clockTimer = null

const dateText = computed(() => {
  const d = now.value
  const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} 星期${week}`
})
const timeText = computed(() => {
  const d = now.value
  return [d.getHours(), d.getMinutes(), d.getSeconds()].map((n) => String(n).padStart(2, '0')).join(':')
})

/* ---------------- 数据 ---------------- */
const overview = ref({})
const flow = ref({ nodes: [], links: [] })
const structure = ref([])
const energyTrend = ref({ axis: [], totals: [] })
const asset = ref({})
const updatedAt = ref('')

const kpi = computed(() => overview.value.kpi || {})
const quotaRate = computed(() => {
  const q = asset.value.quota
  const e = asset.value.emitted
  return q > 0 ? +((e / q) * 100).toFixed(1) : 0
})

/* ---------------- 图表 ---------------- */
/** 读取 CSS 变量实际值（ECharts Canvas 渐变不支持 var() 语法） */
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

const DARK_AXIS = { color: 'var(--screen-text-secondary)', fontSize: 12 }
const DARK_SPLIT = { lineStyle: { color: 'var(--screen-border)', type: 'dashed' } }
const DARK_TOOLTIP = {
  backgroundColor: 'var(--screen-card-bg)',
  borderColor: 'var(--screen-card-border)',
  textStyle: { color: 'var(--screen-text)', fontSize: 12 },
  padding: [8, 12]
}

const barRef = ref(null)
const pieRef = ref(null)
const sankeyRef = ref(null)
const carbonRef = ref(null)
const gaugeRef = ref(null)

const barChart = useEChart(barRef)
const pieChart = useEChart(pieRef)
const sankeyChart = useEChart(sankeyRef)
const carbonChart = useEChart(carbonRef)
const gaugeChart = useEChart(gaugeRef)

function renderBar() {
  const { axis, totals } = energyTrend.value
  if (!axis?.length) return
  barChart.setOption({
    tooltip: { ...DARK_TOOLTIP, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 12, top: 26, bottom: 4, containLabel: true },
    xAxis: { type: 'category', data: axis, axisLabel: { ...DARK_AXIS, fontSize: 10 }, axisLine: { lineStyle: { color: 'rgba(124,147,166,0.3)' } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: DARK_AXIS, splitLine: DARK_SPLIT },
    series: [
      {
        name: '综合能耗',
        type: 'bar',
        barWidth: '46%',
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: cssVar('--screen-accent') },
              { offset: 1, color: 'rgba(42,212,182,0.08)' }
            ]
          }
        },
        data: totals
      }
    ]
  })
}

function renderPie() {
  if (!structure.value?.length) return
  const colors = [cssVar('--screen-accent'), cssVar('--screen-accent-2'), '#f6b352', '#8f7bff', '#ff6b81']
  pieChart.setOption({
    color: colors,
    tooltip: {
      ...DARK_TOOLTIP,
      trigger: 'item',
      formatter: (p) => `${p.name}<br/><b>${Number(p.value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 1 })} tce</b> · ${Number(p.percent || 0).toFixed(1)}%`
    },
    legend: { orient: 'vertical', right: 8, top: 'middle', textStyle: { color: 'var(--screen-text-secondary)', fontSize: 12 }, itemWidth: 10, itemHeight: 10 },
    series: [
      {
        type: 'pie',
        radius: ['52%', '74%'],
        center: ['36%', '50%'],
        itemStyle: { borderColor: cssVar('--screen-bg'), borderWidth: 3, borderRadius: 6 },
        label: { show: false },
        emphasis: { scaleSize: 5 },
        data: structure.value
      }
    ]
  })
}

function renderSankey() {
  if (!flow.value.nodes?.length) return
  sankeyChart.setOption({
    tooltip: {
      ...DARK_TOOLTIP,
      trigger: 'item',
      formatter: (p) =>
        p.dataType === 'edge'
          ? `${p.data.source} → ${p.data.target}<br/><b>${Number(p.data.value).toLocaleString('zh-CN')} tce</b>`
          : `${p.name}<br/><b>${Number(p.value).toLocaleString('zh-CN')} tce</b>`
    },
    series: [
      {
        type: 'sankey',
        data: flow.value.nodes.map((n) => ({ ...n })),
        links: flow.value.links.map((l) => ({ ...l })),
        nodeAlign: 'justify',
        nodeWidth: 12,
        nodeGap: 12,
        left: 8,
        right: 110,
        top: 10,
        bottom: 10,
        emphasis: { focus: 'adjacency' },
        lineStyle: { color: 'gradient', curveness: 0.55, opacity: 0.32 },
        itemStyle: { borderWidth: 0, borderRadius: 3 },
        label: { color: cssVar('--screen-text'), fontSize: 12 },
        levels: [
          { depth: 0, itemStyle: { color: cssVar('--screen-accent') } },
          { depth: 1, itemStyle: { color: cssVar('--screen-accent-2') } },
          { depth: 2, itemStyle: { color: '#f6b352' } },
          { depth: 3, itemStyle: { color: '#6fdc8c' } },
          { depth: 4, itemStyle: { color: '#5c7486' } }
        ]
      }
    ]
  })
}

function renderCarbon() {
  const t = overview.value.carbonTrend
  if (!t?.axis?.length) return
  carbonChart.setOption({
    tooltip: { ...DARK_TOOLTIP, trigger: 'axis' },
    grid: { left: 8, right: 12, top: 26, bottom: 4, containLabel: true },
    xAxis: { type: 'category', data: t.axis, axisLabel: { ...DARK_AXIS, fontSize: 10 }, axisLine: { lineStyle: { color: 'rgba(124,147,166,0.3)' } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: DARK_AXIS, splitLine: DARK_SPLIT },
    series: [
      {
        name: '碳排放',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2, color: '#3ba3ff' },
        itemStyle: { color: '#3ba3ff', borderColor: '#08131e', borderWidth: 1 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59,163,255,0.35)' },
              { offset: 1, color: 'rgba(59,163,255,0)' }
            ]
          }
        },
        data: t.data
      }
    ]
  })
}

function renderGauge() {
  if (!asset.value.quota) return
  const rate = quotaRate.value
  gaugeChart.setOption({
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        radius: '96%',
        progress: {
          show: true, width: 14, roundCap: true,
          itemStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: cssVar('--screen-accent') },
                { offset: 1, color: rate > 90 ? '#ff6b81' : '#3ba3ff' }
              ]
            }
          }
        },
        axisLine: { lineStyle: { width: 14, color: [[1, 'rgba(124,147,166,0.16)']] } },
        axisTick: { distance: -22, length: 4, lineStyle: { color: 'rgba(124,147,166,0.4)' } },
        splitLine: { show: false },
        axisLabel: { show: false },
        pointer: { show: false },
        anchor: { show: false },
        title: { show: true, offsetCenter: [0, '36%'], fontSize: 13, color: cssVar('--screen-text-secondary') },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, '0%'],
          fontSize: 30,
          fontWeight: 700,
          fontFamily: 'Bahnschrift, "DIN Alternate", sans-serif',
          color: cssVar('--screen-text'),
          formatter: '{value}%'
        },
        data: [{ value: rate, name: '配额使用率' }]
      }
    ]
  })
}

/* ---------------- 数据加载与轮询 ---------------- */
async function loadOverview() {
  overview.value = await api.overview()
  updatedAt.value = timeText.value
  renderCarbon()
}

async function loadFlow() {
  flow.value = await api.energyFlow()
  renderSankey()
}

async function loadStatics() {
  try {
    const [analysis, consumption, assetData] = await Promise.all([
      api.energyAnalysis(),
      api.energyConsumption({ period: 'month' }),
      api.carbonAsset()
    ])
    structure.value = analysis.structure || []
    asset.value = assetData || {}
    const trend = consumption.trend
    if (trend?.axis?.length) {
      energyTrend.value = { axis: trend.axis, totals: trend.totals || [] }
    }
    renderPie()
    renderBar()
    renderGauge()
  } catch (e) {
    /* 拦截器已提示 */
  }
}

onMounted(() => {
  onResize()
  window.addEventListener('resize', onResize)
  clockTimer = setInterval(() => (now.value = new Date()), 1000)
  loadOverview()
  loadStatics()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  clearInterval(clockTimer)
})

// 10s 轮询（页面隐藏自动暂停，失败指数退避）
usePolling(loadOverview, { interval: 10000 })
usePolling(loadFlow, { interval: 10000 })
</script>

<template>
  <div class="screen" :class="{ compact }">
    <div class="stage" :style="compact ? {} : { transform: `translate(-50%, -50%) scale(${scale})` }">
      <!-- 顶部标题栏 -->
      <header class="s-head">
        <div class="head-side">
          <router-link class="back-link" to="/admin">← 管理端</router-link>
          <span class="head-date num">{{ dateText }}</span>
        </div>
        <div class="head-center">
          <h1>企业能碳管理驾驶舱</h1>
          <div class="head-line"></div>
        </div>
        <div class="head-side right">
          <button class="theme-toggle" :title="appStore.theme === 'dark' ? '切换白天模式' : '切换夜晚模式'" @click="appStore.toggleTheme()">
            <component :is="appStore.theme === 'dark' ? Sun : Moon" />
          </button>
          <span class="head-time num">{{ timeText }}</span>
        </div>
      </header>

      <!-- 主区域 -->
      <div class="s-main">
        <!-- 左列 -->
        <div class="s-col">
          <section class="panel">
            <div class="panel-head"><i></i>综合能耗趋势 <em>tce / 月</em></div>
            <div ref="barRef" class="panel-chart"></div>
          </section>
          <section class="panel">
            <div class="panel-head"><i></i>能源结构 <em>折标煤占比</em></div>
            <div ref="pieRef" class="panel-chart"></div>
          </section>
        </div>

        <!-- 中部桑基 -->
        <section class="panel panel-center">
          <div class="panel-head"><i></i>全厂能流全景 <em>输入 → 转换 → 分配 → 利用 · tce</em></div>
          <div ref="sankeyRef" class="panel-chart"></div>
        </section>

        <!-- 右列 -->
        <div class="s-col">
          <section class="panel">
            <div class="panel-head"><i></i>碳排放月度趋势 <em>tCO₂e</em></div>
            <div ref="carbonRef" class="panel-chart"></div>
          </section>
          <section class="panel">
            <div class="panel-head"><i></i>碳配额仪表盘 <em>履约周期内</em></div>
            <div ref="gaugeRef" class="panel-chart"></div>
          </section>
        </div>
      </div>

      <!-- 底部 KPI -->
      <footer class="s-kpis">
        <div class="s-kpi">
          <span class="k-label">综合能耗（累计）</span>
          <span class="k-value num"><Ticker :value="Number(kpi.energy?.value) || 0" /> <em>{{ kpi.energy?.unit || 'tce' }}</em></span>
          <span class="k-sub">统计区间 {{ overview.period || '--' }}</span>
        </div>
        <div class="s-kpi">
          <span class="k-label">碳排放（累计）</span>
          <span class="k-value num"><Ticker :value="Number(kpi.carbon?.value) || 0" /> <em>{{ kpi.carbon?.unit || 'tCO₂e' }}</em></span>
          <span class="k-sub">统计区间 {{ overview.period || '--' }}</span>
        </div>
        <div class="s-kpi s-kpi-live">
          <span class="k-label">实时功率 <i class="live-dot"></i></span>
          <span class="k-value num glow"><Ticker :value="Number(overview.powerRealtime) || 0" /> <em>kW</em></span>
          <span class="k-sub">每 10 秒刷新 · {{ updatedAt || '--' }}</span>
        </div>
        <div class="s-kpi">
          <span class="k-label">碳配额盈余</span>
          <span class="k-value num"><Ticker :value="Number(kpi.quotaSurplus?.value) || 0" /> <em>{{ kpi.quotaSurplus?.unit || 'tCO₂e' }}</em></span>
          <span class="k-sub">履约测算见仪表盘</span>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.screen {
  position: fixed;
  inset: 0;
  background:
    radial-gradient(1200px 600px at 50% -10%, var(--screen-radial-1), transparent 60%),
    radial-gradient(900px 500px at 100% 110%, var(--screen-radial-2), transparent 60%),
    var(--screen-bg);
  overflow: hidden;
  color: var(--screen-text);
}
/* 网格底纹 */
.screen::before {
  content: "";
  position: absolute; inset: 0;
  background-image:
    linear-gradient(var(--screen-grid-color) 1px, transparent 1px),
    linear-gradient(90deg, var(--screen-grid-color) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 85%);
  pointer-events: none;
}

.stage {
  width: 1920px; height: 1080px;
  display: flex; flex-direction: column; gap: 14px;
  padding: 18px 22px 20px;
}
.screen:not(.compact) .stage {
  position: absolute; left: 50%; top: 50%;
  transform-origin: center center;
}

/* ---------- 顶部 ---------- */
.s-head {
  height: 76px; flex-shrink: 0;
  display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;
  position: relative;
}
.head-center { text-align: center; }
.head-center h1 {
  margin: 0;
  font-size: 34px; font-weight: 700; letter-spacing: 0.28em; text-indent: 0.28em;
  background: linear-gradient(180deg, #ffffff 20%, #8fd8c9 90%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  text-shadow: 0 0 32px rgba(42, 212, 182, 0.35);
}
.head-line {
  margin: 8px auto 0; width: 460px; height: 2px;
  background: linear-gradient(90deg, transparent, rgba(42, 212, 182, 0.9), transparent);
  position: relative;
}
.head-line::after {
  content: ""; position: absolute; left: 50%; top: -3px; transform: translateX(-50%);
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--screen-accent); box-shadow: 0 0 12px var(--screen-accent);
}
.head-side { display: flex; align-items: center; gap: 12px; padding: 0 8px; }
.head-side.right { justify-content: flex-end; }
.head-date { color: var(--screen-text-secondary); font-size: 16px; letter-spacing: 0.08em; }
.back-link {
  color: var(--screen-text-secondary); text-decoration: none; font-size: 13px; letter-spacing: 0.06em;
  padding: 4px 12px; border: 1px solid var(--screen-border); border-radius: 999px;
  transition: color 0.2s ease, border-color 0.2s ease;
}
.back-link:hover { color: var(--screen-accent); border-color: var(--screen-accent); }
.head-time {
  color: var(--screen-text); font-size: 26px; letter-spacing: 0.1em;
  text-shadow: 0 0 14px var(--screen-accent);
}
.theme-toggle {
  display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--screen-border);
  background: var(--screen-card-bg); color: var(--screen-text-secondary);
  cursor: pointer; transition: color 0.2s, border-color 0.2s;
}
.theme-toggle:hover { color: var(--screen-accent); border-color: var(--screen-accent); }
.theme-toggle svg { width: 18px; height: 18px; }

/* ---------- 主区域 ---------- */
.s-main {
  flex: 1; min-height: 0;
  display: grid; grid-template-columns: 460px 1fr 460px; gap: 14px;
}
.s-col { display: grid; grid-template-rows: 1fr 1fr; gap: 14px; min-height: 0; }

.panel {
  position: relative;
  display: flex; flex-direction: column;
  min-height: 0;
  background: var(--screen-card-bg);
  border: 1px solid var(--screen-card-border);
  border-radius: 10px;
  box-shadow: inset 0 0 40px var(--screen-accent);
  backdrop-filter: blur(4px);
}
/* 四角括号装饰 */
.panel::before, .panel::after {
  content: ""; position: absolute; width: 14px; height: 14px; pointer-events: none;
}
.panel::before { left: -1px; top: -1px; border-left: 2px solid var(--screen-accent); border-top: 2px solid var(--screen-accent); border-radius: 10px 0 0 0; }
.panel::after { right: -1px; bottom: -1px; border-right: 2px solid var(--screen-accent); border-bottom: 2px solid var(--screen-accent); border-radius: 0 0 10px 0; }

.panel-head {
  flex-shrink: 0;
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px 8px;
  font-size: 16px; font-weight: 700; letter-spacing: 0.12em; color: var(--screen-text);
}
.panel-head i {
  width: 4px; height: 16px; border-radius: 2px;
  background: linear-gradient(180deg, var(--screen-accent), var(--screen-accent-2));
  box-shadow: 0 0 8px var(--screen-accent);
}
.panel-head em {
  font-style: normal; font-weight: 400; font-size: 11.5px;
  color: var(--screen-text-secondary); letter-spacing: 0.05em; margin-left: auto;
}
.panel-chart { flex: 1; min-height: 0; padding: 2px 8px 10px; }
.panel-center .panel-head { font-size: 17px; }

/* ---------- 底部 KPI ---------- */
.s-kpis {
  flex-shrink: 0; height: 118px;
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
}
.s-kpi {
  position: relative;
  display: flex; flex-direction: column; justify-content: center; gap: 4px;
  padding: 12px 22px;
  background: var(--screen-card-bg);
  border: 1px solid var(--screen-card-border);
  border-radius: 10px;
  overflow: hidden;
}
.s-kpi::before {
  content: ""; position: absolute; inset: 0 auto 0 0; width: 3px;
  background: linear-gradient(180deg, var(--screen-accent), rgba(42, 212, 182, 0));
}
.k-label { display: flex; align-items: center; gap: 6px; font-size: 13.5px; letter-spacing: 0.14em; color: var(--screen-text-secondary); }
.k-value { font-size: 34px; font-weight: 700; color: var(--screen-text); line-height: 1.15; }
.k-value em { font-style: normal; font-size: 13px; font-weight: 400; color: var(--screen-text-secondary); margin-left: 6px; }
.k-value.glow { color: var(--screen-accent); text-shadow: 0 0 22px var(--screen-accent); }
.k-sub { font-size: 12px; color: var(--screen-text-secondary); letter-spacing: 0.04em; }
.k-sub.good { color: var(--screen-accent); }
.k-sub.bad { color: #ff6b81; }
.live-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--screen-accent); box-shadow: 0 0 0 0 var(--screen-accent);
  animation: live-pulse 1.6s ease-out infinite;
}
@keyframes live-pulse {
  0% { box-shadow: 0 0 0 0 var(--screen-accent); }
  100% { box-shadow: 0 0 0 10px var(--screen-accent); }
}

/* ---------- 小屏降级：纵向堆叠 ---------- */
.screen.compact { overflow-y: auto; }
.screen.compact .stage {
  position: static; width: 100%; height: auto;
  transform: none !important; padding: 12px;
}
.screen.compact .s-head { grid-template-columns: 1fr; height: auto; gap: 4px; }
.screen.compact .head-side { display: none; }
.screen.compact .head-center h1 { font-size: 20px; letter-spacing: 0.18em; }
.screen.compact .head-line { width: 80%; }
.screen.compact .s-main { grid-template-columns: 1fr; }
.screen.compact .s-col { grid-template-rows: none; grid-auto-rows: 240px; }
.screen.compact .panel-center { min-height: 300px; }
.screen.compact .panel-chart { min-height: 200px; }
.screen.compact .s-kpis { grid-template-columns: 1fr 1fr; height: auto; }
.screen.compact .s-kpi { padding: 10px 14px; }
.screen.compact .k-value { font-size: 22px; }
</style>
