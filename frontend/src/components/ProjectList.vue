<template>
  <div>
    <!-- 專案列表 Table -->
    <table class="table table-bordered table-hover mb-6">
      <thead>
        <tr>
          <th>ID</th>
          <th>Project Name</th>
          <th>Job #</th>
          <th>Contractor</th>
          <th>Start Date</th>
          <th>End Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in projects" :key="item.id">
          <td>{{ item.id }}</td>
          <td>{{ item.name }}</td>
          <td>{{ item.job_number }}</td>
          <td>{{ item.contractor }}</td>
          <td>{{ item.start_date }}</td>
          <td>{{ item.end_date }}</td>
          <td>
            <button class="btn btn-info btn-sm me-2" @click="showDetail(item.id)">
              Detail
            </button>
            <button class="btn btn-warning btn-sm me-2" @click="editProject(item.id)">
              Edit
            </button>
            <button class="btn btn-danger btn-sm" @click="deleteProject(item.id)">
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Detail Modal (Bootstrap) -->
    <div
      class="modal"
      :class="{ fade: true, show: detailDialog }"
      :style="{ display: detailDialog ? 'block' : 'none' }"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      v-if="detailDialog"
      @click.self="detailDialog = false"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Project Detail</h5>
            <button
              type="button"
              class="btn-close"
              @click="detailDialog = false"
            ></button>
          </div>
          <div class="modal-body">
            <ProjectDetail :projectId="detailProjectId" />
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              @click="detailDialog = false"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal backdrop -->
    <div
      v-if="detailDialog"
      class="modal-backdrop fade show"
    ></div>
  </div>
</template>

<script>
import axios from 'axios'
import ProjectDetail from '@/components/ProjectDetail.vue'

export default {
  name: 'ProjectList',
  components: { ProjectDetail },
  props: {
    projects: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      detailDialog: false,
      detailProjectId: null
    }
  },
  methods: {
    showDetail(projectId) {
      this.detailProjectId = projectId
      this.detailDialog = true
    },
    editProject(projectId) {
      this.$emit('edit-project', projectId)
    },
    async deleteProject(id) {
      if (!confirm('確定要刪除此專案嗎？')) return
      try {
        await axios.delete(`/api/projects/${id}`)
        this.$emit('refresh')
      } catch (err) {
        console.error(err)
      }
    }
  }
}
</script>

<style scoped>
.me-2 {
  margin-right: 8px;
}
.mb-6 {
  margin-bottom: 24px;
}

/* ★ 關鍵：確保 modal 與 backdrop 層級正確 */
.modal {
  z-index: 1050; /* Bootstrap默認modal z-index */
}
.modal-backdrop {
  z-index: 1040; /* 低於modal即可 */
}
</style>
