<template>
  <div>
    <!-- 專案列表 Table -->
    <table class="table table-bordered table-hover mb-6">
      <thead>
        <tr>
          <th>ID</th>
          <th>Project Name</th>
          <th>Job #</th>
          <th>Contractor</th>
          <th>Start Date</th>
          <th>End Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in projects" :key="item.id">
          <td>{{ item.id }}</td>
          <td>{{ item.name }}</td>
          <td>{{ item.job_number }}</td>
          <td>{{ item.contractor }}</td>
          <td>{{ item.start_date }}</td>
          <td>{{ item.end_date }}</td>
          <td>
            <!-- 改為 Gantt 與 Documents -->
            <router-link
              class="btn btn-warning btn-sm me-2"
              :to="`/projects/${item.id}/gantt`"
            >
              Gantt
            </router-link>

            <router-link
              class="btn btn-secondary btn-sm me-2"
              :to="`/projects/${item.id}/documents`"
            >
              Documents
            </router-link>

            <!-- Edit -->
            <button
              class="btn btn-info btn-sm me-2"
              @click="editProject(item.id)"
            >
              Edit
            </button>

            <!-- Delete -->
            <button
              class="btn btn-danger btn-sm"
              @click="deleteProject(item.id)"
            >
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ProjectList',
  props: {
    projects: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    editProject(projectId) {
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
.me-2 {
  margin-right: 8px;
}
.mb-6 {
  margin-bottom: 24px;
}
</style>
