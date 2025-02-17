# backend/site_diary/routes.py

import traceback
import logging
from flask import Blueprint, request, jsonify, send_file, Response, abort, current_app
from datetime import datetime
from urllib.parse import quote
import os
import tempfile
import shutil
import zipfile

from backend.db import mongo, get_next_sequence, to_iso_date, to_iso_datetime
logger = logging.getLogger(__name__)

site_diary_bp = Blueprint('site_diary_bp', __name__)

# ★ 新增
import threading
import uuid
from backend.site_diary.progress_sse import progress_store
from backend.site_diary.services import (
    generate_diary_xlsx_only,
    generate_diary_pdf_sheet,
)


@site_diary_bp.route('/<int:project_id>/site_diaries', methods=['POST'])
def create_site_diary(project_id):
    logger.debug("create_site_diary() called, project_id=%s", project_id)

    project_doc = mongo.db.projects.find_one({"id": project_id})
    if not project_doc:
        logger.warning("Project not found: project_id=%s, returning 404", project_id)
        abort(404, description="Project not found")

    data = request.json or {}
    logger.debug("Received data for create_site_diary: %s", data)

    report_date_str = data.get('report_date')
    if report_date_str:
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d')
    else:
        report_date = None

    doc_id = get_next_sequence("site_diaries")

    workers_dict = data.get('workers', {})
    machines_dict = data.get('machines', {})
    staff_ids = data.get('staff_ids', [])

    site_diary_doc = {
        "id": doc_id,
        "project_id": project_id,
        "report_date": report_date,
        "weather_morning": data.get('weather_morning', ''),
        "weather_noon": data.get('weather_noon', ''),
        "day_count": data.get('day_count'),
        "summary": data.get('summary', ''),
        "workers": workers_dict,
        "machines": machines_dict,
        "staff_ids": staff_ids,
        "updated_at": datetime.now()
    }

    # 若未填 day_count，則自動計算
    if site_diary_doc["day_count"] is None:
        max_day = mongo.db.site_diaries.find(
            {"project_id": project_id, "day_count": {"$ne": None}},
            {"day_count": 1}
        ).sort("day_count", -1).limit(1)
        row = next(max_day, None)
        if row:
            site_diary_doc["day_count"] = row["day_count"] + 1
        else:
            site_diary_doc["day_count"] = 1

    mongo.db.site_diaries.insert_one(site_diary_doc)
    logger.info("Site diary created: diary_id=%s, day_count=%s", doc_id, site_diary_doc["day_count"])

    return jsonify({
        "message": "Site diary created",
        "site_diary_id": doc_id,
        "day_count": site_diary_doc["day_count"]
    }), 201


@site_diary_bp.route('/<int:project_id>/site_diaries', methods=['GET'])
def get_site_diaries(project_id):
    """
    可傳 query param:
      - sort_by=(report_date|day_count|updated_at|...) 預設 report_date
      - sort_order=(1|-1) 預設 1 (ASC)
    """
    logger.debug("get_site_diaries() called, project_id=%s", project_id)

    project_doc = mongo.db.projects.find_one({"id": project_id})
    if not project_doc:
        logger.warning("Project not found: project_id=%s, returning 404", project_id)
        abort(404, description="Project not found")

    sort_by = request.args.get('sort_by', 'report_date').strip() or 'report_date'
    sort_order_str = request.args.get('sort_order', '1').strip()
    try:
        sort_order = int(sort_order_str)
        if sort_order not in (1, -1):
            sort_order = 1
    except ValueError:
        sort_order = 1

    cursor = mongo.db.site_diaries.find({"project_id": project_id}).sort([(sort_by, sort_order)])
    results = []

    for sd in cursor:
        worker_list = []
        for w_type, qty in sd.get("workers", {}).items():
            worker_list.append({"type": w_type, "quantity": qty})
        machine_list = []
        for m_type, qty in sd.get("machines", {}).items():
            machine_list.append({"type": m_type, "quantity": qty})
        staff_list = []
        staff_ids = sd.get("staff_ids", [])
        if staff_ids:
            staff_docs = list(mongo.db.staff.find({"id": {"$in": staff_ids}}))
            staff_map = {s["id"]: s for s in staff_docs}
            for sid in staff_ids:
                st_doc = staff_map.get(sid)
                if st_doc:
                    staff_list.append({
                        "id": st_doc["id"],
                        "name": st_doc.get("name"),
                        "role": st_doc.get("role")
                    })

        results.append({
            "id": sd["id"],
            "report_date": to_iso_date(sd.get("report_date")),
            "weather_morning": sd.get("weather_morning", ""),
            "weather_noon": sd.get("weather_noon", ""),
            "day_count": sd.get("day_count"),
            "summary": sd.get("summary", ""),
            "workers": worker_list,
            "machines": machine_list,
            "staffs": staff_list,
            "updated_at": to_iso_datetime(sd.get("updated_at"))
        })

    logger.debug("Returning %d diaries for project_id=%s", len(results), project_id)
    return jsonify(results), 200


