// build.js - 非常基礎的構建腳本
import { execSync } from 'child_process'
import fs from 'fs'

// 確保 dist 目錄存在
if (!fs.existsSync('./dist')) {
  fs.mkdirSync('./dist')
}

try {
  console.log('正在執行超輕量構建（使用 npx）...')
  // 使用 npx 確保能找到 vite 命令
  execSync('npx vite build --mode production --outDir dist', { 
    stdio: 'inherit',
    env: {
      ...process.env,
      VITE_SKIP_TS_CHECK: 'true',
      NODE_ENV: 'production'
    }
  })
  console.log('構建完成!')
} catch (error) {
  console.error('構建失敗:', error)
  process.exit(1)
} 