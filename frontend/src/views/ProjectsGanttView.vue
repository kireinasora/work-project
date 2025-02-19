<template>
  <div
    class="full-gantt d-flex flex-column"
    style="height: 100vh; width: 100vw; margin:0; padding:0; overflow: hidden;"
  >
    <!-- 工具列 -->
    <div
      class="bg-light border-bottom d-flex align-items-center flex-wrap"
      style="padding: 0.5rem; gap: 1rem; flex: 0 0 auto;"
    >
      <button class="btn btn-secondary" @click="goBack">
        ← Back
      </button>

      <!-- Manage Snapshots 按鈕 (開啟 modal) -->
      <button class="btn btn-dark btn-sm" @click="showManageSnapshotsModal = true">
        Manage Snapshots
      </button>

      <!-- 下拉 / 新增 新快照(當前最新tasks) -->
      <div class="d-flex align-items-center" style="gap: 0.5rem;">
        <label>Snapshot:</label>
        <select
          v-model="selectedSnapshot"
          @change="loadSnapshot"
          class="form-select form-select-sm"
          style="width:auto;"
        >
          <option value="">(Latest)</option>
          <option
            v-for="(snap, idx) in snapshots"
            :key="idx"
            :value="snap.date"
          >
            {{ snap.date }} (created {{ snap.created_at ? snap.created_at.substring(0,16) : '' }})
          </option>
        </select>
      </div>
      <button class="btn btn-info btn-sm" @click="createSnapshot">
        Save Snapshot
      </button>

      <!-- 若目前處於「已選取 snapshot」且「允許編輯」模式，才顯示 Update Snapshot 按鈕 -->
      <button
        class="btn btn-success btn-sm"
        v-if="selectedSnapshot"
        @click="updateCurrentSnapshot"
      >
        Update Current Snapshot
      </button>

      <!-- Zoom 選擇 -->
      <div class="d-flex align-items-center" style="gap: 0.5rem;">
        <label>Zoom:</label>
        <select
          v-model="activeZoomLevel"
          @change="applyZoomLevel"
          class="form-select form-select-sm"
          style="width:auto;"
        >
          <option
            v-for="z in zoomConfigs"
            :key="z.name"
            :value="z.name"
          >
            {{ z.name }}
          </option>
        </select>
      </div>

      <!-- Prev / Next Day -->
      <div class="btn-group">
        <button class="btn btn-outline-secondary btn-sm" @click="shiftDate(-1)">Prev Day</button>
        <button class="btn btn-outline-secondary btn-sm" @click="shiftDate(1)">Next Day</button>
      </div>

      <!-- Go to Date -->
      <div class="d-flex align-items-center">
        <label for="gotoDate" class="me-1">Go to:</label>
        <input
          type="date"
          id="gotoDate"
          v-model="gotoDateStr"
          class="form-control form-control-sm"
          style="width:auto;"
          @change="jumpToDate"
        />
      </div>

      <!-- 假日管理 -->
      <button class="btn btn-warning btn-sm" @click="openHolidayModal">
        Manage Holidays
      </button>
    </div>

    <!-- Gantt 容器 -->
    <div id="gantt_here" style="flex:1; width:100%;"></div>

    <!-- 建立每日快照 (當前最新tasks) -->
    <div
      class="modal"
      :class="{ fade: true, show: showSnapshotModal }"
      :style="{ display: showSnapshotModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      @click.self="closeSnapshotModal"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content p-3">
          <h5>建立每日快照</h5>
          <label for="snapDate">Snapshot Date:</label>
          <input
            type="date"
            id="snapDate"
            v-model="tempSnapDate"
            class="form-control"
          />
          <div class="mt-3 d-flex justify-content-end">
            <button class="btn btn-secondary me-2" @click="closeSnapshotModal">
              Cancel
            </button>
            <button class="btn btn-primary" @click="confirmSnapshotDate">
              OK
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showSnapshotModal" class="modal-backdrop fade show"></div>

    <!-- 假日管理 Modal -->
    <div
      class="modal"
      :class="{ fade: true, show: showHolidayModal }"
      :style="{ display: showHolidayModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      @click.self="closeHolidayModal"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content p-3">
          <h5>Holidays &amp; Workday Settings</h5>
          <div class="mb-3">
            <label class="form-label">Workdays / week:</label>
            <input
              type="number"
              v-model.number="holidaySettings.workdays_per_week"
              class="form-control"
              min="1"
              max="7"
            />
          </div>
          <div class="mb-3">
            <label class="form-label">
              指定哪幾天是工作日 (0=Sun,1=Mon,...6=Sat)：
            </label>
            <p class="small text-muted">
              若此陣列非空，優先視為工作日；否則改用 workdays_per_week。
            </p>
            <div
              v-for="(dw, idx) in holidaySettings.workday_weekdays"
              :key="'dw_'+idx"
              class="d-flex align-items-center mb-1"
            >
              <input
                type="number"
                class="form-control form-control-sm me-2"
                v-model.number="holidaySettings.workday_weekdays[idx]"
                min="0"
                max="6"
              />
              <button class="btn btn-danger btn-sm" @click="removeWorkdayWeekday(idx)">X</button>
            </div>
            <button class="btn btn-secondary btn-sm" @click="addWorkdayWeekday">
              + Add Day
            </button>
          </div>

          <div class="mb-3">
            <label class="form-label">Holidays (YYYY-MM-DD):</label>
            <div
              v-for="(h, idx) in holidaySettings.holidays"
              :key="'hol_'+idx"
              class="d-flex align-items-center mb-1"
            >
              <input
                type="text"
                v-model="holidaySettings.holidays[idx]"
                class="form-control form-control-sm me-2"
              />
              <button class="btn btn-danger btn-sm" @click="removeHoliday(idx)">X</button>
            </div>
            <button class="btn btn-secondary btn-sm" @click="addHoliday">+ Add Holiday</button>
          </div>

          <div class="mb-3">
            <label class="form-label">Special Workdays:</label>
            <p class="small text-muted">(若假日也需算工作日，可輸入特例日期)</p>
            <div
              v-for="(sw, idx) in holidaySettings.special_workdays"
              :key="'sw_'+idx"
              class="d-flex align-items-center mb-1"
            >
              <input
                type="text"
                v-model="holidaySettings.special_workdays[idx]"
                class="form-control form-control-sm me-2"
              />
              <button class="btn btn-danger btn-sm" @click="removeSpecialWorkday(idx)">X</button>
            </div>
            <button class="btn btn-secondary btn-sm" @click="addSpecialWorkday">
              + Add Special Workday
            </button>
          </div>

          <div class="mt-3 d-flex justify-content-end">
            <button class="btn btn-secondary me-2" @click="closeHolidayModal">
              Cancel
            </button>
            <button class="btn btn-primary" @click="saveHolidays">
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showHolidayModal" class="modal-backdrop fade show"></div>

    <!-- Manage Snapshots Modal: 可 Load for Edit, Delete -->
    <div
      class="modal"
      :class="{ fade: true, show: showManageSnapshotsModal }"
      :style="{ display: showManageSnapshotsModal ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      @click.self="showManageSnapshotsModal = false"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content p-3">
          <h5 class="mb-3">Manage Snapshots</h5>
          <div v-if="snapshots.length === 0" class="text-muted">
            No snapshots found.
          </div>
          <table v-else class="table table-sm">
            <thead>
              <tr>
                <th>Date</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(snap, i) in snapshots" :key="i">
                <td>{{ snap.date }}</td>
                <td>{{ snap.created_at ? snap.created_at.substring(0,16) : '' }}</td>
                <td>
                  <!-- Load for Edit: 選該 snapshot 到 Gantt -->
                  <button
                    class="btn btn-warning btn-sm me-2"
                    @click="loadSnapshotForEdit(snap.date)"
                  >
                    Load for Edit
                  </button>
                  <!-- Delete  -->
                  <button
                    class="btn btn-danger btn-sm"
                    @click="deleteSnapshot(snap.date)"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="mt-3 d-flex justify-content-end">
            <button
              type="button"
              class="btn btn-secondary"
              @click="showManageSnapshotsModal = false"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showManageSnapshotsModal" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { gantt } from 'dhtmlx-gantt'
