<template>
  <v-container fluid>
    <v-form @submit.prevent="handleSubmit">
      <v-row dense>
        <v-col cols="12" md="6">
          <v-text-field
            label="Project Name"
            v-model="formData.name"
            required
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            label="Owner"
            v-model="formData.owner"
          />
        </v-col>
      </v-row>

      <!-- 新增：工作編號 / 承建商 -->
      <v-row dense>
        <v-col cols="12" md="6">
          <v-text-field
            label="工作編號"
            v-model="formData.job_number"
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            label="承建商"
            v-model="formData.contractor"
          />
        </v-col>
      </v-row>
      <!-- ------------------------- -->

      <v-row dense>
        <v-col cols="12" md="6">
          <v-text-field
            label="Start Date"
            v-model="formData.start_date"
            type="date"
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            label="End Date"
            v-model="formData.end_date"
            type="date"
          />
        </v-col>
      </v-row>

      <v-row dense>
        <v-col cols="12" md="6">
          <v-text-field
            label="Duration (Days)"
            v-model.number="formData.duration_days"
            type="number"
          />
        </v-col>
        <v-col cols="12" md="6">
          <div>Duration Type</div>
          <v-radio-group v-model="formData.duration_type" class="mt-2">
            <v-radio label="Business" value="business" />
            <v-radio label="Calendar" value="calendar" />
          </v-radio-group>
        </v-col>
      </v-row>

      <v-row dense>
        <v-col cols="12">
          <v-textarea
            label="Description"
            v-model="formData.description"
            rows="2"
          />
        </v-col>
      </v-row>

      <v-row dense>
        <v-col cols="12">
          <v-textarea
            label="Project Objective"
            v-model="formData.objective"
            rows="2"
          />
        </v-col>
      </v-row>

      <v-row dense class="mt-4" justify="end">
        <v-btn color="primary" type="submit">
          {{ projectId ? 'Save' : 'Create' }}
        </v-btn>
        <v-btn variant="text" class="ms-2" @click="closeForm">Close</v-btn>
      </v-row>
    </v-form>
  </v-container>
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
        // 新增
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

        // 載入 job_number / contractor
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
