<template>
  <div class="container-fluid">
    <h1>All Projects</h1>
    <button class="btn btn-primary mb-4" @click="openCreateProjectDialog">
      Create New Project
    </button>

    <ProjectList
      :projects="projects"
      @refresh="fetchProjects"
      @edit-project="openEditProjectDialog"
    />

    <!-- Bootstrap Modal for Create/Edit Project -->
    <div
      class="modal"
      :class="{ fade: true, show: showProjectDialog }"
      :style="{ display: showProjectDialog ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="showProjectDialog"
      @click.self="closeProjectDialog"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editingProjectId ? 'Edit Project' : 'Create Project' }}
            </h5>
            <button
              type="button"
              class="btn-close"
              aria-label="Close"
              @click="closeProjectDialog"
            ></button>
          </div>
          <div class="modal-body">
            <ProjectForm
              :projectId="editingProjectId"
              @close="closeProjectDialog"
              @refresh="onProjectSaved"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Modal backdrop -->
    <div
      v-if="showProjectDialog"
      class="modal-backdrop fade show"
    ></div>
  </div>
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

/* ★ 與 ProjectList.vue 相同的 z-index 設定，確保顯示優先順序正確 */
.modal {
  z-index: 1050;
}
.modal-backdrop {
  z-index: 1040;
}
</style>
