from flask import Flask, render_template, request, send_file
from openpyxl import load_workbook
from openpyxl.styles import Font
import shutil
import os
from datetime import datetime
import tempfile
import requests

app = Flask(__name__)

template_file_id = "1v0kQrMN2N83NJVjGgBBsS7OZ2nZuyQRq"

special_fields = {
    "工程編號": (6, 2, 4, "37/2024/DVPS"),
    "工程名稱": (7, 2, 4, "黑沙馬路行人道優化工程(第二期)"),
    "文件編號": (6, 8, 8, "") 
}
regular_fields = [
    ("報批之材料", 11, 3),
    ("牌子(如有)", 12, 3),
    ("預算表之項目編號", 11, 7),
    ("型號", 12, 6),
    ("貨期", 13, 6),
    ("數量", 14, 6),
    ("附件", 15, 6)
]
material_type_checkboxes = [
    ("結構", 7, 6),
    ("供水", 8, 6),
    ("建築", 7, 8),
    ("電氣", 8, 8),
    ("排水", 7, 10),
    ("其他", 8, 10)
]
material_status_checkboxes = [
    ("與設計相同", 13, 1),
    ("與標書相同", 14, 1),
    ("與後加工程建議書相同", 15, 1),
    ("同等質量", 16, 1),
    ("替換材料", 17, 1),
    ("原設計沒有指定", 18, 1)
]
attachment_type_checkboxes = [
    ("樣板", 16, 5),
    ("目錄", 17, 5),
    ("來源證", 16, 7),
    ("其他", 17, 7)
]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Process form data and generate Excel file
        excel_file = generate_excel(request.form)
        return send_file(
            excel_file,
            as_attachment=True,
            download_name="材料報批表_filled.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    return render_template('form.html', 
                           special_fields=special_fields,
                           regular_fields=regular_fields,
                           material_type_checkboxes=material_type_checkboxes,
                           material_status_checkboxes=material_status_checkboxes,
                           attachment_type_checkboxes=attachment_type_checkboxes)

def generate_excel(form_data):
    # Construct correct Google Drive download URL
    url = f'https://drive.google.com/uc?id={template_file_id}'
    
    # Use requests to download the file
    response = requests.get(url)
    if response.status_code == 200:
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception(f"Failed to download the template file. Status code: {response.status_code}")

    # Load the downloaded file into memory
    file_content = BytesIO(response.content)

    # Load the workbook
    wb = load_workbook(file_content)
    wb._external_links = []
    ws = wb.active

    # Fill in the special fields
    for field, (row, start_col, end_col, _) in special_fields.items():
        merged_cell = ws.cell(row=row, column=start_col)
        merged_cell.value = form_data.get(field, '')
        if field == "工程名稱":
            merged_cell.font = Font(size=10)
    
    # Fill in the regular fields
    for field, row, col in regular_fields:
        ws.cell(row=row, column=col, value=form_data.get(field, ''))

    # Fill in the checkboxes
    for checkboxes in [material_type_checkboxes, material_status_checkboxes, attachment_type_checkboxes]:
        for field, row, col in checkboxes:
            ws.cell(row=row, column=col, value="☑" + field if field in form_data else "□" + field)

    # Fill in the date
    ws.cell(row=21, column=7, value=form_data.get('日期', datetime.now().strftime("%Y/%m/%d")))

    # Save to BytesIO object
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return output

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)