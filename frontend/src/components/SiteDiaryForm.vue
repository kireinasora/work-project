<template>
  <div class="site-diary-form border p-3" style="max-height:90vh; overflow-y:auto;">
    <!-- Title + Close Button -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="m-0">Site Diary Form</h5>
      <button class="btn btn-sm btn-outline-secondary" @click="cancelForm">Close</button>
    </div>

    <form @submit.prevent="handleSubmit">
      <!-- Row 1: Date, Weather, Day Count -->
      <div class="row mb-3">
        <div class="col-sm-6 col-md-3 mb-2">
          <label class="form-label">Report Date</label>
          <input
            type="date"
            v-model="localReportDateStr"
            class="form-control form-control-sm"
          />
        </div>
        <div class="col-sm-6 col-md-3 mb-2">
          <label class="form-label">Weather (Morning)</label>
          <input
            type="text"
            v-model="formData.weather_morning"
            class="form-control form-control-sm"
          />
        </div>
        <div class="col-sm-6 col-md-3 mb-2">
          <label class="form-label">Weather (Noon)</label>
          <input
            type="text"
            v-model="formData.weather_noon"
            class="form-control form-control-sm"
          />
        </div>
        <div class="col-sm-6 col-md-3 mb-2">
          <label class="form-label">Day Count</label>
          <input
            type="number"
            v-model.number="formData.day_count"
            class="form-control form-control-sm"
          />
        </div>
      </div>

      <!-- Summary -->
      <div class="mb-3">
        <label class="form-label">Summary</label>
        <textarea
          v-model="formData.summary"
          class="form-control form-control-sm"
          rows="2"
        ></textarea>
      </div>

      <!-- Workers -->
      <h6>Workers</h6>
      <div class="row">
        <div
          class="col-sm-6 col-md-4 col-lg-3 mb-2"
          v-for="(count, type) in formData.workers"
          :key="type"
        >
          <label class="form-label">{{ type }}</label>
          <input
            type="number"
            v-model.number="formData.workers[type]"
            class="form-control form-control-sm"
          />
        </div>
      </div>

      <!-- Machines -->
      <h6 class="mt-3">Machines</h6>
      <div class="row">
        <div
          class="col-sm-6 col-md-4 col-lg-3 mb-2"
          v-for="(count, type) in formData.machines"
          :key="type"
        >
          <label class="form-label">{{ type }}</label>
          <input
            type="number"
            v-model.number="formData.machines[type]"
            class="form-control form-control-sm"
          />
        </div>
      </div>

      <!-- Staff (multiple select) -->
      <div class="mt-3 mb-3">
        <label class="form-label">Staffs</label>
        <select
          multiple
          v-model="selectedStaffIds"
          class="form-select"
          size="5"
        >
          <option
            v-for="staff in staffList"
            :key="staff.id"
            :value="staff.id"
          >
            {{ staff.name }} ({{ staff.role || 'N/A' }})
          </option>
        </select>
      </div>

      <!-- Footer buttons -->
      <div class="d-flex justify-content-end mt-3">
        <button
          type="button"
          class="btn btn-secondary me-2"
          @click="clearForm"
        >
          Clear
        </button>
        <button
          type="button"
          class="btn btn-secondary me-2"
          @click="cancelForm"
        >
          Cancel
        </button>
        <button
          type="submit"
          class="btn btn-primary"
        >
          {{ diaryId ? 'Update' : 'Create' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted, watch } from 'vue'

export default {
  name: 'SiteDiaryForm',
  props: {
    projectId: { type: Number, required: true },
    diaryId: { type: Number, default: null }
  },
  setup(props, { emit }) {
    const initialFormData = {
      report_date: null,
      weather_morning: '',
      weather_noon: '',
      day_count: null,
      summary: '',
      workers: {
        '地盤總管': 0,
        '工程師': 0,
        '管工': 0,
        '平水員': 0,
        '燒焊焊工': 0,
        '機手': 0,
        '泥水工': 0,
        '紮鐵工': 0,
        '木板工': 0,
        '電工': 0,
        '水喉工': 0,
        '雜工': 0,
        '其他': 0
      },
      machines: {
        '挖掘機': 0,
        '發電機': 0,
        '風機': 0,
        '泥頭車': 0,
        '吊機': 0,
        '機炮': 0,
        '屈鐵機': 0,
        '風車鋸': 0
      }
    }

    const formData = ref({ ...initialFormData })
    const selectedStaffIds = ref([])
    const localReportDateStr = ref('')
    const staffList = ref([])

    const fetchStaff = async () => {
      try {
        const { data } = await axios.get('/api/staff')
        staffList.value = data
      } catch (err) {
        console.error(err)
      }
    }

    const fetchExistingDiary = async () => {
      if (!props.diaryId) return
      try {
        const { data } = await axios.get(`/api/projects/${props.projectId}/site_diaries`)
        const target = data.find(d => d.id === props.diaryId)
        if (!target) return
        setFormDataFromDiary(target)
      } catch (err) {
        console.error(err)
      }
    }

    const fetchLastDiaryAsDefault = async () => {
      if (props.diaryId) return
      try {
        const { data } = await axios.get(
          `/api/projects/${props.projectId}/site_diaries/last`
        )
        if (!data.id) {
          // 無資料，不做預設
          return
        }
        setFormDataFromDiary(data)
      } catch (err) {
        console.error(err)
      }
    }

    function setFormDataFromDiary(diaryData) {
      // 報表日期
      localReportDateStr.value = diaryData.report_date || ''
      // Weather, summary, day_count
      formData.value.weather_morning = diaryData.weather_morning || ''
      formData.value.weather_noon = diaryData.weather_noon || ''
      formData.value.day_count = diaryData.day_count || null
      formData.value.summary = diaryData.summary || ''

      // Workers
      const updatedWorkers = { ...initialFormData.workers }
      for (const w of diaryData.workers || []) {
        updatedWorkers[w.type] = w.quantity
      }
      formData.value.workers = updatedWorkers

      // Machines
      const updatedMachines = { ...initialFormData.machines }
      for (const m of diaryData.machines || []) {
        updatedMachines[m.type] = m.quantity
      }
      formData.value.machines = updatedMachines

      // Staff
      selectedStaffIds.value = (diaryData.staffs || []).map(s => s.id)
    }

    const handleSubmit = async () => {
      try {
        formData.value.report_date = localReportDateStr.value || null
        const payload = {
          report_date: formData.value.report_date,
          weather_morning: formData.value.weather_morning,
          weather_noon: formData.value.weather_noon,
          day_count: formData.value.day_count,
          summary: formData.value.summary,
          workers: formData.value.workers,
          machines: formData.value.machines,
          staff_ids: selectedStaffIds.value
        }

        if (!props.diaryId) {
          // create
          await axios.post(`/api/projects/${props.projectId}/site_diaries`, payload)
        } else {
          // update
          await axios.put(
            `/api/projects/${props.projectId}/site_diaries/${props.diaryId}`,
            payload
          )
        }
        emit('updated')
      } catch (err) {
        console.error(err)
      }
    }

    const cancelForm = () => {
      emit('cancel')
    }

    const clearForm = () => {
      formData.value = { ...initialFormData }
      localReportDateStr.value = ''
      selectedStaffIds.value = []
    }

    watch(
      () => props.diaryId,
      () => {
        fetchExistingDiary()
      }
    )

    onMounted(async () => {
      await fetchStaff()
      if (!props.diaryId) {
        fetchLastDiaryAsDefault()
      } else {
        fetchExistingDiary()
      }
    })

    return {
      formData,
      selectedStaffIds,
      localReportDateStr,
      staffList,
      handleSubmit,
      cancelForm,
      clearForm
    }
  }
}
</script>

<style scoped>
.site-diary-form {
  font-size: 0.875rem;
}
.me-2 {
  margin-right: 8px !important;
}
.mt-2 {
  margin-top: 8px !important;
}
</style>
