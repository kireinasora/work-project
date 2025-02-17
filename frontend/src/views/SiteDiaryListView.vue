<template>
  <div class="container-fluid" style="max-width:2000px; margin:0 auto;">
    <h2>Site Diaries Management</h2>

    <div v-if="projectInfo" class="border p-3 mb-4">
      <h3>Project: {{ projectInfo.name }}</h3>
      <p>Owner: {{ projectInfo.owner }}</p>
    </div>

    <!-- 排序操作 -->
    <div class="d-flex align-items-center mb-3" style="gap: 1rem;">
      <div>
        <label>Sort By:</label>
        <select v-model="sortBy" class="form-select form-select-sm w-auto d-inline-block">
          <option value="report_date">Date</option>
          <option value="day_count">Day Count</option>
          <option value="updated_at">Last Edited</option>
        </select>
      </div>
      <div>
        <label>Order:</label>
        <select v-model.number="sortOrder" class="form-select form-select-sm w-auto d-inline-block">
          <option :value="1">ASC</option>
          <option :value="-1">DESC</option>
        </select>
      </div>
      <button class="btn btn-secondary btn-sm" @click="fetchSiteDiaries">Apply Sort</button>
    </div>

    <button class="btn btn-success mb-4" @click="openCreateDialog">NEW SITE DIARY</button>

    <!-- 多選下載操作區 -->
    <div class="mb-3 d-flex align-items-center" style="gap: 1rem;">
      <div class="form-check">
        <input
          class="form-check-input"
          type="checkbox"
          id="selectAll"
          :checked="isAllSelected"
          @change="toggleSelectAll"
        />
        <label class="form-check-label" for="selectAll">全選</label>
      </div>

      <!-- 改用非同步 + SSE 的下載按鈕 -->
      <button class="btn btn-outline-primary btn-sm" @click="downloadMultipleAsync('xlsx')">
        Download XLSX (多筆, SSE)
      </button>
      <button class="btn btn-outline-primary btn-sm" @click="downloadMultipleAsync('sheet1')">
        Download PDF(表1) (SSE)
      </button>
      <button class="btn btn-outline-primary btn-sm" @click="downloadMultipleAsync('sheet2')">
        Download PDF(表2) (SSE)
      </button>
    </div>

    <div class="table-responsive">
      <!-- 使用 table-sm 並在 :class="getRowClass(item)" 來標示星期天 -->
      <table class="table table-sm table-bordered table-hover mb-6">
        <thead>
          <tr>
            <th>#</th>
            <th>勾選</th>
            <th>日期</th>
            <th>天氣(早)</th>
            <th>天氣(中)</th>
            <th>日數</th>
            <th>Last Edited</th>
            <th>EDIT</th>
            <th>DELETE</th>
            <th>DOWNLOAD (Single)</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, index) in siteDiaries"
            :key="item.id"
            :class="getRowClass(item)"
          >
            <td>{{ index + 1 }}</td>
            <td>
              <input
                type="checkbox"
                class="form-check-input"
                :value="item.id"
                v-model="selectedDiaryIds"
              />
            </td>
            <td>{{ item.report_date }}</td>
            <td>{{ item.weather_morning }}</td>
            <td>{{ item.weather_noon }}</td>
            <td>{{ item.day_count }}</td>
            <td>{{ item.updated_at || '' }}</td>
            <td>
              <button class="btn btn-warning btn-sm" @click="openEditDialog(item.id)">
                EDIT
              </button>
            </td>
            <td>
              <button class="btn btn-danger btn-sm" @click="deleteDiary(item.id)">
                DELETE
              </button>
            </td>
            <td>
              <div class="dropdown">
                <button
                  class="btn btn-info btn-sm dropdown-toggle"
                  type="button"
                  data-bs-toggle="dropdown"
                >
                  DOWNLOAD
                </button>
                <ul class="dropdown-menu">
                  <li>
                    <a
                      class="dropdown-item"
                      href="#"
                      @click.prevent="downloadReport(item.id, 'xlsx')"
                    >
                      Excel (XLSX)
                    </a>
                  </li>
                  <li>
                    <a
                      class="dropdown-item"
                      href="#"
                      @click.prevent="downloadReport(item.id, 'sheet1')"
                    >
                      PDF(表1)
                    </a>
                  </li>
                  <li>
                    <a
                      class="dropdown-item"
                      href="#"
                      @click.prevent="downloadReport(item.id, 'sheet2')"
                    >
                      PDF(表2)
                    </a>
                  </li>
                </ul>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Diary Form Modal -->
    <div
      class="modal"
      :class="{ fade: true, show: displayFormDialog }"
      :style="{ display: displayFormDialog ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="displayFormDialog"
    >
      <div class="modal-dialog modal-xl" role="document">
        <div class="modal-content">
          <div class="modal-body">
            <SiteDiaryForm
              :projectId="projectIdNumber"
              :diaryId="editingDiaryId"
              @updated="onDiaryUpdated"
              @cancel="onDiaryCancelled"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Modal backdrop for form -->
    <div
      v-if="displayFormDialog"
      class="modal-backdrop fade show"
    ></div>

    <!-- SSE 進度 Modal -->
    <div
      class="modal"
      :class="{ fade: true, show: showProgressModal }"
      :style="{ display: showProgressModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="showProgressModal"
    >
      <div class="modal-dialog modal-sm" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Export Progress</h5>
            <button
              type="button"
              class="btn-close"
              @click="abortSse"
            ></button>
          </div>
          <div class="modal-body text-center">
            <p v-if="progressStatus === 'error'" class="text-danger">
              Error: {{ progressErrorMsg }}
            </p>
            <p v-else-if="progressStatus === 'done'" class="text-success">
              All done!
            </p>
            <p v-else>
              Exporting... ({{ sseProgress }}%)
            </p>

            <!-- Bootstrap 進度條範例 -->
            <div class="progress" style="height: 24px;">
              <div
                class="progress-bar"
                role="progressbar"
                :style="{width: sseProgress + '%'}"
                :aria-valuenow="sseProgress"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {{ sseProgress }}%
              </div>
            </div>

          </div>
          <div class="modal-footer">
            <button
              v-if="progressStatus === 'done' || progressStatus === 'error'"
              type="button"
              class="btn btn-secondary"
              @click="closeProgressModal"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal backdrop for SSE progress -->
    <div
      v-if="showProgressModal"
      class="modal-backdrop fade show"
    ></div>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import SiteDiaryForm from '@/components/SiteDiaryForm.vue'

