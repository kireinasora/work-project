# backend/staff_management/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from backend.project_management.models import db

class Staff(db.Model):
    """
    施工人員 (Staff)，用來全域管理可用人員
    """
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 人員姓名
    role = db.Column(db.String(100), nullable=True)    # 角色、職稱(可選)

    # 與 SiteDiary 的多對多關係
    site_diaries = db.relationship('SiteDiary',
                                   secondary='site_diary_staff',
                                   back_populates='staffs',
                                   lazy=True)


class SiteDiaryStaff(db.Model):
    """
    替代原本 DailyReportStaff：中介表 (site_diary_staff)
    """
    __tablename__ = 'site_diary_staff'

    site_diary_id = db.Column(db.Integer, db.ForeignKey('site_diaries.id'), primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), primary_key=True)
