# backend/site_diary/routes.py

import traceback
from flask import Blueprint, request, jsonify, send_file, Response
from datetime import datetime
from urllib.parse import quote

from backend.project_management.models import db, Project
from backend.staff_management.models import Staff
from backend.site_diary.models import (
    SiteDiary,
    SiteDiaryWorker,
    SiteDiaryMachine
)
from backend.site_diary.services import (
    auto_compute_day_count_if_needed,
    generate_diary_xlsx_only,
    generate_diary_pdf_sheet
)

site_diary_bp = Blueprint('site_diary_bp', __name__)


@site_diary_bp.route('/<int:project_id>/site_diaries', methods=['POST'])
def create_site_diary(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.json

    report_date_str = data.get('report_date')
    if report_date_str:
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
    else:
        report_date = datetime.utcnow().date()

    site_diary = SiteDiary(
        project_id=project.id,
        report_date=report_date,
        weather_morning=data.get('weather_morning', ''),
        weather_noon=data.get('weather_noon', ''),
        day_count=data.get('day_count', None),
        summary=data.get('summary', '')
    )
    db.session.add(site_diary)
    db.session.flush()

    auto_compute_day_count_if_needed(site_diary)
    db.session.flush()

    workers_dict = data.get('workers', {})
    for worker_type, quantity in workers_dict.items():
        db.session.add(SiteDiaryWorker(
            site_diary_id=site_diary.id,
            worker_type=worker_type,
            quantity=quantity
        ))

    machines_dict = data.get('machines', {})
    for machine_type, quantity in machines_dict.items():
        db.session.add(SiteDiaryMachine(
            site_diary_id=site_diary.id,
            machine_type=machine_type,
            quantity=quantity
        ))

    staff_ids = data.get('staff_ids', [])
    for sid in staff_ids:
        staff_obj = Staff.query.get(sid)
        if staff_obj:
            site_diary.staffs.append(staff_obj)

    db.session.commit()

    return jsonify({
        "message": "Site diary created",
        "site_diary_id": site_diary.id,
        "day_count": site_diary.day_count
    }), 201


@site_diary_bp.route('/<int:project_id>/site_diaries', methods=['GET'])
def get_site_diaries(project_id):
    project = Project.query.get_or_404(project_id)
    diaries = SiteDiary.query.filter_by(project_id=project.id).all()

    results = []
    for sd in diaries:
        worker_list = [{
            "id": w.id,
            "type": w.worker_type,
            "quantity": w.quantity
        } for w in sd.workers]

        machine_list = [{
            "id": m.id,
            "type": m.machine_type,
            "quantity": m.quantity
        } for m in sd.machines]

        staff_list = [{
            "id": st.id,
            "name": st.name,
            "role": st.role
        } for st in sd.staffs]

        results.append({
            "id": sd.id,
            "report_date": sd.report_date.isoformat() if sd.report_date else None,
            "weather_morning": sd.weather_morning,
            "weather_noon": sd.weather_noon,
            "day_count": sd.day_count,
            "summary": sd.summary,
            "workers": worker_list,
            "machines": machine_list,
            "staffs": staff_list
        })

    return jsonify(results), 200


@site_diary_bp.route('/<int:project_id>/site_diaries/<int:diary_id>', methods=['PUT'])
def update_site_diary(project_id, diary_id):
    site_diary = SiteDiary.query.filter_by(project_id=project_id, id=diary_id).first_or_404()
    data = request.json

    report_date_str = data.get('report_date')
    if report_date_str:
        site_diary.report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
    else:
        site_diary.report_date = None

    site_diary.weather_morning = data.get('weather_morning', '')
    site_diary.weather_noon = data.get('weather_noon', '')
    site_diary.day_count = data.get('day_count') or None
    site_diary.summary = data.get('summary', '')

    SiteDiaryWorker.query.filter_by(site_diary_id=site_diary.id).delete()
    for worker_type, quantity in data.get('workers', {}).items():
        db.session.add(SiteDiaryWorker(
            site_diary_id=site_diary.id,
            worker_type=worker_type,
            quantity=quantity
        ))

    SiteDiaryMachine.query.filter_by(site_diary_id=site_diary.id).delete()
    for machine_type, quantity in data.get('machines', {}).items():
        db.session.add(SiteDiaryMachine(
            site_diary_id=site_diary.id,
            machine_type=machine_type,
            quantity=quantity
        ))

    site_diary.staffs.clear()
    for sid in data.get('staff_ids', []):
        staff_obj = Staff.query.get(sid)
        if staff_obj:
            site_diary.staffs.append(staff_obj)

    auto_compute_day_count_if_needed(site_diary)
    db.session.commit()

    return jsonify({
        "message": "Site diary updated",
        "day_count": site_diary.day_count
    }), 200


@site_diary_bp.route('/<int:project_id>/site_diaries/<int:diary_id>', methods=['DELETE'])
def delete_site_diary(project_id, diary_id):
    site_diary = SiteDiary.query.filter_by(project_id=project_id, id=diary_id).first_or_404()
    db.session.delete(site_diary)
    db.session.commit()
    return jsonify({"message": "Site diary deleted"}), 200


@site_diary_bp.route('/<int:project_id>/site_diaries/<int:diary_id>/download_report', methods=['GET'])
def download_site_diary_report(project_id, diary_id):
    """
    依照 ?file= 參數決定下載哪個檔案：
      - xlsx   => "YYYYMMDD_daily_report.xlsx"
      - sheet1 => "YYYYMMDD每日施工進度報告表.pdf"
      - sheet2 => "YYYYMMDD施工人員紀錄表.pdf"
    """
    site_diary = SiteDiary.query.filter_by(project_id=project_id, id=diary_id).first_or_404()
    file_type = request.args.get('file', 'xlsx')

    date_str = site_diary.report_date.strftime("%Y%m%d") if site_diary.report_date else "noDate"

    try:
        if file_type == 'xlsx':
            xlsx_path = generate_diary_xlsx_only(site_diary)
            download_name = f"{date_str}_daily_report.xlsx"
            return _send_file_with_utf8_filename(xlsx_path, download_name)

        elif file_type in ('sheet1', 'sheet2'):
            pdf_path = generate_diary_pdf_sheet(site_diary, sheet_name=file_type)
            if file_type == 'sheet1':
                # 假設想要英文化 fallback
                download_name = f"{date_str}每日施工進度報告表.pdf"  # 中文
                ascii_fallback = f"{date_str}_daily_report.pdf"     # 英文
            else:
                download_name = f"{date_str}施工人員紀錄表.pdf"      # 中文
                ascii_fallback = f"{date_str}_worker_log.pdf"       # 英文

            return _send_file_with_utf8_filename(pdf_path, download_name, ascii_fallback)
        else:
            return jsonify({"error": f"Unknown file type '{file_type}'"}), 400

    except FileNotFoundError as e:
        return jsonify({"error": f"FileNotFoundError: {e}"}), 404
    except PermissionError as e:
        return jsonify({"error": f"PermissionError: {e}"}), 403
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"error": str(e), "traceback": tb}), 500


