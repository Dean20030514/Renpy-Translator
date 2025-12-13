"""
缓存模块 - 提供基于 SQLite 的键值缓存

支持:
- 线程安全的连接管理
- 自动创建缓存目录
- WAL 模式提高并发性能
- 优雅的资源清理
"""

from __future__ import annotations

import atexit
import hashlib
import logging
import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

_LOCAL = threading.local()
_ALL_CONNS: dict[str, sqlite3.Connection] = {}
_CONNS_LOCK = threading.Lock()


def _default_db_path() -> Path:
    """获取默认数据库路径，支持环境变量覆盖"""
    p = os.environ.get("RENPY_CN_CACHE_DB")
    if p:
        return Path(p)
    return Path.cwd() / "outputs" / "cache.sqlite"


def _get_conn(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    """获取数据库连接（线程局部缓存）"""
    key = str(db_path or _default_db_path())

    if not hasattr(_LOCAL, "conns"):
        _LOCAL.conns = {}
    conns = _LOCAL.conns

    if key in conns:
        return conns[key]

    path = Path(db_path) if db_path else _default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(str(path), timeout=10.0)
        conn.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
        conn.execute("PRAGMA journal_mode=WAL;")
        conns[key] = conn

        # 注册全局连接以便清理
        with _CONNS_LOCK:
            _ALL_CONNS[f"{threading.current_thread().ident}:{key}"] = conn

        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to cache database {path}: {e}")
        raise


def close_all_connections() -> None:
    """关闭所有缓存数据库连接"""
    with _CONNS_LOCK:
        for conn_key, conn in list(_ALL_CONNS.items()):
            try:
                conn.close()
            except sqlite3.Error:
                pass  # 忽略关闭错误
        _ALL_CONNS.clear()

    # 清理线程局部存储
    if hasattr(_LOCAL, "conns"):
        _LOCAL.conns.clear()


# 注册退出时清理
atexit.register(close_all_connections)


def kv_get(key: str, db_path: Optional[str | Path] = None) -> Optional[str]:
    """
    从缓存获取值

    Args:
        key: 缓存键
        db_path: 可选的数据库路径

    Returns:
        缓存的值，如果不存在或出错返回 None
    """
    try:
        cur = _get_conn(db_path).execute("SELECT v FROM kv WHERE k=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        logger.warning(f"Cache read failed for key '{key[:50]}...': {e}")
        return None
    except (OSError, IOError) as e:
        logger.warning(f"Cache I/O error: {e}")
        return None


def kv_set(key: str, value: str, db_path: Optional[str | Path] = None) -> bool:
    """
    设置缓存值

    Args:
        key: 缓存键
        value: 缓存值
        db_path: 可选的数据库路径

    Returns:
        是否成功设置
    """
    try:
        conn = _get_conn(db_path)
        conn.execute("INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)", (key, value))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Cache write failed for key '{key[:50]}...': {e}")
        return False
    except (OSError, IOError) as e:
        logger.warning(f"Cache I/O error: {e}")
        return False


def text_hash(s: str) -> str:
    """计算文本的 SHA256 哈希（用于缓存键）"""
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


# 保留旧名称以保持向后兼容
text_sha1 = text_hash


def cached(
    algo: str,
    version: str,
    text: str,
    compute: Callable[[str], str],
    db_path: Optional[str | Path] = None
) -> str:
    """
    通用缓存装饰器

    以 {algo}:{version}:{hash} 为 key 缓存计算结果字符串。

    Args:
        algo: 算法名称
        version: 版本号
        text: 输入文本
        compute: 计算函数
        db_path: 可选的数据库路径

    Returns:
        计算结果（可能来自缓存）
    """
    key = f"{algo}:{version}:{text_hash(text)}"
    v = kv_get(key, db_path)
    if v is not None:
        return v
    v = compute(text)
    kv_set(key, v, db_path)
    return v
