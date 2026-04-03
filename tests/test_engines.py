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
# RPG Maker MV/MZ 测试
# ============================================================

def _make_rpgm_mv_dir(d):
    """创建最小 RPG Maker MV 目录结构。"""
    data = Path(d) / "www" / "data"
    data.mkdir(parents=True)
    (data / "System.json").write_text('{"gameTitle":"TestGame","currencyUnit":"G","terms":{"basic":["Level","HP"],"commands":["Fight","Escape"],"params":["ATK","DEF"],"messages":{"alwaysDash":"Always Dash"}}}', encoding="utf-8")
    return data


def _make_rpgm_mz_dir(d):
    """创建最小 RPG Maker MZ 目录结构。"""
    data = Path(d) / "data"
    data.mkdir()
    (data / "System.json").write_text('{"gameTitle":"TestGame","currencyUnit":"G","terms":{"basic":[],"commands":[],"params":[],"messages":{}}}', encoding="utf-8")
    return data


def test_rpgm_detect_mv():
    """RPGMakerMVEngine.detect: MV 目录"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    with tempfile.TemporaryDirectory() as d:
        _make_rpgm_mv_dir(d)
        assert engine.detect(Path(d)) is True
    print("[OK] rpgm_detect_mv")


def test_rpgm_detect_mz():
    """RPGMakerMVEngine.detect: MZ 目录"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    with tempfile.TemporaryDirectory() as d:
        _make_rpgm_mz_dir(d)
        assert engine.detect(Path(d)) is True
    print("[OK] rpgm_detect_mz")


def test_rpgm_detect_false():
    """RPGMakerMVEngine.detect: 非 RPG Maker 目录"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    with tempfile.TemporaryDirectory() as d:
        assert engine.detect(Path(d)) is False
    print("[OK] rpgm_detect_false")


def test_rpgm_find_data_dir():
    """_find_data_dir: MV 和 MZ"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    with tempfile.TemporaryDirectory() as d:
        data = _make_rpgm_mv_dir(d)
        assert RPGMakerMVEngine._find_data_dir(Path(d)) == data
    with tempfile.TemporaryDirectory() as d:
        data = _make_rpgm_mz_dir(d)
        assert RPGMakerMVEngine._find_data_dir(Path(d)) == data
    print("[OK] rpgm_find_data_dir")


def test_rpgm_extract_401_merge():
    """事件指令: 连续 401 合并为一个对话 unit"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    cmds = [
        {"code": 101, "indent": 0, "parameters": ["Actor1", 0, 0, 2]},
        {"code": 401, "indent": 0, "parameters": ["Hello, traveler!"]},
        {"code": 401, "indent": 0, "parameters": ["Welcome to our town."]},
        {"code": 401, "indent": 0, "parameters": ["Please enjoy your stay."]},
        {"code": 0, "indent": 0, "parameters": []},
    ]
    units = engine._extract_event_commands(cmds, "Map001.json", "events[0].pages[0].list")
    assert len(units) == 1
    assert units[0].original == "Hello, traveler!\nWelcome to our town.\nPlease enjoy your stay."
    assert units[0].metadata["line_count"] == 3
    assert units[0].metadata["type"] == "dialogue"
    print("[OK] rpgm_extract_401_merge")


def test_rpgm_extract_102_choices():
    """事件指令: 102 选项提取"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    cmds = [
        {"code": 102, "indent": 0, "parameters": [["Yes", "No", "Maybe"], 0]},
        {"code": 0, "indent": 0, "parameters": []},
    ]
    units = engine._extract_event_commands(cmds, "Map001.json", "events[0].pages[0].list")
    assert len(units) == 3
    assert units[0].original == "Yes"
    assert units[2].original == "Maybe"
    assert units[0].metadata["type"] == "choice"
    print("[OK] rpgm_extract_102_choices")


def test_rpgm_extract_405_scroll():
    """事件指令: 连续 405 滚动文本合并"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    cmds = [
        {"code": 105, "indent": 0, "parameters": [2, False]},
        {"code": 405, "indent": 0, "parameters": ["Once upon a time..."]},
        {"code": 405, "indent": 0, "parameters": ["In a land far away."]},
        {"code": 0, "indent": 0, "parameters": []},
    ]
    units = engine._extract_event_commands(cmds, "Map001.json", "events[0].pages[0].list")
    assert len(units) == 1
    assert "Once upon a time..." in units[0].original
    assert units[0].metadata["code"] == 405
    print("[OK] rpgm_extract_405_scroll")


def test_rpgm_extract_320_name():
    """事件指令: 320 改名"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    cmds = [
        {"code": 320, "indent": 0, "parameters": [1, "Harold"]},
        {"code": 0, "indent": 0, "parameters": []},
    ]
    units = engine._extract_event_commands(cmds, "Map001.json", "events[0].pages[0].list")
    assert len(units) == 1
    assert units[0].original == "Harold"
    assert units[0].metadata["type"] == "name_change"
    print("[OK] rpgm_extract_320_name")


