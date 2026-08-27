/**
 * API 集中适配层：以后端真实响应为唯一事实来源，
 * 将后端字段统一转换为页面所需结构，并对所有数值做兜底（null/undefined → 0），
 * 避免页面出现 NaN / -- / 空表。页面只消费这里输出的结构。
 */

/** 能源编码 → 中文名 */
export const ENERGY_NAME = {
  electricity: '电力',
  natural_gas: '天然气',
  coal: '煤炭',
  heat: '热力',
  diesel: '柴油'
}

/** 能耗查询能源类型下拉（value 为后端 energy_code） */
export const ENERGY_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: 'electricity', label: '电力' },
  { value: 'natural_gas', label: '天然气' },
  { value: 'coal', label: '煤炭' },
  { value: 'heat', label: '热力' },
  { value: 'diesel', label: '柴油' }
]

/** 数值兜底：非有限数返回 fallback */
export function num(v, fallback = 0) {
  const n = Number(v)
  return Number.isFinite(n) ? n : fallback
}

/** 组织编码 → 名称 */
const ORG_NAME = { ws1: '一车间', ws2: '二车间', ws3: '三车间' }
export const orgName = (code) => ORG_NAME[code] || code || '全厂'

/* ---------------- 枚举翻译 ---------------- */

const POINT_STATUS = { normal: '正常', offline: '离线', alarm: '报警', fault: '故障' }
const DATA_STATUS = { verified: '已核查', reported: '已上报', pending: '待上报' }
const ALERT_LEVEL = { danger: '红色', error: '红色', warning: '黄色', info: '蓝色' }

export const pointStatusText = (s) => POINT_STATUS[s] || s || '--'
export const dataStatusText = (s) => DATA_STATUS[s] || s || '--'
export const alertLevelText = (l) => ALERT_LEVEL[l] || l || '提示'

/** 预警规范化：{level(中文), content} */
function adapAlerts(alerts) {
  return (Array.isArray(alerts) ? alerts : []).map((a) => ({
    level: alertLevelText(a?.level),
    content: a?.message || a?.content || '--'
  }))
}

/* ---------------- 总览（大屏） ---------------- */

export function adapOverview(d = {}) {
  const kpi = d.kpi || {}
  const rt = d.realtime_power || {}
  const trend = Array.isArray(d.carbon_trend) ? d.carbon_trend : []
  return {
    period: d.period || '',
    kpi: {
      energy: kpi.comprehensive_energy || { value: 0, unit: 'tce' },
      carbon: kpi.carbon_emission || { value: 0, unit: 'tCO2' },
      quotaSurplus: kpi.quota_surplus || { value: 0, unit: 'tCO2' }
    },
    powerRealtime: num(kpi.realtime_power?.value ?? rt.value),
    powerUpdatedAt: rt.updated_at || '',
    carbonTrend: {
      axis: trend.map((t) => t.period),
      data: trend.map((t) => num(t.emission))
    }
  }
}

/* ---------------- 能耗查询 ---------------- */

export function adapConsumption(d = {}) {
  const details = (Array.isArray(d.details) ? d.details : []).map((r) => ({
    energy_code: r.energy_code,
    energy_name: r.energy_name || ENERGY_NAME[r.energy_code] || r.energy_code,
    unit: r.unit || '',
    quantity: num(r.quantity),
    ce_tce: num(r.ce_tce)
  }))
  const trend = Array.isArray(d.trend) ? d.trend : []
  const totalTce = num(d.total_tce, details.reduce((s, r) => s + r.ce_tce, 0))

  // 分能源堆叠序列（折标煤口径）
  const codes = []
  trend.forEach((t) => Object.keys(t.by_energy || {}).forEach((c) => !codes.includes(c) && codes.push(c)))
  const series = codes.map((code) => ({
    code,
    name: ENERGY_NAME[code] || code,
    data: trend.map((t) => num(t.by_energy?.[code]))
  }))

  return {
    period: d.period,
    range: d.range || [],
    total_tce: totalTce,
    details: details.map((r) => ({
      ...r,
      share: totalTce ? +((r.ce_tce / totalTce) * 100).toFixed(2) : 0
    })),
    trend: {
      axis: trend.map((t) => t.period),
      totals: trend.map((t) => num(t.total_tce)),
      series
    }
  }
}

/* ---------------- 单器具曲线查询（新增） ---------------- */

export function adapMeterCurve(d = {}) {
  return {
    point_code: d.point_code || '--',
    point_name: d.point_name || '--',
    energy_code: d.energy_code || '--',
    energy_name: d.energy_name || '--',
    period: d.period || 'day',
    dimension: d.dimension || 'energy',
    data: (Array.isArray(d.data) ? d.data : []).map((item) => ({
      time: item.time || '--',
      value: num(item.value),
      unit: item.unit || ''
    }))
  }
}

