<template>
  <div class="container my-4">
    <h2>Documents of Project #{{ projectId }}</h2>

    <!-- ★ Tabs -->
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
        <div v-if="dailyReports.length > 0">
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="selectAllDiaries"
              :checked="isAllSelected"
              @change="toggleSelectAll"
            />
            <label class="form-check-label" for="selectAllDiaries">Select All</label>
          </div>
          <button
            class="btn btn-primary btn-sm"
            :disabled="selectedDiaryIds.length === 0"
            @click="downloadMultiple('xlsx')"
          >
            XLSX
          </button>
          <button
            class="btn btn-primary btn-sm ms-1"
            :disabled="selectedDiaryIds.length === 0"
            @click="downloadMultiple('sheet1')"
          >
            PDF (Sheet1)
          </button>
          <button
            class="btn btn-primary btn-sm ms-1"
            :disabled="selectedDiaryIds.length === 0"
            @click="downloadMultiple('sheet2')"
          >
            PDF (Sheet2)
          </button>
        </div>
        <button
          class="btn btn-success btn-sm"
          @click="openCreateDiary"
        >
          + New Daily Report
        </button>
      </div>

      <!-- Diary Table -->
      <table class="table table-sm table-bordered">
        <thead>
          <tr>
            <th style="width:40px;">
              <input
                type="checkbox"
                :checked="isAllSelected"
                @change="toggleSelectAll"
                class="form-check-input"
              />
            </th>
            <th>ID</th>
            <th>Date</th>
            <th>Weather(M)</th>
            <th>Weather(N)</th>
            <th>Day#</th>
            <th>Updated</th>
            <th>Edit</th>
            <th>Del</th>
            <th>Download</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="dr in dailyReports"
            :key="dr.id"
            :class="rowClass(dr)"
          >
            <td>
              <input
                type="checkbox"
                class="form-check-input"
                :value="dr.id"
                v-model="selectedDiaryIds"
              />
            </td>
            <td>{{ dr.id }}</td>
            <td>{{ dr.report_date }}</td>
            <td>{{ dr.weather_morning }}</td>
            <td>{{ dr.weather_noon }}</td>
            <td>{{ dr.day_count }}</td>
            <td>{{ dr.updated_at }}</td>
            <td>
              <button
                class="btn btn-warning btn-sm"
                @click="editDiary(dr.id)"
              >
                Edit
              </button>
            </td>
            <td>
              <button
                class="btn btn-danger btn-sm"
                @click="deleteDiary(dr.id)"
              >
                Del
              </button>
            </td>
            <td>
              <div class="btn-group btn-group-sm">
                <button
                  class="btn btn-outline-primary"
                  @click="downloadSingle(dr.id, 'xlsx')"
                >
                  XLSX
                </button>
                <button
                  class="btn btn-outline-primary"
                  @click="downloadSingle(dr.id, 'sheet1')"
                >
                  PDF1
                </button>
                <button
                  class="btn btn-outline-primary"
                  @click="downloadSingle(dr.id, 'sheet2')"
                >
                  PDF2
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 其他 doc_type 省略... -->

    <!-- (略) 新增文件 Modal ... -->

    <!-- 日報用的 Modal (Create/Edit) -->
    <div
      class="modal"
      :class="{ fade: true, show: showDiaryModal }"
      :style="{ display: showDiaryModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="showDiaryModal"
      @click.self="closeDiaryModal"
    >
      <div class="modal-dialog modal-xl" role="document">
        <div class="modal-content">
          <div class="modal-body">
            <DailyReportForm
              :projectId="Number(projectId)"
              :editingId="editingDiaryId"
              @saved="onDiarySaved"
              @cancel="closeDiaryModal"
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
      :class="{ fade: true, show: showProgress }"
      :style="{ display: showProgress ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="showProgress"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5>Export Progress</h5>
            <button
              type="button"
              class="btn-close"
              @click="closeProgressModal"
            ></button>
          </div>
          <div class="modal-body">
            <div v-if="exportError" class="alert alert-danger">
              {{ exportError }}
            </div>
            <div v-else-if="exportDone" class="alert alert-success">
              Done! (Auto-Download triggered)
            </div>
            <p v-else>Processing... {{ exportProgress }}%</p>
            <div class="progress mb-2">
              <div
                class="progress-bar"
                role="progressbar"
                :style="{ width: exportProgress + '%' }"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {{ exportProgress }}%
              </div>
            </div>
          </div>
          <div
            class="modal-footer"
            v-if="exportDone || exportError"
          >
            <button
              class="btn btn-secondary"
              @click="closeProgressModal"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="showProgress"
      class="modal-backdrop fade show"
    ></div>

    <!-- ★ 用於自動點擊下載的隱藏連結 -->
    <a ref="hiddenDownloadLink" style="display:none;"></a>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import DailyReportForm from '@/components/SiteDiaryForm.vue'