export default {
  name: 'SiteDiaryListView',
  components: { SiteDiaryForm },
  setup() {
    const route = useRoute()
    const siteDiaries = ref([])
    const projectInfo = ref(null)
    const displayFormDialog = ref(false)
    const editingDiaryId = ref(null)

    // 多選勾選
    const selectedDiaryIds = ref([])

    // 排序
    const sortBy = ref('report_date')
    const sortOrder = ref(1)

    const projectIdNumber = computed(() => Number(route.params.projectId))

    // =============== SSE 相關的狀態 ===============
    const showProgressModal = ref(false)
    const sseProgress = ref(0)
    const progressStatus = ref('idle') // idle, in_progress, done, error
    const progressErrorMsg = ref('')
    let sse = null // 用於記錄 SSE 連線物件 (EventSource)

    // 取得專案資訊
    const fetchProjectInfo = async () => {
      try {
        const { data } = await axios.get(`/api/projects/${projectIdNumber.value}`)
        projectInfo.value = data
      } catch (error) {
        console.error(error)
      }
    }

    // 取得日報列表
    const fetchSiteDiaries = async () => {
      try {
        const { data } = await axios.get(
          `/api/projects/${projectIdNumber.value}/site_diaries`,
          { params: { sort_by: sortBy.value, sort_order: sortOrder.value } }
        )
        siteDiaries.value = data
        selectedDiaryIds.value = [] // 每次重新載入都清空勾選
      } catch (err) {
        console.error(err)
      }
    }

    // 開啟「新建」對話框
    const openCreateDialog = () => {
      editingDiaryId.value = null
      displayFormDialog.value = true
    }

    // 開啟「編輯」對話框
    const openEditDialog = (diaryId) => {
      editingDiaryId.value = diaryId
      displayFormDialog.value = true
    }

    // 刪除日報
    const deleteDiary = async (diaryId) => {
      if (!confirm('Are you sure you want to delete this Site Diary?')) return
      try {
        await axios.delete(`/api/projects/${projectIdNumber.value}/site_diaries/${diaryId}`)
        alert('Diary deleted.')
        fetchSiteDiaries()
      } catch (err) {
        console.error(err)
      }
    }

    // 單筆下載 (維持原狀)
    const downloadReport = async (diaryId, fileType) => {
      try {
        const response = await axios.get(
          `/api/projects/${projectIdNumber.value}/site_diaries/${diaryId}/download_report?file=${fileType}`,
          { responseType: 'blob' }
        )
        let filename
        if (fileType === 'xlsx') {
          filename = 'daily_report_filled.xlsx'
        } else if (fileType === 'sheet1') {
          filename = 'daily_report_sheet1.pdf'
        } else {
          filename = 'daily_report_sheet2.pdf'
        }

        // 嘗試從 headers 取得後端回傳檔名
        const cd = response.headers['content-disposition']
        if (cd) {
          const m = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(cd)
          if (m && m[1]) {
            filename = m[1].replace(/['"]/g, '')
          }
        }

        const blobUrl = window.URL.createObjectURL(response.data)
        const link = document.createElement('a')
        link.href = blobUrl
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(blobUrl)
      } catch (err) {
        console.error('Download failed:', err)
      }
    }

    // ================ 重新改寫多筆下載 (SSE 版本) ====================
    const downloadMultipleAsync = async (fileType) => {
      if (!selectedDiaryIds.value.length) {
        alert('請先勾選一筆以上的日報！')
        return
      }
      // 先呼叫非同步 API => 取得 job_id
      try {
        // 重置 SSE 狀態
        sseProgress.value = 0
        progressStatus.value = 'in_progress'
        progressErrorMsg.value = ''
        showProgressModal.value = true

        const payload = {
          diary_ids: selectedDiaryIds.value,
          file_type: fileType
        }
        const res = await axios.post(
          `/api/projects/${projectIdNumber.value}/site_diaries/multi_download_async`,
          payload
        )
        const { job_id } = res.data

        // 開始 SSE 監聽
        startSse(job_id)
      } catch (err) {
        console.error('multi_download_async error:', err)
        alert('多筆下載時發生錯誤。請查看 console log')
      }
    }

    function startSse(jobId) {
      const sseUrl = `/api/progress-sse/${jobId}`
      sse = new EventSource(sseUrl)

      sse.onmessage = (evt) => {
        const data = JSON.parse(evt.data) // { progress, status, error_msg? }
        sseProgress.value = data.progress
        progressStatus.value = data.status || 'unknown'

        if (data.status === 'error') {
          progressErrorMsg.value = data.error_msg || ''
          sse.close()
        } else if (data.status === 'done') {
          sse.close()

          // SSE 結束後，再下載最後 ZIP
          fetchFinalZip(jobId)
        }
      }

      sse.onerror = (err) => {
        console.error('SSE error:', err)
        if (sse) {
          sse.close()
        }
        progressStatus.value = 'error'
        progressErrorMsg.value = 'SSE 連線出錯'
      }
    }

    async function fetchFinalZip(jobId) {
      try {
        // 直接透過 window.location 下載
        //   GET /api/projects/:projectId/site_diaries/multi_download_result?job_id=xxx
        const finalUrl = `/api/projects/${projectIdNumber.value}/site_diaries/multi_download_result?job_id=${jobId}`
        window.location = finalUrl
      } catch (err) {
        console.error('fetchFinalZip error:', err)
        progressStatus.value = 'error'
        progressErrorMsg.value = String(err)
      }
    }

    // 讓使用者有機會手動關閉 SSE
    function abortSse() {
      if (sse) {
        sse.close()
      }
      progressStatus.value = 'error'
      progressErrorMsg.value = 'User aborted.'
    }

    // 關閉 SSE 進度視窗
    function closeProgressModal() {
      showProgressModal.value = false
    }

    // ===============================================

    // 點擊「儲存 / 更新」後 => 關閉表單並重整列表
    const onDiaryUpdated = () => {
      displayFormDialog.value = false
      fetchSiteDiaries()
    }

    // 點擊 Cancel => 僅關閉表單
    const onDiaryCancelled = () => {
      displayFormDialog.value = false
    }

    // 是否全選
    const isAllSelected = computed(() => {
      return siteDiaries.value.length > 0 &&
        selectedDiaryIds.value.length === siteDiaries.value.length
    })
    const toggleSelectAll = (e) => {
      if (e.target.checked) {
        selectedDiaryIds.value = siteDiaries.value.map(d => d.id)
      } else {
        selectedDiaryIds.value = []
      }
    }

    // 若是星期天 => 顯示特殊背景
    const getRowClass = (diary) => {
      if (!diary.report_date) return ''
      const d = new Date(diary.report_date)
      return d.getDay() === 0 ? 'sunday-row' : ''
    }

    onMounted(() => {
      fetchProjectInfo()
      fetchSiteDiaries()
    })

    return {
      siteDiaries,
      projectInfo,
      displayFormDialog,
      editingDiaryId,

      selectedDiaryIds,
      isAllSelected,
      toggleSelectAll,

      sortBy,
      sortOrder,
      projectIdNumber,

      fetchSiteDiaries,
      openCreateDialog,
      openEditDialog,
      deleteDiary,
      downloadReport,

      // 新增 SSE 相關
      downloadMultipleAsync,
      showProgressModal,
      sseProgress,
      progressStatus,
      progressErrorMsg,
      abortSse,
      closeProgressModal,

      onDiaryUpdated,
      onDiaryCancelled,
      getRowClass
    }
  }
}
</script>

<style scoped>
.mb-6 {
  margin-bottom: 24px;
}

/*  專門針對星期天列，套用底色 */
.sunday-row td {
  background-color: #e9e9e9 !important;
}

/*  更改 table-sm 的內補與行高 => 更緊湊的列高 */
.table-sm > :not(caption) > * > * {
  padding: 0.3rem 0.5rem !important;
  line-height: 1.1 !important;
}

/* Modal 層級調整 */
.modal {
  z-index: 1050;
}
.modal-backdrop {
  z-index: 1040;
}
</style>
