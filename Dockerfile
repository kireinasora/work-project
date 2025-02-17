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

# 確保 APT 安裝過程不出現互動式介面
ENV DEBIAN_FRONTEND=noninteractive

# 先更新並安裝可能需要的工具（包含 GNUPG / CA certificate 等）
RUN apt-get update --allow-releaseinfo-change \
 && apt-get install -y --no-install-recommends \
    gnupg \
    ca-certificates \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 再進行 LibreOffice 與 fontconfig 安裝
RUN apt-get update --allow-releaseinfo-change \
 && apt-get install -y --no-install-recommends \
    libreoffice \
    fontconfig \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# -- 以下這兩行為「安裝字型」的關鍵步驟 --
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

################################################################################
# 直接在 Gunicorn 的參數中設定較高的 timeout、使用多 workers/threads
################################################################################
CMD ["/bin/sh", "-c", "gunicorn 'backend.main:create_app()' \
--bind 0.0.0.0:$PORT \
--workers 2 \
--threads 4 \
--timeout 300"]
