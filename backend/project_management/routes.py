# backend/project_management/routes.py

from flask import Blueprint, request, jsonify, abort
from datetime import datetime
from bson import ObjectId

from backend.db import mongo, get_next_sequence, to_iso_date

projects_bp = Blueprint('projects_bp', __name__)

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """
    取得所有專案列表
    """
    cursor = mongo.db.projects.find({}, sort=[("id", 1)])
    result = []
    for doc in cursor:
        result.append({
            "id": doc["id"],
            "name": doc.get("name"),
            "description": doc.get("description"),
            "start_date": to_iso_date(doc.get("start_date")),
            "end_date": to_iso_date(doc.get("end_date")),
            "owner": doc.get("owner"),
            "objective": doc.get("objective"),
            "duration_type": doc.get("duration_type"),
            "duration_days": doc.get("duration_days"),
            "job_number": doc.get("job_number"),
            "contractor": doc.get("contractor"),
        })
    return jsonify(result), 200


@projects_bp.route('/', methods=['POST'])
def create_project():
    """
    建立新專案
    """
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({"error": "Project name is required"}), 400

    description = data.get('description')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    owner = data.get('owner')
    objective = data.get('objective')
    duration_type = data.get('duration_type')
    duration_days = data.get('duration_days')
    job_number = data.get('job_number')
    contractor = data.get('contractor')

    # 轉換為 datetime(yyyy,mm,dd) 而不是 date()，以讓 PyMongo 能正常儲存
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    # 取得此集合下一個可用的整數 ID
    new_id = get_next_sequence("projects")

    doc = {
        "id": new_id,
        "name": name,
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "owner": owner,
        "objective": objective,
        "duration_type": duration_type,
        "duration_days": duration_days,
        "job_number": job_number,
        "contractor": contractor,
    }

    mongo.db.projects.insert_one(doc)

    return jsonify({"message": "Project created", "project_id": new_id}), 201


@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project_detail(project_id):
    """
    取得單一專案詳細資訊
    """
    doc = mongo.db.projects.find_one({"id": project_id})
    if not doc:
        abort(404, description="Project not found")

    return jsonify({
        "id": doc["id"],
        "name": doc.get("name"),
        "description": doc.get("description"),
        "start_date": to_iso_date(doc.get("start_date")),
        "end_date": to_iso_date(doc.get("end_date")),
        "owner": doc.get("owner"),
        "objective": doc.get("objective"),
        "duration_type": doc.get("duration_type"),
        "duration_days": doc.get("duration_days"),
        "job_number": doc.get("job_number"),
        "contractor": doc.get("contractor"),
    }), 200


@projects_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    更新專案
    """
    doc = mongo.db.projects.find_one({"id": project_id})
    if not doc:
        abort(404, description="Project not found")

    data = request.json or {}
    update_fields = {}

    if "name" in data:
        update_fields["name"] = data["name"]
    if "description" in data:
        update_fields["description"] = data["description"]
    if "owner" in data:
        update_fields["owner"] = data["owner"]
    if "objective" in data:
        update_fields["objective"] = data["objective"]
    if "duration_type" in data:
        update_fields["duration_type"] = data["duration_type"]
    if "duration_days" in data:
        update_fields["duration_days"] = data["duration_days"]
    if "job_number" in data:
        update_fields["job_number"] = data["job_number"]
    if "contractor" in data:
        update_fields["contractor"] = data["contractor"]

    # 處理日期，改為存 datetime 而非 date
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    if start_date_str is not None:
        if start_date_str == "":
            update_fields["start_date"] = None
        else:
            update_fields["start_date"] = datetime.strptime(start_date_str, '%Y-%m-%d')
    if end_date_str is not None:
        if end_date_str == "":
            update_fields["end_date"] = None
        else:
            update_fields["end_date"] = datetime.strptime(end_date_str, '%Y-%m-%d')

    if update_fields:
        mongo.db.projects.update_one({"id": project_id}, {"$set": update_fields})

    return jsonify({"message": "Project updated"}), 200


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    刪除專案
    """
    result = mongo.db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        abort(404, description="Project not found")

    return jsonify({"message": "Project deleted"}), 200
