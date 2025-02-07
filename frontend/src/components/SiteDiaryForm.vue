<template>
  <!-- 外層容器，含了標題列與關閉按鈕 -->
  <v-card
    class="site-diary-form-card"
    max-width="100%"
  >
    <!-- 頂部標題列 + 關閉按鈕 -->
    <v-card-title class="header-row d-flex justify-space-between align-center">
      <span class="text-h6">Site Diary Form</span>
      <!-- 右上角關閉按鈕 -->
      <v-btn
        icon
        size="x-small"
        @click="cancelForm"
        aria-label="Close"
      >
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-card-title>

    <!-- 主要表單內容 (滾動區) -->
    <v-card-text class="form-content">
      <!-- 第一排: 日期/天氣/天數等 -->
      <v-row density="compact">
        <!-- 報表日期 -->
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="localReportDateStr"
            label="Report Date"
            type="date"
            dense
            outlined
            hide-details
          />
        </v-col>

        <!-- Weather (Morning) -->
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="formData.weather_morning"
            label="Weather (Morning)"
            dense
            outlined
            hide-details
          />
        </v-col>

        <!-- Weather (Noon) -->
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="formData.weather_noon"
            label="Weather (Noon)"
            dense
            outlined
            hide-details
          />
        </v-col>

        <!-- Day Count -->
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model.number="formData.day_count"
            label="Day Count"
            type="number"
            dense
            outlined
            hide-details
          />
        </v-col>
      </v-row>

      <!-- 第二排: Summary -->
      <v-row density="compact" class="mt-2">
        <v-col cols="12">
          <v-textarea
            v-model="formData.summary"
            label="Summary"
            rows="2"
            density="compact"
            outlined
            hide-details
          />
        </v-col>
      </v-row>

      <!-- 第三排: Workers (多欄) -->
      <v-row density="compact" class="mt-2">
        <h3 class="section-title">Workers</h3>
        <v-col
          v-for="(count, type) in formData.workers"
          :key="type"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <v-text-field
            :label="type"
            v-model.number="formData.workers[type]"
            type="number"
            dense
            outlined
            hide-details
          />
        </v-col>
      </v-row>

      <!-- 第四排: Machines (多欄) -->
      <v-row density="compact" class="mt-2">
        <h3 class="section-title">Machines</h3>
        <v-col
          v-for="(count, type) in formData.machines"
          :key="type"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <v-text-field
            :label="type"
            v-model.number="formData.machines[type]"
            type="number"
            dense
            outlined
            hide-details
          />
        </v-col>
      </v-row>

      <!-- 第五排: 施工人員多選 -->
      <v-row density="compact" class="mt-2">
        <v-col cols="12">
          <v-select
            v-model="selectedStaffIds"
            :items="staffDropdownOptions"
            item-title="label"
            item-value="value"
            label="Staffs"
            multiple
            dense
            outlined
            hide-details
            chips
          />
        </v-col>
      </v-row>
    </v-card-text>

    <!-- 底部操作按鈕區 -->
    <v-card-actions class="footer-buttons justify-end">
      <!-- 清空表單 -->
      <v-btn
        size="small"
        variant="text"
        class="me-2"
        @click="clearForm"
      >
        Clear
      </v-btn>

      <!-- Cancel -->
      <v-btn
        size="small"
        variant="text"
        class="me-2"
        @click="cancelForm"
      >
        Cancel
      </v-btn>

      <!-- Submit(Create/Update) -->
      <v-btn
        size="small"
        color="primary"
        @click="handleSubmit"
      >
        {{ diaryId ? 'Update' : 'Create' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import axios from 'axios'
import { ref, onMounted, watch, computed } from 'vue'

export default {
  name: 'SiteDiaryForm',
  props: {
    projectId: { type: Number, required: true },
    diaryId: { type: Number, default: null }
  },
  setup(props, { emit }) {
    // ========== 預設空白表單結構 ========== 
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
        // ★ 新增「機炮」
        '機炮': 0,
        '屈鐵機': 0,
        '風車鋸': 0
      }
    }

    // 綁定在表單的資料
    const formData = ref(JSON.parse(JSON.stringify(initialFormData)))

    // 被選的人員 id 列表
    const selectedStaffIds = ref([])

    // 報表日期 (與 <v-text-field type="date"> 雙向綁定)
    const localReportDateStr = ref('')

    // 施工人員清單
    const staffList = ref([])

    // 下拉選單選項
    const staffDropdownOptions = computed(() => {
      return staffList.value.map(s => ({
        label: `${s.name} (${s.role || 'N/A'})`,
        value: s.id
      }))
    })

    // 載入人員
    const fetchStaff = async () => {
      try {
        const { data } = await axios.get('/api/staff')
        staffList.value = data
      } catch (err) {
        console.error(err)
      }
    }

    // 取得並載入 diaryId 對應的日報
    const fetchExistingDiary = async () => {
      if (!props.diaryId) return
      try {
        const { data } = await axios.get(
          `/api/projects/${props.projectId}/site_diaries`
        )
        const target = data.find(d => d.id === props.diaryId)
        if (!target) return
        setFormDataFromDiary(target)
      } catch (err) {
        console.error(err)
      }
    }

    // 取得「最後一筆」日報作為預設
    const fetchLastDiaryAsDefault = async () => {
      if (props.diaryId) return
      try {
        const { data } = await axios.get(
          `/api/projects/${props.projectId}/site_diaries/last`
        )
        if (!data.id) {
          // 無任何日報
          return
        }
        // 有上一筆 => 帶入
        setFormDataFromDiary(data)
      } catch (err) {
        console.error(err)
      }
    }

    // 將已存在的日報資料寫入 formData
    function setFormDataFromDiary(diaryData) {
      if (diaryData.report_date) {
        localReportDateStr.value = diaryData.report_date
      } else {
        localReportDateStr.value = ''
      }

      formData.value.weather_morning = diaryData.weather_morning || ''
      formData.value.weather_noon = diaryData.weather_noon || ''
      formData.value.day_count = diaryData.day_count || null
      formData.value.summary = diaryData.summary || ''

      // Workers
      const updatedWorkers = JSON.parse(JSON.stringify(initialFormData.workers))
      for (const w of diaryData.workers || []) {
        updatedWorkers[w.type] = w.quantity
      }
      formData.value.workers = updatedWorkers

      // Machines
      const updatedMachines = JSON.parse(JSON.stringify(initialFormData.machines))
      for (const m of diaryData.machines || []) {
        updatedMachines[m.type] = m.quantity
      }
      formData.value.machines = updatedMachines

      // Staff
      selectedStaffIds.value = (diaryData.staffs || []).map(s => s.id)
    }

    // 新增/更新
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
          await axios.post(
            `/api/projects/${props.projectId}/site_diaries`,
            payload
          )
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

    // 取消
    const cancelForm = () => {
      emit('cancel')
    }

    // 清空表單
    const clearForm = () => {
      formData.value = JSON.parse(JSON.stringify(initialFormData))
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
      // 若為新建模式 => 預帶最後一筆
      if (!props.diaryId) {
        fetchLastDiaryAsDefault()
      } else {
        // 編輯模式 => 帶入指定日報
        fetchExistingDiary()
      }
    })

    return {
      formData,
      selectedStaffIds,
      staffDropdownOptions,
      localReportDateStr,
      handleSubmit,
      cancelForm,
      clearForm
    }
  }
}
</script>

<style scoped>
.site-diary-form-card {
  font-size: 0.875rem; /* 小一點的字體 */
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.header-row {
  border-bottom: 1px solid #eee;
  padding-bottom: 4px;
}

.form-content {
  padding-top: 8px;
  padding-bottom: 8px;
  overflow-y: auto;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  width: 100%;
}

.footer-buttons {
  border-top: 1px solid #eee;
}

.me-2 {
  margin-right: 8px !important;
}
.mt-2 {
  margin-top: 8px !important;
}
</style>