import 'dhtmlx-gantt/codebase/dhtmlxgantt.css'

export default {
  name: 'ProjectsGanttView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const projectId = computed(() => Number(route.params.projectId))

    // ------------------
    // UI 狀態
    // ------------------
    const showSnapshotModal = ref(false)
    const tempSnapDate = ref('')
    const showHolidayModal = ref(false)
    const showManageSnapshotsModal = ref(false)

    // ------------------
    // 假日管理
    // ------------------
    const holidaySettings = ref({
      project_id: projectId.value,
      holidays: [],
      workdays_per_week: 5,
      workday_weekdays: [],
      special_workdays: []
    })

    // ------------------
    // Snapshots 管理
    // ------------------
    const snapshots = ref([])
    const selectedSnapshot = ref('') // 若為 "" => 最新; 否則舊快照

    // Gantt 已初始化
    let ganttInited = false

    // Zoom
    const zoomConfigs = [
      {
        name: 'hour',
        scale_height: 60,
        min_column_width: 50,
        scales: [
          { unit: 'day', step: 1, format: '%Y-%m-%d' },
          { unit: 'hour', step: 1, format: '%H:%i' }
        ]
      },
      {
        name: 'day',
        scale_height: 60,
        min_column_width: 70,
        scales: [{ unit: 'day', step: 1, format: '%Y-%m-%d' }]
      },
      {
        name: 'week',
        scale_height: 50,
        min_column_width: 50,
        scales: [
          { unit: 'week', step: 1, format: 'Week %W, %Y' },
          { unit: 'day', step: 1, format: '%D' }
        ]
      },
      {
        name: 'month',
        scale_height: 50,
        min_column_width: 70,
        scales: [
          { unit: 'month', step: 1, format: '%Y %M' },
          { unit: 'week', step: 1, format: 'Week %W' }
        ]
      },
      {
        name: 'quarter',
        scale_height: 50,
        min_column_width: 90,
        scales: [
          { unit: 'month', step: 1, format: '%M' },
          { unit: 'quarter', step: 1, format: 'Q%q' }
        ]
      },
      {
        name: 'year',
        scale_height: 50,
        min_column_width: 80,
        scales: [{ unit: 'year', step: 1, format: '%Y' }]
      }
    ]
    const activeZoomLevel = ref('month')

    // Go to date
    const gotoDateStr = ref('')

    // ------------------
    // 初始化 Gantt
    // ------------------
    function initGantt() {
      if (ganttInited) return
      ganttInited = true

      // layout + columns
      gantt.config.layout = {
        css: "gantt_container",
        rows: [
          {
            cols: [
              {
                view: "grid",
                scrollX: "gridScroll",
                scrollY: "scrollVer",
                scrollable: true,
                config: {
                  columns: [
                    {
                      name: "text",
                      label: "Task Name",
                      tree: true,
                      width: 250,
                      resize: true
                    },
                    {
                      name: "start_date",
                      label: "Start",
                      align: "center",
                      width: 120,
                      resize: true
                    },
                    {
                      name: "end_date",
                      label: "End",
                      align: "center",
                      width: 120,
                      resize: true
                    },
                    {
                      name: "duration",
                      label: "Dur.",
                      align: "center",
                      width: 50,
                      resize: true
                    },
                    { name: "add", label: "", width: 44 }
                  ]
                }
              },
              { view: "scrollbar", id: "gridScroll" },
              {
                view: "timeline",
                scrollX: "scrollHor",
                scrollY: "scrollVer"
              },
              { view: "scrollbar", id: "scrollVer" },
              { view: "scrollbar", id: "scrollHor", height: 20 }
            ]
          }
        ]
      }

      gantt.config.date_format = '%Y-%m-%d'
      gantt.config.drag_move = true
      gantt.config.drag_resize = true
      gantt.config.drag_progress = true
      gantt.config.prevent_default_scroll = true
      gantt.config.horizontal_scroll_key = 'altKey'

      // 自定週末/假日顯示
      gantt.templates.scale_cell_class = (date) => {
        const ymd = formatDateToYMD(date)
        if (holidaySettings.value.holidays.includes(ymd)) {
          return 'weekend'
        }
        return ''
      }
      gantt.templates.timeline_cell_class = (item, date) => {
        const ymd = formatDateToYMD(date)
        if (holidaySettings.value.holidays.includes(ymd)) {
          return 'weekend'
        }
        return ''
      }

      // CRUD 事件
      gantt.attachEvent('onAfterTaskAdd', async (id, item) => {
        // 舊快照也可編輯 => 直接調對應 createTaskInServer
        try {
          const newId = await createTaskInServer(item)
          if (newId) {
            gantt.changeTaskId(id, newId)
          }
        } catch (err) {
          console.error(err)
          gantt.deleteTask(id)
        }
      })
      gantt.attachEvent('onAfterTaskUpdate', async (id, item) => {
        // 同上
        try {
          await updateTaskInServer(item)
        } catch (err) {
          console.error(err)
          loadTasks() // revert
        }
      })
      gantt.attachEvent('onAfterTaskDelete', async (id, item) => {
        // 同上
        try {
          await deleteTaskInServer(id)
        } catch (err) {
          console.error(err)
          loadTasks()
        }
      })

      gantt.init('gantt_here')
      gantt.plugins({ zoom: true })
      applyZoomLevel()
    }

    // ------------------
    // 後端 Task CRUD
    // (若 selectedSnapshot, 就操作該 snapshot? => 本示範: 先全部操作「當前 loaded」的 tasks。
    //  最後再由 "updateCurrentSnapshot()" 一次 PUT 服務端)
    // ------------------
    async function createTaskInServer(item) {
      // 前端暫時只在 Gantt 新增，真正要儲存到 snapshot 須再主動呼叫 updateCurrentSnapshot()
      // 但若 snapshot=""(最新) => 新增就調 /gantt/tasks
      if (!selectedSnapshot.value) {
        // create to "current" (最新)
        const payload = buildTaskPayload(item)
        const { data } = await axios.post(
          `/api/projects/${projectId.value}/gantt/tasks`,
          payload
        )
        return data.task_id
      } else {
        // 只更新 Gantt 內部；最終以 updateCurrentSnapshot() PUT 回服務端
        return `snaplocal-${Date.now()}`
      }
    }
    async function updateTaskInServer(item) {
      if (!selectedSnapshot.value) {
        // update to "current" (最新)
        const payload = buildTaskPayload(item)
        await axios.put(
          `/api/projects/${projectId.value}/gantt/tasks/${item.id}`,
          payload
        )
      } else {
        // 只更新 Gantt 內部
      }
    }
    async function deleteTaskInServer(taskId) {
      if (!selectedSnapshot.value) {
        // delete from "current" (最新)
        await axios.delete(
          `/api/projects/${projectId.value}/gantt/tasks/${taskId}`
        )
      } else {
        // 只更新 Gantt 內部
      }
    }

    function buildTaskPayload(item) {
      const startYmd = formatDateToYMD(item.start_date)
      const endYmd = item.end_date ? formatDateToYMD(item.end_date) : null
      const payload = {
        text: item.text,
        start_date: startYmd,
        duration: item.duration || 1,
        progress: item.progress || 0,
        parent_id: item.parent || null
      }
      if (endYmd) payload.end_date = endYmd
      return payload
    }

    // 載入(最新 or 指定 snapshot)
    async function loadTasks() {
      try {
        const params = {}
        if (selectedSnapshot.value) {
          params.snapshot_date = selectedSnapshot.value
        }
        const { data } = await axios.get(
          `/api/projects/${projectId.value}/gantt/tasks`,
          { params }
        )
        gantt.clearAll()
        gantt.parse({ data })
      } catch (err) {
        console.error(err)
        alert('Load tasks failed.')
      }
    }

    // ★ 新增: updateCurrentSnapshot
    async function updateCurrentSnapshot() {
      if (!selectedSnapshot.value) {
        alert('No snapshot selected.')
        return
      }
      try {
        // 取出當前 Gantt tasks => PUT
        const all = []
        gantt.eachTask((tsk) => {
          // dhtmlx gantt內的資料
          all.push({
            id: tsk.id,
            text: tsk.text,
            start_date: tsk.start_date,
            end_date: tsk.end_date,
            duration: tsk.duration,
            progress: tsk.progress,
            parent_id: tsk.parent,
            depends: tsk.depends || []
          })
        })
        const payload = {
          tasks: all
        }
        await axios.put(
          `/api/projects/${projectId.value}/gantt/snapshots/${selectedSnapshot.value}`,
          payload
        )
        alert('Snapshot updated!')
      } catch (err) {
        console.error(err)
        alert('Update snapshot failed.')
      }
    }

    // ------------------
    // Snapshot: List, Load for Edit, Create, Delete
    // ------------------
    async function loadSnapshotsList() {
      try {
        const { data } = await axios.get(`/api/projects/${projectId.value}/gantt/snapshots`)
        snapshots.value = data
      } catch (err) {
        console.error(err)
      }
    }

    function loadSnapshot() {
      loadTasks()
    }

    function createSnapshot() {
      showSnapshotModal.value = true
      tempSnapDate.value = ''
    }
    function closeSnapshotModal() {
      showSnapshotModal.value = false
    }
    async function confirmSnapshotDate() {
      closeSnapshotModal()
      const body = {}
      if (tempSnapDate.value) {
        body.snapshot_date = tempSnapDate.value
      }
      try {
        const { data } = await axios.post(
          `/api/projects/${projectId.value}/gantt/snapshots`,
          body
        )
        alert(`Snapshot created for ${data.snapshot_date}`)
        loadSnapshotsList()
      } catch (err) {
        console.error(err)
        alert('Create snapshot failed.')
      }
    }

    // 在 Manage Snapshots modal 選擇「Load for Edit」
    async function loadSnapshotForEdit(dateStr) {
      selectedSnapshot.value = dateStr
      await loadTasks()
      showManageSnapshotsModal.value = false
    }

    // Delete snapshot
    async function deleteSnapshot(dateStr) {
      if (!confirm(`Delete snapshot ${dateStr}?`)) return
      try {
        await axios.delete(
          `/api/projects/${projectId.value}/gantt/snapshots/${dateStr}`
        )
        alert(`Snapshot ${dateStr} deleted.`)
        // 若目前正選取的 snapshot 剛好是被刪除者，也要重置
        if (selectedSnapshot.value === dateStr) {
          selectedSnapshot.value = ''
          loadTasks()
        }
        loadSnapshotsList()
      } catch (err) {
        console.error(err)
        alert('Delete snapshot failed.')
      }
    }

    // ------------------
    // 假日
    // ------------------
    async function fetchHolidays() {
      try {
        const { data } = await axios.get(
          `/api/projects/${projectId.value}/gantt/holidays`
        )
        holidaySettings.value = data
      } catch (err) {
        console.error(err)
      }
    }
    function openHolidayModal() {
      showHolidayModal.value = true
    }
    function closeHolidayModal() {
      showHolidayModal.value = false
    }
    function addWorkdayWeekday() {
      holidaySettings.value.workday_weekdays.push(1)
    }
    function removeWorkdayWeekday(idx) {
      holidaySettings.value.workday_weekdays.splice(idx, 1)
    }
    function addHoliday() {
      holidaySettings.value.holidays.push('')
    }
    function removeHoliday(idx) {
      holidaySettings.value.holidays.splice(idx, 1)
    }
    function addSpecialWorkday() {
      holidaySettings.value.special_workdays.push('')
    }
    function removeSpecialWorkday(idx) {
      holidaySettings.value.special_workdays.splice(idx, 1)
    }
    async function saveHolidays() {
      try {
        await axios.put(
          `/api/projects/${projectId.value}/gantt/holidays`,
          holidaySettings.value
        )
        alert('Holidays updated!')
        closeHolidayModal()
        applyHolidaysToGantt()
      } catch (err) {
        console.error(err)
        alert('Save holiday failed.')
      }
    }
    function applyHolidaysToGantt() {
      gantt.unsetWorkTime({ day: "fullweek" })
      if (
        holidaySettings.value.workday_weekdays &&
        holidaySettings.value.workday_weekdays.length
      ) {
        // 先全關，再指定可工作
        holidaySettings.value.workday_weekdays.forEach((dw) => {
          gantt.setWorkTime({ day: dw, hours: "full" })
        })
      } else {
        // 依 workdays_per_week
        gantt.setWorkTime({ day: [0,1,2,3,4,5,6] })
        if (holidaySettings.value.workdays_per_week === 5) {
          gantt.setWorkTime({ day: 0, hours: false })
          gantt.setWorkTime({ day: 6, hours: false })
        } else if (holidaySettings.value.workdays_per_week === 6) {
          gantt.setWorkTime({ day: 0, hours: false })
        }
      }
      // 關閉列於 holidays
      holidaySettings.value.holidays.forEach((h) => {
        const d = parseYMD(h)
        if (d) {
          gantt.setWorkTime({ date: d, hours: false })
        }
      })
      // special_workdays => 打開
      holidaySettings.value.special_workdays.forEach((sw) => {
        const d = parseYMD(sw)
        if (d) {
          gantt.setWorkTime({ date: d, hours: "full" })
        }
      })
      gantt.render()
    }

    // ------------------
    // Zoom / 其他功能
    // ------------------
    function applyZoomLevel() {
      gantt.ext.zoom.init({
        levels: zoomConfigs,
        useKey: 'shiftKey',
        trigger: 'wheel'
      })
      gantt.ext.zoom.setLevel(activeZoomLevel.value)
    }
    function shiftDate(delta) {
      const state = gantt.getState()
      const shiftTime = 24 * 60 * 60 * 1000 * delta
      const newMin = new Date(state.min_date.getTime() + shiftTime)
      const newMax = new Date(state.max_date.getTime() + shiftTime)
      gantt.ext.zoom.setDateRange(newMin, newMax)
    }
    function jumpToDate() {
      if (!gotoDateStr.value) return
      const d = parseYMD(gotoDateStr.value)
      if (!d) return
      const st = gantt.getState()
      const range = st.max_date - st.min_date
      const half = range / 2
      const newMin = new Date(d.getTime() - half)
      const newMax = new Date(d.getTime() + half)
      gantt.ext.zoom.setDateRange(newMin, newMax)
    }

    // ------------------
    // 工具
    // ------------------
    function formatDateToYMD(dateVal) {
      if (!(dateVal instanceof Date)) return ''
      const y = dateVal.getFullYear()
      const m = String(dateVal.getMonth() + 1).padStart(2, '0')
      const d = String(dateVal.getDate()).padStart(2, '0')
      return `${y}-${m}-${d}`
    }
    function parseYMD(ymd) {
      if (!ymd) return null
      const parts = ymd.split('-')
      if (parts.length !== 3) return null
      return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
    }

    function goBack() {
      router.go(-1)
    }

    // ------------------
    // onMounted
    // ------------------
    onMounted(async () => {
      initGantt()
      await loadTasks()
      await loadSnapshotsList()
      await fetchHolidays()
      applyHolidaysToGantt()
    })

    onBeforeUnmount(() => {
      if (ganttInited) {
        gantt.clearAll()
        gantt.detachAllEvents()
        ganttInited = false
      }
    })

    return {
      // state
      projectId,
      showSnapshotModal,
      tempSnapDate,
      showHolidayModal,
      showManageSnapshotsModal,
      selectedSnapshot,
      snapshots,
      holidaySettings,
      zoomConfigs,
      activeZoomLevel,
      gotoDateStr,

      // methods
      goBack,
      loadSnapshot,
      createSnapshot,
      closeSnapshotModal,
      confirmSnapshotDate,
      loadSnapshotForEdit,
      deleteSnapshot,
      updateCurrentSnapshot,

      openHolidayModal,
      closeHolidayModal,
      addWorkdayWeekday,
      removeWorkdayWeekday,
      addHoliday,
      removeHoliday,
      addSpecialWorkday,
      removeSpecialWorkday,
      saveHolidays,
      applyHolidaysToGantt,
      applyZoomLevel,
      shiftDate,
      jumpToDate,
    }
  }
}
</script>

<style scoped>
.weekend {
  background-color: #f2dede !important;
}
.modal-backdrop {
  z-index: 1040;
}
.modal {
  z-index: 1050;
}
</style>
