<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { Moon, Sunny as Sun } from '@element-plus/icons-vue'

const route = useRoute()
const store = useAppStore()

const NAV_GROUPS = [
  {
    label: '能耗管理',
    items: [
      { path: '/admin/energy/consumption', title: '能耗查询', mark: '01' },
      { path: '/admin/energy/meter-curve', title: '单器具曲线', mark: '01-1' },
      { path: '/admin/energy/analysis-enhanced', title: '能源分析增强', mark: '01-2' },
      { path: '/admin/energy/calculation', title: '能耗计算', mark: '02' },
      { path: '/admin/energy/analysis', title: '用能分析与策略', mark: '03' },
      { path: '/admin/energy/benchmark', title: '能效对标', mark: '04' },
      { path: '/admin/energy/flow', title: '能流分析', mark: '05' },
      { path: '/admin/energy/optimization', title: '能效平衡与优化', mark: '06' }
    ]
  },
  {
    label: '碳管理',
    items: [
      { path: '/admin/carbon/budget', title: '碳预算管理', mark: '07' },
      { path: '/admin/carbon/emission', title: '碳排放核算', mark: '08' },
      { path: '/admin/carbon/footprint', title: '产品碳足迹', mark: '09' },
      { path: '/admin/carbon/supply-chain', title: '供应链碳管理', mark: '10' },
      { path: '/admin/carbon/audit', title: '碳核查支撑', mark: '11' },
      { path: '/admin/carbon/asset', title: '碳资产管理', mark: '12' }
    ]
  },
  {
    label: '数据采集',
    items: [{ path: '/admin/ingest', title: '采集与手工填报', mark: 'IN' }]
  }
]

const pageTitle = computed(() => route.meta?.title || '')
const isMobile = ref(false)
let mq = null

function syncMedia() {
  if (!mq) return
  isMobile.value = mq.matches
  if (!mq.matches) store.closeSide()
}

onMounted(() => {
  mq = window.matchMedia('(max-width: 767px)')
  syncMedia()
  mq.addEventListener('change', syncMedia)
})
onBeforeUnmount(() => mq && mq.removeEventListener('change', syncMedia))

function navTo() {
  if (isMobile.value) store.closeSide()
}
</script>

<template>
  <div class="admin-layout">
    <!-- 侧边导航 -->
    <aside class="side" :class="{ open: store.sideOpen }">
      <div class="side-brand">
        <div class="brand-mark">CB</div>
        <div class="brand-text">
          <strong>长沙水泵厂能<br/>碳管理中心</strong>
          <span>Energy &amp; Carbon Platform</span>
        </div>
      </div>

      <nav class="side-nav">
        <section v-for="g in NAV_GROUPS" :key="g.label" class="nav-group">
          <div class="group-label">{{ g.label }}</div>
          <router-link
            v-for="it in g.items"
            :key="it.path"
            :to="it.path"
            class="nav-item"
            :class="{ active: route.path === it.path }"
            @click="navTo"
          >
            <span class="nav-mark num">{{ it.mark }}</span>
            <span class="nav-title">{{ it.title }}</span>
          </router-link>
        </section>
      </nav>

      <div class="side-foot">
        <span class="tag-dot" style="color: #34d399">系统运行正常</span>
      </div>
    </aside>

    <!-- 移动端遮罩 -->
    <div v-if="store.sideOpen" class="side-mask" @click="store.closeSide()"></div>

    <!-- 主区域 -->
    <div class="main">
      <header class="topbar">
        <button class="hamburger" aria-label="打开菜单" @click="store.toggleSide()">
          <span></span><span></span><span></span>
        </button>
        <div class="topbar-title">
          <span class="crumb-root">长沙水泵厂能碳管理中心</span>
          <span class="crumb-sep">/</span>
          <span class="crumb-cur">{{ pageTitle }}</span>
        </div>
        <div class="topbar-right">
          <el-switch
            v-model="store.theme"
            active-value="dark"
            inactive-value="light"
            inline-prompt
            :active-icon="Moon"
            :inactive-icon="Sun"
            @change="store.setTheme(store.theme)"
            style="margin-right: 12px;"
          />
          <router-link to="/screen" class="screen-entry">
            <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
              <rect x="1.5" y="2.5" width="13" height="9" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.4" />
              <path d="M5.5 14h5M8 11.5V14" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
            </svg>
            可视化大屏
          </router-link>
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout { display: flex; min-height: 100%; background: var(--bg); }

