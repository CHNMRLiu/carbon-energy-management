<script setup>
import { ref } from 'vue'
import { useEChart } from '@/composables/useEChart'

const props = defineProps({
  title: { type: String, default: '' },
  desc: { type: String, default: '' },
  /** 图表区域高度 */
  height: { type: String, default: '320px' },
  loading: { type: Boolean, default: false }
})

const boxRef = ref(null)
const { setOption, getInstance } = useEChart(boxRef)

defineExpose({ setOption, getInstance })
</script>

<template>
  <section class="chart-card card" v-loading="loading">
    <header v-if="title || $slots.header || $slots.extra" class="chart-head">
      <slot name="header">
        <div>
          <h3 class="chart-title">{{ title }}</h3>
          <p v-if="desc" class="chart-desc">{{ desc }}</p>
        </div>
      </slot>
      <div class="chart-extra"><slot name="extra" /></div>
    </header>
    <div v-if="$slots.default" class="chart-body" :style="{ height: props.height }"><slot /></div>
    <div v-else ref="boxRef" class="chart-body" :style="{ height: props.height }"></div>
    <div v-if="$slots.footer" class="chart-foot"><slot name="footer" /></div>
  </section>
</template>

<style scoped>
.chart-card { display: flex; flex-direction: column; overflow: hidden; }
.chart-head {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 14px 18px 0;
}
.chart-title {
  margin: 0; font-size: 15px; font-weight: 700; color: var(--ink);
  display: flex; align-items: center; gap: 8px;
}
.chart-title::before {
  content: ""; width: 14px; height: 3px; border-radius: 2px;
  background: var(--brand);
}
.chart-desc { margin: 3px 0 0; font-size: 12px; color: var(--ink-3); }
.chart-extra { display: flex; align-items: center; gap: 8px; }
.chart-body { width: 100%; padding: 6px 10px 10px; }
.chart-foot { border-top: 1px dashed var(--line); padding: 10px 18px; font-size: 12px; color: var(--ink-2); }
</style>
