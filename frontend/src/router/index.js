import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/admin' },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/admin/energy/consumption',
    children: [
      // 能耗管理（功能 1-6）
      { path: 'energy/consumption', name: 'EnergyConsumption', component: () => import('@/views/admin/EnergyConsumption.vue'), meta: { title: '能耗查询' } },
      { path: 'energy/calculation', name: 'EnergyCalculation', component: () => import('@/views/admin/EnergyCalculation.vue'), meta: { title: '能耗计算' } },
      { path: 'energy/analysis', name: 'EnergyAnalysis', component: () => import('@/views/admin/EnergyAnalysis.vue'), meta: { title: '用能分析与策略推荐' } },
      { path: 'energy/benchmark', name: 'EnergyBenchmark', component: () => import('@/views/admin/EnergyBenchmark.vue'), meta: { title: '能效对标' } },
      { path: 'energy/flow', name: 'EnergyFlow', component: () => import('@/views/admin/EnergyFlow.vue'), meta: { title: '能流分析' } },
      { path: 'energy/optimization', name: 'EnergyOptimization', component: () => import('@/views/admin/EnergyOptimization.vue'), meta: { title: '能效平衡与优化' } },
      // 碳管理（功能 7-12）
      { path: 'carbon/budget', name: 'CarbonBudget', component: () => import('@/views/admin/CarbonBudget.vue'), meta: { title: '碳预算管理' } },
      { path: 'carbon/emission', name: 'CarbonEmission', component: () => import('@/views/admin/CarbonEmission.vue'), meta: { title: '碳排放核算' } },
      { path: 'carbon/footprint', name: 'CarbonFootprint', component: () => import('@/views/admin/CarbonFootprint.vue'), meta: { title: '产品碳足迹' } },
      { path: 'carbon/supply-chain', name: 'CarbonSupplyChain', component: () => import('@/views/admin/CarbonSupplyChain.vue'), meta: { title: '供应链碳管理' } },
      { path: 'carbon/audit', name: 'CarbonAudit', component: () => import('@/views/admin/CarbonAudit.vue'), meta: { title: '碳核查支撑' } },
      { path: 'carbon/asset', name: 'CarbonAsset', component: () => import('@/views/admin/CarbonAsset.vue'), meta: { title: '碳资产管理' } },
      // 数据采集
      { path: 'ingest', name: 'DataIngest', component: () => import('@/views/admin/DataIngest.vue'), meta: { title: '数据采集与填报' } }
    ]
  },
  {
    path: '/screen',
    component: () => import('@/layouts/ScreenLayout.vue'),
    children: [
      { path: '', name: 'ScreenDashboard', component: () => import('@/views/screen/Dashboard.vue'), meta: { title: '能碳驾驶舱' } }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/admin' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  const base = '长沙水泵厂能碳管理中心'
  document.title = to.meta?.title ? `${to.meta.title} · ${base}` : base
})

export default router
