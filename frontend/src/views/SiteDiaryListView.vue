<template>
  <div class="container-fluid" style="max-width:2000px; margin:0 auto;">
    <h2>Site Diaries Management</h2>

    <div v-if="projectInfo" class="border p-3 mb-4">
      <h3>Project: {{ projectInfo.name }}</h3>
      <p>Owner: {{ projectInfo.owner }}</p>
    </div>

    <button class="btn btn-success mb-4" @click="openCreateDialog">
      NEW SITE DIARY
    </button>

    <div class="table-responsive">
      <table class="table table-bordered table-hover mb-6">
        <thead>
          <tr>
            <th>#</th>
            <th>日期</th>
            <th>天氣(早)</th>
            <th>天氣(中)</th>
            <th>日數</th>
            <th>Last Edited</th>
            <th>EDIT</th>
            <th>DELETE</th>
            <th>DOWNLOAD</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, index) in siteDiaries"
            :key="item.id"
          >
            <td>{{ index + 1 }}</td>
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

    <!-- Form Modal -->
    <div
      class="modal fade"
      :class="{ show: displayFormDialog }"
      style="display: block;"
      tabindex="-1"
      role="dialog"
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
      <!-- backdrop -->
      <div class="modal-backdrop fade show"></div>
    </div>
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

    const projectIdNumber = computed(() => Number(route.params.projectId))

    const fetchProjectInfo = async () => {
      try {
        const { data } = await axios.get(`/api/projects/${projectIdNumber.value}`)
        projectInfo.value = data
      } catch (error) {
        console.error(error)
      }
    }

    const fetchSiteDiaries = async () => {
      try {
        const { data } = await axios.get(
          `/api/projects/${projectIdNumber.value}/site_diaries`
        )
        siteDiaries.value = data
      } catch (err) {
        console.error(err)
      }
    }

    const openCreateDialog = () => {
      editingDiaryId.value = null
      displayFormDialog.value = true
    }

    const openEditDialog = (diaryId) => {
      editingDiaryId.value = diaryId
      displayFormDialog.value = true
    }

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

    const downloadReport = async (diaryId, fileType) => {
      try {
        const response = await axios.get(
          `/api/projects/${projectIdNumber.value}/site_diaries/${diaryId}/download_report?file=${fileType}`,
          { responseType: 'blob' }
        )
        let filename =
          fileType === 'xlsx'
            ? 'daily_report_filled.xlsx'
            : fileType === 'sheet1'
            ? 'daily_report_sheet1.pdf'
            : 'daily_report_sheet2.pdf'

        // 嘗試從 headers 取得 filename
        const contentDisposition = response.headers['content-disposition']
        if (contentDisposition) {
          const cdRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
          const matches = cdRegex.exec(contentDisposition)
          if (matches && matches[1]) {
            filename = matches[1].replace(/['"]/g, '')
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

    const onDiaryUpdated = () => {
      displayFormDialog.value = false
      fetchSiteDiaries()
    }

    const onDiaryCancelled = () => {
      displayFormDialog.value = false
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
      projectIdNumber,
      openCreateDialog,
      openEditDialog,
      deleteDiary,
      downloadReport,
      onDiaryUpdated,
      onDiaryCancelled
    }
  }
}
</script>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}
.mb-6 {
  margin-bottom: 24px;
}
</style>
