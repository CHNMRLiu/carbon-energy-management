<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  decimals: { type: Number, default: 1 },
  duration: { type: Number, default: 900 }
})

const shown = ref(0)
let raf = null

watch(
  () => props.value,
  (nv) => {
    const from = shown.value
    const to = Number.isFinite(nv) ? nv : 0
    if (from === to) return
    const t0 = performance.now()
    cancelAnimationFrame(raf)
    const step = (t) => {
      const p = Math.min(1, (t - t0) / props.duration)
      const eased = 1 - Math.pow(1 - p, 3)
      shown.value = from + (to - from) * eased
      if (p < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
  },
  { immediate: true }
)

onBeforeUnmount(() => cancelAnimationFrame(raf))

const text = computed(() =>
  shown.value.toLocaleString('zh-CN', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals
  })
)
</script>

<template>
  <span class="ticker">{{ text }}</span>
</template>
