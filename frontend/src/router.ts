// frontend/src/router.ts
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import ProjectsView from './views/ProjectsView.vue'
import MaterialFormView from './views/MaterialFormView.vue'
import StaffView from './views/StaffView.vue'
import SiteDiaryListView from './views/SiteDiaryListView.vue'
import ProjectsGanttView from './views/ProjectsGanttView.vue'

// ★ 新增：專案文件管理頁面
import ProjectDocumentsView from './views/ProjectDocumentsView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/projects', component: ProjectsView },
  { path: '/material', component: MaterialFormView },
  { path: '/staff', component: StaffView },

  // ======= 移除舊的 /projects/:projectId/diaries 以免呼叫 /site_diaries =======
  // { path: '/projects/:projectId/diaries', component: SiteDiaryListView },

  { path: '/projects/:projectId/gantt', component: ProjectsGanttView },

  // ★ 新增：各 project 的文件列表頁 (裡面含 Daily Report)
  {
    path: '/projects/:projectId/documents',
    component: ProjectDocumentsView
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
