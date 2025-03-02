<template>
  <div class="container my-4">
    <h2>Documents of Project #{{ projectId }}</h2>

    <!-- ★ Tabs (英文 + 指定順序) -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item" v-for="tab in docTypeTabs" :key="tab.value">
        <a
          href="#"
          class="nav-link"
          :class="{ active: activeTab === tab.value }"
          @click.prevent="activeTab = tab.value"
        >
          {{ tab.label }}
        </a>
      </li>
    </ul>

    <!-- 若為 DAILY_REPORT => 顯示日報 -->
    <div v-if="activeTab === 'DAILY_REPORT'">
      <h4>Daily Reports</h4>

      <!-- 多選下載: XLSX / PDF(表1) / PDF(表2) -->
      <div class="d-flex justify-content-between mb-2">
        <div class="multi-select-actions" v-if="dailyReports.length > 0">
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="selectAllDiaries"
              :checked="isAllDiariesSelected"
              @change="toggleSelectAllDiaries"
            />
            <label class="form-check-label" for="selectAllDiaries">Select All</label>
          </div>
          <button
            class="btn btn-primary btn-sm"
            :disabled="selectedDiaryIds.length === 0"
            @click="downloadMultipleAsync('xlsx')"
          >
            Download XLSX
          </button>
          <button
            class="btn btn-primary btn-sm ms-1"
            :disabled="selectedDiaryIds.length === 0"
            @click="downloadMultipleAsync('sheet1')"
          >
            PDF (Sheet1)
          </button>
          <button
            class="btn btn-primary btn-sm ms-1"
            :disabled="selectedDiaryIds.length === 0"
            @click="downloadMultipleAsync('sheet2')"
          >
            PDF (Sheet2)
          </button>
        </div>
        <div>
          <button class="btn btn-success btn-sm" @click="openCreateDiary">
            + New Daily Report
          </button>
        </div>
      </div>

      <!-- Diary Table -->
      <table class="table table-sm table-bordered">
        <thead>
          <tr>
            <th style="width: 40px;">
              <input
                type="checkbox"
                :checked="isAllDiariesSelected"
                @change="toggleSelectAllDiaries"
                class="form-check-input"
              />
            </th>
            <th>ID</th>
            <th>Date</th>
            <th>Weather(M)</th>
            <th>Weather(N)</th>
            <th>Day Count</th>
            <th>Last Updated</th>
            <th>Edit</th>
            <th>Del</th>
            <th>Download</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in dailyReports"
            :key="item.id"
            :class="getDiaryRowClass(item)"
          >
            <td>
              <input
                type="checkbox"
                v-model="selectedDiaryIds"
                :value="item.id"
                class="form-check-input"
              />
            </td>
            <td>{{ item.id }}</td>
            <td>{{ item.report_date }}</td>
            <td>{{ item.weather_morning }}</td>
            <td>{{ item.weather_noon }}</td>
            <td>{{ item.day_count }}</td>
            <td>{{ item.updated_at || '' }}</td>
            <td>
              <button
                class="btn btn-warning btn-sm"
                @click="editDiary(item.id)"
              >
                Edit
              </button>
            </td>
            <td>
              <button
                class="btn btn-danger btn-sm"
                @click="deleteDiary(item.id)"
              >
                Del
              </button>
            </td>
            <td>
              <div class="btn-group btn-group-sm">
                <button
                  class="btn btn-outline-primary"
                  @click="downloadSingleDiary(item.id, 'xlsx')"
                >
                  XLSX
                </button>
                <button
                  class="btn btn-outline-primary"
                  @click="downloadSingleDiary(item.id, 'sheet1')"
                >
                  PDF1
                </button>
                <button
                  class="btn btn-outline-primary"
                  @click="downloadSingleDiary(item.id, 'sheet2')"
                >
                  PDF2
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 其餘 doc_type (DRAWING, TECH_APPROVAL, MAT, LETTER, ... ) 略 -->

    <!-- [Modal] 日報 (Create/Edit) -->
    <div
      class="modal"
      :class="{ fade: true, show: showDiaryModal }"
      :style="{ display: showDiaryModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="showDiaryModal"
      @click.self="showDiaryModal = false"
    >
      <div class="modal-dialog modal-xl" role="document">
        <div class="modal-content">
          <div class="modal-body">
            <DailyReportForm
              :projectId="Number(projectId)"
              :diaryId="editingDiaryId"
              @updated="onDiaryUpdated"
              @cancel="onDiaryCancelled"
            />
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="showDiaryModal"
      class="modal-backdrop fade show"
    ></div>

    <!-- SSE 下載進度 (自動下載) -->
    <div
      class="modal"
      :class="{ fade: true, show: showProgressModal }"
      :style="{ display: showProgressModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="showProgressModal"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Export Progress</h5>
            <button type="button" class="btn-close" @click="closeProgressModal"></button>
          </div>
          <div class="modal-body">
            <div v-if="exportError" class="alert alert-danger">
              {{ exportError }}
            </div>
            <div v-else-if="exportDone" class="alert alert-success">
              Export completed! (Auto Download)
            </div>
            <p v-else>Preparing files... ({{ exportProgress }}%)</p>
            <div class="progress mb-2">
              <div
                class="progress-bar"
                role="progressbar"
                :style="{ width: exportProgress + '%' }"
                :aria-valuenow="exportProgress"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {{ exportProgress }}%
              </div>
            </div>
          </div>
          <div class="modal-footer" v-if="exportDone || exportError">
            <button type="button" class="btn btn-secondary" @click="closeProgressModal">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="showProgressModal"
      class="modal-backdrop fade show"
    ></div>

    <!-- ★ 隱藏的 <a> 用於自動觸發下載 -->
    <a ref="hiddenDownloadLink" style="display:none;"></a>
  </div>
