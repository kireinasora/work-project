# gunicorn_config.py

worker_class = "gevent"     # 改用 gevent worker
workers = 2                 # 可自行斟酌調整 worker 數
bind = "0.0.0.0:8080"       # 與 Dockerfile / container expose 相對應

timeout = 1800              # ★ 改為半小時 (30分鐘) 
graceful_timeout = 1800     # ★ 同樣30分鐘
keepalive = 2

# 可視需求再增加其他參數，如 max_requests、max_requests_jitter 等
# max_requests = 1000
# max_requests_jitter = 100
