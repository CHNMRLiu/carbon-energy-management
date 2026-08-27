/**
 * Mock 数据模块（仅用于无后端时的前端验证）
 * 开关：默认关闭；浏览器控制台执行
 *   localStorage.setItem('ecms.mock', '1') 开启
 *   localStorage.setItem('ecms.mock', '0') 关闭
 * 命中 mock 路由时返回模拟响应，未命中仍走真实请求路径。
 * 注意：mock 返回结构与后端真实响应完全一致，统一由 ./adapters 适配。
 */

const DEFAULT_MOCK = false
const STORAGE_KEY = 'ecms.mock'

export function isMockEnabled() {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === '1') return true
    if (v === '0') return false
  } catch (e) {
    /* localStorage 不可用时回退默认值 */
  }
  return DEFAULT_MOCK
}

/* ---------------- 数据生成工具 ---------------- */

const AXIS_12 = ['2025-09', '2025-10', '2025-11', '2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08']

const wave = (base, i, amp = 0.14, phase = 1.7) =>
  +(base * (1 + amp * Math.sin(i * phase + (base % 7)))).toFixed(1)

const series = (base, axis = AXIS_12, amp) => axis.map((_, i) => wave(base, i, amp))

const ENERGIES = [
  { code: 'coal', name: '煤炭', unit: 'kg', ce: 0.0007143 },
  { code: 'electricity', name: '电力', unit: 'kWh', ce: 0.0001229 },
  { code: 'natural_gas', name: '天然气', unit: 'm3', ce: 0.00133 },
  { code: 'heat', name: '热力', unit: 'MJ', ce: 0.0000341 },
  { code: 'diesel', name: '柴油', unit: 'kg', ce: 0.0014571 }
]

/* ---------------- 各端点 mock（与后端真实结构一致） ---------------- */

function mockOverview() {
  return {
    period: '2026年1-8月',
    kpi: {
      comprehensive_energy: { value: 3867.1, unit: 'tce' },
      carbon_emission: { value: 11456.8, unit: 'tCO2' },
      realtime_power: { value: +(13500 + Math.random() * 1200).toFixed(0), unit: 'kW' },
      quota_surplus: { value: 14543.2, unit: 'tCO2' }
    },
    realtime_power: { value: +(13500 + Math.random() * 1200).toFixed(0), unit: 'kW', updated_at: new Date().toLocaleString('zh-CN') },
    carbon_trend: AXIS_12.map((p, i) => ({ period: p, emission: wave(1410, i, 0.05) }))
  }
}

function mockConsumption(params = {}) {
  const period = params.period === 'year' ? 'year' : 'month'
  const axis = period === 'year' ? ['2024', '2025', '2026'] : AXIS_12
  const energies = params.energy_type && params.energy_type !== 'all'
    ? ENERGIES.filter((e) => e.code === params.energy_type)
    : ENERGIES
  const details = energies.map((e, i) => {
    const quantity = wave(1000000 - i * 180000, 3) * (period === 'year' ? 12 : 1)
    return { energy_code: e.code, energy_name: e.name, unit: e.unit, quantity: +quantity.toFixed(1), ce_tce: +(quantity * e.ce).toFixed(2) }
  })
  const trend = axis.map((p, i) => {
    const by_energy = {}
    energies.forEach((e, j) => (by_energy[e.code] = wave(180 - j * 34, i)))
    return { period: p, total_tce: +Object.values(by_energy).reduce((s, v) => s + v, 0).toFixed(2), by_energy }
  })
  return {
    period,
    range: [axis[0], axis[axis.length - 1]],
    details,
    total_tce: +details.reduce((s, r) => s + r.ce_tce, 0).toFixed(2),
    trend
  }
}

function mockCalculation() {
  return {
    period: 'month',
    current_period: '2026-08',
    comprehensive_energy: { value: 495.15, unit: 'tce', yoy: 5.7, mom: 1.82 },
    unit_product_energy: { value: 33.89, unit: 'kgce/t', yoy: 1.74, mom: 2.48 },
    unit_value_energy: { value: 0.0608, unit: 'tce/万元', yoy: 1.0, mom: 3.23 },
    output: { output_t: 14609.9, output_value_wan: 8148.5 },
    compare_labels: { yoy: '2025-08', mom: '2026-07' }
  }
}

