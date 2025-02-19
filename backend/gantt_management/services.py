# backend/gantt_management/services.py

import math
import uuid
from datetime import datetime, date
from typing import Dict, Any, Optional
from bson.objectid import ObjectId

from backend.db import mongo

# --------------------------------------------------------------------------
# Gantt Tasks (當前最新資料，不屬於任何 snapshot)
# --------------------------------------------------------------------------

def get_all_tasks_for_project(project_id: int):
    """
    查詢當前最新資料(不含版本快照)的 tasks。
    """
    cursor = mongo.db["gantt_tasks"].find({"project_id": project_id})
    tasks = []
    for doc in cursor:
        tasks.append(_format_task_doc(doc))
    return tasks


def create_gantt_task(data: Dict[str, Any]) -> str:
    """
    新增一筆任務
    """
    project_id = data["project_id"]
    text = data.get("text", "Unnamed Task")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    duration = data.get("duration")
    progress = data.get("progress", 0)
    parent_id = data.get("parent_id")
    depends = data.get("depends", [])

    if not start_date_str and not end_date_str and not duration:
        raise ValueError("start_date + (end_date or duration) is required")

    # 計算 end_date 或 duration
    if start_date_str:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        if end_date_str:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
            duration = (end_dt - start_dt).days + 1
        else:
            # end_date = start_date + duration - 1
            end_dt = start_dt
            if duration:
                end_dt = start_dt + _days_timedelta(duration - 1)
        start_date_iso = start_dt.date().isoformat()
        end_date_iso = end_dt.date().isoformat()
    else:
        raise ValueError("Must provide start_date")

    task_doc = {
        "project_id": project_id,
        "text": text,
        "start_date": start_date_iso,
        "end_date": end_date_iso,
        "progress": float(progress),
        "parent_id": parent_id,
        "depends": depends,
        "created_at": datetime.now(),
    }
    # 產生 task_id (string)
    task_doc["_id"] = str(uuid.uuid4())

    mongo.db["gantt_tasks"].insert_one(task_doc)
    return task_doc["_id"]


