<template>
  <div>
    <v-data-table
      :headers="headers"
      :items="projects"
      :density="'compact'"
      class="mb-6"
    >
      <template #item.actions="{ item }">
        <v-btn color="info" variant="text" class="me-2" @click="showDetail(item.id)">
          Detail
        </v-btn>
        <v-btn color="warning" variant="text" class="me-2" @click="editProject(item.id)">
          Edit
        </v-btn>
        <v-btn color="error" variant="text" @click="deleteProject(item.id)">
          Delete
        </v-btn>
      </template>
    </v-data-table>

    <!-- 詳細資訊 Dialog -->
    <v-dialog v-model="detailDialog" max-width="600px">
      <v-card>
        <v-card-title>
          <span class="text-h6">Project Detail</span>
        </v-card-title>
        <v-card-text>
          <ProjectDetail :projectId="detailProjectId" />
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="detailDialog=false">
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import ProjectDetail from '@/components/ProjectDetail.vue'

export default {
  name: 'ProjectList',
  components: { ProjectDetail },
  props: {
    projects: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      detailDialog: false,
      detailProjectId: null,
      headers: [
        { text: 'ID', value: 'id', width: 60 },
        { text: 'Project Name', value: 'name' },
        // ★ 新增兩欄做示範 (工作編號、承建商)
        { text: 'Job #', value: 'job_number', width: 120 },
        { text: 'Contractor', value: 'contractor' },
        // ---
        { text: 'Start Date', value: 'start_date', width: 120 },
        { text: 'End Date', value: 'end_date', width: 120 },
        { text: 'Actions', value: 'actions', sortable: false }
      ]
    }
  },
  methods: {
    showDetail(projectId) {
      this.detailProjectId = projectId
      this.detailDialog = true
    },
    editProject(projectId) {
      // 發出事件給父層(ProjectsView)
      this.$emit('edit-project', projectId)
    },
    async deleteProject(id) {
      if (!confirm('確定要刪除此專案嗎？')) return
      try {
        await axios.delete(`/api/projects/${id}`)
        this.$emit('refresh')
      } catch (err) {
        console.error(err)
      }
    }
  }
}
</script>

<style scoped>
.mb-6 {
  margin-bottom: 24px;
}
.me-2 {
  margin-right: 8px;
}
</style>
