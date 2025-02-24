<template>
  <div class="projects-gantt-view container-fluid py-3">
    <!-- 頁面標題 & 專案資訊 -->
    <div class="row mb-3">
      <div class="col-12 col-md-6 mb-3">
        <div class="card">
          <div class="card-body">
            <h4 class="card-title mb-3">
              專案 #{{ projectId }} - 甘特圖
            </h4>
            <div v-if="projectInfo">
              <p class="mb-1">名稱：<strong>{{ projectInfo.name }}</strong></p>
              <p class="mb-1">承建商：{{ projectInfo.contractor || '(未填)' }}</p>
              <p class="mb-1">期間：{{ projectInfo.start_date || 'N/A' }} ~ {{ projectInfo.end_date || 'N/A' }}</p>
            </div>
            <div v-else>
              <p class="text-muted">載入專案資訊中...</p>
            </div>
          </div>
        </div>
      </div>
      <!-- Snapshot 快照管理卡片 -->
      <div class="col-12 col-md-6 mb-3">
        <div class="card h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">甘特圖快照管理</h5>
            <div class="row g-2 mb-2 align-items-end">
              <div class="col-auto">
                <label class="form-label mb-0" style="font-size:0.9rem;">載入快照</label>
                <select
                  v-model="selectedSnapshotDate"
                  class="form-select form-select-sm"
                  style="width:auto;"
                >
                  <option value="">(當前最新)</option>
                  <option
                    v-for="snap in snapshots"
                    :key="snap.date"
                    :value="snap.date"
                  >
                    {{ snap.date }} ({{ snap.created_at || 'unknown' }})
                  </option>
                </select>
              </div>
              <div class="col-auto">
                <button
                  class="btn btn-sm btn-primary"
                  @click="loadSnapshot"
                >
                  載入
                </button>
              </div>
            </div>

            <div class="d-flex flex-wrap gap-2 mt-auto">
              <button
                class="btn btn-sm btn-success"
                @click="createSnapshot"
              >
                建立今日快照
              </button>
              <button
                class="btn btn-sm btn-danger"
                v-if="selectedSnapshotDate"
                @click="deleteSnapshot"
              >
                刪除此快照
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 工具列：假日設定、新增任務、清空任務、重新分配ID -->
    <div class="toolbar-section d-flex flex-wrap gap-2 mb-3">
      <button
        class="btn btn-secondary btn-sm"
        @click="showHolidaysModal = true"
      >
        管理假日設定
      </button>

      <button
        class="btn btn-primary btn-sm"
        @click="onAddTask"
      >
        新增任務
      </button>

      <button
        class="btn btn-danger btn-sm"
        @click="clearAllTasks"
      >
        清空所有任務
      </button>

      <!-- ★ 新增重新分配 ID 按鈕 -->
      <button
        class="btn btn-warning btn-sm"
        @click="reassignAllTaskIds"
      >
        重新分配任務ID
      </button>
    </div>

    <!-- 甘特圖本體 -->
    <div
      class="gantt-container border rounded"
      style="height: calc(100vh - 320px); overflow: hidden;"
      v-if="tasksLoaded"
    >
      <template v-if="tasks.length > 0">
        <GanttElastic
          :tasks="tasks"
          :options="ganttOptions"
          @chart-task-click="onTaskClick"
          style="width: 100%; height: 100%;"
        >
          <template #header>
            <GanttElasticHeader2 />
          </template>
        </GanttElastic>
      </template>
      <template v-else>
        <div class="p-3 text-center text-muted">
          目前沒有任何任務。
        </div>
      </template>
    </div>
    <div v-else class="text-center p-5 text-muted">
      載入任務資料中...
    </div>

    <!-- [Modal] 任務編輯/新增 -->
    <div
      class="modal"
      :class="{ fade: true, show: showEditTaskModal }"
      :style="{ display: showEditTaskModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="showEditTaskModal"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content p-3">
          <GanttTaskForm
            :projectId="projectIdNum"
            :snapshotDate="selectedSnapshotDate"
            :task="currentEditTask"
            @cancel="closeEditTaskModal"
            @saved="onTaskSaved"
          />
        </div>
      </div>
    </div>
    <div
      v-if="showEditTaskModal"
      class="modal-backdrop fade show"
    ></div>

    <!-- [Modal] 假日設定 -->
    <div
      class="modal"
      :class="{ fade: true, show: showHolidaysModal }"
      :style="{ display: showHolidaysModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="showHolidaysModal"
      @click.self="showHolidaysModal = false"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">假日 / 工作日設定</h5>
            <button
              type="button"
              class="btn-close"
              @click="showHolidaysModal = false"
            ></button>
          </div>
          <div class="modal-body">
            <div v-if="holidayData">
              <div class="mb-3">
                <label class="form-label">專案假日 (以逗號分隔)</label>
                <textarea
                  rows="2"
                  class="form-control form-control-sm"
                  v-model="holidayData.holidaysStr"
                  placeholder="e.g. 2025-01-01,2025-02-10"
                ></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">特別工作日</label>
                <textarea
                  rows="2"
                  class="form-control form-control-sm"
                  v-model="holidayData.specialWorkdaysStr"
                  placeholder="e.g. 2025-02-11"
                ></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">每週工作天數 (1-7)</label>
                <input
                  type="number"
                  min="1"
                  max="7"
                  class="form-control form-control-sm"
                  v-model.number="holidayData.workdays_per_week"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">工作日對應星期幾 (0=日,1=一,...)</label>
                <input
                  type="text"
                  class="form-control form-control-sm"
                  v-model="holidayData.workday_weekdaysStr"
                  placeholder="e.g. 1,2,3,4,5"
                />
              </div>
            </div>
            <div v-else class="text-muted">
              載入中...
            </div>
          </div>
          <div class="modal-footer">
            <button
              class="btn btn-secondary btn-sm"
              @click="showHolidaysModal = false"
            >
              取消
            </button>
            <button
              class="btn btn-primary btn-sm"
              @click="updateHolidays"
            >
              儲存設定
            </button>
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="showHolidaysModal"
      class="modal-backdrop fade show"
    ></div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { GanttElastic, GanttElasticHeader2 } from 'gantt-elastic-wrapvue3'