/* ---------------- 计量对标/计量环比/单元对标（新增） ---------------- */

export function adapMeterComparison(d = {}) {
  const m1 = d.meter1 || {}
  const m2 = d.meter2 || {}
  const comp = d.comparison || {}
  
  return {
    meter1: {
      id: m1.id,
      code: m1.code,
      name: m1.name || '计量点1',
      energy_code: m1.energy_code,
      energy_name: ENERGY_NAME[m1.energy_code] || m1.energy_code,
      unit: m1.unit || '',
      total: num(m1.total),
      series: Array.isArray(m1.series) ? m1.series : []
    },
    meter2: {
      id: m2.id,
      code: m2.code,
      name: m2.name || '计量点2',
      energy_code: m2.energy_code,
      energy_name: ENERGY_NAME[m2.energy_code] || m2.energy_code,
      unit: m2.unit || '',
      total: num(m2.total),
      series: Array.isArray(m2.series) ? m2.series : []
    },
    comparison: {
      difference: num(comp.difference),
      diff_percent: num(comp.diff_percent),
      higher: comp.higher,
      time_labels: Array.isArray(comp.time_labels) ? comp.time_labels : []
    }
  }
}

export function adapMeterTrend(d = {}) {
  const meter = d.meter || {}
  const trend = d.trend || {}
  
  return {
    meter: {
      id: meter.id,
      code: meter.code,
      name: meter.name || '未知计量点',
      energy_code: meter.energy_code,
      energy_name: ENERGY_NAME[meter.energy_code] || meter.energy_code,
      unit: meter.unit || ''
    },
    trend: {
      period_type: trend.period_type,
      period_names: Array.isArray(trend.period_names) ? trend.period_names : [],
      values: Array.isArray(trend.values) ? trend.values : [],
      change: num(trend.change),
      change_percent: num(trend.change_percent)
    }
  }
}

export function adapUnitComparison(d = {}) {
  const u1 = d.unit1 || {}
  const u2 = d.unit2 || {}
  const comp = d.comparison || {}
  
  const adaptDetails = (details) => {
    return (Array.isArray(details) ? details : []).map((r) => ({
      energy_code: r.energy_code,
      energy_name: r.energy_name || ENERGY_NAME[r.energy_code] || r.energy_code,
      unit: r.unit || '',
      quantity: num(r.quantity),
      ce_tce: num(r.ce_quantity)
    }))
  }
  
  return {
    unit1: {
      code: u1.code,
      name: u1.name || '用能单元1',
      total_ce_tce: num(u1.total_ce_tce),
      details: adaptDetails(u1.details)
    },
    unit2: {
      code: u2.code,
      name: u2.name || '用能单元2',
      total_ce_tce: num(u2.total_ce_tce),
      details: adaptDetails(u2.details)
    },
    comparison: {
      difference: num(comp.difference),
      diff_percent: num(comp.diff_percent),
      higher: comp.higher
    }
  }
}

/* ---------------- 能耗计算 ---------------- */

export function adapCalculation(d = {}) {
  const pick = (o = {}) => ({
    value: num(o.value),
    unit: o.unit || '',
    yoy: o.yoy === null || o.yoy === undefined ? null : num(o.yoy),
    mom: o.mom === null || o.mom === undefined ? null : num(o.mom)
  })
  return {
    period: d.period,
    current_period: d.current_period || '--',
    comprehensive: pick(d.comprehensive_energy),
    unitProduct: pick(d.unit_product_energy),
    unitOutput: pick(d.unit_value_energy),
    output: {
      output_t: num(d.output?.output_t),
      output_value_wan: num(d.output?.output_value_wan)
    },
    compare_labels: d.compare_labels || {}
  }
}

/* ---------------- 用能分析与策略 ---------------- */

export function adapAnalysis(d = {}) {
  const structure = (Array.isArray(d.structure) ? d.structure : []).map((r) => ({
    energy_code: r.energy_code,
    name: r.energy_name || ENERGY_NAME[r.energy_code] || r.energy_code,
    value: num(r.ce_tce),
    share: num(r.share)
  }))
  const cost = (Array.isArray(d.cost) ? d.cost : []).map((r) => ({
    energy_code: r.energy_code,
    name: r.energy_name || ENERGY_NAME[r.energy_code] || r.energy_code,
    value: +(num(r.cost) / 10000).toFixed(1), // 元 → 万元
    share: num(r.share)
  }))
  const eff = Array.isArray(d.efficiency_trend) ? d.efficiency_trend : []
  return {
    range: d.range || [],
    structure,
    cost,
    total_cost: num(d.total_cost), // 元
    total_cost_wan: +(num(d.total_cost) / 10000).toFixed(1),
    total_tce: num(d.total_tce),
    efficiency: {
      axis: eff.map((t) => t.period),
      series: [{ name: '单位产品能耗 (kgce/t)', data: eff.map((t) => num(t.value)) }]
    },
    strategies: (Array.isArray(d.strategies) ? d.strategies : []).map((s) => ({
      dimension: s.dimension || '--',
      priority: s.priority || '中',
      suggestion: s.suggestion || '--',
      expected_effect: s.expected_effect || '--'
    }))
  }
}

