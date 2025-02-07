# backend/site_diary/models.py

from datetime import datetime
# 注意：這裡我們只需要引用 db 自 backend.project_management.models
from backend.project_management.models import db
# 如果有需要使用 Staff，可引用 (但示範通常在關聯那裡再做)
from backend.staff_management.models import Staff

class SiteDiary(db.Model):
    """
    替代原本的 DailyReport：日報 (SiteDiary) 主表
    """
    __tablename__ = 'site_diaries'

    id = db.Column(db.Integer, primary_key=True)
    # 與 Project 的外鍵關係
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    # 報表日期
    report_date = db.Column(db.Date, default=datetime.utcnow)

    # 天氣
    weather_morning = db.Column(db.String(50), nullable=True)  # 早上天氣
    weather_noon = db.Column(db.String(50), nullable=True)     # 中午天氣

    # 開工日數
    # （若不想手動填，可在 services.py 裏做自動計算）
    day_count = db.Column(db.Integer, nullable=True)

    # 本日工作概述
    summary = db.Column(db.Text, nullable=False)

    # 一對多: SiteDiaryWorker
    workers = db.relationship('SiteDiaryWorker', 
                              backref='site_diary', 
                              cascade='all, delete-orphan', 
                              lazy=True)

    # 一對多: SiteDiaryMachine
    machines = db.relationship('SiteDiaryMachine', 
                               backref='site_diary', 
                               cascade='all, delete-orphan', 
                               lazy=True)

    # 多對多: Staff (through site_diary_staff)
    staffs = db.relationship('Staff',
                             secondary='site_diary_staff',
                             back_populates='site_diaries',
                             lazy=True)


class SiteDiaryWorker(db.Model):
    """
    替代原本的 DailyReportWorker
    """
    __tablename__ = 'site_diary_workers'

    id = db.Column(db.Integer, primary_key=True)
    site_diary_id = db.Column(db.Integer, db.ForeignKey('site_diaries.id'), nullable=False)
    worker_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)


class SiteDiaryMachine(db.Model):
    """
    替代原本的 DailyReportMachine
    """
    __tablename__ = 'site_diary_machines'

    id = db.Column(db.Integer, primary_key=True)
    site_diary_id = db.Column(db.Integer, db.ForeignKey('site_diaries.id'), nullable=False)
    machine_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
