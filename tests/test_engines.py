#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引擎抽象层测试。覆盖 EngineProfile / TranslatableUnit / EngineDetector / RenPyEngine。"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ============================================================
# EngineProfile 测试
# ============================================================

def test_profile_compile_placeholder_empty():
    """空占位符列表 → None"""
    from engines.engine_base import EngineProfile
    p = EngineProfile(name="test", display_name="Test", placeholder_patterns=[])
    assert p.compile_placeholder_re() is None
    print("[OK] profile_compile_placeholder_empty")


def test_profile_compile_placeholder_single():
    """单模式编译正确"""
    from engines.engine_base import EngineProfile
    p = EngineProfile(name="test", display_name="Test",
                      placeholder_patterns=[r"\[\w+\]"])
    regex = p.compile_placeholder_re()
    assert regex is not None
    assert regex.search("[name]") is not None
    assert regex.search("hello") is None
    print("[OK] profile_compile_placeholder_single")


def test_profile_compile_placeholder_multi():
    """多模式用 | 合并"""
    from engines.engine_base import EngineProfile
    p = EngineProfile(name="test", display_name="Test",
                      placeholder_patterns=[r"\[\w+\]", r"\{[^}]+\}"])
    regex = p.compile_placeholder_re()
    assert regex is not None
    assert regex.search("[var]") is not None
    assert regex.search("{tag}") is not None
    assert regex.search("plain") is None
    print("[OK] profile_compile_placeholder_multi")


def test_profile_compile_skip_empty():
    """空 skip 列表 → None"""
    from engines.engine_base import EngineProfile
    p = EngineProfile(name="test", display_name="Test", skip_line_patterns=[])
    assert p.compile_skip_re() is None
    print("[OK] profile_compile_skip_empty")


def test_profile_compile_skip_pattern():
    """skip 模式编译正确"""
    from engines.engine_base import EngineProfile
    p = EngineProfile(name="test", display_name="Test",
                      skip_line_patterns=[r"^\s*label\s+", r"^\s*screen\s+"])
    regex = p.compile_skip_re()
    assert regex is not None
    assert regex.search("label start:") is not None
    assert regex.search("    screen main():") is not None
    assert regex.search('    "Hello"') is None
    print("[OK] profile_compile_skip_pattern")


def test_engine_profiles_registry():
    """ENGINE_PROFILES 字典完整性 + rpgmaker_mv/mz 指向同一实例"""
    from engines.engine_base import ENGINE_PROFILES
    assert "renpy" in ENGINE_PROFILES
    assert "rpgmaker_mv" in ENGINE_PROFILES
    assert "rpgmaker_mz" in ENGINE_PROFILES
    assert "csv" in ENGINE_PROFILES
    # MV 和 MZ 指向同一个 Profile 实例
    assert ENGINE_PROFILES["rpgmaker_mv"] is ENGINE_PROFILES["rpgmaker_mz"]
    print("[OK] engine_profiles_registry")


# ============================================================
# TranslatableUnit 测试
# ============================================================

def test_unit_defaults():
    """TranslatableUnit 默认值正确"""
    from engines.engine_base import TranslatableUnit
    u = TranslatableUnit(id="test_001", original="Hello", file_path="test.json")
    assert u.status == "pending"
    assert u.translation == ""
    assert u.context == ""
    assert u.speaker == ""
    assert u.metadata == {}
    print("[OK] unit_defaults")


def test_unit_fields():
    """TranslatableUnit 字段赋值和读取"""
    from engines.engine_base import TranslatableUnit
    u = TranslatableUnit(
        id="map1:ev3", original="Welcome!", file_path="Map001.json",
        speaker="Guard", context="near gate", translation="欢迎！",
        status="translated", metadata={"code": 401, "idx": 5},
    )
    assert u.id == "map1:ev3"
    assert u.speaker == "Guard"
    assert u.metadata["code"] == 401
    assert u.status == "translated"
    print("[OK] unit_fields")


def test_unit_metadata_roundtrip():
    """metadata round-trip"""
    from engines.engine_base import TranslatableUnit
    meta = {"start_idx": 5, "line_count": 3, "type": "dialogue"}
    u = TranslatableUnit(id="t1", original="hi", file_path="f.json", metadata=meta)
    assert u.metadata is meta  # 同一引用
    u.metadata["extra"] = True
    assert meta["extra"] is True
    print("[OK] unit_metadata_roundtrip")


# ============================================================
# EngineDetector 测试
# ============================================================

def test_detect_renpy():
    """检测 Ren'Py 目录（有 game/*.rpy）"""
    from engines.engine_detector import detect_engine_type, EngineType
    with tempfile.TemporaryDirectory() as d:
        game = Path(d) / "game"
        game.mkdir()
        (game / "script.rpy").write_text("label start:", encoding="utf-8")
        assert detect_engine_type(Path(d)) == EngineType.RENPY
    print("[OK] detect_renpy")


def test_detect_renpy_root():
    """检测 Ren'Py 目录（根目录有 .rpy）"""
    from engines.engine_detector import detect_engine_type, EngineType
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "script.rpy").write_text("label start:", encoding="utf-8")
        assert detect_engine_type(Path(d)) == EngineType.RENPY
    print("[OK] detect_renpy_root")


