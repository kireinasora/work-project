# backend/main.py

import os
from flask import Flask, send_from_directory, request, jsonify
from werkzeug.exceptions import NotFound

from backend.project_management.routes import projects_bp
from backend.material_management.routes import material_bp
from backend.site_diary.routes import site_diary_bp
from backend.staff_management.routes import staff_bp
from backend.server import download_bp

# ★ 新增：改用我們的 db.py 來初始化 Mongo
from backend.db import init_mongo_app

# ★ 新增：SSE Blueprint
from backend.site_diary.progress_sse import progress_sse_bp

# ★ 新增: 匯入 Gantt Management blueprint
from backend.gantt_management.routes import gantt_bp

def create_app():
    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")

    # 初始化 MongoDB
    init_mongo_app(app)

    # Blueprint 註冊
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(material_bp, url_prefix='/api')
    app.register_blueprint(site_diary_bp, url_prefix='/api/projects')
    app.register_blueprint(staff_bp, url_prefix='/api/staff')
    app.register_blueprint(download_bp)

    # ★ 新增：SSE blueprint
    app.register_blueprint(progress_sse_bp, url_prefix='/api')

    # ★ 新增：Gantt blueprint
    # 提供 /api/projects/<int:project_id>/gantt/... 路徑
    app.register_blueprint(gantt_bp, url_prefix='/api/projects')

    # 提供前端打包後檔案 (SPA)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_vue_app(path):
        dist_dir = os.path.abspath(app.static_folder)
        full_path = os.path.join(dist_dir, path)
        if path and os.path.exists(full_path):
            return send_from_directory(dist_dir, path)
        else:
            return send_from_directory(dist_dir, 'index.html')

    # ===============★ 關鍵新增：處理 404 ★===============
    # 如果路由未匹配到，而且不是 /api/... ，就回傳 index.html 讓前端接管
    @app.errorhandler(NotFound)
    def handle_404(e):
        # 如果是 API 開頭，則真的是 404
        if request.path.startswith('/api'):
            return jsonify({"error": "Not found"}), 404

        # 否則一律回傳前端打包後的 index.html
        dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
        return send_from_directory(dist_dir, 'index.html')

    return app