@site_diary_bp.route('/<int:project_id>/site_diaries/<int:diary_id>', methods=['PUT'])
def update_site_diary(project_id, diary_id):
    logger.debug("update_site_diary() called, project_id=%s, diary_id=%s", project_id, diary_id)

    site_diary = mongo.db.site_diaries.find_one({"project_id": project_id, "id": diary_id})
    if not site_diary:
        logger.warning("SiteDiary not found: project_id=%s, diary_id=%s", project_id, diary_id)
        abort(404, description="SiteDiary not found")

    data = request.json or {}
    logger.debug("Received data for update_site_diary: %s", data)

    update_fields = {}
    report_date_str = data.get('report_date')
    if report_date_str == "":
        update_fields["report_date"] = None
    elif report_date_str:
        update_fields["report_date"] = datetime.strptime(report_date_str, '%Y-%m-%d')

    if "weather_morning" in data:
        update_fields["weather_morning"] = data["weather_morning"]
    if "weather_noon" in data:
        update_fields["weather_noon"] = data["weather_noon"]
    if "day_count" in data:
        update_fields["day_count"] = data["day_count"]
    if "summary" in data:
        update_fields["summary"] = data["summary"]
    if "workers" in data:
        update_fields["workers"] = data["workers"]
    if "machines" in data:
        update_fields["machines"] = data["machines"]
    if "staff_ids" in data:
        update_fields["staff_ids"] = data["staff_ids"]

    # 若前端沒傳 day_count 或給 null，就繼續自動計算
    if ("day_count" not in data) or (data["day_count"] is None):
        max_day = mongo.db.site_diaries.find(
            {"project_id": project_id, "day_count": {"$ne": None}},
            {"day_count": 1}
        ).sort("day_count", -1).limit(1)
        row = next(max_day, None)
        if row:
            update_fields["day_count"] = row["day_count"] + 1
        else:
            update_fields["day_count"] = 1

    update_fields["updated_at"] = datetime.now()

    if update_fields:
        mongo.db.site_diaries.update_one(
            {"project_id": project_id, "id": diary_id},
            {"$set": update_fields}
        )
        logger.info("Site diary updated: project_id=%s, diary_id=%s, fields=%s",
                    project_id, diary_id, list(update_fields.keys()))
    else:
        logger.debug("No fields updated.")

    return jsonify({
        "message": "Site diary updated",
        "day_count": update_fields.get("day_count", site_diary.get("day_count"))
    }), 200


@site_diary_bp.route('/<int:project_id>/site_diaries/<int:diary_id>', methods=['DELETE'])
def delete_site_diary(project_id, diary_id):
    logger.debug("delete_site_diary() called, project_id=%s, diary_id=%s", project_id, diary_id)

    result = mongo.db.site_diaries.delete_one({"project_id": project_id, "id": diary_id})
    if result.deleted_count == 0:
        logger.warning("Site diary not found, cannot delete: project_id=%s, diary_id=%s", project_id, diary_id)
        abort(404, description="Site diary not found")

    logger.info("Site diary deleted: project_id=%s, diary_id=%s", project_id, diary_id)
    return jsonify({"message": "Site diary deleted"}), 200