def _send_file_with_utf8_filename(
    file_path: str,
    full_chinese_name: str,
    ascii_fallback: str = None
) -> Response:
    """
    改良後: 若有指定 ascii_fallback，則 filename="ascii_fallback";
    否則就自動做個 fallback(全部非 ASCII 改成 '_').
    而 filename*=UTF-8''... 用 full_chinese_name (URL-encoded)。
    """
    response = send_file(file_path, as_attachment=True)

    if not ascii_fallback:
        # 若沒傳入 fallback => 將所有非 ASCII 改成 _
        # (含中文皆視為非 ASCII)
        ascii_fallback = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" 
                                 for ch in full_chinese_name)

    # quote() 後只包含 ASCII 範圍字元
    utf8_quoted = quote(full_chinese_name, encoding="utf-8")

    disposition_value = (
        f'attachment; filename="{ascii_fallback}"; '
        f'filename*=UTF-8\'\'{utf8_quoted}'
    )
    # encode+decode 防止任何潛在的超 ASCII 字元
    safe_disposition = disposition_value.encode('latin-1', 'replace').decode('latin-1')
    response.headers["Content-Disposition"] = safe_disposition

    return response


@site_diary_bp.route('/<int:project_id>/site_diaries/last', methods=['GET'])
def get_last_site_diary(project_id):
    project = Project.query.get_or_404(project_id)
    last_diary = (SiteDiary.query
                  .filter_by(project_id=project.id)
                  .order_by(SiteDiary.report_date.desc(), SiteDiary.id.desc())
                  .first())
    if not last_diary:
        return jsonify({}), 200

    worker_list = [{
        "id": w.id,
        "type": w.worker_type,
        "quantity": w.quantity
    } for w in last_diary.workers]

    machine_list = [{
        "id": m.id,
        "type": m.machine_type,
        "quantity": m.quantity
    } for m in last_diary.machines]

    staff_list = [{
        "id": st.id,
        "name": st.name,
        "role": st.role
    } for st in last_diary.staffs]

    result = {
        "id": last_diary.id,
        "report_date": last_diary.report_date.isoformat() if last_diary.report_date else None,
        "weather_morning": last_diary.weather_morning,
        "weather_noon": last_diary.weather_noon,
        "day_count": last_diary.day_count,
        "summary": last_diary.summary,
        "workers": worker_list,
        "machines": machine_list,
        "staffs": staff_list
    }
    return jsonify(result), 200
