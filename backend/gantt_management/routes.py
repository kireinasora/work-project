# backend/gantt_management/routes.py

import logging
from datetime import datetime, date
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
    update_gantt_snapshot,
    delete_gantt_snapshot,
    reassign_task_ids,
)
from backend.db import to_iso_datetime, mongo

logger = logging.getLogger(__name__)

gantt_bp = Blueprint("gantt_bp", __name__)


# --------------------------------------------------------------------------------
# Gantt 任務相關
# --------------------------------------------------------------------------------

@gantt_bp.route("/<int:project_id>/gantt/tasks", methods=["GET"])
def list_gantt_tasks(project_id):
    logger.info("list_gantt_tasks called. project_id=%s", project_id)
    snapshot_date_str = request.args.get("snapshot_date", "").strip()

    try:
        if snapshot_date_str:
            logger.debug("Fetching snapshot tasks for date=%s", snapshot_date_str)
            # 取得舊版快照
            snapshot_doc = get_specific_snapshot(project_id, snapshot_date_str)
            if not snapshot_doc:
                logger.warning("No snapshot found for %s (project_id=%s)", snapshot_date_str, project_id)
                return jsonify({"error": f"No snapshot found for {snapshot_date_str}"}), 404

            tasks_data = snapshot_doc.get("tasks", [])
            logger.debug("Snapshot date=%s, tasks count=%d", snapshot_date_str, len(tasks_data))
            return jsonify(tasks_data), 200
        else:
            logger.debug("Fetching latest tasks for project_id=%s", project_id)
            tasks = get_all_tasks_for_project(project_id)
            logger.debug("Fetched %d tasks for project_id=%s", len(tasks), project_id)
            return jsonify(tasks), 200

    except Exception as e:
        logger.exception("list_gantt_tasks error:")
        return jsonify({"error": str(e)}), 500


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
      "parent_id": null,
      "depends": [2, 3],
      "type": "project"|"milestone"|"task"  (可選, 預設 "task")
    }
    """
    data = request.json or {}
    data["project_id"] = project_id

    snapshot_date_str = request.args.get("snapshot_date", "").strip()
    try:
        # 傳到 service 裡: create_gantt_task() 會自動寫入 DB 或更新 snapshot
        task_id = create_gantt_task(data, snapshot_date_str)
        return jsonify({"message": "Task created", "task_id": task_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as ex:
        logger.exception("create_task error:")
        return jsonify({"error": str(ex)}), 500


@gantt_bp.route("/<int:project_id>/gantt/tasks/<int:task_id>", methods=["PUT"])
def put_task(project_id, task_id):
    """
    更新某任務
    body JSON 與 create 相似
    """
    data = request.json or {}
    data["project_id"] = project_id
    data["task_id"] = task_id

    snapshot_date_str = request.args.get("snapshot_date", "").strip()
    try:
        update_gantt_task(task_id, data, snapshot_date_str)
        return jsonify({"message": "Task updated"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError:
        abort(404, description="Task not found")
    except Exception as ex:
        logger.exception("put_task error:")
        return jsonify({"error": str(ex)}), 500


@gantt_bp.route("/<int:project_id>/gantt/tasks/<int:task_id>", methods=["DELETE"])
def remove_task(project_id, task_id):
    """
    刪除某任務
    """
    snapshot_date_str = request.args.get("snapshot_date", "").strip()
    try:
        delete_gantt_task(project_id, task_id, snapshot_date_str)
        return jsonify({"message": "Task deleted"}), 200
    except KeyError:
        abort(404, description="Task not found")
    except Exception as ex:
        logger.exception("remove_task error:")
        return jsonify({"error": str(ex)}), 500


# ★★★ 新增：清空所有任務 (可支援當前最新或指定snapshot) ★★★
@gantt_bp.route("/<int:project_id>/gantt/tasks/clear", methods=["DELETE"])
def clear_all_tasks(project_id):
    """
    query param: snapshot_date=xxxx-xx-xx (可選)
      - 若有指定 snapshot_date => 清空該快照內 tasks
      - 若沒指定 => 清空「當前最新」
    """
    snapshot_date_str = request.args.get("snapshot_date", "").strip()
    try:
        if snapshot_date_str:
            snap_doc = get_specific_snapshot(project_id, snapshot_date_str)
            if not snap_doc:
                return jsonify({"error": f"Snapshot not found for {snapshot_date_str}"}), 404

            updated = update_gantt_snapshot(project_id, snapshot_date_str, new_tasks=[])
            if not updated:
                return jsonify({"error": "Snapshot update failed"}), 400
            return jsonify({"message": f"All tasks cleared in snapshot {snapshot_date_str}"}), 200
        else:
            result = mongo.db["gantt_tasks"].delete_many({"project_id": project_id})
            return jsonify({
                "message": "All current tasks cleared",
                "deleted_count": result.deleted_count
            }), 200

    except Exception as e:
        logger.exception("clear_all_tasks error:")
        return jsonify({"error": str(e)}), 500


# ★★★ 新增：重新分配任務ID => /<int:project_id>/gantt/tasks/reassign-ids ★★★
@gantt_bp.route("/<int:project_id>/gantt/tasks/reassign-ids", methods=["POST"])
def reassign_ids(project_id):
    """
    POST /api/projects/{project_id}/gantt/tasks/reassign-ids(?snapshot_date=xxxx-xx-xx)
    重新分配所有 tasks 的 ID (從1開始依序下去)。同時必須考慮 parent_id, depends, 
    以及可能存在的階層關係，確保重新分配後依賴關係仍然正確。

    前端若有指定 query param snapshot_date => 操作該 snapshot
    若無 => 操作當前最新 gantt_tasks
    """
    snapshot_date_str = request.args.get("snapshot_date", "").strip()
    try:
        reassign_task_ids(project_id, snapshot_date_str)
        return jsonify({"message": "Task IDs have been reassigned"}), 200
    except Exception as ex:
        logger.exception("reassign_ids error:")
        return jsonify({"error": str(ex)}), 500


# --------------------------------------------------------------------------------
# 版本快照
# --------------------------------------------------------------------------------

@gantt_bp.route("/<int:project_id>/gantt/snapshots", methods=["GET"])
def list_snapshots(project_id):
    snapshots = get_gantt_snapshots_for_project(project_id)
    out = []
    for snap in snapshots:
        out.append({
            "date": snap["snapshot_date"],
            "created_at": to_iso_datetime(snap.get("created_at"))
        })
    return jsonify(out), 200


@gantt_bp.route("/<int:project_id>/gantt/snapshots", methods=["POST"])
def make_snapshot(project_id):
    data = request.json or {}
    snap_date_str = data.get("snapshot_date")
    if snap_date_str:
        snap_date = datetime.strptime(snap_date_str, "%Y-%m-%d").date()
    else:
        snap_date = date.today()

    try:
        snap_id = create_daily_snapshot(project_id, snap_date)
        return jsonify({
            "message": "Snapshot created",
            "snapshot_date": snap_date.isoformat(),
            "snapshot_id": snap_id
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@gantt_bp.route("/<int:project_id>/gantt/snapshots/<snapshot_date_str>", methods=["PUT"])
def put_snapshot(project_id, snapshot_date_str):
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
    result = get_holiday_settings(project_id)
    if not result:
        result = {
            "project_id": project_id,
            "holidays": [],
            "workdays_per_week": 5,
            "workday_weekdays": [],
            "special_workdays": []
        }
    return jsonify(result), 200


@gantt_bp.route("/<int:project_id>/gantt/holidays", methods=["PUT"])
def put_holidays(project_id):
    data = request.json or {}
    data["project_id"] = project_id
    update_holiday_settings(project_id, data)
    return jsonify({"message": "Holiday settings updated"}), 200
