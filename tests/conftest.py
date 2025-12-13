"""
Pytest 配置文件

为所有测试配置共享的 fixtures 和设置
"""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


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
