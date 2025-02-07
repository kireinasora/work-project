# backend/staff_management/routes.py
from flask import Blueprint, request, jsonify

# 改用 from backend.project_management.models
from backend.project_management.models import db
from .models import Staff

staff_bp = Blueprint('staff_bp', __name__)

@staff_bp.route('', methods=['GET'])
def list_staff():
    staff_list = Staff.query.all()
    results = []
    for s in staff_list:
        results.append({
            "id": s.id,
            "name": s.name,
            "role": s.role
        })
    return jsonify(results), 200

@staff_bp.route('', methods=['POST'])
def create_staff():
    data = request.json
    staff = Staff(
        name=data['name'],
        role=data.get('role', '')
    )
    db.session.add(staff)
    db.session.commit()
    return jsonify({
        "message": "Staff created",
        "staff_id": staff.id
    }), 201

# ★ 新增：刪除人員
@staff_bp.route('/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    return jsonify({"message": "Staff deleted"}), 200
