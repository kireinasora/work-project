# backend/staff_management/routes.py
from flask import Blueprint, request, jsonify, abort

from backend.db import mongo, get_next_sequence

staff_bp = Blueprint('staff_bp', __name__)

@staff_bp.route('', methods=['GET'])
def list_staff():
    cursor = mongo.db.staff.find({}, sort=[("id", 1)])
    results = []
    for s in cursor:
        results.append({
            "id": s["id"],
            "name": s.get("name", ""),
            "role": s.get("role", "")
        })
    return jsonify(results), 200


@staff_bp.route('', methods=['POST'])
def create_staff():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "Name is required"}), 400

    role = data.get("role", "")
    new_id = get_next_sequence("staff")
    doc = {
        "id": new_id,
        "name": name,
        "role": role
    }
    mongo.db.staff.insert_one(doc)

    return jsonify({
        "message": "Staff created",
        "staff_id": new_id
    }), 201


@staff_bp.route('/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    result = mongo.db.staff.delete_one({"id": staff_id})
    if result.deleted_count == 0:
        abort(404, description="Staff not found")
    return jsonify({"message": "Staff deleted"}), 200