/* ---------------- 能效对标 ---------------- */

const CATEGORY_LABEL = { product: '产品对标', process: '工序对标', equipment: '设备对标' }

export function adapBenchmark(d = {}) {
  const items = (Array.isArray(d.items) ? d.items : []).map((r) => ({
    category: r.category,
    item_code: r.item_code,
    name: r.item_name || '--',
    actual: num(r.actual_value),
    limit: num(r.limit_value),
    unit: r.unit || '',
    direction: r.direction,
    pass: !!r.achieved,
    gap: num(r.deviation_pct),
    advice: r.advice || '--'
  }))
  const group = (cat) => items.filter((i) => i.category === cat)
  const summary = d.summary || {}
  return {
    period: d.period || '',
    product: group('product'),
    process: group('process'),
    equipment: group('equipment'),
    categoryLabel: CATEGORY_LABEL,
    summary: {
      total: num(summary.total, items.length),
      achieved: num(summary.achieved, items.filter((i) => i.pass).length),
      rate: num(summary.rate)
    }
  }
}

/* ---------------- 能流分析 ---------------- */

export function adapFlow(d = {}) {
  return {
    unit: d.unit || 'tce',
    total_input: num(d.total_input),
    nodes: Array.isArray(d.nodes) ? d.nodes : [],
    links: (Array.isArray(d.links) ? d.links : []).map((l) => ({
      source: l.source,
      target: l.target,
      value: num(l.value)
    }))
  }
}

/* ---------------- 能效优化 ---------------- */

export function adapOptimization(d = {}) {
  const items = (Array.isArray(d.suggestions) ? d.suggestions : []).map((s) => {
    const current = s.current || {}
    const suggested = s.suggested || {}
    const param = Object.keys(suggested).find((k) => k !== '措施') || Object.keys(current)[0] || '--'
    return {
      device: s.equipment || '--',
      category: s.category || '--',
      org: orgName(s.org_code),
      param,
      current: current[param] ?? '--',
      suggested: suggested[param] ?? '--',
      measure: suggested['措施'] || '--',
      saving: num(s.saving_tce),
      saving_kwh: num(s.saving_kwh),
      unit: 'tce/年',
      status: '待执行'
    }
  })
  return {
    totalSaving: num(d.total_saving_tce),
    totalSavingKwh: num(d.total_saving_kwh),
    equipmentCount: num(d.equipment_count, items.length),
    items
  }
}

/* ---------------- 碳预算 ---------------- */

export function adapBudget(d = {}) {
  const pick = (o = {}, unit) => ({
    budget: num(o.budget),
    used: num(o.actual),
    rate: num(o.rate),
    time_progress: num(o.time_progress),
    forecast: num(o.forecast_year_end),
    unit: unit,
    status: o.status || '--'
  })
  return {
    year: d.year,
    period_label: d.period_label || '',
    energy: pick(d.energy, 'tce'),
    carbon: pick(d.carbon, 'tCO₂e'),
    warnings: adapAlerts(d.alerts)
  }
}

/* ---------------- 碳排放核算 ---------------- */

export function adapEmission(d = {}) {
  const trend = Array.isArray(d.trend) ? d.trend : []
  const breakdown = (Array.isArray(d.breakdown) ? d.breakdown : []).map((r) => ({
    name: r.energy_name || ENERGY_NAME[r.energy_code] || r.energy_code,
    value: num(r.emission),
    share: num(r.share)
  }))
  return {
    range: d.range || [],
    total: num(d.total),
    unit: d.unit || 'tCO₂e',
    intensity: num(d.intensity),
    intensity_unit: d.intensity_unit || '',
    bySource: breakdown,
    topSource: breakdown[0] || null,
    trend: {
      axis: trend.map((t) => t.period),
      data: trend.map((t) => num(t.emission))
    },
    items: trend.map((t) => ({ period: t.period, emission: num(t.emission) })),
    warnings: adapAlerts(d.alerts)
  }
}

/* ---------------- 产品碳足迹 ---------------- */

