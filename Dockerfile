# Dockerfile

###############################################
# 1) 前端：Node 環境
###############################################
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

ENV NODE_OPTIONS="--max-old-space-size=768"

RUN echo "[DEBUG] Node version: $(node -v)"
RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN npm i -g npm@11.1.0
RUN echo "[DEBUG] Upgraded to npm version: $(npm --version)"

COPY frontend/package*.json ./
RUN echo "[DEBUG] Removing node_modules & package-lock to avoid npm optional deps bug"
RUN rm -rf node_modules package-lock.json

RUN npm install --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

###############################################
# 2) 後端 + 最終映像
###############################################
FROM python:3.9-slim

WORKDIR /app

# ★ 安裝 libreoffice、fontconfig，並將專案裡的 MINGLIU.TTC 拷貝至系統字型目錄。
#   接著執行 fc-cache -fv 以更新字型快取，確保 LibreOffice 能辨識該字型。
RUN apt-get update && \
    apt-get install -y --no-install-recommends fontconfig libreoffice && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY fonts/MINGLIU.TTC /usr/share/fonts/truetype/MINGLIU.TTC
RUN fc-cache -fv

# 設定語系；可依需求改為 zh_TW.UTF-8 / zh_CN.UTF-8 等。
ENV LANG=zh_TW.UTF-8
ENV LC_ALL=zh_TW.UTF-8

# 將前端編譯產物複製進來
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# 安裝後端相依套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 在安裝後，偵錯檢查 gevent 版本
RUN echo "[DEBUG] Checking gevent version..." && pip freeze | grep gevent || true

# 複製後端程式
COPY backend/ /app/backend/

# ★ 新增：將 gunicorn_config.py 也複製進容器
COPY gunicorn_config.py .

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# 幫助偵錯，確認 gunicorn_config.py 存在與否
RUN echo "[DEBUG] Checking gunicorn_config.py..." && ls -al

# 使用 Gunicorn (WSGI) 執行，並呼叫 backend.main:create_app() 工廠函式
RUN echo "[DEBUG] Using Gunicorn with 'backend.main:create_app()'..."

CMD ["gunicorn", "-c", "gunicorn_config.py", "backend.main:create_app()"]
