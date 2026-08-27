import { defineStore } from 'pinia'

/** 主题偏好持久化 key */
const THEME_KEY = 'ecms.theme'

function readTheme() {
  try {
    const v = localStorage.getItem(THEME_KEY)
    if (v === 'dark' || v === 'light') return v
  } catch (e) {
    /* localStorage 不可用 */
  }
  return null
}

function applyThemeClass(theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

/** 全局应用状态：移动端侧栏抽屉 + 日夜主题 */
export const useAppStore = defineStore('app', {
  state: () => ({
    sideOpen: false,
    /** 当前主题：light / dark */
    theme: readTheme() || 'light',
    /** 用户是否显式设置过主题（未设置过大屏默认进入夜间模式） */
    themeExplicit: readTheme() !== null
  }),
  actions: {
    toggleSide() {
      this.sideOpen = !this.sideOpen
    },
    closeSide() {
      this.sideOpen = false
    },
    /** 应用主题（不持久化） */
    applyTheme(theme) {
      this.theme = theme
      applyThemeClass(theme)
    },
    /** 用户显式切换主题并持久化 */
    setTheme(theme) {
      this.theme = theme
      this.themeExplicit = true
      try {
        localStorage.setItem(THEME_KEY, theme)
      } catch (e) {
        /* 忽略持久化失败 */
      }
      applyThemeClass(theme)
    },
    toggleTheme() {
      this.setTheme(this.theme === 'dark' ? 'light' : 'dark')
    },
    /** 初始化：按当前状态同步 html.dark class（页面加载后调用一次） */
    initTheme() {
      applyThemeClass(this.theme)
    }
  }
})
