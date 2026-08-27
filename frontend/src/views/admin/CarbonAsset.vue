<script setup>
import { onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'
import { ElMessage, ElDialog, ElForm, ElFormItem, ElInput, ElRadioGroup, ElRadio, ElButton } from 'element-plus'

const loading = ref(false)
const data = ref({})

// 碳价与交易相关状态
const carbonPrice = ref(0) // 实时碳价（元/tCO₂）
const priceHistory = ref([]) // 碳价历史趋势
const showTradeDialog = ref(false)
const tradeForm = ref({
  type: 'buy', // buy | sell
  amount: 0,
  price: 0
})
const tradeRecords = ref([]) // 交易记录

const gaugeRef = ref(null)
const trendRef = ref(null)

const columns = [
  { prop: 'level', label: '级别', width: 100, align: 'center', slot: true },
  { prop: 'content', label: '预警内容', minWidth: 360 }
]

const LEVEL_TYPE = { 红色: 'danger', 橙色: 'warning', 黄色: 'warning', 蓝色: 'info' }

function renderGauge(rate) {
  if (!gaugeRef.value || rate === undefined) return
  gaugeRef.value.setOption({
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        radius: '92%',
        progress: { show: true, width: 16, roundCap: true, itemStyle: { color: rate > 90 ? '#d64545' : '#0c8f7a' } },
        axisLine: { lineStyle: { width: 16, color: [[1, '#eef2f0']] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        pointer: { show: false },
        anchor: { show: false },
        title: { show: true, offsetCenter: [0, '34%'], fontSize: 13, color: '#55655f' },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, '2%'],
          fontSize: 30,
          fontWeight: 700,
          fontFamily: 'Bahnschrift, "DIN Alternate", sans-serif',
          color: '#16241f',
          formatter: '{value}%'
        },
        data: [{ value: rate, name: '配额使用率' }]
      }
    ]
  })
}