def test_rpgm_extract_database():
    """数据库: Actors.json 提取 name/nickname/profile"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    data = [None, {"id": 1, "name": "Harold", "nickname": "Hero", "profile": "A brave warrior."}]
    units = engine._extract_database(data, "Actors.json", ["name", "nickname", "profile"])
    assert len(units) == 3
    names = {u.original for u in units}
    assert "Harold" in names
    assert "Hero" in names
    assert "A brave warrior." in names
    print("[OK] rpgm_extract_database")


def test_rpgm_extract_system():
    """System.json 提取"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    engine = RPGMakerMVEngine()
    data = {
        "gameTitle": "My Game", "currencyUnit": "Gold",
        "armorTypes": ["", "Shield", "Helmet"],
        "terms": {
            "basic": ["Level", "HP"], "commands": ["Fight", "Escape"],
            "params": ["ATK"], "messages": {"alwaysDash": "Always Dash"},
        },
    }
    units = engine._extract_system(data, "System.json")
    ids = {u.id for u in units}
    assert "System.json:gameTitle" in ids
    assert "System.json:currencyUnit" in ids
    assert "System.json:armorTypes[1]" in ids
    assert "System.json:terms.basic[0]" in ids
    assert "System.json:terms.messages.alwaysDash" in ids
    print("[OK] rpgm_extract_system")


def test_rpgm_writeback_dialogue():
    """回写: 对话块（行数匹配）"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    from engines.engine_base import TranslatableUnit
    engine = RPGMakerMVEngine()
    data = {
        "events": [None, {"pages": [{"list": [
            {"code": 101, "parameters": ["Actor1", 0, 0, 2]},
            {"code": 401, "parameters": ["Hello!"]},
            {"code": 401, "parameters": ["World!"]},
            {"code": 0, "parameters": []},
        ]}]}],
    }
    unit = TranslatableUnit(
        id="test", original="Hello!\nWorld!", file_path="Map001.json",
        translation="你好！\n世界！", status="translated",
        metadata={"type": "dialogue", "code": 401, "start_idx": 1,
                  "line_count": 2, "json_prefix": "events[1].pages[0].list"},
    )
    assert engine._patch_unit(data, unit)
    assert data["events"][1]["pages"][0]["list"][1]["parameters"][0] == "你好！"
    assert data["events"][1]["pages"][0]["list"][2]["parameters"][0] == "世界！"
    print("[OK] rpgm_writeback_dialogue")


def test_rpgm_writeback_dialogue_fewer_lines():
    """回写: 翻译行数 < 原行数（补空串）"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    from engines.engine_base import TranslatableUnit
    engine = RPGMakerMVEngine()
    data = {"events": [None, {"pages": [{"list": [
        {"code": 401, "parameters": ["Line 1"]},
        {"code": 401, "parameters": ["Line 2"]},
        {"code": 401, "parameters": ["Line 3"]},
    ]}]}]}
    unit = TranslatableUnit(
        id="test", original="Line 1\nLine 2\nLine 3", file_path="Map.json",
        translation="第一行", status="translated",
        metadata={"type": "dialogue", "code": 401, "start_idx": 0,
                  "line_count": 3, "json_prefix": "events[1].pages[0].list"},
    )
    assert engine._patch_unit(data, unit)
    cmds = data["events"][1]["pages"][0]["list"]
    assert cmds[0]["parameters"][0] == "第一行"
    assert cmds[1]["parameters"][0] == ""
    assert cmds[2]["parameters"][0] == ""
    print("[OK] rpgm_writeback_dialogue_fewer_lines")


def test_rpgm_patch_by_json_path():
    """_patch_by_json_path: 嵌套路径赋值"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    data = {"terms": {"basic": ["Level", "HP", "MP"]}}
    assert RPGMakerMVEngine._patch_by_json_path(data, "terms.basic[1]", "生命值")
    assert data["terms"]["basic"][1] == "生命值"
    # 顶层字段
    data2 = {"gameTitle": "Old"}
    assert RPGMakerMVEngine._patch_by_json_path(data2, "gameTitle", "新标题")
    assert data2["gameTitle"] == "新标题"
    print("[OK] rpgm_patch_by_json_path")


def test_rpgm_navigate_to_node():
    """_navigate_to_node: 复杂路径导航"""
    from engines.rpgmaker_engine import RPGMakerMVEngine
    data = {"events": [None, {"pages": [{"list": [{"code": 401}]}]}]}
    result = RPGMakerMVEngine._navigate_to_node(data, "events[1].pages[0].list")
    assert isinstance(result, list)
    assert result[0]["code"] == 401
    print("[OK] rpgm_navigate_to_node")


def test_glossary_scan_rpgmaker():
    """glossary.scan_rpgmaker_database: 从 Actors.json 提取角色名"""
    from core.glossary import Glossary
    g = Glossary()
    with tempfile.TemporaryDirectory() as d:
        data = _make_rpgm_mv_dir(d)
        (data / "Actors.json").write_text(
            '[null, {"id": 1, "name": "Harold", "nickname": "Hero"}]',
            encoding="utf-8",
        )
        g.scan_rpgmaker_database(d)
        assert "harold" in g.characters
        assert "hero" in g.characters
        # System.json terms
        assert len(g.terms) > 0  # Level, HP, Fight, Escape, ATK, DEF
    print("[OK] glossary_scan_rpgmaker")


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
    # RPG Maker MV/MZ
    test_rpgm_detect_mv()
    test_rpgm_detect_mz()
    test_rpgm_detect_false()
    test_rpgm_find_data_dir()
    test_rpgm_extract_401_merge()
    test_rpgm_extract_102_choices()
    test_rpgm_extract_405_scroll()
    test_rpgm_extract_320_name()
    test_rpgm_extract_database()
    test_rpgm_extract_system()
    test_rpgm_writeback_dialogue()
    test_rpgm_writeback_dialogue_fewer_lines()
    test_rpgm_patch_by_json_path()
    test_rpgm_navigate_to_node()
    test_glossary_scan_rpgmaker()

    print()
    print("=" * 40)
    print("ALL 62 ENGINE TESTS PASSED")
    print("=" * 40)
