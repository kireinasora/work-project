<!-- frontend/src/views/SiteDiaryListView.vue -->
<template>
  <v-container
    fluid
    style="max-width:2000px; margin:0 auto;"
  >
    <!-- 此行修改為 2000px，以使列表更寬 -->

    <h2>Site Diaries Management</h2>

    <div v-if="projectInfo" class="project-info-box mb-4">
      <h3>Project: {{ projectInfo.name }}</h3>
      <p>Owner: {{ projectInfo.owner }}</p>
    </div>

    <v-btn color="success" class="mb-4" @click="openCreateDialog">
      NEW SITE DIARY
    </v-btn>

    <!-- 
      外層包一層可水平捲動的 div，
      以防在小螢幕或欄位較多時，仍能左右捲動 
    -->
    <div class="table-scroll-wrapper">
      <v-data-table
        :headers="headers"
        :items="siteDiaries"
        :density="'compact'"
        class="mb-6 diary-table"
        :sort-by="['report_date']"
        :sort-desc="[true]"
        show-expand
        :items-per-page="-1"
        item-key="id"
      >
        <!-- 
          ↑ 使用 :items-per-page="-1" 使預設顯示所有資料、不分頁 
        -->

        <!-- # 欄位：顯示索引 (row index + 1) -->
        <template #item.index="{ index }">
          {{ index + 1 }}
        </template>

        <!-- last edited( updated_at ) 直接顯示 item.updated_at (字串) -->
        <template #item.updated_at="{ item }">
          {{ item.updated_at || '' }}
        </template>

        <!-- EDIT 按鈕 -->
        <template #item.edit="{ item }">
          <v-btn color="warning" variant="text" @click="openEditDialog(item.id)">
            EDIT
          </v-btn>
        </template>

        <!-- DELETE 按鈕 -->
        <template #item.delete="{ item }">
          <v-btn color="error" variant="text" @click="deleteDiary(item.id)">
            DELETE
          </v-btn>
        </template>

        <!-- DOWNLOAD 下拉 -->
        <template #item.download="{ item }">
          <v-menu>
            <template #activator="{ props }">
              <v-btn v-bind="props" variant="outlined" color="info">
                DOWNLOAD
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="downloadReport(item.id, 'xlsx')">
                <v-list-item-title>Excel (XLSX)</v-list-item-title>
              </v-list-item>
              <v-list-item @click="downloadReport(item.id, 'sheet1')">
                <v-list-item-title>PDF(表1)</v-list-item-title>
              </v-list-item>
              <v-list-item @click="downloadReport(item.id, 'sheet2')">
                <v-list-item-title>PDF(表2)</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </template>
      </v-data-table>
    </div>

    <!-- 表單對話框 -->
    <v-dialog
      v-model="displayFormDialog"
      max-width="1200px"
      persistent
    >
      <v-card>
        <v-card-title>
          <span class="text-h6">Site Diary</span>
        </v-card-title>
        <v-card-text>
          <SiteDiaryForm
            :projectId="projectIdNumber"
            :diaryId="editingDiaryId"
            @updated="onDiaryUpdated"
            @cancel="onDiaryCancelled"
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
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

    // 預設欄位配置
    const headers = ref([
      { text: '#', value: 'index', width: 50, align: 'center', sortable: false },
      { text: '日期', value: 'report_date', width: 130, align: 'start', sortable: true },
      { text: '天氣(早)', value: 'weather_morning', width: 90, align: 'center', sortable: true },
      { text: '天氣(中)', value: 'weather_noon', width: 90, align: 'center', sortable: true },
      { text: '日數', value: 'day_count', width: 60, align: 'center', sortable: true },
      { text: 'Last Edited', value: 'updated_at', align: 'start', sortable: true },
      { text: 'EDIT', value: 'edit', sortable: false, width: 70, align: 'center' },
      { text: 'DELETE', value: 'delete', sortable: false, width: 80, align: 'center' },
      { text: 'DOWNLOAD', value: 'download', sortable: false, width: 110, align: 'center' }
    ])

    const projectIdNumber = computed(() => Number(route.params.projectId))

    // 取得專案資訊
    const fetchProjectInfo = async () => {
      try {
        const { data } = await axios.get(`/api/projects/${projectIdNumber.value}`)
        projectInfo.value = data
      } catch (error) {
        console.error(error)
      }
    }

    // 取得該專案的所有日報
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

    // 建立新的 SiteDiary
    const openCreateDialog = () => {
      editingDiaryId.value = null
      displayFormDialog.value = true
    }

    // 編輯 SiteDiary
    const openEditDialog = (diaryId) => {
      editingDiaryId.value = diaryId
      displayFormDialog.value = true
    }

    // 刪除 SiteDiary
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

    // 下載報表 (XLSX, PDF(表1), PDF(表2))
    const downloadReport = async (diaryId, fileType) => {
      try {
        const response = await axios.get(
          `/api/projects/${projectIdNumber.value}/site_diaries/${diaryId}/download_report?file=${fileType}`,
          { responseType: 'blob' }
        )

        let filename = fileType === 'xlsx'
          ? 'daily_report_filled.xlsx'
          : (fileType === 'sheet1'
              ? 'daily_report_sheet1.pdf'
              : 'daily_report_sheet2.pdf')

        // 嘗試從後端 headers 裡拿檔名
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

    // 當表單存檔成功
    const onDiaryUpdated = () => {
      displayFormDialog.value = false
      fetchSiteDiaries()
    }

    // 當表單取消
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
      headers,
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
.project-info-box {
  border: 1px solid #ccc;
  padding: 10px;
  background-color: #f9f9f9;
  margin-bottom: 16px;
}

/* 用於在小螢幕或欄位多時，允許水平捲動 */
.table-scroll-wrapper {
  width: 100%;
  overflow-x: auto;
  margin-bottom: 16px;
}

/* 使表格最小寬度稍微大些 */
.diary-table {
  min-width: 900px;
}

.mb-4 {
  margin-bottom: 16px;
}
.mb-6 {
  margin-bottom: 24px;
}
</style>
