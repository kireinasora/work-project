# backend/gantt_management/services.py

import math
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from bson.objectid import ObjectId

from backend.db import mongo, get_next_sequence

logger = logging.getLogger(__name__)


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
        formatted = _format_task_doc(doc)
        if formatted is not None:
            tasks.append(formatted)
    return tasks


def create_gantt_task(data: Dict[str, Any], snapshot_date_str: str = "") -> int:
    """
    新增一筆任務（至最新或指定 snapshot）。
    - 若 snapshot_date_str 有值 => 直接操作該 snapshot 的 tasks (in-memory + update snapshot)
    - 否則 => 建立於 gantt_tasks 集合中。
    """
    project_id = data["project_id"]
    text = data.get("text", "Unnamed Task")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    duration = data.get("duration")
    progress = data.get("progress", 0)
    parent_id = data.get("parent_id")
    depends = data.get("depends", [])
    task_type = data.get("type", "task")  # "project"|"milestone"|"task"

    if not start_date_str and not end_date_str and not duration:
        raise ValueError("start_date + (end_date or duration) is required")

    # 檢查 & 修正日期
    if not start_date_str:
        raise ValueError("Must provide start_date")

    start_dt = _parse_date_str(start_date_str, default_date_str="2025-01-01")
    if end_date_str:
        end_dt = _parse_date_str(end_date_str, default_date_str=None)  # None代表就用start+1
        if end_dt is None:
            end_dt = start_dt + timedelta(days=1)
    else:
        if duration:
            end_dt = start_dt + timedelta(days=duration - 1)
        else:
            end_dt = start_dt + timedelta(days=1)

    # 若 end < start，則修正
    if end_dt < start_dt:
        logger.warning(f"[create_gantt_task] end_date < start_date => auto-fix. end={end_dt}, start={start_dt}")
        end_dt = start_dt + timedelta(days=1)

    # 若 type=milestone => force start_date == end_date
    if task_type == "milestone":
        end_dt = start_dt

    # progress
    progress_val = _normalize_progress(progress)

    # 如果是 snapshot 模式 => 先讀出 tasks array，再 in-memory 新增
    if snapshot_date_str:
        snap_doc = mongo.db["gantt_snapshots"].find_one({
            "project_id": project_id,
            "snapshot_date": snapshot_date_str
        })
        if not snap_doc:
            raise ValueError(f"Snapshot not found for {snapshot_date_str}")

        tasks_list = snap_doc.get("tasks", [])

        # 產生一個新的暫定 ID => 找當前 tasks_list 的 max id
        max_id = 0
        for t in tasks_list:
            if t["id"] > max_id:
                max_id = t["id"]
        new_id = max_id + 1

        new_task = {
            "id": new_id,
            "project_id": project_id,
            "text": text,
            "start_date": start_dt.date().isoformat(),
            "end_date": end_dt.date().isoformat(),
            "progress": progress_val,
            "parent_id": parent_id,
            "depends": depends,
            "type": task_type,
            "created_at": datetime.now(),
        }
        tasks_list.append(new_task)

        # 接著更新 snapshot doc
        # 先寫回 tasks_list (未計算父任務), 再進行父任務的自動更新
        mongo.db["gantt_snapshots"].update_one(
            {"_id": snap_doc["_id"]},
            {"$set": {"tasks": tasks_list}}
        )

        # ★重新計算父任務
        _recalc_parent_chain_in_snapshot(project_id, new_id, snapshot_date_str)

        return new_id

    else:
        # 建立於 gantt_tasks 集合
        new_task_id = get_next_sequence("gantt_tasks")
        task_doc = {
            "id": new_task_id,
            "project_id": project_id,
            "text": text,
            "start_date": start_dt.date().isoformat(),
            "end_date": end_dt.date().isoformat(),
            "progress": progress_val,
            "parent_id": parent_id,
            "depends": depends,
            "type": task_type,
            "created_at": datetime.now(),
        }
        mongo.db["gantt_tasks"].insert_one(task_doc)

        # 重新計算父任務
        _recalc_parent_chain_in_db(project_id, new_task_id)

        return new_task_id


