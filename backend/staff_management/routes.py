# backend/staff_management/routes.py
from flask import Blueprint, request, jsonify, abort

from backend.db import mongo, get_next_sequence, find_all_and_format, find_one_or_404

staff_bp = Blueprint('staff_bp', __name__)

@staff_bp.route('', methods=['GET'])
def list_staff():
    def format_staff(doc):
        return {
            "id": doc["id"],
            "name": doc.get("name", ""),
            "role": doc.get("role", "")
        }
    
    results = find_all_and_format(collection='staff', formatter=format_staff)
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


@staff_bp.route('/<int:staff_id>', methods=['GET'])
def get_staff(staff_id):
    staff = find_one_or_404('staff', {"id": staff_id}, "Staff not found")
    
    return jsonify({
        "id": staff["id"],
        "name": staff.get("name", ""),
        "role": staff.get("role", "")
    }), 200


@staff_bp.route('/<int:staff_id>', methods=['PUT'])
def update_staff(staff_id):
    staff = find_one_or_404('staff', {"id": staff_id}, "Staff not found")
    
    data = request.json or {}
    update_fields = {}
    if "name" in data:
        update_fields["name"] = data["name"]
    if "role" in data:
        update_fields["role"] = data["role"]
    
    if update_fields:
        mongo.db.staff.update_one({"id": staff_id}, {"$set": update_fields})
    
    return jsonify({"message": "Staff updated"}), 200


@staff_bp.route('/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    result = mongo.db.staff.delete_one({"id": staff_id})
    if result.deleted_count == 0:
        abort(404, description="Staff not found")
    
    return jsonify({"message": "Staff deleted"}), 200
