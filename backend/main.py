# backend/main.py

from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os

# 改用 project_management.models 來初始化 db
from backend.project_management.models import db
from backend.project_management.routes import projects_bp
from backend.material_management.routes import material_bp
from backend.site_diary.routes import site_diary_bp

# Flask-Migrate
from flask_migrate import Migrate

# staff_management 仍保留
from backend.staff_management.routes import staff_bp

# ★ 新增：引入我們在 server.py 裏定義的下載 Blueprint
from backend.server import download_bp


def create_app():
    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")

    # 設定資料庫
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # 使用 flask-migrate，指定 migrations 資料夾為 backend/migrations
    migrate = Migrate(app, db, directory="backend/migrations")

    # Blueprint 註冊
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(material_bp, url_prefix='/api')
    app.register_blueprint(site_diary_bp, url_prefix='/api/projects')
    app.register_blueprint(staff_bp, url_prefix='/api/staff')

    # ★ 新增：註冊提供下載的 Blueprint（對應 /download-diary）
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


if __name__ == "__main__":
    import os
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)