/* ---------- 侧栏 ---------- */
.side {
  width: 236px; flex-shrink: 0;
  display: flex; flex-direction: column;
  background: linear-gradient(180deg, var(--side-bg) 0%, var(--side-bg-2) 100%);
  color: var(--side-ink);
  position: sticky; top: 0; height: 100vh;
  z-index: 30;
}
.side-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 20px 18px 16px;
  border-bottom: 1px solid var(--side-border);
}
.brand-mark {
  width: 38px; height: 38px; border-radius: 10px;
  display: grid; place-items: center;
  font-family: var(--font-num); font-weight: 700; font-size: 15px; letter-spacing: 0.04em;
  color: var(--brand-mark-color);
  background: var(--brand-mark-bg);
  box-shadow: var(--brand-mark-shadow);
}
.brand-text strong { display: block; color: var(--side-ink-active); font-size: 15px; letter-spacing: 0.02em; }
.brand-text span { font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; opacity: 0.55; }

.side-nav { flex: 1; overflow-y: auto; padding: 12px 12px 20px; }
.group-label {
  padding: 14px 8px 6px;
  font-size: 11px; letter-spacing: 0.22em; text-transform: uppercase;
  color: rgba(255, 255, 255, 0.34);
}
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; margin: 2px 0;
  border-radius: 9px; text-decoration: none;
  color: var(--side-ink); font-size: 13.5px;
  transition: background 0.2s ease, color 0.2s ease, transform 0.15s ease;
}
.nav-item:hover { background: var(--side-hover); color: #d9fff5; transform: translateX(2px); }
.nav-item.active {
  background: var(--side-active-bg);
  color: var(--side-ink-active);
  box-shadow: inset 2px 0 0 var(--side-active-border);
}
.nav-mark {
  width: 26px; height: 20px; border-radius: 5px; flex-shrink: 0;
  display: grid; place-items: center;
  font-size: 10.5px; font-weight: 700;
  background: var(--side-mark-bg); color: var(--side-mark-color);
}
.nav-item.active .nav-mark { background: var(--side-mark-active-bg); color: var(--side-mark-active-color); }

.side-foot {
  padding: 12px 18px; border-top: 1px solid var(--side-foot-border);
  font-size: 12px;
}
.side-foot :deep(.tag-dot::before), .side-foot .tag-dot::before { box-shadow: 0 0 8px currentColor; }

/* ---------- 主区域 ---------- */
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar {
  height: 58px; flex-shrink: 0;
  display: flex; align-items: center; gap: 14px;
  padding: 0 22px;
  background: var(--topbar-bg);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--topbar-border);
  position: sticky; top: 0; z-index: 20;
}
.topbar-title { display: flex; align-items: center; gap: 8px; font-size: 13.5px; }
.crumb-root { color: var(--ink-3); }
.crumb-sep { color: var(--line-strong); }
.crumb-cur { color: var(--ink); font-weight: 600; }
.topbar-right { margin-left: auto; }
.screen-entry {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 999px;
  font-size: 13px; font-weight: 600; text-decoration: none;
  color: var(--screen-entry-color);
  background: var(--screen-entry-bg);
  box-shadow: var(--screen-entry-shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.screen-entry:hover { transform: translateY(-1px); box-shadow: var(--screen-entry-shadow); }

.hamburger {
  display: none; width: 36px; height: 36px;
  border: 1px solid var(--line); border-radius: 8px; background: var(--surface);
  cursor: pointer; flex-direction: column; align-items: center; justify-content: center; gap: 4px;
}
.hamburger span { width: 16px; height: 2px; border-radius: 2px; background: var(--ink); }

.content { padding: 20px 22px 32px; flex: 1; }

.side-mask { display: none; }

/* ---------- 手机端 ---------- */
@media (max-width: 767px) {
  .side {
    position: fixed; left: 0; top: 0; bottom: 0; height: 100%;
    transform: translateX(-100%);
    transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 12px 0 40px rgba(0, 0, 0, 0.3);
  }
  .side.open { transform: none; }
  .side-mask {
    display: block; position: fixed; inset: 0; z-index: 25;
    background: rgba(10, 20, 17, 0.5); backdrop-filter: blur(2px);
  }
  .hamburger { display: flex; }
  .content { padding: 14px 12px 24px; }
  .topbar { padding: 0 12px; }
}
</style>