@site_diary_bp.route('/<int:project_id>/site_diaries/<int:diary_id>/download_report', methods=['GET'])
def download_site_diary_report(project_id, diary_id):
    """
    依照 ?file= 參數決定下載哪個檔案 (xlsx, sheet1, sheet2)。
    若帶有冒號 (例如 sheet1:1)，則自動擷取冒號前部分避免錯誤。
    """
    logger.debug("download_site_diary_report() called, project_id=%s, diary_id=%s", project_id, diary_id)

    site_diary = mongo.db.site_diaries.find_one({"project_id": project_id, "id": diary_id})
    if not site_diary:
        logger.warning("SiteDiary not found, returning 404: project_id=%s, diary_id=%s", project_id, diary_id)
        return jsonify({"error": "SiteDiary not found"}), 404

    file_type_param = request.args.get('file', 'xlsx')
    main_file_type = file_type_param.split(':')[0].strip()
    logger.debug("Raw file param=%r => main_file_type=%r", file_type_param, main_file_type)

    if site_diary.get("report_date"):
        date_str = site_diary["report_date"].strftime("%Y%m%d")
    else:
        date_str = "noDate"

    try:
        if main_file_type == 'xlsx':
            from backend.site_diary.services import generate_diary_xlsx_only
            xlsx_path = generate_diary_xlsx_only(site_diary)
            download_name = f"{date_str}_daily_report.xlsx"
            logger.info("Returning XLSX report: %s", download_name)
            return _send_file_with_utf8_filename(xlsx_path, download_name)

        elif main_file_type in ('sheet1', 'sheet2'):
            from backend.site_diary.services import generate_diary_pdf_sheet
            pdf_path = generate_diary_pdf_sheet(site_diary, sheet_name=main_file_type)
            if main_file_type == 'sheet1':
                download_name = f"{date_str}每日施工進度報告表.pdf"
                ascii_fallback = f"{date_str}_daily_report.pdf"
            else:
                download_name = f"{date_str}施工人員紀錄表.pdf"
                ascii_fallback = f"{date_str}_worker_log.pdf"

            logger.info("Returning PDF report: %s (sheet=%s)", download_name, main_file_type)
            return _send_file_with_utf8_filename(pdf_path, download_name, ascii_fallback)

        else:
            logger.warning("Unknown file type: %r => returning 400", file_type_param)
            return jsonify({"error": f"Unknown file type '{file_type_param}'"}), 400

    except FileNotFoundError as e:
        logger.error("FileNotFoundError: %s", e, exc_info=True)
        return jsonify({"error": f"FileNotFoundError: {e}"}), 404
    except PermissionError as e:
        logger.error("PermissionError: %s", e, exc_info=True)
        return jsonify({"error": f"PermissionError: {e}"}), 403
    except RuntimeError as e:
        logger.error("RuntimeError: %s", e, exc_info=True)
        return jsonify({"error": f"RuntimeError: {e}"}), 500
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("Unhandled exception during download_site_diary_report:")
        return jsonify({"error": str(e), "traceback": tb}), 500


def _send_file_with_utf8_filename(file_path: str, download_name: str, ascii_fallback: str = None) -> Response:
    """
    統一版本：可接收 2~3 個參數。
      file_path:      實際檔案路徑
      download_name:  想顯示給使用者下載的檔名(可能含中文)
      ascii_fallback: 若瀏覽器不支援 RFC 5987 filename*=UTF-8 用的備用檔名
    """
    from flask import send_file
    from urllib.parse import quote

    response = send_file(file_path, as_attachment=True)

    if not ascii_fallback:
        # 若呼叫者沒傳入 ascii_fallback 就自動生成簡易檔名
        ascii_fallback = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in download_name)

    utf8_quoted = quote(download_name, encoding="utf-8")
    disposition_value = (
        f'attachment; filename="{ascii_fallback}"; '
        f'filename*=UTF-8\'\'{utf8_quoted}'
    )
    safe_disposition = disposition_value.encode('latin-1', 'replace').decode('latin-1')
    response.headers["Content-Disposition"] = safe_disposition

    return response


@site_diary_bp.route('/<int:project_id>/site_diaries/last', methods=['GET'])
def get_last_site_diary(project_id):
    """
    取得該 project 最後一筆日報(依報表日期 desc, id desc)
    """
    logger.debug("get_last_site_diary() called, project_id=%s", project_id)

    project_doc = mongo.db.projects.find_one({"id": project_id})
    if not project_doc:
        logger.debug("Project not found for last site diary: project_id=%s", project_id)
        return jsonify({}), 200

    last_sd = mongo.db.site_diaries.find({"project_id": project_id}).sort("id", -1).limit(1)
    last_diary = next(last_sd, None)
    if not last_diary:
        logger.debug("No diaries found for project_id=%s", project_id)
        return jsonify({}), 200

    worker_list = [{"id": i, "type": w_type, "quantity": qty}
                   for i, (w_type, qty) in enumerate(last_diary.get("workers", {}).items(), start=1)]
    machine_list = [{"id": i, "type": m_type, "quantity": qty}
                    for i, (m_type, qty) in enumerate(last_diary.get("machines", {}).items(), start=1)]

    staff_list = []
    staff_ids = last_diary.get("staff_ids", [])
    if staff_ids:
        staff_docs = list(mongo.db.staff.find({"id": {"$in": staff_ids}}))
        staff_map = {s["id"]: s for s in staff_docs}
        for sid in staff_ids:
            st_doc = staff_map.get(sid)
            if st_doc:
                staff_list.append({
                    "id": st_doc["id"],
                    "name": st_doc.get("name"),
                    "role": st_doc.get("role")
                })

    result = {
        "id": last_diary["id"],
        "report_date": to_iso_date(last_diary.get("report_date")),
        "weather_morning": last_diary.get("weather_morning", ""),
        "weather_noon": last_diary.get("weather_noon", ""),
        "day_count": last_diary.get("day_count"),
        "summary": last_diary.get("summary", ""),
        "workers": worker_list,
        "machines": machine_list,
        "staffs": staff_list
    }

    logger.debug("Returning last diary for project_id=%s => diary_id=%s", project_id, last_diary["id"])
    return jsonify(result), 200


