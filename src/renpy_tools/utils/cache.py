from __future__ import annotations
import sqlite3, threading, hashlib, os
from pathlib import Path
from typing import Optional, Callable

_LOCAL = threading.local()


def _default_db_path() -> Path:
    # 允许通过环境变量覆盖；否则存放到 outputs/cache.sqlite
    p = os.environ.get("RENPY_CN_CACHE_DB")
    if p:
        return Path(p)
    return Path.cwd() / "outputs" / "cache.sqlite"


def _get_conn(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    key = str(db_path or _default_db_path())
    if not hasattr(_LOCAL, "conns"):
        _LOCAL.conns = {}
    conns = _LOCAL.conns
    if key in conns:
        return conns[key]
    path = Path(db_path) if db_path else _default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
    conn.execute("PRAGMA journal_mode=WAL;")
    conns[key] = conn
    return conn


def kv_get(key: str, db_path: Optional[str | Path] = None) -> Optional[str]:
    try:
        cur = _get_conn(db_path).execute("SELECT v FROM kv WHERE k=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None
    except Exception:
        return None


def kv_set(key: str, value: str, db_path: Optional[str | Path] = None) -> None:
    try:
        conn = _get_conn(db_path)
        conn.execute("INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)", (key, value))
        conn.commit()
    except Exception:
        pass


def text_sha1(s: str) -> str:
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()


def cached(algo: str, version: str, text: str, compute: Callable[[str], str], db_path: Optional[str | Path] = None) -> str:
    """通用缓存：以 {algo}:{version}:{sha1} 为 key 缓存计算结果字符串。"""
    key = f"{algo}:{version}:{text_sha1(text)}"
    v = kv_get(key, db_path)
    if v is not None:
        return v
    v = compute(text)
    kv_set(key, v, db_path)
    return v