def update_gantt_task(task_id: int, data: Dict[str, Any], snapshot_date_str: str = ""):
    """
    更新任務；若 snapshot_date_str 有值 => 更新 snapshot tasks
              否則更新 gantt_tasks 集合
    """
    project_id = data["project_id"]

    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    duration = data.get("duration")
    progress = data.get("progress")
    parent_id = data.get("parent_id") if "parent_id" in data else None
    depends = data.get("depends") if "depends" in data else None
    task_type = data.get("type", None)  # 可能是 "project"|"milestone"|"task"

    if snapshot_date_str:
        # 更新快照 in memory
        snap = mongo.db["gantt_snapshots"].find_one({
            "project_id": project_id,
            "snapshot_date": snapshot_date_str
        })
        if not snap:
            raise KeyError("Snapshot not found")

        tasks_list = snap.get("tasks", [])
        # 找到該task
        found_index = -1
        for i, t in enumerate(tasks_list):
            if t["id"] == task_id:
                found_index = i
                break
        if found_index < 0:
            raise KeyError("Task not found in snapshot")

        updated_doc = dict(tasks_list[found_index])  # copy

        # 更新字段
        if data.get("text") is not None:
            updated_doc["text"] = data["text"]

        if progress is not None:
            updated_doc["progress"] = _normalize_progress(progress)

        if parent_id is not None:
            updated_doc["parent_id"] = parent_id

        if depends is not None:
            updated_doc["depends"] = depends

        # start/end/duration
        old_start = _parse_date_str(updated_doc.get("start_date", ""), "2025-01-01")
        old_end = _parse_date_str(updated_doc.get("end_date", ""), None)
        if start_date_str or end_date_str or duration is not None:
            start_dt = old_start
            end_dt = old_end if old_end else (old_start + timedelta(days=1))

            if start_date_str:
                start_dt = _parse_date_str(start_date_str, "2025-01-01")
            if end_date_str:
                end_dt = _parse_date_str(end_date_str, None)
                if end_dt is None:
                    end_dt = start_dt + timedelta(days=1)
            elif duration is not None:
                end_dt = start_dt + timedelta(days=duration - 1)

            if end_dt < start_dt:
                end_dt = start_dt + timedelta(days=1)

            # 若 type=milestone => 令 start==end
            the_type = task_type or updated_doc.get("type", "task")
            if the_type == "milestone":
                end_dt = start_dt

            updated_doc["start_date"] = start_dt.date().isoformat()
            updated_doc["end_date"] = end_dt.date().isoformat()

        # type
        if task_type:
            updated_doc["type"] = task_type
            # 如果是 milestone, 要強制同一天
            if task_type == "milestone":
                sdt = _parse_date_str(updated_doc["start_date"], "2025-01-01")
                updated_doc["end_date"] = sdt.date().isoformat()

        updated_doc["updated_at"] = datetime.now()

        # 更新回 tasks_list
        tasks_list[found_index] = updated_doc
        # 先寫回
        mongo.db["gantt_snapshots"].update_one(
            {"_id": snap["_id"]},
            {"$set": {"tasks": tasks_list}}
        )

        # 再重新計算父任務
        _recalc_parent_chain_in_snapshot(project_id, task_id, snapshot_date_str)

    else:
        # 更新 DB
        doc = mongo.db["gantt_tasks"].find_one({"id": task_id, "project_id": project_id})
        if not doc:
            raise KeyError("Task not found")

        update_fields = {}

        if data.get("text") is not None:
            update_fields["text"] = data["text"]

        if progress is not None:
            update_fields["progress"] = _normalize_progress(progress)

        if parent_id is not None:
            update_fields["parent_id"] = parent_id
        if depends is not None:
            update_fields["depends"] = depends

        old_start_str = doc.get("start_date", "")
        old_end_str = doc.get("end_date", "")
        old_start_dt = _parse_date_str(old_start_str, "2025-01-01")
        old_end_dt = _parse_date_str(old_end_str, None)

        if start_date_str or end_date_str or duration is not None:
            start_dt = old_start_dt
            end_dt = old_end_dt if old_end_dt else (old_start_dt + timedelta(days=1))

            if start_date_str:
                start_dt = _parse_date_str(start_date_str, "2025-01-01")
            if end_date_str:
                end_dt = _parse_date_str(end_date_str, None)
                if end_dt is None:
                    end_dt = start_dt + timedelta(days=1)
            elif duration is not None:
                end_dt = start_dt + timedelta(days=duration - 1)

            if end_dt < start_dt:
                end_dt = start_dt + timedelta(days=1)

            # 若 type=milestone => 令 start==end
            the_type = task_type or doc.get("type", "task")
            if the_type == "milestone":
                end_dt = start_dt

            update_fields["start_date"] = start_dt.date().isoformat()
            update_fields["end_date"] = end_dt.date().isoformat()

        if task_type:
            update_fields["type"] = task_type
            if task_type == "milestone":
                sdt = _parse_date_str(update_fields.get("start_date") or old_start_str, "2025-01-01")
                update_fields["end_date"] = sdt.date().isoformat()

        update_fields["updated_at"] = datetime.now()

        if update_fields:
            mongo.db["gantt_tasks"].update_one(
                {"id": task_id, "project_id": project_id},
                {"$set": update_fields}
            )

        # 重新計算父任務
        _recalc_parent_chain_in_db(project_id, task_id)


