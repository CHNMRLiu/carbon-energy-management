<script setup>
defineEmits(['query', 'reset'])

defineProps({
  /** 隐藏查询/重置按钮（由插槽内自定义操作代替） */
  bare: { type: Boolean, default: false }
})
</script>

<template>
  <div class="filter-bar card">
    <div class="filter-fields">
      <slot />
    </div>
    <div v-if="!bare" class="filter-actions">
      <el-button type="primary" @click="$emit('query')">查询</el-button>
      <el-button plain @click="$emit('reset')">重置</el-button>
      <slot name="extra" />
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px 16px;
  padding: 14px 16px;
  flex-wrap: wrap;
}
.filter-fields { display: flex; align-items: center; gap: 12px 14px; flex-wrap: wrap; }
.filter-fields :deep(.el-select) { width: 150px; }
.filter-fields :deep(.field-label) { color: var(--ink-2); font-size: 13px; white-space: nowrap; }
.filter-actions { display: flex; align-items: center; gap: 8px; }
@media (max-width: 767px) {
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-actions { justify-content: flex-end; }
}
</style>
