// frontend/src/router.ts
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import ProjectsView from './views/ProjectsView.vue'
import MaterialFormView from './views/MaterialFormView.vue'
import StaffView from './views/StaffView.vue'
import SiteDiaryListView from './views/SiteDiaryListView.vue'

// ★ 新增 import
import ProjectsGanttView from './views/ProjectsGanttView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/projects', component: ProjectsView },
  { path: '/material', component: MaterialFormView },
  { path: '/staff', component: StaffView },
  { path: '/projects/:projectId/diaries', component: SiteDiaryListView },

  // ★ 新增：Gantt 頁面
  { path: '/projects/:projectId/gantt', component: ProjectsGanttView }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
