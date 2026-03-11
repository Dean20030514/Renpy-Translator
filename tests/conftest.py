"""
Pytest 配置文件

为所有测试配置共享的 fixtures 和设置
"""

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root_path():
    """返回项目根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def tools_path(project_root_path):
    """返回 tools 目录路径"""
    return project_root_path / "tools"


@pytest.fixture(scope="session")
def src_path(project_root_path):
    """返回 src 目录路径"""
    return project_root_path / "src"


@pytest.fixture
def sample_rpy_content():
    """返回标准的 Ren'Py 测试内容"""
    return '''\
label start:
    "Hello, world!"
    mc "How are you?"
    menu:
        "Option A":
            jump optionA
        "Option B":
            jump optionB
'''


@pytest.fixture
def sample_jsonl_entries():
    """返回标准的 JSONL 测试条目列表"""
    return [
        {"id": "test:1:0", "en": "Hello, world!", "file": "test.rpy", "line": 2, "idx": 0},
        {"id": "test:2:0", "en": "How are you?", "zh": "你好吗？", "file": "test.rpy", "line": 3, "idx": 0},
        {"id": "test:3:0", "en": "Option A", "file": "test.rpy", "line": 5, "idx": 0},
    ]


@pytest.fixture
def write_jsonl(tmp_path):
    """返回一个辅助函数用于写入 JSONL 文件"""
    def _write(filename: str, entries: list[dict]) -> Path:
        p = tmp_path / filename
        with p.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return p
    return _write
