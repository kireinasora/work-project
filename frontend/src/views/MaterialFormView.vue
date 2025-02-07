<template>
    <div class="material-form-container">
      <h1>Material Submission Form</h1>
  
      <div class="form-card">
        <form @submit.prevent="handleSubmit">
  
          <!-- Special Fields (工程編號、工程名稱、文件編號) -->
          <div
            v-for="(info, fieldName) in specialFields"
            :key="fieldName"
            class="form-group"
          >
            <label :for="fieldName" class="form-label">
              {{ fieldName }}:
            </label>
            <input
              type="text"
              :id="fieldName"
              v-model="formData[fieldName]"
              class="form-input"
            />
          </div>
  
          <hr />
  
          <!-- Regular Fields (報批之材料、牌子(如有)、預算表之項目編號、型號、貨期、數量) -->
          <div
            v-for="(item, i) in regularFields"
            :key="i"
            class="form-group"
          >
            <label :for="item[0]" class="form-label">
              {{ item[0] }}:
            </label>
            <input
              type="text"
              :id="item[0]"
              v-model="formData[item[0]]"
              class="form-input"
            />
          </div>
  
          <hr />
  
          <!-- Material Type Checkboxes -->
          <h3>Material Type</h3>
          <div
            v-for="(box, i) in materialTypeCheckboxes"
            :key="i"
            class="checkbox-group"
          >
            <input
              type="checkbox"
              :id="box[0]"
              v-model="formData[box[0]]"
            />
            <label :for="box[0]" class="checkbox-label">
              {{ box[0] }}
            </label>
          </div>
  
          <hr />
  
          <!-- Material Status Checkboxes -->
          <h3>Material Status</h3>
          <div
            v-for="(box, i) in materialStatusCheckboxes"
            :key="i"
            class="checkbox-group"
          >
            <input
              type="checkbox"
              :id="box[0]"
              v-model="formData[box[0]]"
            />
            <label :for="box[0]" class="checkbox-label">
              {{ box[0] }}
            </label>
          </div>
  
          <hr />
  
          <!-- Attachment Type -->
          <h3>Attachment Type</h3>
          <div class="form-group">
            <label for="附件" class="form-label">附件:</label>
            <input
              type="text"
              id="附件"
              v-model="formData['附件']"
              class="form-input"
            />
          </div>
          <div
            v-for="(box, i) in attachmentTypeCheckboxes"
            :key="i"
            class="checkbox-group"
          >
            <input
              type="checkbox"
              :id="box[0]"
              v-model="formData[box[0]]"
            />
            <label :for="box[0]" class="checkbox-label">
              {{ box[0] }}
            </label>
          </div>
  
          <hr />
  
          <!-- 日期與檔案名稱 -->
          <div class="form-group">
            <label for="日期" class="form-label">日期:</label>
            <input
              type="date"
              id="日期"
              v-model="formData['日期']"
              class="form-input"
            />
          </div>
  
          <div class="form-group">
            <label for="檔案名稱" class="form-label">檔案名稱:</label>
            <input
              type="text"
              id="檔案名稱"
              v-model="formData['檔案名稱']"
              class="form-input"
            />
          </div>
  
          <button type="submit" class="btn-submit">Generate Excel</button>
        </form>
      </div>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    name: 'MaterialFormView',
    data() {
      return {
        // 前端資料物件：包含所有要傳給後端的欄位
        formData: {
          '工程編號': '',
          '工程名稱': '',
          '文件編號': '',
          '報批之材料': '',
          '牌子(如有)': '',
          '預算表之項目編號': '',
          '型號': '',
          '貨期': '',
          '數量': '',
          // Material Type
          '結構': false,
          '供水': false,
          '建築': false,
          '電氣': false,
          '排水': false,
          '其他': false,
          // Material Status
          '與設計相同': false,
          '與標書相同': false,
          '與後加工程建議書相同': false,
          '同等質量': false,
          '替換材料': false,
          '原設計沒有指定': false,
          // Attachment
          '附件': '',
          // Attachment Type
          '樣板': false,
          '目錄': false,
          '來源證': false,
          '其他(附件)': false, // 避免和 Material Type 的 '其他' 混淆，可稍微改個 key
          // 日期、檔案名稱
          '日期': new Date().toISOString().split('T')[0],
          '檔案名稱': ''
        },
  
        // specialFields: 與後端 constants.py 中的 special_fields 相對應
        specialFields: {
          '工程編號': [6,2,4,'37/2024/DVPS'],
          '工程名稱': [7,2,4,'黑沙馬路行人道優化工程(第二期)'],
          '文件編號': [6,8,8,'']
        },
  
        // regularFields: 與後端 constants.py 中的 regular_fields 相對應
        regularFields: [
          ['報批之材料', 11, 3],
          ['牌子(如有)', 12, 3],
          ['預算表之項目編號', 11, 7],
          ['型號', 12, 6],
          ['貨期', 13, 6],
          ['數量', 14, 6]
        ],
  
        // materialTypeCheckboxes: 與後端 constants.py 中的 material_type_checkboxes 相對應
        materialTypeCheckboxes: [
          ['結構', 7, 6],
          ['供水', 8, 6],
          ['建築', 7, 8],
          ['電氣', 8, 8],
          ['排水', 7, 10],
          ['其他', 8, 10]
        ],
  
        // materialStatusCheckboxes: 與後端 constants.py 中的 material_status_checkboxes 相對應
        materialStatusCheckboxes: [
          ['與設計相同', 13, 1],
          ['與標書相同', 14, 1],
          ['與後加工程建議書相同', 15, 1],
          ['同等質量', 16, 1],
          ['替換材料', 17, 1],
          ['原設計沒有指定', 18, 1]
        ],
  
        // attachmentTypeCheckboxes: 與後端 constants.py 中的 attachment_type_checkboxes 相對應
        attachmentTypeCheckboxes: [
          ['樣板', 16, 5],
          ['目錄', 17, 5],
          ['來源證', 16, 7],
          ['其他(附件)', 17, 7]
        ]
      }
    },
    methods: {
      async handleSubmit() {
        try {
          // 將前端 formData 傳給後端 /api/material-submission
          const response = await axios.post('/api/material-submission', this.formData, {
            responseType: 'blob'
          })
          // 下載後端回傳的 Excel 檔
          const fileURL = window.URL.createObjectURL(new Blob([response.data]))
          const fileLink = document.createElement('a')
          fileLink.href = fileURL
          const filename = this.formData['檔案名稱'] || '材料報批表_filled.xlsx'
          fileLink.setAttribute(
            'download',
            filename.endsWith('.xlsx') ? filename : filename + '.xlsx'
          )
          document.body.appendChild(fileLink)
          fileLink.click()
          fileLink.remove()
        } catch (err) {
          console.error('下載發生錯誤', err)
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .material-form-container {
    max-width: 600px;
    margin: 0 auto;
  }
  .form-card {
    background: #f9f9f9;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    border: 1px solid #ccc;
  }
  .form-group {
    margin-bottom: 1rem;
  }
  .form-label {
    display: inline-block;
    width: 120px;
    font-weight: bold;
    margin-right: 0.5rem;
  }
  .form-input {
    width: calc(100% - 130px);
    padding: 6px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  .checkbox-group {
    margin-bottom: 0.5rem;
  }
  .checkbox-label {
    margin-left: 6px;
  }
  .btn-submit {
    margin-top: 20px;
    padding: 8px 16px;
    background: #646cff;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  .btn-submit:hover {
    background: #535bf2;
  }
  </style>
  