// frontend/src/router.ts
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import ProjectsView from './views/ProjectsView.vue'
import MaterialFormView from './views/MaterialFormView.vue'
import StaffView from './views/StaffView.vue'

// ★ 新增
import SiteDiaryListView from './views/SiteDiaryListView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/projects', component: ProjectsView },
  { path: '/material', component: MaterialFormView },
  { path: '/staff', component: StaffView },

  // 新增日報列表頁（替代舊 daily report）
  { path: '/projects/:projectId/diaries', component: SiteDiaryListView }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
