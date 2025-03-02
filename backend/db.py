# backend/db.py

import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from flask import Flask
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError, ConfigurationError, ConnectionFailure
from datetime import datetime

mongo = PyMongo()

def _ensure_auth_source_admin_if_railway(mongo_uri: str) -> str:
    """
    若偵測到 URI 為 Railway 提供的內部位址 (含 'railway.internal')，
    且尚未設定 authSource，則自動補上 "?authSource=admin" 或 "&authSource=admin"。
    其他平台(非 Railway) 或已經有指定 authSource 時，則不動作。
    """
    if "railway.internal" not in mongo_uri:
        return mongo_uri  # 非 Railway，不動作

    # 解析 URI
    parsed = urlparse(mongo_uri)
    qs = parse_qs(parsed.query)  # 例如 {'authSource': ['admin'], 'replicaSet': ['xxx']}

    # 若已存在 authSource，就不再補
    if "authSource" in qs:
        return mongo_uri

    # 若尚無 authSource，補上 admin
    qs["authSource"] = ["admin"]
    new_query = urlencode(qs, doseq=True)  # 重新組裝 query string
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)


def init_mongo_app(app: Flask):
    """
    初始化 MongoDB 連線。
    
    - 強制要求 MONGO_URI，若未設定則直接報錯，避免默默嘗試 localhost 而出現 Connection refused。
    - 若要在本機開發，可自行在 .env 或系統環境裡設定：
        MONGO_URI="mongodb://127.0.0.1:27017/test"
    - 若偵測到 Railway 提供的 URI (含 railway.internal)，但缺少 authSource，
      則自動加上 "?authSource=admin"（以避免 Authentication failed）。
    """
    raw_uri = os.environ.get("MONGO_URI", "").strip()
    if not raw_uri:
        raise ConfigurationError(
            "ERROR: 環境變數 MONGO_URI 尚未設定，無法連接 MongoDB。\n"
            "請於 Railway/Heroku/本機環境設定有效的 MONGO_URI。"
        )

    # 若是 Railway 的 URI，則自動補 authSource=admin
    mongo_uri = _ensure_auth_source_admin_if_railway(raw_uri)

    print("[INFO] MONGO_URI=", mongo_uri)  # 幫助檢查實際讀到的 URI（可在 logs 看到）

    app.config["MONGO_URI"] = mongo_uri
    mongo.init_app(app)

    try:
        # 檢驗連線是否可行 (會觸發實際連線)
        _ = mongo.cx.server_info()
    except ConnectionFailure as e:
        raise ConnectionFailure(f"無法連接 MongoDB: {e}")

    # 建立好 counters 集合的索引（若不存在）
    # 用來實作「自動遞增序號」功能
    counters_coll = mongo.db["counters"]
    counters_coll.create_index("collection_name", unique=True)


def get_next_sequence(collection_name: str) -> int:
    """
    取得對應 collection_name 的下一個自增序號。
    若尚無紀錄，則從 1 開始。
    """
    counters_coll = mongo.db["counters"]
    result = counters_coll.find_one_and_update(
        {"collection_name": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return result["seq"]


def to_iso_date(date_obj):
    """
    安全轉換 datetime => 'YYYY-MM-DD' 字串。
    若原本是 None 或非 datetime, 則回傳 None。
    """
    if not date_obj:
        return None
    return date_obj.strftime("%Y-%m-%d")


def to_iso_datetime(dt):
    """
    將 datetime 轉成 'YYYY-MM-DD HH:MM:SS' 字串。
    若是 None, 則回傳 None。
    """
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_date_str(date_str: str, default_date_str: str = None):
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


def normalize_progress(progress):
    """
    將 progress 值正規化為 0.0 到 1.0 之間的浮點數。
    """
    # 確保介於 0 ~ 1
    try:
        p = float(progress)
        import math
        if math.isnan(p) or p < 0:
            p = 0.0
        if p > 1:
            p = 1.0
        return p
    except:
        return 0.0


def find_all_and_format(collection, query=None, sort_key="id", sort_order=1, projection=None, formatter=None):
    """
    通用查詢函數，用於查詢集合並返回格式化結果。
    
    參數:
        collection: 集合名稱，如 'projects', 'staff' 等
        query: 查詢條件，默認為 {}
        sort_key: 排序欄位，默認為 'id'
        sort_order: 排序方向，1 為升序，-1 為降序
        projection: 投影，指定要返回的欄位，默認為 None
        formatter: 格式化函數，用於處理每個文檔，默認為 None
    
    返回:
        格式化後的結果列表
    """
    query = query or {}
    cursor = mongo.db[collection].find(query, projection).sort([(sort_key, sort_order)])
    
    results = []
    for doc in cursor:
        if formatter:
            doc = formatter(doc)
        results.append(doc)
    
    return results


def find_one_or_404(collection, query, error_msg=None):
    """
    查詢單個文檔，如果不存在則拋出 404 錯誤。
    
    參數:
        collection: 集合名稱，如 'projects', 'staff' 等
        query: 查詢條件
        error_msg: 當文檔不存在時的錯誤訊息
    
    返回:
        文檔對象
    """
    from flask import abort
    
    doc = mongo.db[collection].find_one(query)
    if not doc:
        abort(404, description=error_msg or f"Document not found in {collection}")
    
    return doc
