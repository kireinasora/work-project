<template>
  <v-container fluid>
    <h1>All Projects</h1>

    <!-- 新增專案按鈕 -->
    <v-btn color="primary" class="mb-4" @click="openCreateProjectDialog">
      Create New Project
    </v-btn>

    <!-- ProjectList 顯示所有專案 -->
    <ProjectList
      :projects="projects"
      @refresh="fetchProjects"
      @edit-project="openEditProjectDialog"
    />

    <!-- 新增/編輯 Project 的 Dialog -->
    <v-dialog v-model="showProjectDialog" max-width="800px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h6">
            {{ editingProjectId ? 'Edit Project' : 'Create Project' }}
          </span>
        </v-card-title>
        <v-card-text>
          <ProjectForm
            :projectId="editingProjectId"
            @close="closeProjectDialog"
            @refresh="onProjectSaved"
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import axios from 'axios'
import { ref, onMounted } from 'vue'
import ProjectList from '@/components/ProjectList.vue'
import ProjectForm from '@/components/ProjectForm.vue'

export default {
  name: 'ProjectsView',
  components: { ProjectList, ProjectForm },
  setup() {
    const projects = ref([])
    const showProjectDialog = ref(false)
    const editingProjectId = ref(null)

    const fetchProjects = async () => {
      try {
        const { data } = await axios.get('/api/projects/')
        projects.value = data
      } catch (err) {
        console.error(err)
      }
    }

    const openCreateProjectDialog = () => {
      editingProjectId.value = null
      showProjectDialog.value = true
    }

    // ★ 新增：當使用者點擊 Edit 按鈕時，開啟對話框
    const openEditProjectDialog = (id) => {
      editingProjectId.value = id
      showProjectDialog.value = true
    }

    const closeProjectDialog = () => {
      showProjectDialog.value = false
    }

    const onProjectSaved = () => {
      showProjectDialog.value = false
      fetchProjects()
    }

    onMounted(() => {
      fetchProjects()
    })

    return {
      projects,
      showProjectDialog,
      editingProjectId,
      fetchProjects,
      openCreateProjectDialog,
      openEditProjectDialog,
      closeProjectDialog,
      onProjectSaved
    }
  }
}
</script>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}
</style>