function mockAnalysis() {
  const structure = [
    { energy_code: 'coal', energy_name: '煤炭', ce_tce: 2350.72, share: 40.86 },
    { energy_code: 'electricity', energy_name: '电力', ce_tce: 1418.11, share: 24.65 },
    { energy_code: 'natural_gas', energy_name: '天然气', ce_tce: 1334.72, share: 23.2 },
    { energy_code: 'heat', energy_name: '热力', ce_tce: 498.75, share: 8.67 },
    { energy_code: 'diesel', energy_name: '柴油', ce_tce: 150.83, share: 2.62 }
  ]
  return {
    range: [AXIS_12[0], AXIS_12[AXIS_12.length - 1]],
    structure,
    cost: [
      { energy_code: 'electricity', energy_name: '电力', cost: 7846350, share: 50.77 },
      { energy_code: 'natural_gas', energy_name: '天然气', cost: 3211352, share: 20.78 },
      { energy_code: 'coal', energy_name: '煤炭', cost: 2961849, share: 19.17 },
      { energy_code: 'diesel', energy_name: '柴油', cost: 776353, share: 5.02 },
      { energy_code: 'heat', energy_name: '热力', cost: 658175, share: 4.26 }
    ],
    total_cost: 15454079,
    total_tce: 5753.13,
    efficiency_trend: AXIS_12.map((p, i) => ({ period: p, value: wave(33.3, i, 0.04) })),
    strategies: [
      { dimension: '成本优化', priority: '高', suggestion: '电力成本占比偏高，建议利用峰谷电价将高耗能工序排至谷段', expected_effect: '电费支出预计下降 5%~8%' },
      { dimension: '能效管理', priority: '高', suggestion: '单位产品能耗呈上升趋势，建议开展专项能效诊断与设备检修', expected_effect: '扭转能效劣化趋势' },
      { dimension: '用能结构', priority: '中', suggestion: '煤炭占比仍较高，建议实施煤改气/电气化替代', expected_effect: '折标煤与颗粒物排放双下降' }
    ]
  }
}

function mockBenchmark() {
  const items = [
    { category: 'product', item_code: 'P001', item_name: '精密铸件单位产品综合能耗', actual_value: 33.09, limit_value: 45.0, unit: 'kgce/t', direction: 'le', achieved: true, deviation_pct: -26.47, advice: '达标，保持当前工艺参数' },
    { category: 'process', item_code: 'ws1', item_name: '熔炼工序单位产品能耗', actual_value: 44.13, limit_value: 46.0, unit: 'kgce/t', direction: 'le', achieved: true, deviation_pct: -4.06, advice: '达标，保持当前工艺参数' },
    { category: 'process', item_code: 'ws2', item_name: '轧制工序单位产品能耗', actual_value: 34.45, limit_value: 40.0, unit: 'kgce/t', direction: 'le', achieved: true, deviation_pct: -13.86, advice: '达标，保持当前工艺参数' },
    { category: 'equipment', item_code: 'EQ001', item_name: '1#电弧炉', actual_value: 82.0, limit_value: 86.0, unit: '%', direction: 'ge', achieved: false, deviation_pct: -4.65, advice: '低于标准 4.65%，建议检修提效或更新设备' },
    { category: 'equipment', item_code: 'EQ002', item_name: '熔炼除尘风机', actual_value: 88.5, limit_value: 92.0, unit: '%', direction: 'ge', achieved: false, deviation_pct: -3.8, advice: '低于标准 3.8%，建议检修提效或更新设备' },
    { category: 'equipment', item_code: 'EQ004', item_name: '轧机主传动', actual_value: 93.5, limit_value: 92.0, unit: '%', direction: 'ge', achieved: true, deviation_pct: 1.63, advice: '达标，保持当前运行水平' }
  ]
  const achieved = items.filter((i) => i.achieved).length
  return {
    period: '2026年累计',
    items,
    summary: { total: items.length, achieved, rate: +((achieved / items.length) * 100).toFixed(2) }
  }
}

function mockFlow() {
  return {
    range: [AXIS_12[0], AXIS_12[AXIS_12.length - 1]],
    unit: 'tce',
    total_input: 5753.13,
    nodes: [
      { name: '煤炭输入' }, { name: '电力输入' }, { name: '天然气输入' }, { name: '热力输入' }, { name: '柴油输入' },
      { name: '能源转换中心' }, { name: '一车间' }, { name: '二车间' }, { name: '三车间' },
      { name: '生产利用' }, { name: '转换输配损失' }
    ],
    links: [
      { source: '煤炭输入', target: '能源转换中心', value: 2350.72 },
      { source: '电力输入', target: '能源转换中心', value: 1418.11 },
      { source: '天然气输入', target: '能源转换中心', value: 1334.72 },
      { source: '热力输入', target: '能源转换中心', value: 498.75 },
      { source: '柴油输入', target: '能源转换中心', value: 150.83 },
      { source: '能源转换中心', target: '一车间', value: 2301.25 },
      { source: '一车间', target: '生产利用', value: 2117.15 },
      { source: '一车间', target: '转换输配损失', value: 184.1 },
      { source: '能源转换中心', target: '二车间', value: 2013.6 },
      { source: '二车间', target: '生产利用', value: 1852.51 },
      { source: '二车间', target: '转换输配损失', value: 161.09 },
      { source: '能源转换中心', target: '三车间', value: 1438.28 },
      { source: '三车间', target: '生产利用', value: 1323.22 },
      { source: '三车间', target: '转换输配损失', value: 115.06 }
    ]
  }
}