def test_detect_rpgmaker_mv():
    """检测 RPG Maker MV（www/data/System.json）"""
    from engines.engine_detector import detect_engine_type, EngineType
    with tempfile.TemporaryDirectory() as d:
        data = Path(d) / "www" / "data"
        data.mkdir(parents=True)
        (data / "System.json").write_text("{}", encoding="utf-8")
        assert detect_engine_type(Path(d)) == EngineType.RPGMAKER_MV
    print("[OK] detect_rpgmaker_mv")


def test_detect_rpgmaker_mz():
    """检测 RPG Maker MZ（data/System.json，无 www/）"""
    from engines.engine_detector import detect_engine_type, EngineType
    with tempfile.TemporaryDirectory() as d:
        data = Path(d) / "data"
        data.mkdir()
        (data / "System.json").write_text("{}", encoding="utf-8")
        assert detect_engine_type(Path(d)) == EngineType.RPGMAKER_MV  # MZ 用同一枚举
    print("[OK] detect_rpgmaker_mz")


def test_detect_vxace():
    """检测 RPG Maker VX/Ace（.rgss3a）"""
    from engines.engine_detector import detect_engine_type, EngineType
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "Game.rgss3a").write_bytes(b"\x00")
        assert detect_engine_type(Path(d)) == EngineType.RPGMAKER_VXACE
    print("[OK] detect_vxace")


def test_detect_unknown():
    """未知目录"""
    from engines.engine_detector import detect_engine_type, EngineType
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "readme.txt").write_text("nothing", encoding="utf-8")
        assert detect_engine_type(Path(d)) == EngineType.UNKNOWN
    print("[OK] detect_unknown")


def test_create_engine_renpy():
    """create_engine: RENPY → RenPyEngine 实例"""
    from engines.engine_detector import create_engine, EngineType
    from engines.renpy_engine import RenPyEngine
    engine = create_engine(EngineType.RENPY)
    assert isinstance(engine, RenPyEngine)
    print("[OK] create_engine_renpy")


def test_create_engine_unknown():
    """create_engine: UNKNOWN → None"""
    from engines.engine_detector import create_engine, EngineType
    engine = create_engine(EngineType.UNKNOWN)
    assert engine is None
    print("[OK] create_engine_unknown")


def test_resolve_engine_auto_renpy():
    """resolve_engine: auto + Ren'Py 目录"""
    from engines.engine_detector import resolve_engine
    from engines.renpy_engine import RenPyEngine
    with tempfile.TemporaryDirectory() as d:
        game = Path(d) / "game"
        game.mkdir()
        (game / "script.rpy").write_text("label start:", encoding="utf-8")
        engine = resolve_engine("auto", Path(d))
        assert isinstance(engine, RenPyEngine)
    print("[OK] resolve_engine_auto_renpy")


def test_resolve_engine_manual_renpy():
    """resolve_engine: renpy 显式指定"""
    from engines.engine_detector import resolve_engine
    from engines.renpy_engine import RenPyEngine
    with tempfile.TemporaryDirectory() as d:
        engine = resolve_engine("renpy", Path(d))
        assert isinstance(engine, RenPyEngine)
    print("[OK] resolve_engine_manual_renpy")


# ============================================================
# RenPyEngine 测试
# ============================================================

def test_renpy_engine_detect_true():
    """RenPyEngine.detect: 有 .rpy 返回 True"""
    from engines.renpy_engine import RenPyEngine
    engine = RenPyEngine()
    with tempfile.TemporaryDirectory() as d:
        game = Path(d) / "game"
        game.mkdir()
        (game / "script.rpy").write_text("label start:", encoding="utf-8")
        assert engine.detect(Path(d)) is True
    print("[OK] renpy_engine_detect_true")


def test_renpy_engine_detect_false():
    """RenPyEngine.detect: 无 .rpy 返回 False"""
    from engines.renpy_engine import RenPyEngine
    engine = RenPyEngine()
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "readme.txt").write_text("nothing", encoding="utf-8")
        assert engine.detect(Path(d)) is False
    print("[OK] renpy_engine_detect_false")


def test_renpy_engine_extract_raises():
    """RenPyEngine.extract_texts: 抛 NotImplementedError"""
    from engines.renpy_engine import RenPyEngine
    engine = RenPyEngine()
    try:
        engine.extract_texts(Path("."))
        assert False, "should raise NotImplementedError"
    except NotImplementedError:
        pass
    print("[OK] renpy_engine_extract_raises")


def test_renpy_engine_writeback_raises():
    """RenPyEngine.write_back: 抛 NotImplementedError"""
    from engines.renpy_engine import RenPyEngine
    engine = RenPyEngine()
    try:
        engine.write_back(Path("."), [], Path("."))
        assert False, "should raise NotImplementedError"
    except NotImplementedError:
        pass
    print("[OK] renpy_engine_writeback_raises")


def test_renpy_engine_profile():
    """RenPyEngine.profile.name == 'renpy'"""
    from engines.renpy_engine import RenPyEngine
    engine = RenPyEngine()
    assert engine.profile.name == "renpy"
    assert engine.profile.display_name == "Ren'Py"
    print("[OK] renpy_engine_profile")


