// frontend/src/main.ts
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 改用 Bootstrap 5（CSS + JS Bundle）
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

const app = createApp(App)
app.use(router)
app.mount('#app')