function mockOptimization() {
  const suggestions = [
    { equipment: '1#电弧炉', category: '电炉', org_code: 'ws1', current: { '运行效率(%)': 82.0, '额定功率(kW)': 2200 }, suggested: { '运行效率(%)': 86.0, 措施: '提高炉衬保温与电极控制精度' }, saving_kwh: 405209, saving_tce: 49.8 },
    { equipment: '退火炉', category: '加热炉', org_code: 'ws3', current: { '运行效率(%)': 84.0, '额定功率(kW)': 800 }, suggested: { '运行效率(%)': 88.0, 措施: '回收烟气余热预热助燃空气' }, saving_kwh: 144000, saving_tce: 17.7 },
    { equipment: '1#空压机', category: '空压机', org_code: 'ws1', current: { '运行效率(%)': 89.0, '额定功率(kW)': 450 }, suggested: { '运行效率(%)': 93.0, 措施: '下调出口压力设定值，治理管网泄漏' }, saving_kwh: 76645, saving_tce: 9.42 }
  ]
  return {
    suggestions,
    total_saving_tce: +suggestions.reduce((s, x) => s + x.saving_tce, 0).toFixed(2),
    total_saving_kwh: suggestions.reduce((s, x) => s + x.saving_kwh, 0),
    equipment_count: 9
  }
}

function mockBudget() {
  return {
    year: 2026,
    period_label: '2026年1-8月',
    energy: { type: 'energy', budget: 5624.6, actual: 3867.1, rate: 68.8, time_progress: 66.7, forecast_year_end: 5879.2, status: '超预算预警' },
    carbon: { type: 'carbon', budget: 26000, actual: 11456.8, rate: 44.1, time_progress: 66.7, forecast_year_end: 17396.1, status: '正常' },
    alerts: [{ level: 'warning', message: '全年用能预测 5879.0 tce 超出预算 5624.6 tce' }]
  }
}

function mockEmission() {
  return {
    range: [AXIS_12[0], AXIS_12[AXIS_12.length - 1]],
    total: 17057.0,
    unit: 'tCO2',
    intensity: 0.0985,
    intensity_unit: 'tCO2/t产品',
    breakdown: [
      { energy_code: 'electricity', energy_name: '电力', emission: 6704.01, share: 39.3 },
      { energy_code: 'coal', energy_name: '煤炭', emission: 6253.78, share: 36.66 },
      { energy_code: 'natural_gas', energy_name: '天然气', emission: 2169.87, share: 12.72 },
      { energy_code: 'heat', energy_name: '热力', emission: 1608.87, share: 9.43 },
      { energy_code: 'diesel', energy_name: '柴油', emission: 320.47, share: 1.88 }
    ],
    trend: AXIS_12.map((p, i) => ({ period: p, emission: wave(1410, i, 0.05) })),
    alerts: []
  }
}

function mockFootprint() {
  return {
    product: '精密铸件',
    standard: 'GB/T 24067',
    range: [AXIS_12[0], AXIS_12[AXIS_12.length - 1]],
    stages: [
      { stage: 'raw_material', stage_name: '原材料获取', emission: 6447.55, share: 42.0 },
      { stage: 'production', stage_name: '生产制造', emission: 4758.9, share: 31.0 },
      { stage: 'transport', stage_name: '运输配送', emission: 1074.59, share: 7.0 },
      { stage: 'use', stage_name: '使用阶段', emission: 2149.18, share: 14.0 },
      { stage: 'recycle', stage_name: '回收处置', emission: 921.08, share: 6.0 }
    ],
    total_emission: 15351.3,
    total_output: 173121.7,
    unit_footprint: 88.673,
    unit_footprint_unit: 'kgCO2e/t',
    label: { grade: 'A', description: '一级（国际先进）', benchmark: 180.0 }
  }
}

function mockSupplyChain() {
  return {
    items: [
      { company: '宏达矿业', direction: '上游', link: '原材料供应-生铁', product: '生铁', emission: 5200, data_status: 'verified', period: '2026' },
      { company: '绿源再生资源', direction: '上游', link: '原材料供应-废钢', product: '废钢', emission: 1150, data_status: 'verified', period: '2026' },
      { company: '中天物流', direction: '上游', link: '原料运输', product: '运输服务', emission: 480, data_status: 'reported', period: '2026' },
      { company: '精工装备制造', direction: '下游', link: '产品使用', product: '精密铸件', emission: 2600, data_status: 'reported', period: '2026' },
      { company: '华成机械', direction: '下游', link: '产品使用', product: '精密铸件', emission: 1900, data_status: 'pending', period: '2026' }
    ],
    summary: { upstream_total: 6830, downstream_total: 4500, verified_count: 2, total: 5 }
  }
}