# ============================================================
# EngineBase 测试
# ============================================================

def test_engine_base_dry_run():
    """EngineBase.dry_run 默认实现"""
    from engines.engine_base import EngineBase, EngineProfile, TranslatableUnit

    class MockEngine(EngineBase):
        def _default_profile(self):
            return EngineProfile(name="mock", display_name="Mock")
        def detect(self, game_dir):
            return False
        def extract_texts(self, game_dir, **kw):
            return [
                TranslatableUnit(id="1", original="Hello", file_path="a.json"),
                TranslatableUnit(id="2", original="World", file_path="a.json"),
                TranslatableUnit(id="3", original="Test", file_path="b.json"),
            ]
        def write_back(self, game_dir, units, output_dir, **kw):
            return 0

    engine = MockEngine()
    result = engine.dry_run(Path("."))
    assert result["texts"] == 3
    assert result["files"] == 2
    assert result["total_chars"] == len("Hello") + len("World") + len("Test")
    print("[OK] engine_base_dry_run")


# ============================================================
# CSV 提取测试
# ============================================================

def test_csv_basic_extract():
    """CSV 基本提取"""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        csv_path = Path(d) / "test.csv"
        csv_path.write_text(
            "id,original,speaker\nline_001,Hello,Guard\nline_002,World,NPC\n",
            encoding="utf-8",
        )
        units = engine.extract_texts(csv_path)
        assert len(units) == 2
        assert units[0].id == "line_001"
        assert units[0].original == "Hello"
        assert units[0].speaker == "Guard"
    print("[OK] csv_basic_extract")


def test_csv_column_aliases():
    """CSV 列名别名（source/text/en 匹配为 original）"""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    for alias in ("source", "text", "en"):
        with tempfile.TemporaryDirectory() as d:
            csv_path = Path(d) / "test.csv"
            csv_path.write_text(f"key,{alias}\nk1,Hello\n", encoding="utf-8")
            units = engine.extract_texts(csv_path)
            assert len(units) == 1, f"alias '{alias}' failed"
            assert units[0].original == "Hello"
    print("[OK] csv_column_aliases")


def test_csv_no_id_column():
    """CSV 无 ID 列（自动用行号）"""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        csv_path = Path(d) / "test.csv"
        csv_path.write_text("original\nHello\nWorld\n", encoding="utf-8")
        units = engine.extract_texts(csv_path)
        assert len(units) == 2
        assert "1" in units[0].id  # 自动生成含行号的 id
    print("[OK] csv_no_id_column")


def test_csv_utf8_bom():
    """CSV UTF-8 BOM 处理"""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        csv_path = Path(d) / "test.csv"
        csv_path.write_bytes(b"\xef\xbb\xbfid,original\nk1,Hello\n")
        units = engine.extract_texts(csv_path)
        assert len(units) == 1
        assert units[0].original == "Hello"
    print("[OK] csv_utf8_bom")


def test_tsv_extract():
    """TSV 提取（tab 分隔）"""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        tsv_path = Path(d) / "test.tsv"
        tsv_path.write_text("id\toriginal\nk1\tHello\n", encoding="utf-8")
        units = engine.extract_texts(tsv_path)
        assert len(units) == 1
        assert units[0].original == "Hello"
    print("[OK] tsv_extract")


def test_jsonl_basic_extract():
    """JSONL 基本提取"""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        jsonl_path = Path(d) / "test.jsonl"
        jsonl_path.write_text(
            '{"id": "l1", "original": "Hello", "speaker": "Guard"}\n'
            '{"id": "l2", "original": "World"}\n',
            encoding="utf-8",
        )
        units = engine.extract_texts(jsonl_path)
        assert len(units) == 2
        assert units[0].speaker == "Guard"
    print("[OK] jsonl_basic_extract")


def test_json_array_fallback():
    """JSON 数组 fallback"""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        json_path = Path(d) / "test.json"
        json_path.write_text(
            '[{"id": "a1", "original": "Hello"}, {"id": "a2", "original": "World"}]',
            encoding="utf-8",
        )
        units = engine.extract_texts(json_path)
        assert len(units) == 2
    print("[OK] json_array_fallback")


def test_csv_write_back():
    """CSV write_back 输出包含翻译列"""
    from engines.csv_engine import CSVEngine
    from engines.engine_base import TranslatableUnit
    engine = CSVEngine()
    units = [
        TranslatableUnit(id="k1", original="Hello", file_path="test.csv",
                         translation="你好", status="translated",
                         metadata={"source_format": "csv"}),
    ]
    with tempfile.TemporaryDirectory() as d:
        written = engine.write_back(Path("."), units, Path(d), target_lang="zh")
        assert written == 1
        out = Path(d) / "translations_zh.csv"
        assert out.exists()
        content = out.read_text(encoding="utf-8-sig")
        assert "你好" in content
    print("[OK] csv_write_back")