import GanttTaskForm from '@/components/GanttTaskForm.vue'
import 'gantt-elastic-wrapvue3/dist/style.css'

export default {
  name: 'ProjectsGanttView',
  components: {
    GanttElastic,
    GanttElasticHeader2,
    GanttTaskForm
  },
  setup() {
    const route = useRoute()
    const projectId = route.params.projectId || ''
    const projectIdNum = Number(projectId)

    const projectInfo = ref(null)

    const tasks = ref([])
    const tasksLoaded = ref(false)

    const snapshots = ref([])
    const selectedSnapshotDate = ref('')

    const holidayData = ref(null)
    const showHolidaysModal = ref(false)

    const showEditTaskModal = ref(false)
    const currentEditTask = ref(null)

    onMounted(() => {
      fetchProjectInfo()
      fetchTasks()
      fetchSnapshots()
      fetchHolidays()
    })

    async function fetchProjectInfo() {
      try {
        const { data } = await axios.get(`/api/projects/${projectIdNum}`)
        projectInfo.value = data
      } catch (err) {
        console.error('fetchProjectInfo error:', err)
      }
    }

    async function fetchTasks(snapshotDate = '') {
      tasksLoaded.value = false
      try {
        const url = snapshotDate
          ? `/api/projects/${projectIdNum}/gantt/tasks?snapshot_date=${snapshotDate}`
          : `/api/projects/${projectIdNum}/gantt/tasks`
        const { data } = await axios.get(url)
        tasks.value = convertTasks(data)
      } catch (err) {
        console.error('fetchTasks error:', err)
        tasks.value = []
      } finally {
        tasksLoaded.value = true
      }
    }

    async function fetchSnapshots() {
      try {
        const { data } = await axios.get(`/api/projects/${projectIdNum}/gantt/snapshots`)
        snapshots.value = data
      } catch (err) {
        console.error('fetchSnapshots error:', err)
      }
    }

    async function fetchHolidays() {
      try {
        const { data } = await axios.get(`/api/projects/${projectIdNum}/gantt/holidays`)
        holidayData.value = transformHolidayData(data)
      } catch (err) {
        console.error('fetchHolidays error:', err)
      }
    }

    function convertTasks(rawList) {
      return rawList.map(item => {
        const progressPercent = item.progress ? Math.round(item.progress * 100) : 0
        return {
          id: Number(item.id),
          label: item.text || 'NoTitle',
          start: parseDateStartOfDay(item.start_date),
          end: parseDateEndOfDay(item.end_date),
          progress: progressPercent,
          parentId: item.parent_id || item.parent || null,
          dependentOn: item.depends || [],
          type: item.type || 'task'  // 新增對 type 的處理
        }
      })
    }

    function parseDateStartOfDay(str) {
      if (!str) {
        const now = new Date()
        now.setHours(0, 0, 0, 0)
        return now.getTime()
      }
      const dateStr = `${str}T00:00:00`
      const d = new Date(dateStr)
      return isNaN(d.getTime()) ? new Date().setHours(0,0,0,0) : d.getTime()
    }

    function parseDateEndOfDay(str) {
      if (!str) {
        const now = new Date()
        now.setHours(23, 59, 59, 999)
        return now.getTime()
      }
      const dateStr = `${str}T23:59:59.999`
      const d = new Date(dateStr)
      return isNaN(d.getTime()) ? new Date().setHours(23,59,59,999) : d.getTime()
    }

    function transformHolidayData(raw) {
      const cloned = { ...raw }
      cloned.holidaysStr = (cloned.holidays || []).join(',')
      cloned.specialWorkdaysStr = (cloned.special_workdays || []).join(',')
      cloned.workday_weekdaysStr = (cloned.workday_weekdays || []).join(',')
      return cloned
    }

    function loadSnapshot() {
      fetchTasks(selectedSnapshotDate.value)
    }

    async function createSnapshot() {
      if (!confirm('確定要建立今天的 Gantt 快照嗎？')) return
      try {
        const { data } = await axios.post(
          `/api/projects/${projectIdNum}/gantt/snapshots`,
          {}
        )
        alert(`已建立快照：${data.snapshot_date}`)
        fetchSnapshots()
      } catch (err) {
        console.error('createSnapshot error:', err)
      }
    }

    async function deleteSnapshot() {
      if (!selectedSnapshotDate.value) return
      if (!confirm(`確定要刪除 ${selectedSnapshotDate.value} 的快照？`)) return
      try {
        await axios.delete(
          `/api/projects/${projectIdNum}/gantt/snapshots/${selectedSnapshotDate.value}`
        )
        alert('已刪除。')
        selectedSnapshotDate.value = ''
        fetchSnapshots()
        fetchTasks('')
      } catch (err) {
        console.error('deleteSnapshot error:', err)
      }
    }

    async function updateHolidays() {
      if (!holidayData.value) return
      try {
        const body = {
          project_id: projectIdNum,
          holidays: parseStringToArr(holidayData.value.holidaysStr),
          special_workdays: parseStringToArr(holidayData.value.specialWorkdaysStr),
          workdays_per_week: holidayData.value.workdays_per_week || 5,
          workday_weekdays: parseNumArr(holidayData.value.workday_weekdaysStr)
        }
        await axios.put(`/api/projects/${projectIdNum}/gantt/holidays`, body)
        alert('假日設定已更新！')
        showHolidaysModal.value = false
      } catch (err) {
        console.error('updateHolidays error:', err)
      }
    }

    function parseStringToArr(str) {
      if (!str) return []
      return str.split(',').map(s => s.trim()).filter(Boolean)
    }
    function parseNumArr(str) {
      if (!str) return []
      return str.split(',').map(x => parseInt(x.trim(), 10)).filter(n => !isNaN(n))
    }

    function onAddTask() {
      currentEditTask.value = {}
      showEditTaskModal.value = true
    }

    async function clearAllTasks() {
      if (!confirm('確定要清空當前顯示的所有任務嗎？')) return
      try {
        let url = `/api/projects/${projectIdNum}/gantt/tasks/clear`
        if (selectedSnapshotDate.value) {
          url += `?snapshot_date=${selectedSnapshotDate.value}`
        }
        const res = await axios.delete(url)
        alert(res.data.message || '已清空完成')
        loadSnapshot()
      } catch (err) {
        console.error('clearAllTasks error:', err)
        alert('清空失敗：請查看 console log')
      }
    }

    // ★ 新增：重新分配ID
    async function reassignAllTaskIds() {
      if (!confirm('確定要重新分配任務ID？這將影響到所有任務的ID。')) return
      try {
        let url = `/api/projects/${projectIdNum}/gantt/tasks/reassign-ids`
        if (selectedSnapshotDate.value) {
          url += `?snapshot_date=${selectedSnapshotDate.value}`
        }
        await axios.post(url)
        alert('重新分配ID完成!')
        loadSnapshot()
      } catch (err) {
        console.error('reassignAllTaskIds error:', err)
        alert('操作失敗')
      }
    }

    function onTaskClick({ data }) {
      currentEditTask.value = data
      showEditTaskModal.value = true
    }

    function closeEditTaskModal() {
      showEditTaskModal.value = false
      currentEditTask.value = null
    }

    function onTaskSaved() {
      showEditTaskModal.value = false
      currentEditTask.value = null
      loadSnapshot()
    }

    const ganttOptions = {
      title: {
        label: `Project #${projectIdNum} Gantt`,
        html: false
      },
      taskList: {
        columns: [
          { id: 'col-id', label: 'ID', value: 'id', width: 40 },
          {
            id: 'col-label',
            label: '任務',
            value: 'label',
            width: 180,
            expander: true
          },
          {
            id: 'col-type',
            label: 'Type',
            value: 'type',   // ★ 顯示 type
            width: 80
          },
          {
            id: 'col-start',
            label: '開始',
            value: task => formatDate(task.start),
            width: 90
          },
          {
            id: 'col-end',
            label: '結束',
            value: task => formatDate(task.end),
            width: 90
          },
          {
            id: 'col-progress',
            label: '進度(%)',
            value: 'progress',
            width: 80
          }
        ]
      },
      chart: {
        progress: { bar: true },
        expander: { display: true }
      },
      scales: [
        {
          time: 'day',
          step: 1,
          name: 'Day',
          format: 'YYYY-MM-DD'
        }
      ],
      autoScale: false,
      minScale: 'day',
      maxScale: 'day',
      defaultZoom: 'day'
    }

    function formatDate(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      const yyyy = d.getFullYear()
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      return `${yyyy}-${mm}-${dd}`
    }

    return {
      projectInfo,
      tasks,
      tasksLoaded,
      snapshots,
      selectedSnapshotDate,
      holidayData,
      showHolidaysModal,
      showEditTaskModal,
      currentEditTask,

      projectId,
      projectIdNum,

      loadSnapshot,
      createSnapshot,
      deleteSnapshot,
      updateHolidays,
      onAddTask,
      clearAllTasks,
      reassignAllTaskIds,
      onTaskClick,
      closeEditTaskModal,
      onTaskSaved,
      ganttOptions
    }
  }
}
</script>

<style scoped>
.projects-gantt-view {
}

.gantt-container {
  background-color: #fff;
}

.modal {
  z-index: 1050;
}
.modal-backdrop {
  z-index: 1040;
}

.toolbar-section > * {
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
}
</style>