function renderHistory(history) {
  if (!history?.length || !trendRef.value) return
  trendRef.value.setOption({
    color: [PALETTE[3], PALETTE[0]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, textStyle: { color: '#55655f', fontSize: 12 } },
    grid: { left: 12, right: 20, top: 36, bottom: 8, containLabel: true },
    xAxis: { type: 'category', data: history.map((h) => `${h.year}年`), axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    yAxis: { type: 'value', name: 'tCO₂e', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      { name: '年度配额', type: 'bar', barWidth: 26, itemStyle: { borderRadius: [6, 6, 0, 0] }, data: history.map((h) => h.quota) },
      { name: '实际排放', type: 'bar', barWidth: 26, itemStyle: { borderRadius: [6, 6, 0, 0] }, data: history.map((h) => h.actual_emission) }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.carbonAsset()
    renderGauge(data.value.usage_rate)
    renderHistory(data.value.history)
    
    // 模拟碳价数据（实际应从 API 获取）
    carbonPrice.value = 68.5 // 当前碳价 68.5 元/tCO₂
    priceHistory.value = [
      { date: '2024-01', price: 62.3 },
      { date: '2024-02', price: 63.8 },
      { date: '2024-03', price: 65.2 },
      { date: '2024-04', price: 64.7 },
      { date: '2024-05', price: 66.1 },
      { date: '2024-06', price: 67.5 },
      { date: '2024-07', price: 68.5 }
    ]
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

// 交易相关函数
function openTradeDialog() {
  showTradeDialog.value = true
  tradeForm.value = {
    type: 'buy',
    amount: 0,
    price: carbonPrice.value
  }
}

function submitTrade() {
  if (!tradeForm.value.amount || tradeForm.value.amount <= 0) {
    ElMessage.warning('请输入有效的交易数量')
    return
  }
  
  const totalAmount = tradeForm.value.amount * tradeForm.value.price
  const actionText = tradeForm.value.type === 'buy' ? '买入' : '卖出'
  
  const record = {
    id: Date.now(),
    time: new Date().toLocaleString('zh-CN'),
    type: tradeForm.value.type,
    typeText: actionText,
    amount: tradeForm.value.amount,
    price: tradeForm.value.price,
    total: totalAmount
  }
  
  tradeRecords.value.unshift(record)
  showTradeDialog.value = false
  ElMessage.success(`${actionText} ${tradeForm.value.amount} tCO₂ 成功，总金额 ${totalAmount.toFixed(2)} 元`)
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>碳资产管理</h2>
        <p>配额管理、履约测算、预测预警 · {{ data.year || '--' }} 年度履约周期，截止 {{ data.compliance_deadline || '--' }}</p>
      </div>
      <div style="display: flex; gap: 12px; align-items: center;">
        <el-tag v-if="carbonPrice > 0" type="success" size="large" effect="dark">
          当前碳价：{{ carbonPrice }} 元/tCO₂
        </el-tag>
        <el-button type="primary" @click="openTradeDialog">
          碳交易模拟
        </el-button>
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="年度配额" :value="data.quota ?? '--'" unit="tCO₂e" :decimals="0" accent="brand" />
      <KpiCard label="已排放" :value="data.emitted ?? '--'" unit="tCO₂e" :decimals="0" accent="danger" />
      <KpiCard label="配额盈余" :value="data.surplus ?? '--'" unit="tCO₂e" :decimals="0" accent="blue" sub="盈余可参与交易" />
      <KpiCard label="年底排放预测" :value="data.forecast_year_end ?? '--'" unit="tCO₂e" :decimals="0" accent="amber" :sub="`预计年底盈余 ${(data.forecast_surplus ?? 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 })} tCO₂e`" />
    </div>

    <div class="two-col">
      <ChartCard ref="gaugeRef" title="配额履约测算" desc="履约截止日（含清缴）" :loading="loading" height="300px">
        <template #extra>
          <el-tag type="info" size="small" effect="plain">截止 {{ data.compliance_deadline || '--' }}</el-tag>
        </template>
      </ChartCard>
      <ChartCard ref="trendRef" title="配额与实际排放对比" desc="年度口径 · tCO₂e" :loading="loading" height="300px" />
    </div>

    <DataTable title="碳资产预警" :columns="columns" :data="data.alerts || []" :loading="loading" show-index empty-text="当前无预警，配额盈余充足，系统持续监控中">
      <template #col-level="{ row }">
        <el-tag :type="LEVEL_TYPE[row.level] || 'info'" size="small" effect="dark">{{ row.level }}</el-tag>
      </template>
    </DataTable>

    <!-- 交易记录表格 -->
    <DataTable 
      v-if="tradeRecords.length > 0"
      title="碳交易记录" 
      :columns="[
        { prop: 'time', label: '交易时间', width: 180 },
        { prop: 'typeText', label: '操作类型', width: 100, align: 'center', slot: true },
        { prop: 'amount', label: '数量 (tCO₂)', width: 130, align: 'right', formatter: (r) => r.amount.toFixed(2) },
        { prop: 'price', label: '单价 (元/tCO₂)', width: 140, align: 'right', formatter: (r) => r.price.toFixed(2) },
        { prop: 'total', label: '总金额 (元)', width: 140, align: 'right', formatter: (r) => r.total.toFixed(2) }
      ]" 
      :data="tradeRecords" 
      :loading="false" 
      show-index
    >
      <template #col-typeText="{ row }">
        <el-tag :type="row.type === 'buy' ? 'danger' : 'success'" size="small" effect="dark">
          {{ row.typeText }}
        </el-tag>
      </template>
    </DataTable>

    <!-- 碳交易对话框 -->
    <el-dialog v-model="showTradeDialog" title="碳交易模拟" width="500px">
      <div style="margin-bottom: 20px; padding: 16px; background: #f5f7fa; border-radius: 8px;">
        <p style="margin: 0; color: #666; font-size: 14px;">
          当前市场碳价：<strong style="color: #0c8f7a; font-size: 18px;">{{ carbonPrice }} 元/tCO₂</strong>
        </p>
      </div>
      <el-form :model="tradeForm" label-width="100px">
        <el-form-item label="交易类型" required>
          <el-radio-group v-model="tradeForm.type">
            <el-radio value="buy">买入配额</el-radio>
            <el-radio value="sell">卖出配额</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="交易数量" required>
          <el-input-number 
            v-model="tradeForm.amount" 
            :min="0.01" 
            :precision="2" 
            :step="1" 
            placeholder="输入交易数量" 
            style="width: 100%;" 
          />
          <div style="margin-top: 8px; color: #999; font-size: 12px;">单位：tCO₂</div>
        </el-form-item>
        <el-form-item label="交易价格">
          <el-input-number 
            v-model="tradeForm.price" 
            :min="0" 
            :precision="2" 
            :step="0.1" 
            style="width: 100%;" 
          />
          <div style="margin-top: 8px; color: #999; font-size: 12px;">单位：元/tCO₂（默认跟随市场价）</div>
        </el-form-item>
        <el-form-item label="预计金额">
          <div style="font-size: 18px; font-weight: bold; color: #16241f;">
            {{ (tradeForm.amount * tradeForm.price).toFixed(2) }} 元
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTradeDialog = false">取消</el-button>
        <el-button type="primary" @click="submitTrade">确认交易</el-button>
      </template>
    </el-dialog>
  </div>
</template>
