<template>
  <div>
    <h1>人員管理</h1>

    <!-- 以 Vuetify 的 v-data-table 展示 staffList -->
    <v-data-table
      :headers="headers"
      :items="staffList"
      class="mb-6"
    >
      <!-- Actions 欄位 (刪除按鈕) -->
      <template #item.actions="{ item }">
        <v-btn color="error" variant="outlined" @click="deleteStaff(item.id)">
          Delete
        </v-btn>
      </template>
    </v-data-table>

    <!-- 新增人員表單 -->
    <h3>新增人員</h3>
    <v-card class="pa-4">
      <v-text-field
        v-model="name"
        label="姓名"
        class="mb-3"
      />
      <v-text-field
        v-model="role"
        label="角色"
        class="mb-3"
      />
      <v-btn variant="outlined" color="primary" @click="createStaff">
        新增
      </v-btn>
    </v-card>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted } from 'vue'
// Vuetify 已在 main.ts 裝入，這裡只需使用即可

export default {
  name: 'StaffView',
  setup() {
    const staffList = ref([])
    const name = ref('')
    const role = ref('')

    // v-data-table 的表頭設定
    const headers = ref([
      { text: 'ID', value: 'id', width: 80 },
      { text: 'Name', value: 'name' },
      { text: 'Role', value: 'role' },
      { text: 'Actions', value: 'actions', sortable: false }
    ])

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
      headers,
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
