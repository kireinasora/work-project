# backend/project_management/models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Project(db.Model):
    """
    專案 (Project) Model
    """
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    # 既有欄位
    owner = db.Column(db.String(100), nullable=True)           # 專案業主
    objective = db.Column(db.Text, nullable=True)              # 專案整體目標
    duration_type = db.Column(db.String(20), nullable=True)    # 'business' or 'calendar'
    duration_days = db.Column(db.Integer, nullable=True)

    # === 新增欄位: 工作編號 & 承建商 ===
    job_number = db.Column(db.String(50), nullable=True)  # 工作編號
    contractor = db.Column(db.String(200), nullable=True) # 承建商
