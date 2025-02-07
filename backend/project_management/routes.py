# backend/project_management/routes.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from .models import db, Project

projects_bp = Blueprint('projects_bp', __name__)

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """
    取得所有專案列表
    """
    projects = Project.query.all()
    result = []
    for p in projects:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None,
            "owner": p.owner,
            "objective": p.objective,
            "duration_type": p.duration_type,
            "duration_days": p.duration_days,
            # 新增回傳
            "job_number": p.job_number,
            "contractor": p.contractor
        })
    return jsonify(result), 200


@projects_bp.route('/', methods=['POST'])
def create_project():
    """
    建立新專案
    """
    data = request.json
    name = data.get('name')
    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    owner = data.get('owner')
    objective = data.get('objective')
    duration_type = data.get('duration_type')
    duration_days_str = data.get('duration_days')

    # 新增接收欄位
    job_number = data.get('job_number')
    contractor = data.get('contractor')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    duration_days = int(duration_days_str) if duration_days_str else None

    project = Project(
        name=name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        owner=owner,
        objective=objective,
        duration_type=duration_type,
        duration_days=duration_days,
        job_number=job_number,
        contractor=contractor
    )
    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created", "project_id": project.id}), 201


@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project_detail(project_id):
    """
    取得單一專案詳細資訊
    """
    project = Project.query.get_or_404(project_id)
    return jsonify({
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "end_date": project.end_date.isoformat() if project.end_date else None,
        "owner": project.owner,
        "objective": project.objective,
        "duration_type": project.duration_type,
        "duration_days": project.duration_days,
        # 新增回傳
        "job_number": project.job_number,
        "contractor": project.contractor
    }), 200


@projects_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    更新專案
    """
    project = Project.query.get_or_404(project_id)
    data = request.json

    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.owner = data.get('owner', project.owner)
    project.objective = data.get('objective', project.objective)
    project.duration_type = data.get('duration_type', project.duration_type)
    project.duration_days = data.get('duration_days', project.duration_days)

    # 新增更新
    project.job_number = data.get('job_number', project.job_number)
    project.contractor = data.get('contractor', project.contractor)

    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    if start_date_str:
        project.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    if end_date_str:
        project.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    db.session.commit()
    return jsonify({"message": "Project updated"}), 200


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    刪除專案
    """
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted"}), 200