function mockAudit() {
  return {
    period_label: '2026-01 ~ 2026-08',
    total_emission: 11456.78,
    items: [
      { energy_code: 'electricity', energy_name: '电力', unit: 'kWh', quantity: 7756476.4, factor: 0.000581, emission: 4506.51, collect_method: '仪表采集', source: 'GB/T 32151', period_label: '2026-01 ~ 2026-08' },
      { energy_code: 'coal', energy_name: '煤炭', unit: 'kg', quantity: 2219364, factor: 0.0019003, emission: 4217.46, collect_method: '系统对接', source: 'GB/T 32151', period_label: '2026-01 ~ 2026-08' },
      { energy_code: 'natural_gas', energy_name: '天然气', unit: 'm3', quantity: 676962.8, factor: 0.0021622, emission: 1463.73, collect_method: '系统对接', source: 'GB/T 32151', period_label: '2026-01 ~ 2026-08' }
    ],
    standards: [
      { code: 'GB/T 2589', name: '综合能耗计算通则', scope: '折标煤/综合能耗' },
      { code: 'GB/T 32151', name: '温室气体排放核算与报告要求', scope: '企业碳排放核算' }
    ],
    data_basis: { meter_readings: 2292, manual_reports: 8, methods: ['仪表采集', '手工填报', '烟感实测', '系统对接'] },
    recent_alerts: []
  }
}

function mockAsset() {
  return {
    year: 2026,
    quota: 26000,
    actual: 11456.8,
    surplus: 14543.2,
    usage_rate: 44.1,
    forecast_year_end: 17396.1,
    compliance_deadline: '2026-12-31',
    status: '盈余充足',
    alerts: [],
    history: [{ year: 2025, quota: 27000, actual_emission: 16524.7, surplus: 10475.3, status: '已履约' }]
  }
}

function mockIngestPoints() {
  return {
    total: 4,
    methods: ['系统对接', '仪表采集', '手工填报', '烟感实测'],
    items: [
      { id: 1, code: 'EP001', name: '煤场皮带秤', energy_code: 'coal', org_code: 'ws1', collect_method: '系统对接', unit: 'kg/h', status: 'normal' },
      { id: 2, code: 'EP010', name: '全厂总进线电表', energy_code: 'electricity', org_code: '', collect_method: '仪表采集', unit: 'kW', status: 'normal' },
      { id: 3, code: 'EP020', name: '柴油储罐库存填报', energy_code: 'diesel', org_code: '', collect_method: '手工填报', unit: 'kg', status: 'normal' },
      { id: 4, code: 'EP030', name: '烟囱CEMS在线监测', energy_code: 'electricity', org_code: '', collect_method: '烟感实测', unit: 'kg/h', status: 'normal' }
    ]
  }
}

/* ---------------- 路由分发 ---------------- */

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const ROUTES = [
  ['GET', /^\/overview$/, mockOverview],
  ['GET', /^\/energy\/consumption$/, mockConsumption],
  ['GET', /^\/energy\/calculation$/, mockCalculation],
  ['GET', /^\/energy\/analysis$/, mockAnalysis],
  ['GET', /^\/energy\/benchmark$/, mockBenchmark],
  ['GET', /^\/energy\/flow$/, mockFlow],
  ['GET', /^\/energy\/optimization$/, mockOptimization],
  ['GET', /^\/carbon\/budget$/, mockBudget],
  ['GET', /^\/carbon\/emission$/, mockEmission],
  ['GET', /^\/carbon\/footprint$/, mockFootprint],
  ['GET', /^\/carbon\/supply-chain$/, mockSupplyChain],
  ['GET', /^\/carbon\/audit$/, mockAudit],
  ['GET', /^\/carbon\/asset$/, mockAsset],
  ['GET', /^\/ingest\/points$/, mockIngestPoints],
  ['POST', /^\/ingest\/manual$/, (params) => ({ id: 1, point_code: params?.point_code || '', period: params?.period || '' })]
]

export async function handleMock(config) {
  const method = (config.method || 'get').toUpperCase()
  const path = (config.url || '').split('?')[0]
  const hit = ROUTES.find(([m, re]) => m === method && re.test(path))
  if (!hit) return null
  await sleep(160 + Math.random() * 240)
  return {
    data: { code: 0, message: 'ok', data: hit[2](config.params || config.data || {}) },
    status: 200,
    statusText: 'OK',
    headers: {},
    config
  }
}
