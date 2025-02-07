import os
from flask import Blueprint, send_file, jsonify

download_bp = Blueprint('download_bp', __name__)

def generate_tree(startpath, ignore_dirs=None, ignore_files=None, files_to_show=None):
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', '.pytest_cache', '.vscode', 'venv', 'env', 'node_modules'}
    if ignore_files is None:
        ignore_files = {'.gitignore', '.env', '*.pyc', '*.pyo', '*.pyd', '.DS_Store'}
    
    tree_str = []
    
    def should_ignore(path, name):
        # 檢查是否應該忽略該目錄或檔案
        if os.path.isdir(os.path.join(path, name)):
            return name in ignore_dirs
        # 檢查副檔名是否為允許的類型
        allowed_extensions = {'.py', '.jpg', '.jpeg', '.html', '.css','.vue','ts','js','json','svg'}
        file_ext = os.path.splitext(name)[1].lower()
        if file_ext not in allowed_extensions:
            return True
        return any(name.endswith(f[1:]) if f.startswith('*') else name == f for f in ignore_files)
    
    def get_description(filepath):
        # 讀取檔案前幾行來尋找註解描述
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                first_lines = ''.join([next(f, '') for _ in range(5)])
                desc = ''
                for line in first_lines.split('\n'):
                    if line.strip().startswith('#'):
                        desc = line.strip('# ').strip()
                        break
                return f" # {desc}" if desc else ''
        except:
            return ''

    def should_show(filepath):
        if files_to_show is None:
            return True
        # 將檔案路徑標準化以進行比較
        filepath = filepath.replace('\\', '/').replace('./', '')
        return filepath in files_to_show

    for root, dirs, files in os.walk(startpath):
        # 過濾掉要忽略的目錄
        dirs[:] = sorted([d for d in dirs if not should_ignore(root, d)])
        
        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * level
        
        # 檢查此目錄是否包含要顯示的文件
        has_files_to_show = False
        if files_to_show is not None:
            for file in files:
                if should_show(os.path.join(root, file)):
                    has_files_to_show = True
                    break
        
        # 只有當目錄包含要顯示的文件時才添加目錄名
        if has_files_to_show or files_to_show is None:
            if level > 0:
                tree_str.append(f'{indent[:-4]}├── {os.path.basename(root)}/')
            else:
                tree_str.append(os.path.basename(root) + '/')
        
        # 添加檔案
        files = sorted([f for f in files if not should_ignore(root, f) and should_show(os.path.join(root, f))])
        for i, file in enumerate(files):
            file_indent = indent + ('├── ' if i < len(files) - 1 else '└── ')
            filepath = os.path.join(root, file)
            description = get_description(filepath) if file.endswith('.py') else ''
            tree_str.append(f'{file_indent}{file}{description}')
    
    return '\n'.join(tree_str)


def combine_python_files():
    """
    執行後會在本地目錄下生成/覆蓋一份 combined_code.txt，
    內容包含指定類型檔案的合併，以及專案的目錄結構。
    """
    # 指定要包含的日誌檔案（若有）
    log_files = [
        # 在此可加入如 logs/xxx.log 之類的路徑
    ]
    
    # 自動搜尋所有指定類型的檔案
    files_to_read = []
    allowed_extensions = ('.py', '.jpg', '.jpeg', '.html', '.css','.vue','ts','js','json','svg')
    for root, _, files in os.walk('.'):
        for file in files:
            if file.lower().endswith(allowed_extensions) and file != 'chaintext.py':
                file_path = os.path.join(root, file)
                file_path = file_path.replace('\\', '/')
                if file_path.startswith('./'):
                    file_path = file_path[2:]
                skip = False
                for ignore_dir in {'.git', '__pycache__', '.pytest_cache', '.vscode', 'venv', 'env', 'node_modules'}:
                    if ignore_dir in file_path.split('/'):
                        skip = True
                        break
                if not skip:
                    files_to_read.append(file_path)
    
    # 排序檔案列表
    files_to_read.sort()

    # 分隔線
    separator = "\n" + "="*80 + "\n"
    
    # 打開輸出文件
    with open('combined_code.txt', 'w', encoding='utf-8') as output_file:
        # 首先寫入日誌檔案
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as input_file:
                    output_file.write(f"\n{log_file}\n")
                    output_file.write(separator)
                    output_file.write(input_file.read())
                    output_file.write(separator)
            except FileNotFoundError:
                print(f"警告：找不到日誌檔案 {log_file}")
            except Exception as e:
                print(f"處理日誌檔案 {log_file} 時發生錯誤：{str(e)}")
        
        # 接著寫入專案檔案架構
        project_structure = generate_tree('.', files_to_show=files_to_read)
        output_file.write("專案檔案架構：\n")
        output_file.write(project_structure)
        output_file.write(separator)
        
        # 遍歷每個文件
        for i, file_name in enumerate(files_to_read):
            try:
                with open(file_name, 'r', encoding='utf-8') as input_file:
                    # 寫入文件名作為標題
                    output_file.write(f"\n{file_name}\n")
                    # 寫入分隔線
                    output_file.write(separator)
                    # 寫入文件內容
                    output_file.write(input_file.read())
                    # 如果不是最後一個文件，再加一個分隔線
                    if i < len(files_to_read) - 1:
                        output_file.write(separator)
                        
            except FileNotFoundError:
                print(f"警告：找不到文件 {file_name}")
            except Exception as e:
                print(f"處理文件 {file_name} 時發生錯誤：{str(e)}")


@download_bp.route('/download-diary', methods=['GET'])
def download_diary():
    """
    產生(或更新) combined_code.txt 後，將其以檔案下載回傳給前端。
    若下載失敗（程式發生問題），則回傳 JSON 錯誤訊息並帶有 500 狀態碼。
    """
    try:
        combine_python_files()
        return send_file(
            'combined_code.txt',
            as_attachment=True,
            download_name='combined_code.txt'  # Flask 2.0+ 用參數 download_name
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
