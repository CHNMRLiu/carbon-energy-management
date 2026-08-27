import client from './client'
import {
  adapOverview, adapConsumption, adapMeterCurve, adapMeterComparison, adapMeterTrend, adapUnitComparison,
  adapCalculation, adapAnalysis, adapBenchmark,
  adapFlow, adapOptimization, adapBudget, adapEmission, adapFootprint,
  adapSupplyChain, adapAudit, adapAsset, adapIngestPoints
} from './adapters'

/**
 * 全部 API 调用（前缀 /api/v1，拦截器已解包）。
 * 响应统一经过 ./adapters 适配层：以后端真实字段为准做映射并做数值兜底。
 */
export const api = {
  // 总览
  overview: () => client.get('/overview').then(adapOverview),

  // 能耗管理
  energyConsumption: (params) => client.get('/energy/consumption', { params }).then(adapConsumption),
  meterCurve: (params) => client.get('/energy/meter-curve', { params }).then(adapMeterCurve),
  meterComparison: (params) => client.get('/energy/meter-comparison', { params }).then(adapMeterComparison),
  meterTrend: (params) => client.get('/energy/meter-trend', { params }).then(adapMeterTrend),
  unitComparison: (params) => client.get('/energy/unit-comparison', { params }).then(adapUnitComparison),
  energyCalculation: (params) => client.get('/energy/calculation', { params }).then(adapCalculation),
  energyAnalysis: () => client.get('/energy/analysis').then(adapAnalysis),
  energyBenchmark: () => client.get('/energy/benchmark').then(adapBenchmark),
  energyFlow: () => client.get('/energy/flow').then(adapFlow),
  energyOptimization: () => client.get('/energy/optimization').then(adapOptimization),

  // 碳管理
  carbonBudget: () => client.get('/carbon/budget').then(adapBudget),
  carbonEmission: () => client.get('/carbon/emission').then(adapEmission),
  carbonFootprint: () => client.get('/carbon/footprint').then(adapFootprint),
  carbonSupplyChain: () => client.get('/carbon/supply-chain').then(adapSupplyChain),
  carbonAudit: () => client.get('/carbon/audit').then(adapAudit),
  carbonAsset: () => client.get('/carbon/asset').then(adapAsset),

  // 数据采集
  ingestPoints: () => client.get('/ingest/points').then(adapIngestPoints),
  ingestManual: (form) => client.post('/ingest/manual', form)
}

/** 碳核查数据导出端点（CSV，直连下载） */
export const AUDIT_EXPORT_URL = '/api/v1/carbon/audit/export'

/** 碳核查报告导出端点（text/plain 附件，直连下载） */
export const AUDIT_REPORT_URL = '/api/v1/carbon/audit/report'
