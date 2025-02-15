<template>
  <!-- 根容器 -->
  <v-app>
    <!-- 以 v-app-bar 作為頂部導覽列 -->
    <v-app-bar color="primary" dark>
      <v-toolbar-title>Project Management System</v-toolbar-title>
      <v-spacer></v-spacer>

      <!-- ★ 改用 to="…" router variant="text" -->
      <v-btn to="/" router variant="text">Home</v-btn>
      <v-btn to="/projects" router variant="text">Projects</v-btn>
      <v-btn to="/material" router variant="text">Material Form</v-btn>
      <v-btn to="/staff" router variant="text">Staff</v-btn>
    </v-app-bar>

    <!-- 主要內容區塊 -->
    <v-main>
      <div style="max-width:1500px; margin:0 auto; padding:20px;">
        <router-view />
      </div>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'App'
}
</script>
