<template>
  <div class="container text-center py-5">
    <h1>Welcome to the Project Management System</h1>
    <p>這裡是專案管理的首頁。</p>
    <img
      src="/vite.svg"
      alt="Vite Logo"
      style="height: 100px;"
      class="d-block mx-auto my-4"
    />
    <router-link to="/projects" class="btn btn-primary">Go to Projects</router-link>
  </div>
</template>

<script>
export default {
  name: 'HomeView'
}
</script>

<style scoped>
/* 可自行增添 */
</style>