export function adapFootprint(d = {}) {
  const stages = (Array.isArray(d.stages) ? d.stages : []).map((s) => ({
    stage: s.stage_name || s.stage || '--',
    value: num(s.emission),
    share: num(s.share)
  }))
  return {
    product: d.product || '--',
    standard: d.standard || '--',
    range: d.range || [],
    stages,
    total: num(d.total_emission, stages.reduce((s, x) => s + x.value, 0)),
    total_output: num(d.total_output),
    unitFootprint: num(d.unit_footprint),
    unit: d.unit_footprint_unit || 'kgCO₂e/t',
    label: {
      grade: d.label?.grade || '--',
      description: d.label?.description || '',
      benchmark: num(d.label?.benchmark)
    }
  }
}

/* ---------------- 供应链碳 ---------------- */

export function adapSupplyChain(d = {}) {
  const mapItem = (r) => ({
    name: r.company || '--',
    scope: r.link || '--',
    product: r.product || '--',
    emission: num(r.emission),
    dataQuality: dataStatusText(r.data_status),
    period: r.period || '--'
  })
  const items = Array.isArray(d.items) ? d.items : []
  const upstream = items.filter((r) => r.direction === '上游').map(mapItem)
  const downstream = items.filter((r) => r.direction === '下游').map(mapItem)
  const all = [...upstream, ...downstream]
  const summary = d.summary || {}
  return {
    upstream,
    downstream,
    topEmitters: [...all].sort((a, b) => b.emission - a.emission).slice(0, 5)
      .map((r) => ({ name: r.name, value: r.emission })),
    summary: {
      upstream_total: num(summary.upstream_total, upstream.reduce((s, r) => s + r.emission, 0)),
      downstream_total: num(summary.downstream_total, downstream.reduce((s, r) => s + r.emission, 0)),
      verified_count: num(summary.verified_count),
      total: num(summary.total, all.length)
    }
  }
}

/* ---------------- 碳核查 ---------------- */

export function adapAudit(d = {}) {
  const items = (Array.isArray(d.items) ? d.items : []).map((r) => ({
    energy_code: r.energy_code,
    energy_name: r.energy_name || ENERGY_NAME[r.energy_code] || r.energy_code,
    unit: r.unit || '',
    quantity: num(r.quantity),
    factor: num(r.factor),
    emission: num(r.emission),
    collect_method: r.collect_method || '--',
    source: r.source || '--',
    period_label: r.period_label || d.period_label || '--'
  }))
  const basis = d.data_basis || {}
  return {
    period_label: d.period_label || '--',
    total: num(d.total_emission, items.reduce((s, r) => s + r.emission, 0)),
    records: items,
    standards: Array.isArray(d.standards) ? d.standards : [],
    dataBasis: {
      meter_readings: num(basis.meter_readings),
      manual_reports: num(basis.manual_reports),
      methods: Array.isArray(basis.methods) ? basis.methods : []
    },
    recent_alerts: adapAlerts(d.recent_alerts)
  }
}

/* ---------------- 碳资产 ---------------- */

export function adapAsset(d = {}) {
  return {
    year: d.year,
    quota: num(d.quota),
    emitted: num(d.actual),
    surplus: num(d.surplus),
    usage_rate: num(d.usage_rate),
    forecast_year_end: num(d.forecast_year_end),
    forecast_surplus: num(d.quota) - num(d.forecast_year_end),
    compliance_deadline: d.compliance_deadline || '--',
    status: d.status || '--',
    alerts: adapAlerts(d.alerts),
    history: (Array.isArray(d.history) ? d.history : []).map((h) => ({
      year: String(h.year),
      quota: num(h.quota),
      actual_emission: num(h.actual_emission),
      surplus: num(h.surplus),
      status: h.status || '--'
    }))
  }
}

/* ---------------- 数据采集 ---------------- */

export function adapIngestPoints(d = {}) {
  const items = (Array.isArray(d.items) ? d.items : []).map((p) => ({
    id: p.id,
    code: p.code || '--',
    name: p.name || '--',
    energy_code: p.energy_code,
    energy_name: ENERGY_NAME[p.energy_code] || p.energy_code || '--',
    org: orgName(p.org_code),
    collect_method: p.collect_method || '--',
    unit: p.unit || '--',
    statusRaw: p.status,
    status: pointStatusText(p.status)
  }))
  const online = items.filter((p) => p.statusRaw === 'normal').length
  return {
    items,
    methods: Array.isArray(d.methods) ? d.methods : [],
    summary: {
      total: num(d.total, items.length),
      online,
      onlineRate: items.length ? +((online / items.length) * 100).toFixed(1) : 0,
      methodCount: Array.isArray(d.methods) ? d.methods.length : 0
    }
  }
}
