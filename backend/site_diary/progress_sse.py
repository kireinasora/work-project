# backend/site_diary/progress_sse.py

import time
import uuid
import threading
from flask import Blueprint, Response, stream_with_context

progress_sse_bp = Blueprint('progress_sse_bp', __name__)

# 全域字典：job_id -> {"status": ..., "progress": ..., "file_path": ..., "error_msg": ...}
# 實務可用 Redis / DB 等替代。
progress_store = {}

@progress_sse_bp.route('/progress-sse/<job_id>', methods=['GET'])
def sse_progress(job_id):
    """
    SSE 端點：前端可透過 EventSource('/api/progress-sse/<job_id>')
    來接收進度 (以 data: {...} 形式送出)。
    只要 status != 'done'/'error'，就持續每秒推送一次。
    """
    @stream_with_context
    def generate_stream():
        while True:
            job_info = progress_store.get(job_id)
            if not job_info:
                # job_id 不存在 => 立即送出錯誤並結束串流
                yield _sse_pack({"error": "Invalid job_id"}, event="error")
                break

            data_dict = {
                "progress": job_info.get("progress", 0),
                "status": job_info.get("status", "unknown"),
                "error_msg": job_info.get("error_msg", "")
            }

            yield _sse_pack(data_dict)

            # 若完成或出錯，結束 SSE
            if data_dict["status"] in ("done", "error"):
                break

            # 否則繼續等待一秒
            time.sleep(1)

    return Response(generate_stream(), mimetype='text/event-stream')


def _sse_pack(data: dict, event=None) -> str:
    """
    將 dict 轉成 SSE 格式字串, 例如:
      event: <event>\n
      data: <json>\n
      \n
    """
    import json
    lines = []
    if event:
        lines.append(f"event: {event}")
    json_str = json.dumps(data, ensure_ascii=False)
    lines.append(f"data: {json_str}")
    lines.append("")  # 空行代表訊息分隔
    return "\n".join(lines) + "\n"
