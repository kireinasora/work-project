<template>
  <div class="gantt-task-form">
    <h5 class="mb-3">
      {{ isNewTask ? '新增任務' : '編輯任務' }}
    </h5>

    <form @submit.prevent="handleSubmit">
      <!-- 任務名稱 -->
      <div class="mb-3">
        <label class="form-label">任務名稱</label>
        <input
          type="text"
          v-model="taskData.label"
          class="form-control form-control-sm"
        />
      </div>

      <!-- 任務類型 -->
      <div class="mb-3">
        <label class="form-label">任務類型</label>
        <select
          v-model="taskData.type"
          class="form-select form-select-sm"
        >
          <option value="task">一般任務 (task)</option>
          <option value="milestone">里程碑 (milestone)</option>
          <option value="project">專案 (project)</option>
        </select>
      </div>

      <!-- 開始 / 結束日期 / 工期 -->
      <div class="row mb-3">
        <div class="col-sm-6">
          <label class="form-label">開始日期</label>
          <input
            type="date"
            v-model="taskData.start_date_str"
            class="form-control form-control-sm"
          />
        </div>
        <div class="col-sm-6">
          <label class="form-label">結束日期</label>
          <input
            type="date"
            v-model="taskData.end_date_str"
            class="form-control form-control-sm"
            placeholder="若未填，則改用工期"
          />
        </div>
      </div>

      <div class="row mb-3">
        <div class="col-sm-6">
          <label class="form-label">工期 (天)</label>
          <input
            type="number"
            v-model.number="taskData.durationDays"
            class="form-control form-control-sm"
            placeholder="若未填結束日期，可輸入工期"
          />
        </div>

        <div class="col-sm-6">
          <label class="form-label">進度 (0 ~ 100%)</label>
          <input
            type="number"
            step="1"
            min="0"
            max="100"
            v-model.number="taskData.progressPercent"
            class="form-control form-control-sm"
          />
        </div>
      </div>

      <!-- 依賴 (depends) -->
      <div class="mb-3">
        <label class="form-label">依賴 (逗號分隔)</label>
        <input
          type="text"
          v-model="taskData.dependsStr"
          class="form-control form-control-sm"
          placeholder="例如：2,3"
        />
      </div>

      <!-- 父任務ID (parent_id) -->
      <div class="mb-3">
        <label class="form-label">父任務ID</label>
        <input
          type="text"
          v-model="taskData.parentIdStr"
          class="form-control form-control-sm"
          placeholder="若無父任務可留空"
        />
      </div>

      <!-- 任務ID（唯讀顯示） -->
      <div v-if="!isNewTask" class="mb-3">
        <label class="form-label">任務 ID (唯讀)</label>
        <input
          type="text"
          :value="String(taskData.id)"
          class="form-control form-control-sm"
          disabled
        />
      </div>

      <!-- 按鈕區 -->
      <div class="d-flex justify-content-end mt-4">
        <!-- 刪除任務按鈕 (若是新增模式就不顯示) -->
        <button
          v-if="!isNewTask"
          type="button"
          class="btn btn-danger me-3"
          @click="handleDelete"
        >
          刪除任務
        </button>

        <button
          type="button"
          class="btn btn-secondary me-3"
          @click="$emit('cancel')"
        >
          取消
        </button>

        <button
          type="submit"
          class="btn btn-primary"
        >
          {{ isNewTask ? '新增' : '儲存' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, watch, computed } from 'vue'

export default {
  name: 'GanttTaskForm',
  props: {
    projectId: {
      type: Number,
      required: true
    },
    snapshotDate: {
      type: String,
      default: '' // 若為空，表示操作當前最新
    },
    task: {
      type: Object,
      default: null
    }
  },
  setup(props, { emit }) {
    const taskData = ref({
      id: null,
      label: '',
      type: 'task',
      start_date_str: '',
      end_date_str: '',
      durationDays: 0,
      progressPercent: 0,
      dependsStr: '',
      parentIdStr: ''
    })

    const isSnapshotMode = computed(() => !!props.snapshotDate)
    const isNewTask = computed(() => !props.task || !props.task.id)

    watch(
      () => props.task,
      (val) => {
        if (!val) {
          resetFormForCreate()
        } else {
          fillForm(val)
        }
      },
      { immediate: true }
    )

    function resetFormForCreate() {
      taskData.value = {
        id: null,
        label: '',
        type: 'task',
        start_date_str: '',
        end_date_str: '',
        durationDays: 0,
        progressPercent: 0,
        dependsStr: '',
        parentIdStr: ''
      }
    }

    function fillForm(task) {
      let startDateStr = ''
      if (task.start) {
        const d = new Date(task.start)
        startDateStr = formatDate(d)
      }
      let endDateStr = ''
      if (task.end) {
        const d2 = new Date(task.end)
        endDateStr = formatDate(d2)
      }
      const parsedId = typeof task.id === 'number' ? task.id : parseInt(task.id, 10) || null
      const progressVal = task.progress != null ? parseInt(task.progress, 10) : 0
      const dependsArr = task.dependentOn || task.depends || []
      const dependsStr = dependsArr.join(', ')
      const parentIdVal = task.parentId || task.parent || null
      const parentIdStr = parentIdVal ? String(parentIdVal) : ''

      // 預設 type: 'task'
      const tType = task.type || 'task'

      taskData.value = {
        id: parsedId,
        label: task.label || '',
        type: tType,
        start_date_str: startDateStr,
        end_date_str: endDateStr,
        durationDays: 0,
        progressPercent: progressVal * 1, // 0~100
        dependsStr,
        parentIdStr
      }
    }

    function formatDate(d) {
      const year = d.getFullYear()
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }

    async function handleSubmit() {
      try {
        const putOrPostData = {
          text: taskData.value.label,
          progress: (taskData.value.progressPercent || 0) / 100,
          depends: parseDepends(taskData.value.dependsStr),
          start_date: taskData.value.start_date_str || null,
          type: taskData.value.type || 'task',
        }
        if (taskData.value.end_date_str) {
          putOrPostData.end_date = taskData.value.end_date_str
        } else if (taskData.value.durationDays > 0) {
          putOrPostData.duration = taskData.value.durationDays
        }

        const parentIdParsed = parseInt(taskData.value.parentIdStr.trim(), 10)
        if (!isNaN(parentIdParsed)) {
          putOrPostData.parent_id = parentIdParsed
        } else {
          putOrPostData.parent_id = null
        }

        const baseUrl = `/api/projects/${props.projectId}/gantt/tasks`
        if (isSnapshotMode.value) {
          // snapshot 模式 => 以 query param 傳給後端
          if (isNewTask.value) {
            await axios.post(`${baseUrl}?snapshot_date=${props.snapshotDate}`, putOrPostData)
          } else {
            await axios.put(`${baseUrl}/${taskData.value.id}?snapshot_date=${props.snapshotDate}`, putOrPostData)
          }
        } else {
          // 非 snapshot
          if (isNewTask.value) {
            await axios.post(baseUrl, putOrPostData)
          } else {
            await axios.put(`${baseUrl}/${taskData.value.id}`, putOrPostData)
          }
        }

        alert(isNewTask.value ? '任務已新增！' : '任務已更新！')
        emit('saved')
      } catch (err) {
        console.error(err)
        alert(`操作失敗：${err}`)
      }
    }

    async function handleDelete() {
      if (!taskData.value.id) return
      if (!confirm('確定要刪除此任務嗎？')) return
      try {
        const baseUrl = `/api/projects/${props.projectId}/gantt/tasks/${taskData.value.id}`
        if (isSnapshotMode.value) {
          await axios.delete(`${baseUrl}?snapshot_date=${props.snapshotDate}`)
        } else {
          await axios.delete(baseUrl)
        }
        alert('任務已刪除。')
        emit('saved')
      } catch (err) {
        console.error(err)
        alert(`刪除失敗：${err}`)
      }
    }

    function parseDepends(str) {
      if (!str) return []
      return str
        .split(',')
        .map(s => parseInt(s.trim(), 10))
        .filter(n => !isNaN(n))
    }

    return {
      taskData,
      isSnapshotMode,
      isNewTask,
      handleSubmit,
      handleDelete
    }
  }
}
</script>

<style scoped>
.gantt-task-form {
  font-size: 0.9rem;
  max-height: 80vh;
  overflow-y: auto;
}
.me-3 {
  margin-right: 1rem !important;
}
</style>