# ============================================================================
# [多筆下載 - 同步版] (原本就有) - 量小可直接使用
# ============================================================================
@site_diary_bp.route('/<int:project_id>/site_diaries/multi_download', methods=['POST'])
def multi_download_site_diary(project_id):
    """
    多筆下載 - 同步版。
    數量較大時，若處理時間過長可能導致 Gunicorn timeout。
    """
    data = request.json or {}
    diary_ids = data.get("diary_ids", [])
    file_type = data.get("file_type", "xlsx")
    logger.info("multi_download_site_diary called => diary_ids=%s, file_type=%s", diary_ids, file_type)

    if not diary_ids:
        return jsonify({"error": "No diary_ids provided"}), 400

    temp_dir = tempfile.mkdtemp(prefix="multi_diary_")
    zip_filename = f"multiple_diaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(temp_dir, zip_filename)

    used_names = set()

    from backend.site_diary.services import generate_diary_xlsx_only, generate_diary_pdf_sheet

    def ensure_unique_filename(base_name, used):
        if base_name not in used:
            used.add(base_name)
            return base_name
        base, ext = os.path.splitext(base_name)
        i = 2
        new_name = f"{base}_{i}{ext}"
        while new_name in used:
            i += 1
            new_name = f"{base}_{i}{ext}"
        used.add(new_name)
        return new_name

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for d_id in diary_ids:
                diary_doc = mongo.db.site_diaries.find_one({"project_id": project_id, "id": d_id})
                if not diary_doc:
                    logger.warning("Diary not found or belongs to another project: id=%s", d_id)
                    continue

                # 依 file_type 產檔
                if diary_doc.get("report_date"):
                    date_prefix = diary_doc["report_date"].strftime("%Y%m%d")
                else:
                    date_prefix = "noDate"

                if file_type == 'xlsx':
                    xlsx_path = generate_diary_xlsx_only(diary_doc)
                    base_name = f"{date_prefix}_daily_report.xlsx"
                    final_name = ensure_unique_filename(base_name, used_names)
                    zf.write(xlsx_path, arcname=final_name)

                elif file_type in ('sheet1', 'sheet2'):
                    pdf_path = generate_diary_pdf_sheet(diary_doc, sheet_name=file_type)
                    if file_type == 'sheet1':
                        base_name = f"{date_prefix}_daily_report.pdf"
                    else:
                        base_name = f"{date_prefix}_worker_log.pdf"
                    final_name = ensure_unique_filename(base_name, used_names)
                    zf.write(pdf_path, arcname=final_name)

                else:
                    logger.warning("Skipping unknown file_type=%s for diary_id=%s", file_type, d_id)
                    continue

        logger.info("multi_download => created ZIP: %s", zip_path)
        return _send_file_with_utf8_filename(zip_path, zip_filename)

    except Exception as exc:
        logger.exception("multi_download_site_diary() exception: ")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": str(exc)}), 500


# ============================================================================
# [多筆下載 - 非同步版 + SSE進度]  ---------------------------------------------
# ============================================================================