def delete_gantt_task(project_id: int, task_id: int, snapshot_date_str: str = ""):
    """
    刪除任務；若 snapshot_date_str 有值 => 在 snapshot 中刪
             否則在 DB 中刪
    """
    if snapshot_date_str:
        snap = mongo.db["gantt_snapshots"].find_one({
            "project_id": project_id,
            "snapshot_date": snapshot_date_str
        })
        if not snap:
            raise KeyError("Snapshot not found")

        tasks_list = snap.get("tasks", [])
        new_tasks_list = []
        deleted = False

        for t in tasks_list:
            if t["id"] == task_id:
                deleted = True
            else:
                new_tasks_list.append(t)

        if not deleted:
            raise KeyError("Task not found")

        # 寫回 snapshot
        mongo.db["gantt_snapshots"].update_one(
            {"_id": snap["_id"]},
            {"$set": {"tasks": new_tasks_list}}
        )

        # 父任務重新計算
        _recalc_parent_chain_in_snapshot(project_id, task_id, snapshot_date_str)

    else:
        result = mongo.db["gantt_tasks"].delete_one({
            "id": task_id,
            "project_id": project_id
        })
        if result.deleted_count == 0:
            raise KeyError("Task not found")

        # 父任務重新計算
        _recalc_parent_chain_in_db(project_id, task_id)


def _format_task_doc(doc):
    """
    將資料庫中的 task doc 格式化成前端需要的欄位結構。
    """
    if "id" not in doc:
        return None  # 理論上已在 DB 內確定都有 id
    return {
        "id": doc["id"],
        "text": doc.get("text", ""),
        "start_date": doc.get("start_date", ""),
        "end_date": doc.get("end_date", ""),
        "progress": doc.get("progress", 0.0),
        "parent_id": doc.get("parent_id"),
        "depends": doc.get("depends", []),
        "duration": _calc_duration(doc.get("start_date"), doc.get("end_date")),
        "type": doc.get("type", "task"),  # 預設是 "task" 以相容舊資料
    }


def _calc_duration(start_date_iso, end_date_iso):
    if not start_date_iso or not end_date_iso:
        return 1
    try:
        sdt = datetime.strptime(start_date_iso, "%Y-%m-%d")
        edt = datetime.strptime(end_date_iso, "%Y-%m-%d")
    except ValueError:
        return 1
    diff = (edt - sdt).days + 1
    if diff < 1:
        return 1
    return diff