</template>

<script lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import DailyReportForm from '@/components/SiteDiaryForm.vue'

interface DailyReportData {
  id: number
  report_date: string
  weather_morning: string
  weather_noon: string
  day_count: number
  updated_at?: string
}

export default {
  name: 'ProjectDocumentsView',
  components: {
    DailyReportForm
  },
  setup() {
    const route = useRoute()
    const projectId = route.params.projectId as string

    const docTypeTabs = [
      { label: 'DRAWING',          value: 'DRAWING' },
      { label: 'TECH_APPROVAL',    value: 'TECH_APPROVAL' },
      { label: 'MAT',              value: 'MAT' },
      { label: 'LETTER',           value: 'LETTER' },
      { label: 'RFI',              value: 'RFI' },
      { label: 'RIN',              value: 'RIN' },
      { label: 'RECEIVED_LETTER',  value: 'RECEIVED_LETTER' },
      { label: 'TEST_REPORT',      value: 'TEST_REPORT' },
      { label: 'DAILY_REPORT',     value: 'DAILY_REPORT' }
    ]
    const activeTab = ref('DAILY_REPORT')

    const dailyReports = ref<DailyReportData[]>([])
    const selectedDiaryIds = ref<number[]>([])
    const editingDiaryId = ref<number>(0)
    const showDiaryModal = ref(false)

    // SSE
    const showProgressModal = ref(false)
    const exportProgress = ref(0)
    const exportError = ref('')
    const exportDone = ref(false)
    const exportDownloadUrl = ref('')
    const hiddenDownloadLink = ref<HTMLAnchorElement | null>(null)

    let eventSource: EventSource | null = null

    async function fetchDailyReports() {
      try {
        const res = await axios.get('/api/documents/daily-reports', {
          params: { project_id: projectId }
        })
        dailyReports.value = res.data
        selectedDiaryIds.value = []
      } catch (err) {
        console.error('[DEBUG] fetchDailyReports error:', err)
      }
    }

    function openCreateDiary() {
      editingDiaryId.value = 0
      showDiaryModal.value = true
    }
    function editDiary(id: number) {
      editingDiaryId.value = id
      showDiaryModal.value = true
    }
    async function deleteDiary(id: number) {
      if (!confirm('Delete this daily report?')) return
      try {
        await axios.delete(`/api/documents/daily-reports/${id}`, {
          params: { project_id: projectId }
        })
        fetchDailyReports()
      } catch (err) {
        console.error(err)
        alert('Delete failed.')
      }
    }
    function onDiaryUpdated() {
      showDiaryModal.value = false
      fetchDailyReports()
    }
    function onDiaryCancelled() {
      showDiaryModal.value = false
    }
    function downloadSingleDiary(id: number, fileType: string) {
      const url = `/api/documents/daily-report/${id}/download?project_id=${projectId}&file_type=${fileType}`
      window.open(url, '_blank')
    }

    const isAllDiariesSelected = computed(() => {
      return (
        dailyReports.value.length > 0 &&
        selectedDiaryIds.value.length === dailyReports.value.length
      )
    })
    function toggleSelectAllDiaries() {
      if (isAllDiariesSelected.value) {
        selectedDiaryIds.value = []
      } else {
        selectedDiaryIds.value = dailyReports.value.map(d => d.id)
      }
    }
    function getDiaryRowClass(d: DailyReportData) {
      return selectedDiaryIds.value.includes(d.id) ? 'table-active' : ''
    }
    function downloadMultipleAsync(fileType: string) {
      if (selectedDiaryIds.value.length === 0) {
        alert('No diaries selected.')
        return
      }
      showProgressModal.value = true
      exportProgress.value = 0
      exportError.value = ''
      exportDone.value = false
      exportDownloadUrl.value = ''

      axios.post('/api/documents/daily-report/multi_download_async', {
        project_id: Number(projectId),
        diary_ids: selectedDiaryIds.value,
        file_type: fileType
      })
      .then(resp => {
        const job_id = resp.data.job_id
        if (!job_id) {
          console.error('[DEBUG] No job_id returned from multi_download_async.')
          throw new Error('No job_id returned')
        }
        eventSource = new EventSource(`/api/documents/daily-report/progress-sse/${job_id}`)
        eventSource.onopen = () => {
          console.log('[DEBUG] SSE connected. job_id=', job_id)
        }
        eventSource.onmessage = evt => {
          try {
            const data = JSON.parse(evt.data)
            exportProgress.value = data.progress || 0
            if (data.status === 'done') {
              exportDone.value = true
              exportProgress.value = 100
              const dlUrl = `/api/documents/daily-report/multi_download_result?job_id=${job_id}`
              exportDownloadUrl.value = dlUrl
              autoDownload(dlUrl)
              if (eventSource) {
                eventSource.close()
                eventSource = null
              }
            } else if (data.status === 'error') {
              exportError.value = data.error_msg || 'Unknown error'
              if (eventSource) {
                eventSource.close()
                eventSource = null
              }
            }
          } catch (parseErr) {
            console.error('[DEBUG] SSE parse error:', parseErr)
          }
        }
        eventSource.onerror = err => {
          console.error('[DEBUG] SSE onerror:', err)
          exportError.value = 'SSE Connection Error'
          if (eventSource) {
            eventSource.close()
            eventSource = null
          }
        }
      })
      .catch(e => {
        console.error('[DEBUG] downloadMultipleAsync error:', e)
        exportError.value = String(e)
      })
    }

    function autoDownload(url: string) {
      if (!hiddenDownloadLink.value) return
      hiddenDownloadLink.value.href = url
      hiddenDownloadLink.value.download = ''
      hiddenDownloadLink.value.click()
    }

    function closeProgressModal() {
      showProgressModal.value = false
      exportProgress.value = 0
      exportDone.value = false
      exportError.value = ''
      exportDownloadUrl.value = ''
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    }

    onMounted(() => {
      if (activeTab.value === 'DAILY_REPORT') {
        fetchDailyReports()
      } else {
        // 省略 fetchDocuments() or other doc type
      }
    })

    return {
      projectId,
      docTypeTabs,
      activeTab,
      dailyReports,
      selectedDiaryIds,
      editingDiaryId,
      showDiaryModal,
      showProgressModal,
      exportProgress,
      exportError,
      exportDone,
      exportDownloadUrl,
      hiddenDownloadLink,

      isAllDiariesSelected,
      toggleSelectAllDiaries,
      getDiaryRowClass,

      fetchDailyReports,
      openCreateDiary,
      editDiary,
      deleteDiary,
      onDiaryUpdated,
      onDiaryCancelled,
      downloadSingleDiary,

      downloadMultipleAsync,
      closeProgressModal,
      autoDownload
    }
  }
}
</script>

<style scoped>
.me-2 {
  margin-right: 8px;
}
.modal {
  z-index: 1050;
}
.modal-backdrop {
  z-index: 1040;
}
.table-active {
  background-color: #f0f8ff !important;
}
</style>
