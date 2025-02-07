# backend/site_diary/services.py

import os
import tempfile
import shutil
import subprocess
from datetime import datetime
from typing import Dict
import platform
from shutil import which

from flask import current_app
from openpyxl import load_workbook
from openpyxl.styles import Alignment

from backend.project_management.models import Project, db
from backend.site_diary.models import SiteDiary


def auto_compute_day_count_if_needed(site_diary: SiteDiary):
    """
    若使用者未手動指定 day_count，則自動計算為該專案已存在的最大 day_count + 1。
    若尚無任何紀錄則從 1 開始。
    """
    if site_diary.day_count is not None:
        return

    max_day_count = db.session.query(db.func.max(SiteDiary.day_count)) \
                              .filter_by(project_id=site_diary.project_id).scalar()
    if max_day_count:
        site_diary.day_count = max_day_count + 1
    else:
        site_diary.day_count = 1


def generate_diary_xlsx_only(site_diary: SiteDiary) -> str:
    """
    產生/填寫 daily_report.xlsx 後，回傳填好的暫存 XLSX 檔路徑。
    同時依需求設定各 Sheet 之列印範圍（整份工作簿都會包含）。
    """
    project = Project.query.get(site_diary.project_id)
    if not project:
        raise ValueError("Project not found.")

    # 找到 daily_report.xlsx 模板位置 (不寫死路徑)
    template_path = os.path.join(
        current_app.root_path,
        'site_diary',
        'templates',
        'daily_report.xlsx'
    )
    if not os.path.isfile(template_path):
        raise FileNotFoundError(
            f"daily_report.xlsx not found at: {template_path}"
        )

    # 在系統臨時資料夾中建立子資料夾
    temp_dir = tempfile.mkdtemp(prefix="diary_xlsx_")

    # 以報表日期組出檔名
    date_str_for_filename = "noDate"
    if site_diary.report_date:
        date_str_for_filename = site_diary.report_date.strftime("%Y%m%d")

    filled_xlsx_path = os.path.join(
        temp_dir,
        f"{date_str_for_filename}_daily_report.xlsx"
    )

    # 先把模板拷貝到暫存檔
    shutil.copy(template_path, filled_xlsx_path)

    # 打開並填寫
    wb = load_workbook(filled_xlsx_path)

    # 準備填入之資料
    date_str = (site_diary.report_date.strftime("%Y-%m-%d")
                if site_diary.report_date else "")
    project_name = project.name or ""
    project_job_number = project.job_number or ""
    contractor_name = project.contractor or ""
    day_count_str = str(site_diary.day_count) if site_diary.day_count else ""
    summary_str = site_diary.summary or ""
    weather_morning = site_diary.weather_morning or ""
    weather_noon = site_diary.weather_noon or ""

    if project.start_date:
        start_date_str = project.start_date.strftime("%Y-%m-%d")
    else:
        start_date_str = ""

    if project.duration_days:
        if project.duration_type == 'business':
            duration_str = f"{project.duration_days}工作天"
        else:
            duration_str = f"{project.duration_days}天"
    else:
        duration_str = ""

    # 映射工人/機器到對應的儲存格
    worker_map = {
        "地盤總管": "D19",
        "工程師":  "D20",
        "管工":    "D21",
        "平水員":  "D22",
        "燒焊焊工": "D23",
        "機手":    "D24",
        "泥水工":  "D25",
        "紮鐵工":  "D26",
        "木板工":  "D27",
        "電工":    "D28",
        "水喉工":  "D29",
        "雜工":    "D30",
    }
    machine_map = {
        "挖掘機": "G19",
        "發電機": "G20",
        "風機":   "G21",
        "泥頭車": "G22",
        "吊機":   "G23",
        "機炮":   "G24",
        "屈鐵機": "G25",
        "風車鋸": "G26",
    }

    # Sheet1: "每日施工進度報告表"
    if "每日施工進度報告表" in wb.sheetnames:
        sh1 = wb["每日施工進度報告表"]

        # 基本欄位
        sh1["C2"].value = date_str
        sh1["C2"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["K2"].value = start_date_str
        sh1["K2"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["D4"].value = project_name
        sh1["D4"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["D5"].value = project_job_number
        sh1["D5"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["D6"].value = contractor_name
        sh1["D6"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["E7"].value = weather_morning
        sh1["E7"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["H7"].value = weather_noon
        sh1["H7"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["D8"].value = duration_str
        sh1["D8"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["J8"].value = day_count_str
        sh1["J8"].alignment = Alignment(horizontal='center', vertical='center')

        sh1["B10"].value = summary_str
        sh1["B10"].alignment = Alignment(horizontal='center', vertical='center')

        # 工人數量
        worker_dict = {w.worker_type: w.quantity for w in site_diary.workers}
        for w_type, cell_ref in worker_map.items():
            qty = worker_dict.get(w_type, 0)
            cell_obj = sh1[cell_ref]
            cell_obj.value = str(qty) if qty else ""
            cell_obj.alignment = Alignment(horizontal='center', vertical='center')

        # 機器數量
        machine_dict = {m.machine_type: m.quantity for m in site_diary.machines}
        for m_type, cell_ref in machine_map.items():
            qty = machine_dict.get(m_type, 0)
            cell_obj = sh1[cell_ref]
            cell_obj.value = str(qty) if qty else ""
            cell_obj.alignment = Alignment(horizontal='center', vertical='center')

        # 列印範圍
        sh1.print_area = "A1:L46"

    # Sheet2: "每日本地工人及外地勞工施工人員紀錄表"
    if "每日本地工人及外地勞工施工人員紀錄表" in wb.sheetnames:
        sh2 = wb["每日本地工人及外地勞工施工人員紀錄表"]
        b3_date = (site_diary.report_date.strftime("%Y/%m/%d")
                   if site_diary.report_date else "")
        sh2["B3"].value = b3_date
        sh2["B3"].alignment = Alignment(horizontal='center', vertical='center')

        sh2["B6"].value = project_name
        sh2["B6"].alignment = Alignment(horizontal='center', vertical='center')

        sh2["B7"].value = project_job_number
        sh2["B7"].alignment = Alignment(horizontal='center', vertical='center')

        sh2["B8"].value = contractor_name
        sh2["B8"].alignment = Alignment(horizontal='center', vertical='center')

        # 列印範圍
        sh2.print_area = "A1:E40"

    wb.save(filled_xlsx_path)
    wb.close()

    return filled_xlsx_path


def generate_diary_pdf_sheet(site_diary: SiteDiary, sheet_name: str) -> str:
    """
    依照 sheet_name ('sheet1' or 'sheet2')，只輸出對應工作表的 PDF：
      - sheet1 => "每日施工進度報告表.pdf"
      - sheet2 => "每日本地工人及外地勞工施工人員紀錄表.pdf"
    並以 --convert-to pdf:calc_pdf_Export + --infilter="Calc Office Open XML"
    匯出。若子程序執行失敗，印出 debug log 以便排查。

    ★ 轉檔完成後，我們會將 LibreOffice 輸出的檔名改為程式預期的 pdf_path，
      避免 "找不到輸出檔" 的狀況。
    """
    project = Project.query.get(site_diary.project_id)
    if not project:
        raise ValueError("Project not found.")

    # 先用 XLSX 產生整本工作簿
    xlsx_path = generate_diary_xlsx_only(site_diary)
    temp_dir = os.path.dirname(xlsx_path)

    date_str = "noDate"
    if site_diary.report_date:
        date_str = site_diary.report_date.strftime("%Y%m%d")

    if sheet_name == 'sheet1':
        pdf_filename = f"{date_str}每日施工進度報告表.pdf"
        target_sheet_name = "每日施工進度報告表"
    else:
        pdf_filename = f"{date_str}施工人員紀錄表.pdf"
        target_sheet_name = "每日本地工人及外地勞工施工人員紀錄表"

    # 程式想要最終回傳的 PDF 路徑
    pdf_path = os.path.join(temp_dir, pdf_filename)

    # 另存一份只保留指定工作表的 XLSX
    single_sheet_xlsx = os.path.join(temp_dir, f"{date_str}_{sheet_name}_only.xlsx")
    shutil.copy(xlsx_path, single_sheet_xlsx)

    wb = load_workbook(single_sheet_xlsx)
    if target_sheet_name not in wb.sheetnames:
        wb.close()
        raise RuntimeError(f"目標工作表 '{target_sheet_name}' 不存在")

    for sn in wb.sheetnames:
        if sn != target_sheet_name:
            wb.remove(wb[sn])
    wb.save(single_sheet_xlsx)
    wb.close()

    lo_exec = get_libreoffice_cmd()

    # 設定輸入 & 輸出 filter
    input_filter = "Calc Office Open XML"
    output_filter = "pdf:calc_pdf_Export"

    # 根據作業系統，組合子程序指令
    if platform.system().lower().startswith("win"):
        cmd = (
            f'"{lo_exec}" --headless --convert-to "{output_filter}" '
            f'--infilter="{input_filter}" "{single_sheet_xlsx}" --outdir "{temp_dir}"'
        )
        print("==== DEBUG => LibreOffice command (Windows) ====")
        print(cmd)
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True)
            print("==== DEBUG => LibreOffice stdout ====")
            print(result.stdout.decode('utf-8', errors='replace'))
            print("==== DEBUG => LibreOffice stderr ====")
            print(result.stderr.decode('utf-8', errors='replace'))
        except subprocess.CalledProcessError as e:
            print("==== DEBUG => LibreOffice ERROR return code:", e.returncode)
            print("==== DEBUG => LibreOffice ERROR output ====")
            if e.stderr:
                print(e.stderr.decode('utf-8', errors='replace'))
            raise RuntimeError(f"LibreOffice PDF conversion failed: {e}") from e
    else:
        cmd_list = [
            lo_exec, "--headless",
            "--convert-to", output_filter,
            f'--infilter={input_filter}',
            single_sheet_xlsx,
            "--outdir", temp_dir
        ]
        print("==== DEBUG => LibreOffice command (Non-Windows) ====")
        print(cmd_list)
        try:
            result = subprocess.run(cmd_list, shell=False, check=True, capture_output=True)
            print("==== DEBUG => LibreOffice stdout ====")
            print(result.stdout.decode('utf-8', errors='replace'))
            print("==== DEBUG => LibreOffice stderr ====")
            print(result.stderr.decode('utf-8', errors='replace'))
        except subprocess.CalledProcessError as e:
            print("==== DEBUG => LibreOffice ERROR return code:", e.returncode)
            print("==== DEBUG => LibreOffice ERROR output ====")
            if e.stderr:
                print(e.stderr.decode('utf-8', errors='replace'))
            raise RuntimeError(f"LibreOffice PDF conversion failed: {e}") from e

    # ★ LibreOffice 轉檔後實際產生的檔案，預設會以 XLSX 同名但副檔名 .pdf
    #   例如 single_sheet_xlsx = C:\...\20250204_sheet1_only.xlsx
    #   則輸出多半是 C:\...\20250204_sheet1_only.pdf
    generated_pdf_name = os.path.splitext(single_sheet_xlsx)[0] + ".pdf"

    # 檔案若確實存在，就將它改名成我們想要的 pdf_path
    if os.path.isfile(generated_pdf_name):
        os.rename(generated_pdf_name, pdf_path)
    else:
        raise RuntimeError(f"PDF 轉檔失敗：找不到 {generated_pdf_name}")

    # 檢查改名後的新檔名是否存在
    if not os.path.isfile(pdf_path):
        raise RuntimeError(f"PDF 轉檔失敗：找不到 {pdf_path}")

    return pdf_path


def get_libreoffice_cmd() -> str:
    """
    智能取得 LibreOffice 執行檔：
      1) 若有環境變數 LIBREOFFICE_PATH（指向檔案或資料夾）則使用
      2) 否則嘗試於 PATH 搜尋 'soffice' 或 'libreoffice'
      3) 全部找不到則拋錯
    """
    custom_path = os.environ.get("LIBREOFFICE_PATH")
    if custom_path:
        # 如果是檔案 => 直接用
        if os.path.isfile(custom_path):
            return custom_path
        # 若只是資料夾，嘗試補上 soffice / libreoffice
        soffice_path = os.path.join(custom_path, "soffice")
        libreoffice_path = os.path.join(custom_path, "libreoffice")
        if os.path.isfile(soffice_path):
            return soffice_path
        if os.path.isfile(libreoffice_path):
            return libreoffice_path
        raise RuntimeError(f"LIBREOFFICE_PATH 無效: {custom_path}")

    # 無自定義 => 從 PATH 中找 soffice / libreoffice
    for candidate in ("soffice", "libreoffice"):
        exe_path = which(candidate)
        if exe_path:
            return exe_path

    raise RuntimeError(
        "系統上找不到 soffice 或 libreoffice，可執行檔未安裝或未加入 PATH。"
        "請安裝 LibreOffice 或於環境變數 LIBREOFFICE_PATH 指定執行檔路徑。"
    )