def test_jsonl_write_back():
    """JSONL write_back"""
    from engines.csv_engine import CSVEngine
    from engines.engine_base import TranslatableUnit
    engine = CSVEngine()
    units = [
        TranslatableUnit(id="k1", original="Hello", file_path="test.jsonl",
                         translation="你好", status="translated",
                         metadata={"source_format": "jsonl"}),
    ]
    with tempfile.TemporaryDirectory() as d:
        written = engine.write_back(Path("."), units, Path(d), target_lang="zh")
        assert written == 1
        out = Path(d) / "translations_zh.jsonl"
        assert out.exists()
        line = out.read_text(encoding="utf-8").strip()
        obj = json.loads(line)
        assert obj["zh"] == "你好"
    print("[OK] jsonl_write_back")


def test_csv_directory_scan():
    """CSV 目录扫描提取"""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "a.csv").write_text("original\nHello\n", encoding="utf-8")
        (Path(d) / "b.jsonl").write_text('{"original": "World"}\n', encoding="utf-8")
        (Path(d) / "readme.txt").write_text("ignore me", encoding="utf-8")
        units = engine.extract_texts(Path(d))
        assert len(units) == 2
    print("[OK] csv_directory_scan")


def test_csv_engine_rejects_oversized_json():
    """Round 44 audit-tail: CSVEngine._extract_json_or_jsonl and
    _extract_jsonl skip operator-supplied files above
    _MAX_CSV_JSON_SIZE (50 MB) with a warning rather than loading the
    whole file into memory.  Uses a 51 MB sparse file so the test runs
    instantly without consuming disk; verifies the cap semantics + the
    mixed-directory scan still extracts from the other files."""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        # Legitimate small file — must still be extracted
        (Path(d) / "small.csv").write_text(
            "original\nHello\n", encoding="utf-8",
        )
        # 51 MB sparse oversized JSONL — must be skipped
        big_jsonl = Path(d) / "big.jsonl"
        with open(big_jsonl, "wb") as f:
            f.seek(51 * 1024 * 1024 - 1)
            f.write(b"\0")
        # 51 MB sparse oversized JSON — must be skipped
        big_json = Path(d) / "big.json"
        with open(big_json, "wb") as f:
            f.seek(51 * 1024 * 1024 - 1)
            f.write(b"\0")

        units = engine.extract_texts(Path(d))
        # Only the small.csv entry should extract; big.jsonl / big.json
        # are both skipped by the cap gate.
        rel_files = {u.file_path for u in units}
        assert "big.jsonl" not in rel_files, (
            "oversized .jsonl must be skipped, got units: "
            f"{[u.file_path for u in units]}"
        )
        assert "big.json" not in rel_files, (
            "oversized .json must be skipped, got units: "
            f"{[u.file_path for u in units]}"
        )
        # Small file unaffected.
        assert len(units) == 1, (
            f"expected 1 unit from small.csv, got {len(units)}: "
            f"{[u.file_path for u in units]}"
        )
    print("[OK] csv_engine_rejects_oversized_json")


def test_csv_engine_rejects_oversized_csv():
    """Round 46 Step 4 (G1): CSVEngine._extract_csv skips operator-
    supplied .csv / .tsv files above _MAX_CSV_JSON_SIZE (50 MB) with
    a warning rather than streaming the whole file into the
    accumulated units list.  The r44 audit-tail covered _extract_jsonl
    and _extract_json_or_jsonl but missed _extract_csv; closed by the
    round 45 audit's optional MEDIUM list.  Uses a 51 MB sparse file
    so the test runs instantly without consuming disk."""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        # Legitimate small file — must still be extracted
        (Path(d) / "small.csv").write_text(
            "original\nHello\n", encoding="utf-8",
        )
        # 51 MB sparse oversized .csv — must be skipped
        big_csv = Path(d) / "big.csv"
        with open(big_csv, "wb") as f:
            f.seek(51 * 1024 * 1024 - 1)
            f.write(b"\0")
        # 51 MB sparse oversized .tsv — must be skipped
        big_tsv = Path(d) / "big.tsv"
        with open(big_tsv, "wb") as f:
            f.seek(51 * 1024 * 1024 - 1)
            f.write(b"\0")

        units = engine.extract_texts(Path(d))
        rel_files = {u.file_path for u in units}
        assert "big.csv" not in rel_files, (
            "oversized .csv must be skipped, got units: "
            f"{[u.file_path for u in units]}"
        )
        assert "big.tsv" not in rel_files, (
            "oversized .tsv must be skipped, got units: "
            f"{[u.file_path for u in units]}"
        )
        assert len(units) == 1, (
            f"expected 1 unit from small.csv, got {len(units)}: "
            f"{[u.file_path for u in units]}"
        )
    print("[OK] csv_engine_rejects_oversized_csv")


def test_csv_engine_accepts_exact_cap_csv():
    """Round 47 Step 2 (G1 boundary): exact-cap-size CSV must NOT
    trigger the cap because the operator is ``>`` not ``>=`` (line 219
    of csv_engine.py).  Pins this contract — a future change to ``>=``
    would silently reject many legitimate large CSVs at the boundary.
    Uses mock.patch on _MAX_CSV_JSON_SIZE so we don't need a real
    50 MB file."""
    from unittest import mock
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        exact_csv = Path(d) / "exact.csv"
        # Build a small valid CSV; remember its exact size for cap mock
        exact_csv.write_text("original\nHello\n", encoding="utf-8")
        size = exact_csv.stat().st_size
        with mock.patch("engines.csv_engine._MAX_CSV_JSON_SIZE", size):
            units = engine.extract_texts(Path(d))
        originals = [u.original for u in units if u.file_path == "exact.csv"]
        assert "Hello" in originals, (
            f"exact-cap-size CSV (file_size == cap) must NOT trigger > cap; "
            f"expected 'Hello' in extracted units, got {originals}"
        )
    print("[OK] csv_engine_accepts_exact_cap_csv")


