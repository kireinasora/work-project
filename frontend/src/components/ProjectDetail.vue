<template>
  <div v-if="project">
    <p>Description: {{ project.description }}</p>
    <p>Objective: {{ project.objective }}</p>
    <p>Owner: {{ project.owner }}</p>
    <p>Duration: {{ project.duration_days }} ({{ project.duration_type }})</p>
    <p>Start Date: {{ project.start_date }}</p>
    <p>End Date: {{ project.end_date }}</p>

    <!-- ★ 新增顯示工程編號與承建商 -->
    <p>Job Number: {{ project.job_number }}</p>
    <p>Contractor: {{ project.contractor }}</p>

    <div style="margin-top:20px;">
      <router-link
        :to="`/projects/${projectId}/diaries`"
        style="background:#646cff; color:white; padding:6px 10px; border-radius:4px; text-decoration:none;"
      >
        Manage Site Diaries
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
/* 按需求增添樣式 */
</style>
