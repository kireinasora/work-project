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
      <router-link
        :to="`/projects/${projectId}/diaries`"
        class="btn btn-info"
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
/* 可視需求，自行增減 */
</style>
