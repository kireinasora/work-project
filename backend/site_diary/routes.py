# backend/site_diary/routes.py

import traceback
import logging
from flask import Blueprint, request, jsonify, send_file, Response, abort
from datetime import datetime
from urllib.parse import quote

from backend.db import mongo, get_next_sequence, to_iso_date

# 建立 logger
logger = logging.getLogger(__name__)

site_diary_bp = Blueprint('site_diary_bp', __name__)

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
    logger.debug("get_site_diaries() called, project_id=%s", project_id)

    project_doc = mongo.db.projects.find_one({"id": project_id})
    if not project_doc:
        logger.warning("Project not found: project_id=%s, returning 404", project_id)
        abort(404, description="Project not found")

    cursor = mongo.db.site_diaries.find({"project_id": project_id}, sort=[("id", 1)])
    results = []

    for sd in cursor:
        worker_list = []
        for w_type, qty in sd.get("workers", {}).items():
            worker_list.append({
                "type": w_type,
                "quantity": qty
            })
        machine_list = []
        for m_type, qty in sd.get("machines", {}).items():
            machine_list.append({
                "type": m_type,
                "quantity": qty
            })
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
            "staffs": staff_list
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
    if "day_count" not in data or data["day_count"] is None:
        max_day = mongo.db.site_diaries.find(
            {"project_id": project_id, "day_count": {"$ne": None}},
            {"day_count": 1}
        ).sort("day_count", -1).limit(1)
        row = next(max_day, None)
        if row:
            update_fields["day_count"] = row["day_count"] + 1
        else:
            update_fields["day_count"] = 1

    if update_fields:
        mongo.db.site_diaries.update_one(
            {"project_id": project_id, "id": diary_id},
            {"$set": update_fields}
        )
        logger.info("Site diary updated: project_id=%s, diary_id=%s, fields=%s", project_id, diary_id, list(update_fields.keys()))
    else:
        logger.debug("No fields updated, data was empty or invalid.")

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

    # 擷取 file=? 參數，移除冒號後字串
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


def _send_file_with_utf8_filename(file_path: str, full_chinese_name: str, ascii_fallback: str = None) -> Response:
    from flask import send_file
    from urllib.parse import quote

    response = send_file(file_path, as_attachment=True)

    if not ascii_fallback:
        ascii_fallback = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in full_chinese_name)
    utf8_quoted = quote(full_chinese_name, encoding="utf-8")

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