def test_csv_engine_handles_empty_csv():
    """Round 47 Step 2 (G1 boundary): empty 0-byte CSV file must not
    crash the cap check or csv.DictReader.  Returns 0 units (no header
    means csv.DictReader.fieldnames is None -> early return [])."""
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        empty_csv = Path(d) / "empty.csv"
        empty_csv.write_bytes(b"")  # exactly 0 bytes
        assert empty_csv.stat().st_size == 0
        units = engine.extract_texts(Path(d))
        empty_units = [u for u in units if u.file_path == "empty.csv"]
        assert len(empty_units) == 0, (
            f"empty 0-byte CSV must yield 0 units, got {len(empty_units)}"
        )
    print("[OK] csv_engine_handles_empty_csv")


def test_csv_engine_handles_stat_oserror_fail_open():
    """Round 47 Step 2 (G1 boundary): Path.stat() OSError must trigger
    the fail-open path (fsize=0 < cap), so the file goes through normal
    csv.DictReader processing rather than being skipped.  Pins the
    intentional fail-open design.  The post-open os.fstat() (r47 D3
    defense) is unaffected because it uses the open file descriptor."""
    import os as _os
    from unittest import mock
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        target_csv = Path(d) / "target.csv"
        target_csv.write_text("original\nHello\n", encoding="utf-8")
        # Selectively raise OSError only for target.csv path.stat()
        original_stat = Path.stat
        def _selective_stat(self, *, follow_symlinks=True):
            if self.name == "target.csv":
                raise OSError("simulated stat failure")
            return original_stat(self, follow_symlinks=follow_symlinks)
        with mock.patch.object(Path, "stat", _selective_stat):
            units = engine.extract_texts(Path(d))
        originals = [u.original for u in units if u.file_path == "target.csv"]
        assert "Hello" in originals, (
            f"stat() OSError fail-open: file must still be processed via "
            f"normal path; got originals={originals}"
        )
    print("[OK] csv_engine_handles_stat_oserror_fail_open")


def test_csv_engine_rejects_toctou_growth_attack():
    """Round 47 Step 2 (D3 TOCTOU defense): if a file appears small at
    Path.stat() but has grown to > cap by the time of the post-open
    os.fstat() inside the with-open block, the file must be rejected.
    Pins the new TOCTOU defense added in round 47 Step 2."""
    from unittest import mock
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        target_csv = Path(d) / "toctou.csv"
        target_csv.write_text("original\nHello\n", encoding="utf-8")
        small_cap = 100  # mock cap

        # Mock os.fstat to return huge size — simulates "file grew
        # between Path.stat() and open()".  The real Path.stat() above
        # returns the actual small size (~ 15 bytes < 100 cap), so the
        # pre-open gate passes; the post-open fstat() now sees > cap.
        class _LargeStatResult:
            st_size = 99999  # > small_cap = 100
        def _patched_os_fstat(fd):
            return _LargeStatResult()

        with mock.patch("engines.csv_engine.os.fstat", _patched_os_fstat), \
             mock.patch("engines.csv_engine._MAX_CSV_JSON_SIZE", small_cap):
            units = engine.extract_texts(Path(d))

        originals = [u.original for u in units if u.file_path == "toctou.csv"]
        assert "Hello" not in originals, (
            "TOCTOU defense: file that grew past cap between stat and "
            f"open must be rejected; got originals={originals}"
        )
    print("[OK] csv_engine_rejects_toctou_growth_attack")


def test_csv_engine_accepts_cap_minus_1_csv():
    """Round 48 Step 1 (G1.1 boundary expansion): file size = cap-1
    must NOT trigger ``> cap``.  Together with r47's
    ``test_csv_engine_accepts_exact_cap_csv`` (== cap) and the new
    ``test_csv_engine_rejects_cap_plus_1_csv`` below, fully pins the
    lower / equal / upper edges of the ``>`` operator contract."""
    from unittest import mock
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        cm1_csv = Path(d) / "cap_minus_1.csv"
        cm1_csv.write_text("original\nHello\n", encoding="utf-8")
        size = cm1_csv.stat().st_size
        # mock cap = size + 1 -> file_size = cap - 1
        with mock.patch("engines.csv_engine._MAX_CSV_JSON_SIZE", size + 1):
            units = engine.extract_texts(Path(d))
        originals = [u.original for u in units if u.file_path == "cap_minus_1.csv"]
        assert "Hello" in originals, (
            f"cap-1 file size must NOT trigger > cap; "
            f"expected 'Hello' in extracted units, got {originals}"
        )
    print("[OK] csv_engine_accepts_cap_minus_1_csv")


