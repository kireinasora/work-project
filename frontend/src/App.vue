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

    <!-- Main Content -->
    <div class="container my-4">
      <router-view />
    </div>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
/* 可視需求自行增減 */
</style>
