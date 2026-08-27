<script setup>
defineProps({
  /** [{ prop, label, width?, minWidth?, align?, formatter?, sortable? }] */
  columns: { type: Array, required: true },
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  maxHeight: { type: [String, Number], default: undefined },
  showIndex: { type: Boolean, default: false },
  emptyText: { type: String, default: '暂无数据' },
  title: { type: String, default: '' }
})
</script>

<template>
  <section class="data-table card">
    <header v-if="title || $slots.header || $slots.extra" class="dt-head">
      <div class="dt-title"><slot name="header">{{ title }}</slot></div>
      <div class="dt-extra"><slot name="extra" /></div>
    </header>
    <div class="table-wrap">
      <el-table
        :data="data"
        v-loading="loading"
        :max-height="maxHeight"
        stripe
        :empty-text="emptyText"
        style="width: 100%"
      >
        <el-table-column v-if="showIndex" type="index" label="#" width="56" align="center" />
        <el-table-column
          v-for="c in columns"
          :key="c.prop"
          :prop="c.prop"
          :label="c.label"
          :width="c.width"
          :min-width="c.minWidth"
          :align="c.align || 'left'"
          :sortable="c.sortable || false"
          :formatter="c.slot ? undefined : c.formatter"
        >
          <template v-if="c.slot" #default="scope">
            <slot :name="`col-${c.prop}`" v-bind="scope" />
          </template>
        </el-table-column>
      </el-table>
    </div>
    <footer v-if="$slots.footer" class="dt-foot"><slot name="footer" /></footer>
  </section>
</template>

<style scoped>
.data-table { overflow: hidden; }
.dt-head {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 14px 18px 12px;
}
.dt-title { font-size: 15px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.dt-title::before { content: ""; width: 14px; height: 3px; border-radius: 2px; background: var(--brand); }
.dt-extra { display: flex; align-items: center; gap: 8px; }
.table-wrap { padding: 0 6px 6px; overflow-x: auto; }
.dt-foot { border-top: 1px dashed var(--line); padding: 10px 18px; font-size: 12px; color: var(--ink-2); }
</style>