def test_csv_engine_rejects_cap_plus_1_csv():
    """Round 48 Step 1 (G1.1 boundary expansion): file size = cap+1
    MUST trigger ``> cap`` and reject.  The smallest size that should
    be rejected — the upper edge of the ``>`` operator contract."""
    from unittest import mock
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        cp1_csv = Path(d) / "cap_plus_1.csv"
        cp1_csv.write_text("original\nHello\n", encoding="utf-8")
        size = cp1_csv.stat().st_size
        # mock cap = size - 1 -> file_size = cap + 1
        with mock.patch("engines.csv_engine._MAX_CSV_JSON_SIZE", size - 1):
            units = engine.extract_texts(Path(d))
        originals = [u.original for u in units if u.file_path == "cap_plus_1.csv"]
        assert "Hello" not in originals, (
            f"cap+1 file size must trigger > cap and reject; "
            f"expected empty, got {originals}"
        )
    print("[OK] csv_engine_rejects_cap_plus_1_csv")


def test_csv_engine_logs_csv_error_distinct_from_generic():
    """Round 48 Step 1 (L1 informational): when csv.DictReader raises
    csv.Error (typically on TOCTOU truncation or malformed CSV mid-
    row), the explicit ``except csv.Error`` branch must catch it
    BEFORE the generic ``except Exception`` falls through.  Verified
    via mock injecting csv.Error and checking the operator-facing
    log message uses "CSV 解析错误" (CSV-specific) rather than
    "解析失败" (generic).  Closes the round 47 audit's 1 LOW
    informational gap."""
    import csv
    import logging
    from unittest import mock
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "bad.csv"
        target.write_text("original\nHello\n", encoding="utf-8")

        # Patch _extract_csv to raise csv.Error (simulates DictReader
        # crashing on a truncated row inside extract_texts try/except).
        def _raise_csv_error(self, filepath, delimiter=","):
            raise csv.Error("simulated truncation: line missing field")

        with mock.patch.object(CSVEngine, "_extract_csv", _raise_csv_error):
            # Capture logger output to verify the CSV-specific message
            # branch fired (not the generic "解析失败" fallback).
            captured: list[str] = []

            class _CaptureHandler(logging.Handler):
                def emit(self, record: logging.LogRecord) -> None:
                    captured.append(record.getMessage())

            handler = _CaptureHandler(level=logging.ERROR)
            logger = logging.getLogger("renpy_translator")
            logger.addHandler(handler)
            try:
                units = engine.extract_texts(Path(d))
            finally:
                logger.removeHandler(handler)

        # No units extracted (csv.Error caught, return []).
        assert not [u for u in units if u.file_path == "bad.csv"], (
            "csv.Error must result in 0 units for the failing file"
        )
        # The CSV-specific log message branch fired.
        csv_error_msgs = [m for m in captured if "CSV 解析错误" in m]
        generic_fail_msgs = [m for m in captured if "解析失败" in m]
        assert csv_error_msgs, (
            f"csv.Error must trigger the explicit 'CSV 解析错误' branch; "
            f"captured={captured}"
        )
        assert not generic_fail_msgs, (
            f"csv.Error must NOT fall through to generic '解析失败' branch; "
            f"captured={captured}"
        )
    print("[OK] csv_engine_logs_csv_error_distinct_from_generic")


def test_csv_engine_rejects_jsonl_toctou_growth_attack():
    """Round 48 Step 2 (D method scope expansion): jsonl extractor must
    reject files that grew between Path.stat() and open() so the
    post-open fstat sees > cap.  Mirrors r47 Step 2's csv TOCTOU test
    but for the _extract_jsonl path (which reads entire file via
    f.read() before splitting lines — without fstat re-check, attacker
    can OOM the host with a sparse-then-grown file)."""
    from unittest import mock
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        target_jsonl = Path(d) / "toctou.jsonl"
        target_jsonl.write_text(
            '{"original": "Hello"}\n', encoding="utf-8"
        )
        small_cap = 100  # mock cap

        # Mock check_fstat_size to return (False, huge) — simulates
        # "file grew between Path.stat and open" inside _extract_jsonl.
        # Path.stat() above returns the actual small size, passing the
        # pre-open gate; the post-open helper now sees > cap.
        def _patched_check(file_obj, max_size):
            return (False, 99999)  # ok=False, size=99999

        with mock.patch("engines.csv_engine.check_fstat_size", _patched_check), \
             mock.patch("engines.csv_engine._MAX_CSV_JSON_SIZE", small_cap):
            units = engine.extract_texts(Path(d))

        originals = [u.original for u in units if u.file_path == "toctou.jsonl"]
        assert "Hello" not in originals, (
            "JSONL TOCTOU defense: file that grew past cap between stat "
            f"and open must be rejected; got originals={originals}"
        )
    print("[OK] csv_engine_rejects_jsonl_toctou_growth_attack")


