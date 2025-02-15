<template>
  <div>
    <form @submit.prevent="handleSubmit">
      <div class="mb-3 row">
        <label class="col-sm-3 col-form-label">Project Name</label>
        <div class="col-sm-9">
          <input
            type="text"
            v-model="formData.name"
            class="form-control"
            required
          />
        </div>
      </div>

      <div class="mb-3 row">
        <label class="col-sm-3 col-form-label">Owner</label>
        <div class="col-sm-9">
          <input
            type="text"
            v-model="formData.owner"
            class="form-control"
          />
        </div>
      </div>

      <!-- 工作編號 / 承建商 -->
      <div class="mb-3 row">
        <label class="col-sm-3 col-form-label">工作編號</label>
        <div class="col-sm-9">
          <input
            type="text"
            v-model="formData.job_number"
            class="form-control"
          />
        </div>
      </div>

      <div class="mb-3 row">
        <label class="col-sm-3 col-form-label">承建商</label>
        <div class="col-sm-9">
          <input
            type="text"
            v-model="formData.contractor"
            class="form-control"
          />
        </div>
      </div>

      <div class="mb-3 row">
        <label class="col-sm-3 col-form-label">Start Date</label>
        <div class="col-sm-9">
          <input
            type="date"
            v-model="formData.start_date"
            class="form-control"
          />
        </div>
      </div>

      <div class="mb-3 row">
        <label class="col-sm-3 col-form-label">End Date</label>
        <div class="col-sm-9">
          <input
            type="date"
            v-model="formData.end_date"
            class="form-control"
          />
        </div>
      </div>

      <div class="mb-3 row">
        <label class="col-sm-3 col-form-label">Duration (Days)</label>
        <div class="col-sm-9">
          <input
            type="number"
            v-model.number="formData.duration_days"
            class="form-control"
          />
        </div>
      </div>

      <div class="mb-3">
        <label>Duration Type:</label>
        <div class="form-check form-check-inline ms-3">
          <input
            class="form-check-input"
            type="radio"
            value="business"
            v-model="formData.duration_type"
            id="durationBusiness"
          />
          <label class="form-check-label" for="durationBusiness">Business</label>
        </div>
        <div class="form-check form-check-inline">
          <input
            class="form-check-input"
            type="radio"
            value="calendar"
            v-model="formData.duration_type"
            id="durationCalendar"
          />
          <label class="form-check-label" for="durationCalendar">Calendar</label>
        </div>
      </div>

      <div class="mb-3">
        <label class="form-label">Description</label>
        <textarea
          v-model="formData.description"
          class="form-control"
          rows="2"
        ></textarea>
      </div>

      <div class="mb-3">
        <label class="form-label">Project Objective</label>
        <textarea
          v-model="formData.objective"
          class="form-control"
          rows="2"
        ></textarea>
      </div>

      <div class="d-flex justify-content-end mt-4">
        <button type="submit" class="btn btn-primary">
          {{ projectId ? 'Save' : 'Create' }}
        </button>
        <button type="button" class="btn btn-secondary ms-2" @click="closeForm">
          Close
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ProjectForm',
  props: {
    projectId: Number
  },
  data() {
    return {
      formData: {
        name: '',
        description: '',
        objective: '',
        owner: '',
        duration_days: '',
        duration_type: 'business',
        start_date: '',
        end_date: '',
        job_number: '',
        contractor: ''
      }
    }
  },
  methods: {
    async fetchProject() {
      if (!this.projectId) return
      try {
        const { data } = await axios.get(`/api/projects/${this.projectId}`)
        this.formData.name = data.name
        this.formData.description = data.description
        this.formData.objective = data.objective
        this.formData.owner = data.owner
        this.formData.duration_days = data.duration_days
        this.formData.duration_type = data.duration_type || 'business'
        this.formData.start_date = data.start_date
        this.formData.end_date = data.end_date
        this.formData.job_number = data.job_number
        this.formData.contractor = data.contractor
      } catch (err) {
        console.error(err)
      }
    },
    async handleSubmit() {
      try {
        if (this.projectId) {
          await axios.put(`/api/projects/${this.projectId}`, this.formData)
        } else {
          await axios.post('/api/projects/', this.formData)
        }
        this.$emit('refresh')
        this.closeForm()
      } catch (err) {
        console.error(err)
      }
    },
    closeForm() {
      this.$emit('close')
    }
  },
  mounted() {
    if (this.projectId) this.fetchProject()
  }
}
</script>

<style scoped>
.ms-2 {
  margin-left: 8px;
}
.mt-4 {
  margin-top: 1rem;
}
</style>
