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


def kv_set_batch(
    items: list[tuple[str, str]],
    db_path: Optional[str | Path] = None,
    chunk_size: int = 500
) -> tuple[int, int]:
    """
    批量设置缓存值（高效）

    Args:
        items: (key, value) 元组列表
        db_path: 可选的数据库路径
        chunk_size: 每批提交的数量（防止事务过大）

    Returns:
        (成功数, 失败数)
    """
    if not items:
        return 0, 0
    
    success_count = 0
    fail_count = 0
    
    try:
        conn = _get_conn(db_path)
        
        # 分块处理，避免事务过大
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            try:
                conn.executemany(
                    "INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)",
                    chunk
                )
                conn.commit()
                success_count += len(chunk)
            except sqlite3.Error as e:
                logger.warning(f"Batch write failed for chunk {i//chunk_size}: {e}")
                # 回退到单条写入
                for key, value in chunk:
                    if kv_set(key, value, db_path):
                        success_count += 1
                    else:
                        fail_count += 1
        
        return success_count, fail_count
        
    except sqlite3.Error as e:
        logger.error(f"Batch cache write failed: {e}")
        return success_count, len(items) - success_count


def kv_get_batch(
    keys: list[str],
    db_path: Optional[str | Path] = None
) -> dict[str, Optional[str]]:
    """
    批量获取缓存值

    Args:
        keys: 缓存键列表
        db_path: 可选的数据库路径

    Returns:
        {key: value} 字典，未找到的键值为 None
    """
    if not keys:
        return {}
    
    result = {k: None for k in keys}
    
    try:
        conn = _get_conn(db_path)
        # 使用 IN 查询批量获取
        placeholders = ','.join('?' * len(keys))
        query = f"SELECT k, v FROM kv WHERE k IN ({placeholders})"
        cur = conn.execute(query, keys)
        
        for row in cur.fetchall():
            result[row[0]] = row[1]
        
        return result
        
    except sqlite3.Error as e:
        logger.warning(f"Batch cache read failed: {e}")
        return result
    except (OSError, IOError) as e:
        logger.warning(f"Cache I/O error: {e}")
        return result


def kv_delete(key: str, db_path: Optional[str | Path] = None) -> bool:
    """
    删除缓存值

    Args:
        key: 缓存键
        db_path: 可选的数据库路径

    Returns:
        是否成功删除
    """
    try:
        conn = _get_conn(db_path)
        conn.execute("DELETE FROM kv WHERE k=?", (key,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Cache delete failed for key '{key[:50]}...': {e}")
        return False


def kv_clear(db_path: Optional[str | Path] = None) -> bool:
    """
    清空所有缓存

    Args:
        db_path: 可选的数据库路径

    Returns:
        是否成功清空
    """
    try:
        conn = _get_conn(db_path)
        conn.execute("DELETE FROM kv")
        conn.commit()
        logger.info("Cache cleared")
        return True
    except sqlite3.Error as e:
        logger.error(f"Cache clear failed: {e}")
        return False


def kv_count(db_path: Optional[str | Path] = None) -> int:
    """
    获取缓存条目数

    Args:
        db_path: 可选的数据库路径

    Returns:
        缓存条目数
    """
    try:
        conn = _get_conn(db_path)
        cur = conn.execute("SELECT COUNT(*) FROM kv")
        return cur.fetchone()[0]
    except sqlite3.Error as e:
        logger.warning(f"Cache count failed: {e}")
        return 0


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