# --------------------------------------------------------------------------
# 版本快照 (gantt_snapshots) ...
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
    建立該日期的快照(若已存在則擲錯)。
    """
    exists = mongo.db["gantt_snapshots"].find_one({
        "project_id": project_id,
        "snapshot_date": snap_date.isoformat()
    })
    if exists:
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


def update_gantt_snapshot(project_id: int, snapshot_date_str: str, new_tasks: list) -> bool:
    filter_ = {
        "project_id": project_id,
        "snapshot_date": snapshot_date_str
    }
    existing = mongo.db["gantt_snapshots"].find_one(filter_)
    if not existing:
        return False

    update_data = {
        "tasks": new_tasks,
        "updated_at": datetime.now()
    }
    mongo.db["gantt_snapshots"].update_one(filter_, {"$set": update_data})
    return True


def delete_gantt_snapshot(project_id: int, snapshot_date_str: str) -> bool:
    filter_ = {
        "project_id": project_id,
        "snapshot_date": snapshot_date_str
    }
    result = mongo.db["gantt_snapshots"].delete_one(filter_)
    return (result.deleted_count > 0)


# --------------------------------------------------------------------------
# 假日 & 工作日設定 (gantt_holidays) ...
# --------------------------------------------------------------------------

def get_holiday_settings(project_id: int) -> Optional[dict]:
    doc = mongo.db["gantt_holidays"].find_one({"project_id": project_id})
    return doc


def update_holiday_settings(project_id: int, data: Dict[str, Any]):
    filter_ = {"project_id": project_id}
    update_data = {
        "project_id": project_id,
        "holidays": data.get("holidays", []),
        "workdays_per_week": data.get("workdays_per_week", 5),
        "workday_weekdays": data.get("workday_weekdays", []),
        "special_workdays": data.get("special_workdays", []),
        "updated_at": datetime.now()
    }
    mongo.db["gantt_holidays"].update_one(
        filter_,
        {"$set": update_data},
        upsert=True
    )


# --------------------------------------------------------------------------
# 「父任務自動計算」的輔助函式
# --------------------------------------------------------------------------

def _recalc_parent_chain_in_db(project_id: int, changed_task_id: int):
    """
    從 changed_task_id 開始，向上遞歸更新父任務(start_date, end_date, progress)。
    使用 gantt_tasks 集合。
    """
    coll = mongo.db["gantt_tasks"]

    # 先找到該任務
    changed_doc = coll.find_one({"project_id": project_id, "id": changed_task_id})
    if not changed_doc:
        # 可能是被刪除了
        pass

    # 逐層向上更新
    # 例如 BFS: 先找 changed_doc 的 parent, 再找 parent 的 parent...
    visited = set()
    current_parent_id = changed_doc["parent_id"] if changed_doc else None

    while current_parent_id:
        if current_parent_id in visited:
            # 避免環
            break
        visited.add(current_parent_id)

        parent_doc = coll.find_one({"project_id": project_id, "id": current_parent_id})
        if not parent_doc:
            break

        # 找出所有孩子
        children = list(coll.find({"project_id": project_id, "parent_id": current_parent_id}))

        new_start, new_end, new_progress = _calc_parent_fields(children, parent_doc.get("type", "task"))
        coll.update_one(
            {"_id": parent_doc["_id"]},
            {"$set": {
                "start_date": new_start.isoformat(),
                "end_date": new_end.isoformat(),
                "progress": new_progress,
                "updated_at": datetime.now()
            }}
        )
        current_parent_id = parent_doc.get("parent_id")


def _recalc_parent_chain_in_snapshot(project_id: int, changed_task_id: int, snapshot_date: str):
    """
    與上面類似，但針對 snapshot 裡的 tasks array (in-memory)。
    """
    snap = mongo.db["gantt_snapshots"].find_one({
        "project_id": project_id,
        "snapshot_date": snapshot_date
    })
    if not snap:
        return
    tasks_list = snap.get("tasks", [])
    # 先找 changed task
    changed_doc = None
    for t in tasks_list:
        if t["id"] == changed_task_id:
            changed_doc = t
            break

    visited = set()
    current_parent_id = changed_doc["parent_id"] if changed_doc else None

    while current_parent_id:
        if current_parent_id in visited:
            break
        visited.add(current_parent_id)

        parent_task = None
        for t in tasks_list:
            if t["id"] == current_parent_id:
                parent_task = t
                break

        if not parent_task:
            break

        # 找出所有孩子
        children = [c for c in tasks_list if c.get("parent_id") == current_parent_id]

        new_start, new_end, new_progress = _calc_parent_fields(children, parent_task.get("type", "task"))
        parent_task["start_date"] = new_start.isoformat()
        parent_task["end_date"] = new_end.isoformat()
        parent_task["progress"] = new_progress
        parent_task["updated_at"] = datetime.now()

        current_parent_id = parent_task.get("parent_id")

    # 最後寫回 DB
    mongo.db["gantt_snapshots"].update_one(
        {"_id": snap["_id"]},
        {"$set": {"tasks": tasks_list}}
    )


def _calc_parent_fields(child_tasks: List[dict], parent_type: str):
    """
    給定所有子任務 (child_tasks)，計算父任務的 start_date, end_date, progress.
    - start_date = min( child.start )
    - end_date = max( child.end )
    - progress = ( 所有子任務 progress 的「平均」 ) (亦可改成加權平均)
    - 若 parent_type == "milestone"，強制 start_date=end_date
    """
    if not child_tasks:
        # 沒小孩 => 父任務可能是空殼 => 預設 progress=0, start/end=今日
        today = datetime.today().date()
        return (today, today, 0.0)

    min_start = None
    max_end = None
    total_progress = 0.0
    for c in child_tasks:
        s = _parse_date_str(c.get("start_date", ""), "2025-01-01")
        e = _parse_date_str(c.get("end_date", ""), "2025-01-02")
        p = c.get("progress", 0.0)
        if min_start is None or s < min_start:
            min_start = s
        if max_end is None or e > max_end:
            max_end = e
        total_progress += float(p)

    avg_progress = total_progress / len(child_tasks)
    if avg_progress < 0:
        avg_progress = 0
    if avg_progress > 1:
        avg_progress = 1.0

    if parent_type == "milestone":
        # 強制同一天
        if min_start and max_end:
            # 就以min_start為準
            return (min_start.date(), min_start.date(), avg_progress)
        else:
            today = datetime.today().date()
            return (today, today, avg_progress)

    # 一般( project / task )
    if min_start is None:
        min_start = datetime.today()
    if max_end is None:
        max_end = min_start
    return (min_start.date(), max_end.date(), avg_progress)


# --------------------------------------------------------------------------
# 重新分配任務ID
# --------------------------------------------------------------------------

def reassign_task_ids(project_id: int, snapshot_date_str: str = ""):
    """
    將所有 (當前最新 or 指定snapshot) 之 tasks 重新分配 ID。
    重新分配時，需要保持依賴關係與父子關係的結構不變。
      - parent_id / depends 裡的 id 也要跟著改。
    從1開始連號，建議依照「無 parent 的排在前面(可能有多個樹根)，再 BFS or DFS 排子」。
    """
    if snapshot_date_str:
        snap = mongo.db["gantt_snapshots"].find_one({
            "project_id": project_id,
            "snapshot_date": snapshot_date_str
        })
        if not snap:
            raise ValueError(f"Snapshot not found for {snapshot_date_str}")
        tasks_list = snap.get("tasks", [])
        new_tasks_list = _reassign_ids_in_memory(tasks_list)
        # 寫回
        mongo.db["gantt_snapshots"].update_one(
            {"_id": snap["_id"]},
            {"$set": {"tasks": new_tasks_list}}
        )
    else:
        # 從 DB 讀取
        tasks_cursor = mongo.db["gantt_tasks"].find({"project_id": project_id})
        tasks_list = list(tasks_cursor)
        if not tasks_list:
            return  # no tasks, nothing to do

        new_tasks_list = _reassign_ids_in_memory(tasks_list)
        # 先清空後再插入? 或者update?
        # 最完美方式：為避免刪除插入後 counters 出問題，
        # 這裡直接一筆筆 update 也行。不過最簡單安全做法就是「整個 mapping」後逐筆 update。
        # new_tasks_list只是「doc + new_id, new_depends, new_parent_id」。我們只更新 id/depends/parent_id。
        # 其餘欄位不變。
        id_map = {}  # old_id -> new_id
        for d in new_tasks_list:
            id_map[d["_original_id"]] = d["id"]

        for new_doc in new_tasks_list:
            # 依 new_doc["id"], new_doc["depends"], new_doc["parent_id"] 去 update
            old_id = new_doc["_original_id"]
            update_fields = {
                "id": new_doc["id"],
                "parent_id": new_doc.get("parent_id"),
                "depends": new_doc.get("depends", [])
            }
            mongo.db["gantt_tasks"].update_one(
                {"project_id": project_id, "id": old_id},
                {"$set": update_fields}
            )


def _reassign_ids_in_memory(tasks_list: List[dict]) -> List[dict]:
    """
    將 tasks_list (array of dict) 重新分配 id, parent_id, depends 等。
    1) 找出所有無 parent 的作為 root
    2) BFS or DFS 順序依序分配新 ID
    3) 需維護 old_id => new_id map，套用到 depends & parent_id
    4) 回傳新的 tasks_list(帶有新的 id/depends/parent_id)
       其餘欄位不變。
    """
    # 先複製
    cloned = []
    for t in tasks_list:
        cloned.append(dict(t))  # shallow copy

    # old_id => doc
    doc_by_id = {doc["id"]: doc for doc in cloned}
    # adjacency => parent -> list of children
    children_map = {}
    for d in cloned:
        pid = d.get("parent_id")
        if pid not in children_map:
            children_map[pid] = []
        children_map[pid].append(d)

    # 找出 roots => parent_id 不存在或 None
    roots = [d for d in cloned if not d.get("parent_id")]

    queue = []
    for r in roots:
        queue.append(r)

    old_to_new = {}
    new_id_counter = 1

    result_order = []

    while queue:
        current = queue.pop(0)
        old_id = current["id"]

        # 指派新 id
        assigned_id = new_id_counter
        new_id_counter += 1
        old_to_new[old_id] = assigned_id

        result_order.append(current)

        # 把孩子放到 queue
        cid_list = children_map.get(old_id, [])
        # 這邊可根據自己想要的排序(例如按原本id排序)
        cid_list = sorted(cid_list, key=lambda x: x["id"])
        for cdoc in cid_list:
            queue.append(cdoc)

    # 套用到 cloned
    for doc in result_order:
        old_id = doc["id"]
        doc["_original_id"] = old_id
        doc["id"] = old_to_new[old_id]
        # parent_id
        if doc.get("parent_id"):
            doc["parent_id"] = old_to_new[doc["parent_id"]]
        # depends
        new_depends = []
        for dep in doc.get("depends", []):
            if dep in old_to_new:
                new_depends.append(old_to_new[dep])
        doc["depends"] = new_depends

    return result_order


# --------------------------------------------------------------------------
# 工具函式
# --------------------------------------------------------------------------

def _parse_date_str(date_str: str, default_date_str: Optional[str]) -> Optional[datetime]:
    """
    將 'YYYY-MM-DD' parse 成 datetime(YYYY,MM,DD) (無時間)
    若失敗或空 => 若 default_date_str 不為 None 就用 default_date_str; 否則回傳 None
    """
    if not date_str:
        if default_date_str is not None:
            return datetime.strptime(default_date_str, "%Y-%m-%d")
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        if default_date_str is not None:
            return datetime.strptime(default_date_str, "%Y-%m-%d")
        return None


def _normalize_progress(progress):
    # 確保介於 0 ~ 1
    try:
        p = float(progress)
    except:
        p = 0.0
    if math.isnan(p) or p < 0:
        p = 0.0
    if p > 1:
        p = 1.0
    return p
