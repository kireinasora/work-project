# backend/main.py

import os
from flask import Flask, send_from_directory
from backend.project_management.routes import projects_bp
from backend.material_management.routes import material_bp
from backend.site_diary.routes import site_diary_bp
from backend.staff_management.routes import staff_bp
from backend.server import download_bp

# ★ 新增：改用我們的 db.py 來初始化 Mongo
from backend.db import init_mongo_app

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

    return app

# === 以下區段已移除 ===
# if __name__ == "__main__":
#     app = create_app()
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host='0.0.0.0', port=port)
