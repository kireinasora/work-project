<!-- frontend/src/views/ProjectsGanttView.vue -->
<template>
    <div class="container-fluid">
      <h2>Gantt Chart for Project #{{ projectId }}</h2>
  
      <div class="mb-3">
        <button class="btn btn-secondary me-2" @click="goBack">
          &larr; Back
        </button>
        <button class="btn btn-success me-2" @click="addNewTask">
          Add Task
        </button>
        <button class="btn btn-info me-2" @click="exportPDF">
          Export to PDF
        </button>
      </div>
  
      <div
        id="gantt_here"
        style="width:100%; height:600px; border:1px solid #ccc;"
      ></div>
    </div>
  </template>
  
  <script>
  import { onMounted, onBeforeUnmount, computed } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  
  // ★ 改成靜態 import
  import html2canvas from 'html2canvas'
  import { jsPDF } from 'jspdf'
  
  export default {
    name: 'ProjectsGanttView',
    setup() {
      const route = useRoute()
      const router = useRouter()
      const projectId = computed(() => Number(route.params.projectId))
  
      // 假資料
      const tasksData = {
        data: [
          { id: 1, text: 'Task #1', start_date: '2025-01-01', duration: 5, progress: 0.8, open: true },
          { id: 2, text: 'Task #2', start_date: '2025-01-06', duration: 3, progress: 0.2, parent: 1 },
          { id: 3, text: 'Task #3', start_date: '2025-01-09', duration: 5, progress: 0, parent: 1 }
        ],
        links: [
          { id: 1, source: 2, target: 3, type: '0' }
        ]
      }
  
      function initGantt() {
        gantt.config.date_format = "%Y-%m-%d"
        gantt.config.scales = [
          { unit: "month", step: 1, format: "%Y %M" },
          { unit: "day", step: 1, format: "%j, %D" }
        ]
        gantt.config.columns = [
          { name: "text", label: "Task Name", width: "*", tree: true },
          { name: "start_date", label: "Start", align: "center", width: 90 },
          { name: "duration", label: "Dur.", align: "center", width: 50 },
          { name: "add", label: "", width: 44 }
        ]
  
        gantt.init("gantt_here")
        gantt.parse(tasksData)
  
        // 觀察甘特圖更新事件
        gantt.attachEvent("onAfterTaskAdd", (id, item) => {
          console.log("Task added:", id, item)
        })
        gantt.attachEvent("onAfterTaskUpdate", (id, item) => {
          console.log("Task updated:", id, item)
        })
        gantt.attachEvent("onAfterTaskDelete", (id, item) => {
          console.log("Task deleted:", id, item)
        })
      }
  
      function addNewTask() {
        const newId = gantt.uid()
        gantt.addTask({
          id: newId,
          text: "New Task",
          start_date: "2025-01-15",
          duration: 4,
          progress: 0
        })
      }
  
      async function exportPDF() {
        // 對指定 DOM (id="gantt_here") 做畫面快照
        const ganttContainer = document.getElementById('gantt_here')
        if (!ganttContainer) return
        const canvas = await html2canvas(ganttContainer, { useCORS: true })
        const imgData = canvas.toDataURL("image/png")
  
        // 產出 PDF
        const pdf = new jsPDF('landscape', 'pt', 'a4') // 橫向A4
        const pageWidth = pdf.internal.pageSize.getWidth()
        const pageHeight = pdf.internal.pageSize.getHeight()
  
        const ratio = Math.min(pageWidth / canvas.width, pageHeight / canvas.height)
        pdf.addImage(imgData, 'PNG', 0, 0, canvas.width * ratio, canvas.height * ratio)
        pdf.save('gantt_export.pdf')
      }
  
      onMounted(() => {
        // 動態載入 DHTMLX Gantt
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = 'https://cdn.dhtmlx.com/gantt/edge/dhtmlxgantt.css'
        document.head.appendChild(link)
  
        const script = document.createElement('script')
        script.src = 'https://cdn.dhtmlx.com/gantt/edge/dhtmlxgantt.js'
        script.onload = () => {
          initGantt()
        }
        document.head.appendChild(script)
      })
  
      onBeforeUnmount(() => {
        if (window.gantt) {
          gantt.clearAll()
          gantt.detachAllEvents()
        }
      })
  
      function goBack() {
        router.push(`/projects/${projectId.value}`)
      }
  
      return {
        projectId,
        goBack,
        addNewTask,
        exportPDF
      }
    }
  }
  </script>
  
  <style scoped>
  .container-fluid {
    margin-top: 1rem;
  }
  .me-2 {
    margin-right: 8px;
  }
  </style>
  