export default {
  name: 'MaterialFormView',
  components: {
    DailyReportForm
  },
  setup() {
    const route = useRoute()
    const projectId = route.params.projectId

    const docTypeTabs = [
      { label: 'DRAWING', value: 'DRAWING' },
      { label: 'MAT', value: 'MAT' },
      { label: 'LETTER', value: 'LETTER' },
      { label: 'DAILY_REPORT', value: 'DAILY_REPORT' }
    ]
    const activeTab = ref('DAILY_REPORT')

    const dailyReports = ref([])
    const selectedDiaryIds = ref([])
    const editingDiaryId = ref(0)
    const showDiaryModal = ref(false)

    const showProgress = ref(false)
    const exportProgress = ref(0)
    const exportDone = ref(false)
    const exportError = ref('')
    const exportDownloadUrl = ref('')

    // ★ 用於自動下載
    const hiddenDownloadLink = ref(null)

    let evtSrc = null

    function fetchDailyReports() {
      axios
        .get('/api/documents/daily-reports', {
          params: { project_id: projectId }
        })
        .then(res => {
          dailyReports.value = res.data
          selectedDiaryIds.value = []
        })
        .catch(err => console.error(err))
    }

    function openCreateDiary() {
      editingDiaryId.value = 0
      showDiaryModal.value = true
    }
    function editDiary(id) {
      editingDiaryId.value = id
      showDiaryModal.value = true
    }
    function deleteDiary(id) {
      if (!confirm('Delete?')) return
      axios
        .delete(`/api/documents/daily-reports/${id}?project_id=${projectId}`)
        .then(() => {
          fetchDailyReports()
        })
        .catch(err => console.error(err))
    }
    function closeDiaryModal() {
      showDiaryModal.value = false
    }
    function onDiarySaved() {
      showDiaryModal.value = false
      fetchDailyReports()
    }

    function rowClass(d) {
      return selectedDiaryIds.value.includes(d.id) ? 'table-active' : ''
    }
    const isAllSelected = computed(() => {
      return (
        dailyReports.value.length > 0 &&
        selectedDiaryIds.value.length === dailyReports.value.length
      )
    })
    function toggleSelectAll() {
      if (isAllSelected.value) {
        selectedDiaryIds.value = []
      } else {
        selectedDiaryIds.value = dailyReports.value.map(x => x.id)
      }
    }

    function downloadMultiple(fileType) {
      if (selectedDiaryIds.value.length === 0) {
        alert('No diaries selected.')
        return
      }
      showProgress.value = true
      exportProgress.value = 0
      exportDone.value = false
      exportError.value = ''
      exportDownloadUrl.value = ''

      axios
        .post('/api/documents/daily-report/multi_download_async', {
          project_id: Number(projectId),
          diary_ids: selectedDiaryIds.value,
          file_type: fileType
        })
        .then(resp => {
          const job_id = resp.data.job_id
          if (!job_id) {
            console.error('[DEBUG] No job_id returned from multi_download_async.')
            throw new Error('No job_id returned.')
          }

          evtSrc = new EventSource(`/api/documents/daily-report/progress-sse/${job_id}`)
          evtSrc.onopen = () => {
            console.log('[DEBUG] SSE connection opened. job_id=', job_id)
          }
          evtSrc.onmessage = evt => {
            try {
              const data = JSON.parse(evt.data)
              exportProgress.value = data.progress || 0

              if (data.status === 'done') {
                exportDone.value = true
                exportProgress.value = 100
                const dlUrl = `/api/documents/daily-report/multi_download_result?job_id=${job_id}`
                exportDownloadUrl.value = dlUrl
                // ★ 自動觸發下載
                autoDownload(dlUrl)
                if (evtSrc) {
                  evtSrc.close()
                  evtSrc = null
                }
              } else if (data.status === 'error') {
                exportError.value = data.error_msg || 'Unknown Error'
                if (evtSrc) {
                  evtSrc.close()
                  evtSrc = null
                }
              }
            } catch (parseErr) {
              console.error('[DEBUG] SSE parse error:', parseErr)
            }
          }
          evtSrc.onerror = e => {
            console.error('[DEBUG] SSE onerror:', e)
            exportError.value = 'SSE Connection Error'
            if (evtSrc) {
              evtSrc.close()
              evtSrc = null
            }
          }
        })
        .catch(err => {
          console.error('[DEBUG] downloadMultiple error:', err)
          exportError.value = String(err)
        })
    }

    function autoDownload(url) {
      if (!hiddenDownloadLink.value) return
      hiddenDownloadLink.value.href = url
      // 不指定 download filename，後端 Content-Disposition 會帶檔名
      hiddenDownloadLink.value.download = ''
      hiddenDownloadLink.value.click()
    }

    function downloadSingle(id, fileType) {
      const url = `/api/documents/daily-report/${id}/download?project_id=${projectId}&file_type=${fileType}`
      window.open(url, '_blank')
    }

    function closeProgressModal() {
      showProgress.value = false
      exportProgress.value = 0
      exportDone.value = false
      exportError.value = ''
      exportDownloadUrl.value = ''
      if (evtSrc) {
        evtSrc.close()
        evtSrc = null
      }
    }

    onMounted(() => {
      if (activeTab.value === 'DAILY_REPORT') {
        fetchDailyReports()
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
      isAllSelected,
      rowClass,

      openCreateDiary,
      editDiary,
      deleteDiary,
      closeDiaryModal,
      onDiarySaved,

      downloadMultiple,
      downloadSingle,

      toggleSelectAll,

      showProgress,
      exportProgress,
      exportDone,
      exportError,
      exportDownloadUrl,
      closeProgressModal,

      hiddenDownloadLink
    }
  }
}
</script>

<style scoped>
.table-active {
  background-color: #f0f8ff !important;
}
.modal {
  z-index: 1050;
}
.modal-backdrop {
  z-index: 1040;
}
</style>
