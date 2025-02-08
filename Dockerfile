###############################################
# 1) 前端：Node 環境，安裝並打包 Vite/Vue
###############################################
FROM node:18-slim AS frontend-builder

WORKDIR /app/frontend

# 複製前端 package.json / package-lock.json
COPY frontend/package*.json ./

# 安裝前端相依套件
RUN npm install

# 複製前端程式碼
COPY frontend/ ./

# 進行前端打包 (輸出到 /app/frontend/dist)
RUN npm run build


###############################################
# 2) 後端：Python + LibreOffice + 字型
###############################################
FROM python:3.10-slim AS backend

ENV DEBIAN_FRONTEND=noninteractive

# 安裝 LibreOffice
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice \
        fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# -- 以下這兩行為「安裝字型」的關鍵步驟 --
# 建議先建立資料夾：/usr/share/fonts/truetype/custom
RUN mkdir -p /usr/share/fonts/truetype/custom

# 將本機專案裡 ./fonts/MINGLIU.TTC 複製到容器裡
COPY ./fonts/MINGLIU.TTC /usr/share/fonts/truetype/custom/MINGLIU.TTC

# 更新字型快取
RUN fc-cache -f -v

# 安裝 Python 相依
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製後端程式
COPY backend/ ./backend

# 從前端階段帶入打包成果
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 設定 PYTHONPATH，確保可用 `from backend.xxx import ...`
ENV PYTHONPATH=/app

# Flask 對外提供的埠
EXPOSE 5000

# 改用 Gunicorn 執行 backend/main.py 裡的 create_app()
CMD ["/bin/sh", "-c", "gunicorn 'backend.main:create_app()' --bind 0.0.0.0:$PORT"]