def test_csv_engine_rejects_json_toctou_growth_attack():
    """Round 48 Step 2 (D method scope expansion): .json dispatch must
    reject files that grew between Path.stat() and open() so the
    post-open fstat sees > cap.  The .json path reads the entire file
    via f.read() before json.loads(); same TOCTOU surface as
    _extract_jsonl, mitigated via the same helper."""
    from unittest import mock
    from engines.csv_engine import CSVEngine
    engine = CSVEngine()
    with tempfile.TemporaryDirectory() as d:
        target_json = Path(d) / "toctou.json"
        target_json.write_text(
            '[{"original": "Hello"}]', encoding="utf-8"
        )
        small_cap = 100  # mock cap

        def _patched_check(file_obj, max_size):
            return (False, 99999)

        with mock.patch("engines.csv_engine.check_fstat_size", _patched_check), \
             mock.patch("engines.csv_engine._MAX_CSV_JSON_SIZE", small_cap):
            units = engine.extract_texts(Path(d))

        originals = [u.original for u in units if u.file_path == "toctou.json"]
        assert "Hello" not in originals, (
            ".json TOCTOU defense: file that grew past cap between stat "
            f"and open must be rejected; got originals={originals}"
        )
    print("[OK] csv_engine_rejects_json_toctou_growth_attack")


# ============================================================
# generic_pipeline 测试
# ============================================================

def test_build_generic_chunks_single():
    """build_generic_chunks: 30 条 → 1 chunk"""
    from engines.generic_pipeline import build_generic_chunks
    from engines.engine_base import TranslatableUnit
    units = [TranslatableUnit(id=f"u{i}", original=f"line {i}", file_path="a.csv")
             for i in range(25)]
    chunks = build_generic_chunks(units, max_size=30)
    assert len(chunks) == 1
    assert len(chunks[0].units) == 25
    print("[OK] build_generic_chunks_single")


def test_build_generic_chunks_split():
    """build_generic_chunks: 60 条 → 2 chunks"""
    from engines.generic_pipeline import build_generic_chunks
    from engines.engine_base import TranslatableUnit
    units = [TranslatableUnit(id=f"u{i}", original=f"line {i}", file_path="a.csv")
             for i in range(60)]
    chunks = build_generic_chunks(units, max_size=30)
    assert len(chunks) == 2
    assert len(chunks[0].units) + len(chunks[1].units) == 60
    print("[OK] build_generic_chunks_split")


def test_build_generic_chunks_by_file():
    """build_generic_chunks: 按 file_path 分组"""
    from engines.generic_pipeline import build_generic_chunks
    from engines.engine_base import TranslatableUnit
    units = [
        TranslatableUnit(id="a1", original="Hello", file_path="a.csv"),
        TranslatableUnit(id="b1", original="World", file_path="b.csv"),
        TranslatableUnit(id="a2", original="Foo", file_path="a.csv"),
    ]
    chunks = build_generic_chunks(units, max_size=30)
    # a.csv 的 2 条在一个 chunk，b.csv 的 1 条在另一个 chunk
    assert len(chunks) == 2
    print("[OK] build_generic_chunks_by_file")


def test_match_translations_to_units():
    """翻译结果匹配到 TranslatableUnit"""
    from engines.generic_pipeline import _match_translations_to_units
    from engines.engine_base import TranslatableUnit
    units = [
        TranslatableUnit(id="k1", original="Hello", file_path="a.csv"),
        TranslatableUnit(id="k2", original="World", file_path="a.csv"),
    ]
    translations = [
        {"id": "k1", "zh": "你好"},
        {"id": "k2", "zh": "世界"},
    ]
    matched = _match_translations_to_units(translations, units, "zh")
    assert matched == 2
    assert units[0].translation == "你好"
    assert units[0].status == "translated"
    print("[OK] match_translations_to_units")


def test_match_translations_fallback():
    """翻译结果 id 不匹配时按 original fallback"""
    from engines.generic_pipeline import _match_translations_to_units
    from engines.engine_base import TranslatableUnit
    units = [TranslatableUnit(id="k1", original="Hello", file_path="a.csv")]
    translations = [{"id": "wrong_id", "original": "Hello", "zh": "你好"}]
    matched = _match_translations_to_units(translations, units, "zh")
    assert matched == 1
    assert units[0].translation == "你好"
    print("[OK] match_translations_fallback")


# ============================================================
# patcher/checker 参数化测试
# ============================================================

def test_protect_placeholders_custom_patterns():
    """protect_placeholders(patterns=RPG Maker) 正确保护"""
    from file_processor import protect_placeholders
    rpg_patterns = [r"\\V\[\d+\]", r"\\N\[\d+\]"]
    text = r"Hello \V[1], I am \N[2]"
    protected, mapping = protect_placeholders(text, patterns=rpg_patterns)
    assert r"\V[1]" not in protected
    assert "__RENPY_PH_" in protected
    assert len(mapping) == 2
    print("[OK] protect_placeholders_custom_patterns")


def test_protect_placeholders_default_unchanged():
    """protect_placeholders(patterns=None) 行为不变"""
    from file_processor import protect_placeholders
    text = "Hello [name], you have {color=#f00}red{/color} text"
    protected, mapping = protect_placeholders(text)
    assert "[name]" not in protected
    assert "__RENPY_PH_" in protected
    print("[OK] protect_placeholders_default_unchanged")


def test_check_response_item_custom_re():
    """check_response_item(placeholder_re=custom) 使用自定义正则"""
    import re
    from file_processor import check_response_item
    custom_re = re.compile(r"(\\V\[\d+\])")
    # 占位符一致 → 通过
    item_ok = {"original": r"Hi \V[1]", "zh": r"嗨 \V[1]"}
    assert check_response_item(item_ok, placeholder_re=custom_re) == []
    # 占位符缺失 → 不通过
    item_bad = {"original": r"Hi \V[1]", "zh": "嗨"}
    warns = check_response_item(item_bad, placeholder_re=custom_re)
    assert len(warns) > 0
    print("[OK] check_response_item_custom_re")


