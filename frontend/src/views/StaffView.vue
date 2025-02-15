<template>
  <div class="container">
    <h1>人員管理</h1>

    <table class="table table-bordered mb-6">
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Role</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in staffList" :key="item.id">
          <td>{{ item.id }}</td>
          <td>{{ item.name }}</td>
          <td>{{ item.role }}</td>
          <td>
            <button
              class="btn btn-danger btn-sm"
              @click="deleteStaff(item.id)"
            >
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <h3>新增人員</h3>
    <div class="border p-3 mb-6">
      <div class="mb-3">
        <label class="form-label">姓名</label>
        <input
          type="text"
          v-model="name"
          class="form-control"
        />
      </div>
      <div class="mb-3">
        <label class="form-label">角色</label>
        <input
          type="text"
          v-model="role"
          class="form-control"
        />
      </div>
      <button class="btn btn-primary" @click="createStaff">
        新增
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted } from 'vue'

export default {
  name: 'StaffView',
  setup() {
    const staffList = ref([])
    const name = ref('')
    const role = ref('')

    const fetchStaff = async () => {
      try {
        const { data } = await axios.get('/api/staff')
        staffList.value = data
      } catch (err) {
        console.error(err)
      }
    }

    const createStaff = async () => {
      if (!name.value) {
        alert('請輸入姓名')
        return
      }
      try {
        await axios.post('/api/staff', { name: name.value, role: role.value })
        alert('人員已新增！')
        name.value = ''
        role.value = ''
        fetchStaff()
      } catch (err) {
        console.error(err)
      }
    }

    const deleteStaff = async (id) => {
      if (!confirm('是否確定要刪除此人員？')) return
      try {
        await axios.delete(`/api/staff/${id}`)
        alert('人員已刪除')
        fetchStaff()
      } catch (err) {
        console.error(err)
      }
    }

    onMounted(() => {
      fetchStaff()
    })

    return {
      staffList,
      name,
      role,
      createStaff,
      deleteStaff
    }
  }
}
</script>

<style scoped>
.mb-6 {
  margin-bottom: 24px;
}
</style>
