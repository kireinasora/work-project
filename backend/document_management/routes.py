# backend/document_management/routes.py

import logging
import os
import uuid
import zipfile
import tempfile
import threading
import time
from datetime import datetime

import gevent

from flask import Blueprint, request, jsonify, abort, Response, stream_with_context, send_file, current_app
from bson.objectid import ObjectId

from backend.db import mongo, get_next_sequence
from backend.document_management.services import (
    create_document,
    get_document,
    update_document,
    delete_document,
    list_documents,
    add_document_version,
    get_document_versions,
    generate_diary_xlsx_only,
    generate_diary_pdf_sheet
)

document_bp = Blueprint("document_bp", __name__)
logger = logging.getLogger(__name__)

# -------------------- SSE Job store (用於多筆下載) --------------------
# ★ 新增 expires_at: time.time() + 1800 (半小時後過期)
progress_store = {}  # job_id -> {
#   "status":"in_progress"|"done"|"error",
#   "progress":..., "file_path":..., "error_msg":"",
#   "expires_at": float(timestamp)
# }

# =====================================================================
# 通用文件 CRUD
# =====================================================================

@document_bp.route("/", methods=["GET"])
def api_list_documents():
    """
    取得所有或篩選後的文件列表。
    可用 query param 例如:
      - ?project_id=123
      - ?doc_type=DAILY_REPORT / MAT / RFI / ...
    """
    project_id = request.args.get("project_id", "").strip()
    doc_type = request.args.get("doc_type", "").strip()

    try:
        docs = list_documents(project_id=project_id, doc_type=doc_type)
        return jsonify(docs), 200
    except Exception as ex:
        logger.exception("[DEBUG] api_list_documents error:")
        return jsonify({"error": str(ex)}), 500


