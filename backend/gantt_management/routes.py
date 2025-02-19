# backend/gantt_management/routes.py

import logging
from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify, abort

from backend.gantt_management.services import (
    create_gantt_task,
    update_gantt_task,
    delete_gantt_task,
    get_all_tasks_for_project,
    get_gantt_snapshots_for_project,
    create_daily_snapshot,
    get_specific_snapshot,
    get_holiday_settings,
    update_holiday_settings,
    update_gantt_snapshot,       # ★ 新增
    delete_gantt_snapshot,       # ★ 新增
)
from backend.db import to_iso_datetime  # 轉 datetime -> 字串

logger = logging.getLogger(__name__)

gantt_bp = Blueprint("gantt_bp", __name__)

# --------------------------------------------------------------------------------
# Gantt 任務相關
# --------------------------------------------------------------------------------

@gantt_bp.route("/<int:project_id>/gantt/tasks", methods=["GET"])
def list_gantt_tasks(project_id):
    """
    取得某專案當前最新(或指定日期版本) 的所有 Gantt Tasks。
    可帶 query param ?snapshot_date=YYYY-MM-DD 取舊版。
    """
    snapshot_date_str = request.args.get("snapshot_date", "").strip()
    if snapshot_date_str:
        # 取得舊版快照
        snapshot_doc = get_specific_snapshot(project_id, snapshot_date_str)
        if not snapshot_doc:
            return jsonify({
                "error": f"No snapshot found for {snapshot_date_str}"
            }), 404
        # 回傳該 snapshot 裡的 tasks
        return jsonify(snapshot_doc["tasks"]), 200
    else:
        # 回傳當前最新
        tasks = get_all_tasks_for_project(project_id)
        return jsonify(tasks), 200


@gantt_bp.route("/<int:project_id>/gantt/tasks", methods=["POST"])
def create_task(project_id):
    """
    新增一筆任務
    body JSON: {
      "text": "任務名稱",
      "start_date": "2025-01-15",
      "end_date": "2025-01-20",  // 或傳 duration
      "duration": 5,            // 二擇一
      "progress": 0.3,
      "parent_id": null,        // 可支援子任務
      "depends": [ 2, 3 ],      // 依賴哪些任務(簡化)
    }
    """
    data = request.json or {}
    data["project_id"] = project_id

    try:
        task_id = create_gantt_task(data)
        return jsonify({"message": "Task created", "task_id": task_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@gantt_bp.route("/<int:project_id>/gantt/tasks/<string:task_id>", methods=["PUT"])
def put_task(project_id, task_id):
    """
    更新某任務
    body JSON 與 create 相似
    """
    data = request.json or {}
    data["project_id"] = project_id
    data["task_id"] = task_id

    try:
        update_gantt_task(task_id, data)
        return jsonify({"message": "Task updated"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError:
        abort(404, description="Task not found")


@gantt_bp.route("/<int:project_id>/gantt/tasks/<string:task_id>", methods=["DELETE"])
def remove_task(project_id, task_id):
    """
    刪除某任務
    """
    try:
        delete_gantt_task(project_id, task_id)
        return jsonify({"message": "Task deleted"}), 200
    except KeyError:
        abort(404, description="Task not found")


# --------------------------------------------------------------------------------
# 版本快照
# --------------------------------------------------------------------------------

@gantt_bp.route("/<int:project_id>/gantt/snapshots", methods=["GET"])
def list_snapshots(project_id):
    """
    取得某專案所有 Gantt 快照日期列表。
    """
    snapshots = get_gantt_snapshots_for_project(project_id)
    # 僅回傳日期 + created_at 字串
    out = []
    for snap in snapshots:
        out.append({
            "date": snap["snapshot_date"],
            "created_at": to_iso_datetime(snap.get("created_at"))
        })
    return jsonify(out), 200


@gantt_bp.route("/<int:project_id>/gantt/snapshots", methods=["POST"])
def make_snapshot(project_id):
    """
    手動建立當天(或指定日)的快照。
    body JSON: { "snapshot_date": "2025-06-07" } (可不傳，預設今天)
    """
    data = request.json or {}
    snap_date_str = data.get("snapshot_date")
    if snap_date_str:
        snap_date = datetime.strptime(snap_date_str, "%Y-%m-%d").date()
    else:
        snap_date = date.today()  # ★ 預設就是今天

    try:
        snap_id = create_daily_snapshot(project_id, snap_date)
        return jsonify({
            "message": "Snapshot created",
            "snapshot_date": snap_date.isoformat(),
            "snapshot_id": snap_id
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ★★★ 新增：修改 / 刪除舊快照 ★★★

@gantt_bp.route("/<int:project_id>/gantt/snapshots/<snapshot_date_str>", methods=["PUT"])
def put_snapshot(project_id, snapshot_date_str):
    """
    修改已存在的某個日期之 Gantt Snapshot 的 tasks 全量覆蓋，
    body JSON: { "tasks": [...] }
    """
    data = request.json or {}
    new_tasks = data.get("tasks", [])
    try:
        updated = update_gantt_snapshot(project_id, snapshot_date_str, new_tasks)
        if not updated:
            return jsonify({"error": "Snapshot not found"}), 404
        return jsonify({"message": "Snapshot updated"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@gantt_bp.route("/<int:project_id>/gantt/snapshots/<snapshot_date_str>", methods=["DELETE"])
def remove_snapshot(project_id, snapshot_date_str):
    """
    刪除某個日期之 Gantt Snapshot
    """
    try:
        deleted = delete_gantt_snapshot(project_id, snapshot_date_str)
        if not deleted:
            return jsonify({"error": "Snapshot not found"}), 404
        return jsonify({"message": "Snapshot deleted"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# --------------------------------------------------------------------------------
# 假日 & 工作日設定
# --------------------------------------------------------------------------------

@gantt_bp.route("/<int:project_id>/gantt/holidays", methods=["GET"])
def get_holidays(project_id):
    """
    取得該專案的假日設定 (或公司統一維度)
    結構可包含: {
       "project_id": int,
       "holidays": ["2025-01-01", "2025-02-10" ],
       "workdays_per_week": 5,
       "workday_weekdays": [1,2,3,4,5],  # ★ 新增: 指定哪些星期幾是工作日 (0=周日,1=周一,...)
       "special_workdays": [ "2025-02-11" ],
       ...
    }
    """
    result = get_holiday_settings(project_id)
    if not result:
        # 若查無, 回傳預設
        result = {
            "project_id": project_id,
            "holidays": [],
            "workdays_per_week": 5,
            "workday_weekdays": [],   # ★ 新增欄位: 預設空陣列
            "special_workdays": []
        }
    return jsonify(result), 200


@gantt_bp.route("/<int:project_id>/gantt/holidays", methods=["PUT"])
def put_holidays(project_id):
    """
    更新該專案假日設定
    body: {
       "holidays": [ "2025-01-01", "2025-02-10" ],
       "workdays_per_week": 6,
       "workday_weekdays": [1,2,3,4,5,6],
       ...
    }
    """
    data = request.json or {}
    data["project_id"] = project_id
    update_holiday_settings(project_id, data)
    return jsonify({"message": "Holiday settings updated"}), 200
