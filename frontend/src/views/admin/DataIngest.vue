<script setup>
import { onMounted, reactive, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const summary = ref({})
const points = ref([])

const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const periodType = ref('month') // 'day' | 'month'
const form = reactive({
  point_code: '',
  period: '',
  value: null,
  remark: ''
})

const rules = {
  point_code: [{ required: true, message: '请选择计量点', trigger: 'change' }],
  period: [{ required: true, message: '请选择填报期间', trigger: 'change' }],
  value: [{ required: true, message: '请输入数值', trigger: 'blur' }]
}

const columns = [
  { prop: 'code', label: '计量点编码', width: 130 },
  { prop: 'name', label: '名称', minWidth: 200 },
  { prop: 'energy_name', label: '能源类型', width: 110 },
  { prop: 'org', label: '所属组织', width: 110 },
  { prop: 'collect_method', label: '采集方式', width: 120 },
  { prop: 'unit', label: '单位', width: 90 },
  { prop: 'status', label: '状态', width: 100, align: 'center', slot: true },
  { prop: 'op', label: '操作', width: 100, align: 'center', slot: true }
]

async function load() {
  loading.value = true
  try {
    const data = await api.ingestPoints()
    summary.value = data.summary || {}
    points.value = data.items || []
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  form.point_code = row?.code || ''
  periodType.value = 'month'
  form.period = ''
  form.value = null
  form.remark = ''
  dialogVisible.value = true
}

async function submitManual() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await api.ingestManual({ ...form })
    ElMessage.success('手工填报提交成功')
    dialogVisible.value = false
    await load()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>数据采集与填报</h2>
        <p>系统对接 · IoT 仪表采集 · 手工填报 · 烟感实测，四种方式统一接入采集库</p>
      </div>
      <el-button type="primary" @click="openDialog()">手工填报</el-button>
    </div>

    <div class="kpi-grid">
      <KpiCard label="计量点总数" :value="summary.total ?? '--'" unit="个" :decimals="0" accent="brand" />
      <KpiCard label="在线点位" :value="summary.online ?? '--'" unit="个" :decimals="0" accent="blue" />
      <KpiCard label="在线率" :value="summary.onlineRate ?? '--'" unit="%" :good-when-down="false" accent="violet" />
      <KpiCard label="采集方式" :value="summary.methodCount ?? '--'" unit="种" :decimals="0" accent="amber" sub="系统对接 · 仪表采集 · 手工填报 · 烟感实测" />
    </div>

    <DataTable title="计量点列表" :columns="columns" :data="points" :loading="loading" max-height="520" show-index>
      <template #extra>
        <el-button size="small" plain @click="load">刷新</el-button>
      </template>
      <template #col-status="{ row }">
        <span class="tag-dot" :style="{ color: row.statusRaw === 'normal' ? 'var(--brand-deep)' : 'var(--danger)' }">{{ row.status }}</span>
      </template>
      <template #col-op="{ row }">
        <el-button size="small" type="primary" link @click="openDialog(row)">填报</el-button>
      </template>
    </DataTable>

    <el-dialog v-model="dialogVisible" title="手工填报" width="480px" :close-on-click-modal="false" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="计量点" prop="point_code">
          <el-select v-model="form.point_code" placeholder="请选择计量点" filterable style="width: 100%">
            <el-option v-for="p in points" :key="p.code" :label="`${p.code} · ${p.name}`" :value="p.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="周期类型">
          <el-radio-group v-model="periodType">
            <el-radio value="day">日录入</el-radio>
            <el-radio value="month">月录入</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="填报期间" prop="period">
          <el-date-picker 
            v-if="periodType === 'day'"
            v-model="form.period" 
            type="date" 
            placeholder="选择日期" 
            value-format="YYYY-MM-DD" 
            style="width: 100%" 
          />
          <el-date-picker 
            v-else
            v-model="form.period" 
            type="month" 
            placeholder="选择月份" 
            value-format="YYYY-MM" 
            style="width: 100%" 
          />
        </el-form-item>
        <el-form-item label="数值" prop="value">
          <el-input-number v-model="form.value" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="请输入该期间能耗数值" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitManual">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>