@document_bp.route("/", methods=["POST"])
def api_create_document():
    """
    新增文件 (初始版本)
    body JSON:
      {
        "title": "...",
        "doc_type": "LETTER" | "MAT" | "DAILY_REPORT" | ...
        "project_id": 123,
        "description": "...",
        ...
      }
    """
    data = request.json or {}
    try:
        new_id = create_document(data)
        return jsonify({"message": "Document created", "document_id": str(new_id)}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as ex:
        logger.exception("[DEBUG] api_create_document error:")
        return jsonify({"error": str(ex)}), 500


@document_bp.route("/<doc_id>", methods=["GET"])
def api_get_document(doc_id):
    """
    取得單一文件與最新版本資訊
    """
    try:
        doc = get_document(doc_id)
        if not doc:
            abort(404, description="Document not found")
        return jsonify(doc), 200
    except Exception as ex:
        logger.exception("[DEBUG] api_get_document error:")
        return jsonify({"error": str(ex)}), 500


@document_bp.route("/<doc_id>", methods=["PUT"])
def api_update_document(doc_id):
    """
    更新文件的 metadata (不新增版本)。若要更新檔案需用 add version 方式。
    body JSON:
      {
        "title": "...",
        "description": "...",
        ...
      }
    """
    data = request.json or {}
    try:
        updated = update_document(doc_id, data)
        if not updated:
            abort(404, description="Document not found or no changes made")
        return jsonify({"message": "Document updated"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as ex:
        logger.exception("[DEBUG] api_update_document error:")
        return jsonify({"error": str(ex)}), 500


@document_bp.route("/<doc_id>", methods=["DELETE"])
def api_delete_document(doc_id):
    """
    刪除整個文件(及所有版本檔案)
    """
    try:
        deleted = delete_document(doc_id)
        if not deleted:
            abort(404, description="Document not found")
        return jsonify({"message": "Document deleted"}), 200
    except Exception as ex:
        logger.exception("[DEBUG] api_delete_document error:")
        return jsonify({"error": str(ex)}), 500


# ------------------------------------------------------
# 版本管理：新增一個「文件版本」(帶檔案上傳)
# ------------------------------------------------------

@document_bp.route("/<doc_id>/versions", methods=["POST"])
def api_add_document_version(doc_id):
    """
    新增一個版本 (可能包含上傳檔案到 S3)。
    body JSON:
      {
        "version_note": "...",
        "filename": "...",
        "base64_file": "...",
        ...
      }
    """
    data = request.json or {}
    try:
        ver_id = add_document_version(doc_id, data)
        return jsonify({"message": "Version added", "version_id": ver_id}), 201
    except FileNotFoundError as fex:
        return jsonify({"error": f"File not found: {fex}"}), 404
    except Exception as ex:
        logger.exception("[DEBUG] api_add_document_version error:")
        return jsonify({"error": str(ex)}), 500


@document_bp.route("/<doc_id>/versions", methods=["GET"])
def api_get_document_versions(doc_id):
    """
    取得某文件的所有版本列表
    """
    try:
        versions = get_document_versions(doc_id)
        return jsonify(versions), 200
    except Exception as ex:
        logger.exception("[DEBUG] api_get_document_versions error:")
        return jsonify({"error": str(ex)}), 500


# =====================================================================
#  以下為「日報 DAILY_REPORT」的整合 CRUD / 多筆下載 SSE 等
# =====================================================================

def _build_daily_report_query(project_id: int):
    """回傳針對 doc_type=DAILY_REPORT 的 query dict"""
    return {"project_id": project_id, "doc_type": "DAILY_REPORT"}


@document_bp.route("/daily-reports", methods=["GET"])
def list_daily_reports():
    """
    取得指定 project_id 的所有日報文件，並以 report_date(降冪)排序
      GET /api/documents/daily-reports?project_id=xxx
    """
    project_id = request.args.get("project_id", "")
    if not project_id.isdigit():
        return jsonify([]), 200
    pid = int(project_id)

    # 直接按 daily_report_data.report_date 進行排序 (descending)
    query = {
        "doc_type": "DAILY_REPORT",
        "project_id": pid
    }
    docs_cursor = mongo.db["documents"].find(query).sort("daily_report_data.report_date", -1)

    output = []
    for d in docs_cursor:
        dr = d.get("daily_report_data", {})
        item = {
            "doc_db_id": str(d["_id"]),              # documents表的 str(ObjectId)
            "id": d.get("daily_report_id"),          # 整數
            "report_date": dr.get("report_date") or "",
            "weather_morning": dr.get("weather_morning", ""),
            "weather_noon": dr.get("weather_noon", ""),
            "day_count": dr.get("day_count", None),
            "summary": dr.get("summary", ""),
            "staff_ids": dr.get("staff_ids", []),
            "workers": dr.get("workers", {}),
            "machines": dr.get("machines", {}),
        }
        uat = d.get("updated_at")
        if isinstance(uat, datetime):
            # 將原本 T 時區資訊移除，改成更易讀的格式
            item["updated_at"] = uat.strftime("%Y-%m-%d %H:%M:%S")
        else:
            item["updated_at"] = ""
        output.append(item)
    return jsonify(output), 200


@document_bp.route("/daily-reports", methods=["POST"])
def create_daily_report():
    """
    建立一筆日報 => 插入 documents 裏頭 doc_type=DAILY_REPORT
    body JSON 與舊 site_diary 相同
    """
    data = request.json or {}
    project_id = data.get("project_id")
    if not project_id:
        return jsonify({"error": "Missing project_id"}), 400
    try:
        new_report_id = get_next_sequence("daily_reports")

        doc_body = {
            "doc_type": "DAILY_REPORT",
            "project_id": project_id,
            "title": f"DailyReport #{new_report_id}",
            "description": f"Daily report for project {project_id}",
            "daily_report_id": new_report_id,
            "daily_report_data": {
                "report_date": data.get("report_date", ""),
                "weather_morning": data.get("weather_morning", ""),
                "weather_noon": data.get("weather_noon", ""),
                "day_count": data.get("day_count", None),
                "summary": data.get("summary", ""),
                "workers": data.get("workers", {}),
                "machines": data.get("machines", {}),
                "staff_ids": data.get("staff_ids", [])
            }
        }
        result_id = create_document(doc_body)
        return jsonify({
            "message": "Daily report created",
            "daily_report_id": new_report_id
        }), 201
    except Exception as ex:
        logger.exception("[DEBUG] create_daily_report error:")
        return jsonify({"error": str(ex)}), 500


@document_bp.route("/daily-reports/<int:report_id>", methods=["PUT"])
def update_daily_report(report_id):
    """
    更新日報 => 尋找 doc_type=DAILY_REPORT & daily_report_id=report_id
    """
    data = request.json or {}
    project_id = data.get("project_id")
    if not project_id:
        return jsonify({"error": "Missing project_id"}), 400

    doc = mongo.db["documents"].find_one({
        "doc_type": "DAILY_REPORT",
        "daily_report_id": report_id,
        "project_id": int(project_id)
    })
    if not doc:
        abort(404, description="Daily report not found")

    dr_data = doc.get("daily_report_data", {})
    dr_data["report_date"] = data.get("report_date", "")
    dr_data["weather_morning"] = data.get("weather_morning", "")
    dr_data["weather_noon"] = data.get("weather_noon", "")
    dr_data["day_count"] = data.get("day_count", None)
    dr_data["summary"] = data.get("summary", "")
    dr_data["workers"] = data.get("workers", {})
    dr_data["machines"] = data.get("machines", {})
    dr_data["staff_ids"] = data.get("staff_ids", [])

    update_fields = {
        "daily_report_data": dr_data,
        "updated_at": datetime.now()
    }
    mongo.db["documents"].update_one({"_id": doc["_id"]}, {"$set": update_fields})
    return jsonify({"message": "Daily report updated"}), 200


@document_bp.route("/daily-reports/<int:report_id>", methods=["DELETE"])
def delete_daily_report(report_id):
    """
    刪除日報 => doc_type=DAILY_REPORT & daily_report_id=report_id
    """
    project_id = request.args.get("project_id", "")
    if not project_id.isdigit():
        abort(400, description="Missing or invalid project_id")

    doc = mongo.db["documents"].find_one({
        "doc_type": "DAILY_REPORT",
        "daily_report_id": report_id,
        "project_id": int(project_id)
    })
    if not doc:
        abort(404, "Daily report not found")

    doc_id = str(doc["_id"])
    ok = delete_document(doc_id)
    if not ok:
        abort(404, "Daily report not found (delete failed)")

    return jsonify({"message": "Daily report deleted"}), 200


# ===================================================================
# [單筆下載] - XLSX / PDF(sheet1) / PDF(sheet2)
# ===================================================================

@document_bp.route("/daily-report/<int:report_id>/download", methods=["GET"])
def download_single_daily_report(report_id):
    """
    單筆下載日報；query param: file_type=xlsx|sheet1|sheet2
    GET /api/documents/daily-report/<report_id>/download?project_id=xxx&file_type=xxx
    """
    project_id = request.args.get("project_id", "")
    file_type = request.args.get("file_type", "xlsx").strip()
    if not project_id.isdigit():
        abort(400, description="Invalid project_id")

    doc = mongo.db["documents"].find_one({
        "doc_type": "DAILY_REPORT",
        "daily_report_id": report_id,
        "project_id": int(project_id)
    })
    if not doc:
        abort(404, description="Daily report not found")

    dr_data = doc.get("daily_report_data", {})
    raw_date = dr_data.get("report_date", "")
    date_str_for_filename = raw_date.replace("-", "") if raw_date else "noDate"

    if file_type == "xlsx":
        out_path = generate_diary_xlsx_only(doc)
        download_name = f"{date_str_for_filename}_daily_report.xlsx"
    elif file_type == "sheet1":
        out_path = generate_diary_pdf_sheet(doc, sheet_name="sheet1")
        download_name = f"{date_str_for_filename}_daily_report.pdf"
    elif file_type == "sheet2":
        out_path = generate_diary_pdf_sheet(doc, sheet_name="sheet2")
        download_name = f"{date_str_for_filename}_worker_log.pdf"
    else:
        abort(400, description="Unsupported file_type")

    return send_file(out_path, as_attachment=True, download_name=download_name)


# ===================================================================
# [多筆下載 - SSE 版本] - 以 doc_type=DAILY_REPORT 多筆下載
# ===================================================================

@document_bp.route("/daily-report/multi_download_async", methods=["POST"])
def daily_report_multi_download_async():
    """
    非同步多筆下載 SSE:
      body JSON: { "project_id":123, "diary_ids":[...], "file_type":"xlsx|sheet1|sheet2" }
    回傳 { "job_id":... }
    前端再用 SSE(/api/documents/daily-report/progress-sse/<job_id>) 監聽
    完成後拿 /api/documents/daily-report/multi_download_result?job_id=xxx
    """
    data = request.json or {}
    project_id = data.get("project_id")
    diary_ids = data.get("diary_ids", [])
    file_type = data.get("file_type", "xlsx")

    if not project_id or not isinstance(diary_ids, list):
        return jsonify({"error": "Missing project_id or diary_ids"}), 400

    job_id = str(uuid.uuid4())
    # ★ 設定到期時間 (半小時後)
    expires_at = time.time() + 1800

    progress_store[job_id] = {
        "status": "in_progress",
        "progress": 0,
        "file_path": None,
        "error_msg": "",
        "expires_at": expires_at
    }

    try:
        flask_app = current_app._get_current_object()
    except Exception as e:
        logger.exception("[DEBUG] Failed to get current_app object:")
        return jsonify({"error": f"Cannot get Flask app object: {e}"}), 500

    t = threading.Thread(
        target=_background_zip_generation,
        args=(flask_app, job_id, project_id, diary_ids, file_type),
        daemon=True
    )
    t.start()

    return jsonify({"job_id": job_id}), 200


def _background_zip_generation(app, job_id, project_id, diary_ids, file_type):
    logger.debug(
        "[_background_zip_generation] Start job_id=%s project_id=%s diary_ids=%s file_type=%s",
        job_id, project_id, diary_ids, file_type
    )

    with app.app_context():
        from backend.document_management.services import (
            generate_diary_xlsx_only,
            generate_diary_pdf_sheet
        )
        try:
            total = len(diary_ids)
            if total == 0:
                raise ValueError("No diaries specified.")

            temp_dir = tempfile.mkdtemp(prefix="multi_daily_")
            zip_filename = f"multiple_diaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for idx, d_id in enumerate(diary_ids, start=1):
                    # 若該 job 已非 in_progress 狀態就結束
                    if progress_store[job_id]["status"] != "in_progress":
                        logger.debug("[DEBUG] Job %s no longer in progress, break the loop.", job_id)
                        return

                    progress_store[job_id]["progress"] = int(idx * 100 / total)

                    doc = mongo.db["documents"].find_one({
                        "doc_type": "DAILY_REPORT",
                        "daily_report_id": d_id,
                        "project_id": int(project_id)
                    })
                    if not doc:
                        logger.debug(f"[DEBUG] Diary ID={d_id} not found, skipping.")
                        continue

                    dr_data = doc.get("daily_report_data", {})
                    raw_date = dr_data.get("report_date", "")
                    date_str = raw_date.replace("-", "") if raw_date else f"ID{d_id}"

                    if file_type == 'xlsx':
                        path_ = generate_diary_xlsx_only(doc)
                        arcname_ = f"{date_str}_daily_report.xlsx"
                    elif file_type == 'sheet1':
                        path_ = generate_diary_pdf_sheet(doc, sheet_name='sheet1')
                        arcname_ = f"{date_str}_daily_report.pdf"
                    elif file_type == 'sheet2':
                        path_ = generate_diary_pdf_sheet(doc, sheet_name='sheet2')
                        arcname_ = f"{date_str}_worker_log.pdf"
                    else:
                        logger.error(f"[DEBUG] Unsupported file_type={file_type}, skipping this doc.")
                        continue

                    zf.write(path_, arcname=arcname_)

            progress_store[job_id]["status"] = "done"
            progress_store[job_id]["progress"] = 100
            progress_store[job_id]["file_path"] = zip_path

            logger.debug("[_background_zip_generation] Job done. file_path=%s", zip_path)

        except Exception as e:
            logger.exception("[DEBUG] background_zip_generation error:")
            progress_store[job_id]["status"] = "error"
            progress_store[job_id]["error_msg"] = str(e)


@document_bp.route("/daily-report/progress-sse/<job_id>", methods=["GET"])
def daily_report_progress_sse(job_id):
    """
    SSE：前端監看多筆下載進度
    """

    @stream_with_context
    def generate_stream():
        while True:
            job_info = progress_store.get(job_id)
            if not job_info:
                yield _sse_pack({"error": "Invalid job_id"}, event="error")
                break

            # ★ 若已過期，改成 error
            if time.time() > job_info.get("expires_at", 0):
                job_info["status"] = "error"
                job_info["error_msg"] = "Job expired"
                yield _sse_pack({
                    "progress": job_info.get("progress", 0),
                    "status": "error",
                    "error_msg": "Job expired"
                }, event="error")
                break

            data_dict = {
                "progress": job_info.get("progress", 0),
                "status": job_info.get("status", "unknown"),
                "error_msg": job_info.get("error_msg", "")
            }

            logger.debug(
                "[SSE Debug] job_id=%s, progress=%s, status=%s",
                job_id, data_dict["progress"], data_dict["status"]
            )

            yield _sse_pack(data_dict)

            if data_dict["status"] in ("done", "error"):
                break

            gevent.sleep(1)

    return Response(generate_stream(), mimetype='text/event-stream')


def _sse_pack(data: dict, event=None) -> str:
    import json
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append("data: " + json.dumps(data, ensure_ascii=False))
    lines.append("")
    return "\n".join(lines) + "\n"


@document_bp.route("/daily-report/multi_download_result", methods=["GET"])
def daily_report_multi_download_result():
    """
    下載 SSE 完成後的 ZIP
      GET /api/documents/daily-report/multi_download_result?job_id=xxx
    """
    job_id = request.args.get("job_id", "")
    job_info = progress_store.get(job_id)
    if not job_info:
        return jsonify({"error": "Invalid job_id"}), 400

    if job_info["status"] != "done":
        return jsonify({"error": f"Job not done. status={job_info['status']}"}), 400

    # ★ 再檢查是否過期
    if time.time() > job_info.get("expires_at", 0):
        return jsonify({"error": "Job expired"}), 400

    zip_path = job_info["file_path"]
    if not zip_path or not os.path.isfile(zip_path):
        return jsonify({"error": "File not found"}), 404

    filename = os.path.basename(zip_path)
    # 預設 as_attachment=True 時，多數瀏覽器會彈出下載對話框或直接下載
    return send_file(zip_path, as_attachment=True, download_name=filename)
