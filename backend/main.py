# backend/main.py

import os
from flask import Flask, send_from_directory, request, jsonify
from werkzeug.exceptions import NotFound

from backend.project_management.routes import projects_bp
from backend.material_management.routes import material_bp
# from backend.site_diary.routes import site_diary_bp  # <-- 已刪除，不再引用
from backend.staff_management.routes import staff_bp

from backend.db import init_mongo_app

# from backend.site_diary.progress_sse import progress_sse_bp  # <-- 已刪除，不再引用
from backend.gantt_management.routes import gantt_bp

# ★★ 新增文件管理 blueprint
from backend.document_management.routes import document_bp


def create_app():
    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")

    # 初始化 MongoDB
    init_mongo_app(app)

    # Blueprint 註冊
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(material_bp, url_prefix='/api')
    # app.register_blueprint(site_diary_bp, url_prefix='/api/projects')  # <-- 已刪除
    app.register_blueprint(staff_bp, url_prefix='/api/staff')
    # app.register_blueprint(progress_sse_bp, url_prefix='/api')  # <-- 已刪除
    app.register_blueprint(gantt_bp, url_prefix='/api/projects')

    # ★★ 文件管理
    app.register_blueprint(document_bp, url_prefix='/api/documents')

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_vue_app(path):
        dist_dir = os.path.abspath(app.static_folder)
        full_path = os.path.join(dist_dir, path)
        if path and os.path.exists(full_path):
            return send_from_directory(dist_dir, path)
        else:
            return send_from_directory(dist_dir, 'index.html')

    @app.errorhandler(NotFound)
    def handle_404(e):
        if request.path.startswith('/api'):
            return jsonify({"error": "Not found"}), 404

        dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
        return send_from_directory(dist_dir, 'index.html')

    return app
