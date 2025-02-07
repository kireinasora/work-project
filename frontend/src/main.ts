// frontend/src/main.ts
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 匯入 Vuetify 核心樣式
import 'vuetify/styles'

// ★ 新增：把所有 components 與 directives 一次性注入
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// (可選) 匯入官方提供的 mdi iconsets
import { aliases, mdi } from 'vuetify/iconsets/mdi'

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',  // 指定使用哪個 icon set
    aliases,
    sets: { mdi }
  }
})

const app = createApp(App)

app.use(router)
app.use(vuetify)

app.mount('#app')