@site_diary_bp.route('/<int:project_id>/site_diaries/multi_download_async', methods=['POST'])
def multi_download_site_diary_async(project_id):
    """
    非同步版 + SSE:
      1) 前端 POST {diary_ids, file_type} 進來
      2) 後端產生 job_id, 用執行緒背景處理, 立即回傳 {"job_id": ...}
      3) 前端用 SSE(/api/progress-sse/<job_id>) 監看進度
      4) 完成後 (status=done), 再呼叫 multi_download_result 取得最後ZIP
    """
    data = request.json or {}
    diary_ids = data.get("diary_ids", [])
    file_type = data.get("file_type", "xlsx")
    if not diary_ids:
        return jsonify({"error": "No diary_ids provided"}), 400

    project_doc = mongo.db.projects.find_one({"id": project_id})
    if not project_doc:
        abort(404, description="Project not found")

    job_id = str(uuid.uuid4())
    progress_store[job_id] = {
        "status": "in_progress",
        "progress": 0,
        "file_path": None,
        "error_msg": ""
    }

    # ★ 關鍵修正：在啟動背景執行緒前，先抓取「當前 app 物件」並傳進去
    appctx = current_app._get_current_object()

    t = threading.Thread(
        target=_background_zip_generation,
        args=(appctx, job_id, project_id, diary_ids, file_type),
        daemon=True
    )
    t.start()

    return jsonify({"job_id": job_id}), 200


def _background_zip_generation(app, job_id, project_id, diary_ids, file_type):
    """
    在背景執行的打包函式，會更新 progress_store[job_id] 中的 progress/status/file_path

    ★ 使用 with app.app_context(): 避免 'Working outside of application context' 錯誤
    """
    try:
        with app.app_context():
            total = len(diary_ids)
            if total == 0:
                raise ValueError("No diaries specified.")

            temp_dir = tempfile.mkdtemp(prefix="multi_diary_")
            zip_filename = f"multiple_diaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            used_names = set()

            from backend.site_diary.services import generate_diary_xlsx_only, generate_diary_pdf_sheet

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for idx, d_id in enumerate(diary_ids, start=1):
                    # 更新進度
                    progress_store[job_id]["progress"] = int(idx * 100 / total)

                    diary_doc = mongo.db.site_diaries.find_one({"project_id": project_id, "id": d_id})
                    if not diary_doc:
                        continue

                    if diary_doc.get("report_date"):
                        date_str = diary_doc["report_date"].strftime("%Y%m%d")
                    else:
                        date_str = "noDate"

                    if file_type == 'xlsx':
                        path_ = generate_diary_xlsx_only(diary_doc)
                        base_name = f"{date_str}_daily_report.xlsx"
                    elif file_type == 'sheet1':
                        path_ = generate_diary_pdf_sheet(diary_doc, sheet_name='sheet1')
                        base_name = f"{date_str}_daily_report.pdf"
                    elif file_type == 'sheet2':
                        path_ = generate_diary_pdf_sheet(diary_doc, sheet_name='sheet2')
                        base_name = f"{date_str}_worker_log.pdf"
                    else:
                        continue

                    final_name = _ensure_unique_filename(base_name, used_names)
                    zf.write(path_, arcname=final_name)

            progress_store[job_id]["status"] = "done"
            progress_store[job_id]["file_path"] = zip_path

    except Exception as e:
        progress_store[job_id]["status"] = "error"
        progress_store[job_id]["error_msg"] = str(e)
        logger.exception("background_zip_generation error:")
    finally:
        # 確保結束時強制 progress=100
        progress_store[job_id]["progress"] = 100


def _ensure_unique_filename(base_name, used_names):
    if base_name not in used_names:
        used_names.add(base_name)
        return base_name
    base, ext = os.path.splitext(base_name)
    i = 2
    new_name = f"{base}_{i}{ext}"
    while new_name in used_names:
        i += 1
        new_name = f"{base}_{i}{ext}"
    used_names.add(new_name)
    return new_name


@site_diary_bp.route('/<int:project_id>/site_diaries/multi_download_result', methods=['GET'])
def multi_download_result(project_id):
    """
    當 SSE 監測到 status=done 後，前端呼叫:
       GET /api/projects/<project_id>/site_diaries/multi_download_result?job_id=xxx
    以實際拿到 ZIP 檔。
    """
    job_id = request.args.get('job_id')
    if not job_id:
        return jsonify({"error": "Missing job_id"}), 400

    job_info = progress_store.get(job_id)
    if not job_info:
        return jsonify({"error": "Invalid job_id"}), 400

    if job_info["status"] != "done":
        return jsonify({"error": f"Job not done. status={job_info['status']}"}), 400

    zip_path = job_info["file_path"]
    if not zip_path or not os.path.isfile(zip_path):
        return jsonify({"error": "File not found for this job."}), 404

    filename = os.path.basename(zip_path)
    return send_file(zip_path, as_attachment=True, download_name=filename)