def test_check_response_item_default_unchanged():
    """check_response_item(placeholder_re=None) 行为不变"""
    from file_processor import check_response_item
    item = {"original": "Hello [name]", "zh": "你好 [name]"}
    assert check_response_item(item) == []
    print("[OK] check_response_item_default_unchanged")


# ============================================================
# prompts addon 测试
# ============================================================

def test_prompt_addon_none():
    """build_system_prompt(engine_profile=None) 零变更"""
    from core.prompts import build_system_prompt
    base = build_system_prompt(genre="adult")
    with_none = build_system_prompt(genre="adult", engine_profile=None)
    assert base == with_none
    print("[OK] prompt_addon_none")


def test_prompt_addon_rpgmaker():
    """build_system_prompt(engine_profile=rpgmaker) 包含 addon"""
    from core.prompts import build_system_prompt
    from engines.engine_base import RPGMAKER_MV_PROFILE
    result = build_system_prompt(genre="adult", engine_profile=RPGMAKER_MV_PROFILE)
    assert "\\V[n]" in result or "RPG Maker" in result
    print("[OK] prompt_addon_rpgmaker")




# ============================================================
# Runner
# ============================================================

if __name__ == "__main__":
    # EngineProfile
    test_profile_compile_placeholder_empty()
    test_profile_compile_placeholder_single()
    test_profile_compile_placeholder_multi()
    test_profile_compile_skip_empty()
    test_profile_compile_skip_pattern()
    test_engine_profiles_registry()
    # TranslatableUnit
    test_unit_defaults()
    test_unit_fields()
    test_unit_metadata_roundtrip()
    # EngineDetector
    test_detect_renpy()
    test_detect_renpy_root()
    test_detect_rpgmaker_mv()
    test_detect_rpgmaker_mz()
    test_detect_vxace()
    test_detect_unknown()
    test_create_engine_renpy()
    test_create_engine_unknown()
    test_resolve_engine_auto_renpy()
    test_resolve_engine_manual_renpy()
    # RenPyEngine
    test_renpy_engine_detect_true()
    test_renpy_engine_detect_false()
    test_renpy_engine_extract_raises()
    test_renpy_engine_writeback_raises()
    test_renpy_engine_profile()
    # EngineBase
    test_engine_base_dry_run()
    # CSV Engine
    test_csv_basic_extract()
    test_csv_column_aliases()
    test_csv_no_id_column()
    test_csv_utf8_bom()
    test_tsv_extract()
    test_jsonl_basic_extract()
    test_json_array_fallback()
    test_csv_write_back()
    test_jsonl_write_back()
    test_csv_directory_scan()
    # Round 44 audit-tail: CSV/JSON 50 MB cap
    test_csv_engine_rejects_oversized_json()
    # Round 46 Step 4 (G1): CSV/TSV 50 MB cap (audit-tail follow-up)
    test_csv_engine_rejects_oversized_csv()
    # Round 47 Step 2 (G1 boundary + D3 TOCTOU defense)
    test_csv_engine_accepts_exact_cap_csv()
    test_csv_engine_handles_empty_csv()
    test_csv_engine_handles_stat_oserror_fail_open()
    test_csv_engine_rejects_toctou_growth_attack()
    # Round 48 Step 1 (G1.1 boundary expansion + L1 csv.Error branch)
    test_csv_engine_accepts_cap_minus_1_csv()
    test_csv_engine_rejects_cap_plus_1_csv()
    test_csv_engine_logs_csv_error_distinct_from_generic()
    # Round 48 Step 2 (D method scope expansion): TOCTOU defense for jsonl/json
    test_csv_engine_rejects_jsonl_toctou_growth_attack()
    test_csv_engine_rejects_json_toctou_growth_attack()
    # generic_pipeline
    test_build_generic_chunks_single()
    test_build_generic_chunks_split()
    test_build_generic_chunks_by_file()
    test_match_translations_to_units()
    test_match_translations_fallback()
    # patcher/checker parameterization
    test_protect_placeholders_custom_patterns()
    test_protect_placeholders_default_unchanged()
    test_check_response_item_custom_re()
    test_check_response_item_default_unchanged()
    # prompts addon
    test_prompt_addon_none()
    test_prompt_addon_rpgmaker()
    # Round 40: RPG Maker MV/MZ tests (15) moved to
    # tests/test_engines_rpgmaker.py to bring this file under the
    # CLAUDE.md 800-line soft limit (962 -> 694).

    print()
    print("=" * 40)
    # Note: number = main block test_*() invocations (which equals
    # the ``^def test_`` count in this file).  Round 47 had a brief
    # +1 drift from r46 Step 4 baseline math (49 -> 53 was claimed,
    # actually 48 -> 52 + 1 over-count); r48 Step 1 corrected here.
    # See round 47 audit Correctness LOW finding.
    print(f"ALL 57 ENGINE TESTS PASSED")
    print("=" * 40)
