// frontend/src/router.ts
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import ProjectsView from './views/ProjectsView.vue'
import MaterialFormView from './views/MaterialFormView.vue'
import StaffView from './views/StaffView.vue'
import ProjectsGanttView from './views/ProjectsGanttView.vue'

// ★ 移除原先的「SiteDiaryListView」路由，改由 ProjectDocumentsView 裡面的 DAILY_REPORT 分頁
// import SiteDiaryListView from './views/SiteDiaryListView.vue' (已刪除)

import ProjectDocumentsView from './views/ProjectDocumentsView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/projects', component: ProjectsView },
  { path: '/material', component: MaterialFormView },
  { path: '/staff', component: StaffView },

  // ★ 移除 /projects/:projectId/diaries，直接合併到 project documents
  // { path: '/projects/:projectId/diaries', component: SiteDiaryListView },

  { path: '/projects/:projectId/gantt', component: ProjectsGanttView },

  // ★ 調整文件管理頁面
  {
    path: '/projects/:projectId/documents',
    component: ProjectDocumentsView
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