def update_gantt_task(task_id: str, data: Dict[str, Any]):
    """
    更新任務
    """
    doc = mongo.db["gantt_tasks"].find_one({"_id": task_id, "project_id": data["project_id"]})
    if not doc:
        raise KeyError("Task not found")

    update_fields = {}
    if "text" in data:
        update_fields["text"] = data["text"]
    if "progress" in data:
        update_fields["progress"] = float(data["progress"])
    if "parent_id" in data:
        update_fields["parent_id"] = data["parent_id"]
    if "depends" in data:
        update_fields["depends"] = data["depends"]

    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    duration = data.get("duration")

    if start_date_str:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        update_fields["start_date"] = start_dt.date().isoformat()
        if end_date_str:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
            update_fields["end_date"] = end_dt.date().isoformat()
        elif duration:
            end_dt = start_dt + _days_timedelta(duration - 1)
            update_fields["end_date"] = end_dt.date().isoformat()
    elif end_date_str:
        old_start = doc["start_date"]
        if not old_start:
            raise ValueError("No existing start_date to compute from.")
        start_dt = datetime.strptime(old_start, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        update_fields["end_date"] = end_dt.date().isoformat()

    update_fields["updated_at"] = datetime.now()

    mongo.db["gantt_tasks"].update_one(
        {"_id": task_id},
        {"$set": update_fields}
    )


def delete_gantt_task(project_id: int, task_id: str):
    result = mongo.db["gantt_tasks"].delete_one({
        "_id": task_id,
        "project_id": project_id
    })
    if result.deleted_count == 0:
        raise KeyError("Task not found")


def _format_task_doc(doc):
    return {
        "id": doc["_id"],
        "text": doc.get("text", ""),
        "start_date": doc.get("start_date", ""),
        "end_date": doc.get("end_date", ""),
        "progress": doc.get("progress", 0.0),
        "parent": doc.get("parent_id"),
        "depends": doc.get("depends", []),
        "duration": _calc_duration(doc.get("start_date"), doc.get("end_date")),
    }


def _calc_duration(start_date_iso, end_date_iso):
    if not start_date_iso or not end_date_iso:
        return 1
    sdt = datetime.strptime(start_date_iso, "%Y-%m-%d")
    edt = datetime.strptime(end_date_iso, "%Y-%m-%d")
    return (edt - sdt).days + 1


def _days_timedelta(days: int):
    return timedelta(days=days)


# --------------------------------------------------------------------------
# 版本快照 (gantt_snapshots)
# --------------------------------------------------------------------------

def get_gantt_snapshots_for_project(project_id: int):
    cursor = mongo.db["gantt_snapshots"].find(
        {"project_id": project_id},
        sort=[("snapshot_date", 1)]
    )
    return list(cursor)


def get_specific_snapshot(project_id: int, snapshot_date_str: str):
    snap = mongo.db["gantt_snapshots"].find_one({
        "project_id": project_id,
        "snapshot_date": snapshot_date_str
    })
    return snap


def create_daily_snapshot(project_id: int, snap_date: date) -> str:
    """
    建立該日期的快照(若已存在則擲錯或覆蓋)
    """
    exists = mongo.db["gantt_snapshots"].find_one({
        "project_id": project_id,
        "snapshot_date": snap_date.isoformat()
    })
    if exists:
        # 也可選擇直接覆蓋，但此處先擲錯
        raise ValueError(f"Snapshot already exists for {snap_date.isoformat()}")

    tasks = get_all_tasks_for_project(project_id)
    snap_doc = {
        "project_id": project_id,
        "snapshot_date": snap_date.isoformat(),
        "tasks": tasks,
        "created_at": datetime.now()
    }
    result = mongo.db["gantt_snapshots"].insert_one(snap_doc)
    return str(result.inserted_id)


# ★★★ 新增: 修改 / 刪除 舊 snapshot ★★★

def update_gantt_snapshot(project_id: int, snapshot_date_str: str, new_tasks: list) -> bool:
    """
    將某個日期的 snapshot 裡的 tasks 全量覆蓋。
    若找不到該 snapshot，回傳 False。
    """
    filter_ = {
        "project_id": project_id,
        "snapshot_date": snapshot_date_str
    }
    existing = mongo.db["gantt_snapshots"].find_one(filter_)
    if not existing:
        return False

    # 全量覆蓋 tasks
    update_data = {
        "tasks": new_tasks,
        "updated_at": datetime.now()
    }
    mongo.db["gantt_snapshots"].update_one(filter_, {"$set": update_data})
    return True


def delete_gantt_snapshot(project_id: int, snapshot_date_str: str) -> bool:
    """
    刪除某個日期的 snapshot，若找不到則回傳 False
    """
    filter_ = {
        "project_id": project_id,
        "snapshot_date": snapshot_date_str
    }
    result = mongo.db["gantt_snapshots"].delete_one(filter_)
    return (result.deleted_count > 0)


# --------------------------------------------------------------------------
# 假日 & 工作日設定 (gantt_holidays)
# --------------------------------------------------------------------------

def get_holiday_settings(project_id: int) -> Optional[dict]:
    doc = mongo.db["gantt_holidays"].find_one({"project_id": project_id})
    return doc


def update_holiday_settings(project_id: int, data: Dict[str, Any]):
    """
    可支援:
    - holidays: [...],
    - workdays_per_week: int,
    - workday_weekdays: [...],  # <--- 新增
    - special_workdays: [...]
    """
    filter_ = {"project_id": project_id}
    update_data = {
        "project_id": project_id,
        "holidays": data.get("holidays", []),
        "workdays_per_week": data.get("workdays_per_week", 5),
        "workday_weekdays": data.get("workday_weekdays", []),  # ★ 新增或預設空
        "special_workdays": data.get("special_workdays", []),
        "updated_at": datetime.now()
    }
    mongo.db["gantt_holidays"].update_one(
        filter_,
        {"$set": update_data},
        upsert=True
    )
