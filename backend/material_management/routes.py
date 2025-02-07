# backend/material_management/routes.py
from flask import Blueprint, request, send_file
from .services import generate_excel

material_bp = Blueprint('material_bp', __name__)

@material_bp.route('/material-submission', methods=['POST'])
def material_submission():
    """
    接收 JSON 表單資料，產生 Excel 並回傳。
    """
    data = request.json
    temp_file_path = generate_excel(data)
    file_name = data.get('檔案名稱', '材料報批表_filled.xlsx')
    if not file_name.endswith('.xlsx'):
        file_name += '.xlsx'
    return send_file(temp_file_path, as_attachment=True, download_name=file_name)
