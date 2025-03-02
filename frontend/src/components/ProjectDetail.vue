<!-- frontend/src/components/ProjectDetail.vue -->
<template>
  <div v-if="project" class="card p-3">
    <h5 class="card-title">Project Detail</h5>
    <p>Description: {{ project.description }}</p>
    <p>Objective: {{ project.objective }}</p>
    <p>Owner: {{ project.owner }}</p>
    <p>Duration: {{ project.duration_days }} ({{ project.duration_type }})</p>
    <p>Start Date: {{ project.start_date }}</p>
    <p>End Date: {{ project.end_date }}</p>
    <p>Job Number: {{ project.job_number }}</p>
    <p>Contractor: {{ project.contractor }}</p>

    <div class="mt-3">
      <!-- 
        已移除舊的 "Manage Site Diaries" 按鈕，避免觸發 /projects/:projectId/diaries 404
      -->

      <router-link
        :to="`/projects/${projectId}/gantt`"
        class="btn btn-warning me-2"
      >
        Gantt
      </router-link>

      <!-- 新增文件(包含 Daily Reports)的入口 -->
      <router-link
        :to="`/projects/${projectId}/documents`"
        class="btn btn-secondary"
      >
        Documents
      </router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ProjectDetail',
  props: {
    projectId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      project: null
    }
  },
  methods: {
    async fetchProject() {
      try {
        const { data } = await axios.get(`/api/projects/${this.projectId}`)
        this.project = data
      } catch (err) {
        console.error(err)
      }
    }
  },
  mounted() {
    this.fetchProject()
  }
}
</script>

<style scoped>
.me-2 {
  margin-right: 8px;
}
</style>
