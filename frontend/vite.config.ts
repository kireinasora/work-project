import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 最基本的配置，避免使用高級功能
export default defineConfig(({ mode }) => {
  const isProduction = (mode === 'production')
  
  // 生產模式下的基本配置
  if (isProduction) {
    return {
      plugins: [vue()],
      
      // 最基本的構建選項
      build: {
        // 最小化複雜度
        outDir: 'dist',
        emptyOutDir: true,
        // 關閉 sourcemap 以節省記憶體
        sourcemap: false
      },

      // 路徑別名
      resolve: {
        alias: {
          '@': fileURLToPath(new URL('./src', import.meta.url))
        }
      }
    }
  }
  
  // 開發模式配置
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:5000',
          changeOrigin: true
        }
      }
    }
  }
})
