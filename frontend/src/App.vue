<template>
  <div>
    <!-- Bootstrap Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">Project Management System</a>
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarSupportedContent"
          aria-controls="navbarSupportedContent"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarSupportedContent">
          <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <router-link to="/" class="nav-link">Home</router-link>
            </li>
            <li class="nav-item">
              <router-link to="/projects" class="nav-link">Projects</router-link>
            </li>
            <li class="nav-item">
              <router-link to="/material" class="nav-link">Material Form</router-link>
            </li>
            <li class="nav-item">
              <router-link to="/staff" class="nav-link">Staff</router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <!-- 
      根據是否為 Gantt 頁面，決定要不要包在 .container.my-4
      這樣即可避免 Gantt 頁面左側產生 offset
    -->
    <div v-if="isGanttPage" style="margin:0; padding:0;">
      <router-view />
    </div>
    <div v-else class="container my-4">
      <router-view />
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'App',
  setup() {
    const route = useRoute()

    // 簡單判斷路徑中是否包含 /gantt
    // （也可改更精準判斷 route.name === 'ProjectsGantt' 之類）
    const isGanttPage = computed(() => {
      return route.path.includes('/gantt')
    })

    return {
      isGanttPage
    }
  }
}
</script>

<style>
/* 可視需求自行增減 */

/* 說明：若不是 Gantt 頁面，我們保留 .container.my-4。
   若是 Gantt 頁面，則改用上方 <div style="margin:0;padding:0;"> 撐滿整個畫面。 */
</style>
