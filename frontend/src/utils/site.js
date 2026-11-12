import { reactive } from 'vue'
import { siteApi } from '../api'
import fallbackLogo from '../assets/logo.png'

const DEFAULTS = {
  site_name: '铁刷客考试系统',
  site_subtitle: '考试 · 刷题 · 组卷',
  developer_name: '可以云码软件开发',
  footer_text: '铁刷客考试系统',
  icp_no: '',
  logo_url: ''
}

export const site = reactive({ ...DEFAULTS })

export function siteLogo() {
  return site.logo_url || fallbackLogo
}

function applyTitle() {
  document.title = site.site_name || DEFAULTS.site_name
}

export async function loadSiteSettings() {
  try {
    const data = await siteApi.get()
    Object.assign(site, DEFAULTS, data || {})
  } catch (e) {
    // 后端未启动时使用本地默认值，不阻塞页面
  }
  applyTitle()
}
