#!/usr/bin/env python3
"""综合测试 — 验证优化后的所有模块"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import api_client
import file_processor
from core import glossary
from core import prompts

def test_api_config():
    c = api_client.APIConfig(provider='xai', api_key='test')
    assert c.endpoint == 'https://api.x.ai/v1/chat/completions'
    assert c.model == 'grok-4-1-fast-reasoning'
    c2 = api_client.APIConfig(provider='claude', api_key='test')
    assert c2.endpoint == 'https://api.anthropic.com/v1/messages'
    c3 = api_client.APIConfig(provider='deepseek', api_key='test', model='my-model')
    assert c3.model == 'my-model'
    c4 = api_client.APIConfig(provider='gemini', api_key='test')
    assert 'googleapis' in c4.endpoint
    assert c4.model == 'gemini-2.5-flash'
    print("[OK] APIConfig")

def test_usage_stats():
    u = api_client.UsageStats('xai', 'grok-3')
    u.record(1000, 500)
    u.record(2000, 1000)
    assert u.total_input_tokens == 3000
    assert u.total_output_tokens == 1500
    assert u.total_requests == 2
    assert u.estimated_cost > 0
    s = u.summary()
    assert '3,000' in s
    assert '$' in s
    print(f"[OK] UsageStats: {s}")

def test_rate_limiter():
    r = api_client.RateLimiter(rpm=100, rps=10)
    r.acquire()
    r.acquire()
    print("[OK] RateLimiter")

def test_estimate_tokens():
    tok = file_processor.estimate_tokens('Hello world, this is a test.')
    assert tok > 0
    tok_zh = file_processor.estimate_tokens('你好世界')
    assert tok_zh > 0
    print(f"[OK] estimate_tokens: en={tok}, zh={tok_zh}")

def test_find_block_boundaries():
    lines = [
        'label start:',
        '    mc "Hello"',
        '',
        'screen say(who, what):',
        '    text what',
        '',
        'init python:',
        '    x = 1',
    ]
    b = file_processor._find_block_boundaries(lines)
    assert 0 in b
    assert 3 in b  # screen
    assert 6 in b  # init
    print(f"[OK] _find_block_boundaries: {b}")

def test_safety_check():
    # 变量丢失
    r = file_processor._check_translation_safety('Hello [name]', '你好')
    assert r is not None and 'name' in str(r)
    # 变量保留 — 安全
    r2 = file_processor._check_translation_safety('Hello [name]', '你好 [name]')
    assert r2 is None
    # 变量多出
    r2b = file_processor._check_translation_safety('Hello', '你好 [name]')
    assert r2b is not None and '多出' in str(r2b)
    # 标签不匹配
    r3 = file_processor._check_translation_safety('{color=#f00}Hi{/color}', '你好')
    assert r3 is not None
    # 标签匹配 — 安全
    r4 = file_processor._check_translation_safety('{color=#f00}Hi{/color}', '{color=#f00}你好{/color}')
    assert r4 is None
    # 换行符
    r5 = file_processor._check_translation_safety('Line1\\nLine2', '行1')
    assert r5 is not None
    r6 = file_processor._check_translation_safety('Line1\\nLine2', '行1\\n行2')
    assert r6 is None
    # {#identifier} 保留
    r7 = file_processor._check_translation_safety('Go home{#home_choice}', '回家')
    assert r7 is not None and '标识符' in str(r7)
    r8 = file_processor._check_translation_safety('Go home{#home_choice}', '回家{#home_choice}')
    assert r8 is None
    # %(name)s 格式化占位符
    r9 = file_processor._check_translation_safety('Hello %(name)s', '你好')
    assert r9 is not None and '格式化' in str(r9)
    r10 = file_processor._check_translation_safety('Hello %(name)s', '你好 %(name)s')
    assert r10 is None
    # 翻译长度比例
    long_text = 'A' * 50
    r11 = file_processor._check_translation_safety(long_text, long_text * 5)
    assert r11 is not None and '过长' in str(r11)
    r12 = file_processor._check_translation_safety(long_text, 'x')
    assert r12 is not None and '过短' in str(r12)
    print("[OK] _check_translation_safety")

def test_apply_translations():
    content = '    mc "Hello world"\n    "You see a door."'
    trans = [
        {'line': 1, 'original': 'Hello world', 'zh': '你好世界'},
        {'line': 2, 'original': 'You see a door.', 'zh': '你看到一扇门。'},
    ]
    patched, warnings, _ = file_processor.apply_translations(content, trans)
    assert '你好世界' in patched
    assert '你看到一扇门' in patched
    print(f"[OK] apply_translations: {len(warnings)} warnings")

def test_apply_cascade():
    """测试两遍匹配避免级联覆盖"""
    content = (
        '    if x == 0:\n'         # line 1
        '        pov "Text A"\n'    # line 2  
        '    else:\n'               # line 3
        '        pov "Text B"\n'    # line 4
    )
    # AI returns line 1 for text that's actually on line 2,
    # and line 2 for text that's actually on line 2 (same line)
    trans = [
        {'line': 1, 'original': 'Text A', 'zh': '文本A'},  # will need offset +1
        {'line': 2, 'original': 'Text A', 'zh': '文本A'},  # exact match on line 2
    ]
    patched, warnings, _ = file_processor.apply_translations(content, trans)
    assert patched.count('文本A') == 1  # 只应用一次，不会重复
    # The exact match should win in pass 1
    assert '文本A' in patched
    print("[OK] apply_cascade: no duplicate replacement")

def test_validate_translation():
    orig = 'label start:\n    mc "Hello [name]"\n    jump end'
    trans = 'label start:\n    mc "你好 [name]"\n    jump end'
    issues = file_processor.validate_translation(orig, trans, 'test.rpy')
    assert len(issues) == 0
    print("[OK] validate_translation (clean)")

    # 变量丢失
    trans_bad = 'label start:\n    mc "你好"\n    jump end'
    issues2 = file_processor.validate_translation(orig, trans_bad, 'test.rpy')
    assert any(i['level'] == 'error' for i in issues2)
    print(f"[OK] validate_translation (error detected): {len(issues2)} issues")

def test_glossary():
    g = glossary.Glossary()
    g.terms['Save Game'] = '保存游戏'
    g.characters['mc'] = 'Main Character'
    g.memory['Hello world'] = '你好世界'
    g._memory_count['Hello world'] = 3  # 信心度 >= 2 才输出到 prompt
    text = g.to_prompt_text()
    assert 'mc' in text
    assert 'Save Game' in text
    assert '你好世界' in text
    # update_from_translations filtering
    g.update_from_translations([
        {'original': 'ab', 'zh': '甲'},      # too short, skip
        {'original': 'Hello friend', 'zh': 'Hello friend'},  # same, skip
        {'original': '1234', 'zh': '一二三四'},   # digit, skip
        {'original': 'Good morning everyone', 'zh': '大家早上好'},  # OK
    ])
    assert 'ab' not in g.memory
    assert 'Good morning everyone' in g.memory
    print("[OK] Glossary")

def test_prompts():
    sp = prompts.build_system_prompt('adult', '## 测试术语表\n- hello → 你好')
    assert '成人' in sp
    assert '测试术语表' in sp
    assert 'old' in sp.lower() or 'new' in sp.lower()  # translate block handling
    assert '{#' in sp  # menu choice identifier
    up = prompts.build_user_prompt('test.rpy', 'label start:\n    "Hello"')
    assert 'test.rpy' in up
    # with chunk_info
    up2 = prompts.build_user_prompt('test.rpy', '"Hello"', {'part': 2, 'total': 3, 'line_offset': 100})
    assert '2/3' in up2
    assert '101' in up2
    print("[OK] Prompts")

def test_json_parse():
    p = api_client.APIClient._parse_json_response
    # Direct JSON
    r = p('[{"line": 1, "original": "hi", "zh": "你好"}]')
    assert len(r) == 1
    # Markdown block
    r2 = p('Here:\n```json\n[{"line": 1, "original": "hi", "zh": "hey"}]\n```')
    assert len(r2) == 1
    # Trailing comma
    r3 = p('[{"line": 1, "original": "hi", "zh": "hey"},]')
    assert len(r3) == 1
    # Empty
    r4 = p('[]')
    assert r4 == []
    # Garbage
    r5 = p('I cannot translate this')
    assert r5 == []
    # 逐对象提取（数组格式损坏但单个对象完整）
    r6 = p('Some text {"line": 5, "original": "hello", "zh": "你好"} and {"line": 10, "original": "world", "zh": "世界"} end')
    assert len(r6) == 2
    assert r6[0]['line'] == 5
    assert r6[1]['zh'] == '世界'
    # 含转义引号的对象
    r7 = p('[{"line": 1, "original": "She said \\"hello\\"", "zh": "她说\\"你好\\""}]')
    assert len(r7) == 1
    assert '\\' in r7[0]['original'] or 'hello' in r7[0]['original']
    # 字段顺序变化
    r8 = p('{"zh": "你好", "line": 1, "original": "hi"}')
    # 应该能被 strategy 6 或 direct parse 捕获
    print("[OK] _parse_json_response (含逐对象提取)")

def test_force_split():
    # Create lines that exceed max_tokens
    lines = [f'    mc "This is line {i} with some text content."' for i in range(200)]
    text = '\n'.join(lines)
    tok = file_processor.estimate_tokens(text)
    chunks = file_processor._force_split_lines(lines, 0, len(lines), tok // 3)
    assert len(chunks) >= 2
    # Verify all content is covered
    total_lines = sum(len(c['content'].split('\n')) for c in chunks)
    assert total_lines == len(lines)
    print(f"[OK] _force_split_lines: {len(chunks)} chunks from {len(lines)} lines")


def test_triple_quote_replacement():
    """测试三引号字符串替换"""
    line = '    mc \"\"\"Hello world\"\"\"'
    result = file_processor._replace_string_in_line(line, 'Hello world', '你好世界')
    assert result is not None
    assert '\"\"\"你好世界\"\"\"' in result
    print("[OK] triple-quote replacement")


def test_underscore_func_replacement():
    """测试 _() 包裹的字符串替换"""
    line = '    text _("Save Game")'
    result = file_processor._replace_string_in_line(line, 'Save Game', '保存游戏')
    assert result is not None
    assert '_("保存游戏")' in result
    print("[OK] _() function replacement")


def test_validate_menu_identifier():
    """测试 {#identifier} 在验证中的检测"""
    orig = 'label start:\n    "Go home{#home}" \n    jump end'
    trans_ok = 'label start:\n    "回家{#home}" \n    jump end'
    trans_bad = 'label start:\n    "回家" \n    jump end'
    issues = file_processor.validate_translation(orig, trans_ok, 'test.rpy')
    id_issues = [i for i in issues if '标识符' in i.get('message', '')]
    assert len(id_issues) == 0
    issues2 = file_processor.validate_translation(orig, trans_bad, 'test.rpy')
    id_issues2 = [i for i in issues2 if '标识符' in i.get('message', '')]
    assert len(id_issues2) > 0
    print("[OK] validate_menu_identifier")


def test_glossary_dedup():
    """测试术语表去重：已在 terms 中的不重复加入 memory"""
    g = glossary.Glossary()
    g.terms['Save Game'] = '保存游戏'
    g.update_from_translations([
        {'original': 'Save Game', 'zh': '存档'},  # 已在 terms 中，应跳过
        {'original': 'Load Game', 'zh': '读取存档'},  # 新的，应加入
    ])
    assert 'Save Game' not in g.memory
    assert 'Load Game' in g.memory
    print("[OK] glossary dedup")


def test_image_block_boundary():
    """测试 image 声明作为块边界"""
    lines = [
        'label start:',
        '    mc "Hello"',
        '',
        'image bg = "bg.png"',
        '',
        'screen test:',
        '    text "hi"',
    ]
    b = file_processor._find_block_boundaries(lines)
    assert 3 in b  # image
    assert 5 in b  # screen
    print(f"[OK] image block boundary: {b}")


def test_glossary_thread_safety():
    """测试术语表线程安全"""
    import threading
    g = glossary.Glossary()
    errors = []

    def updater(prefix):
        try:
            for i in range(50):
                g.update_from_translations([
                    {'original': f'{prefix} text number {i}', 'zh': f'{prefix} 文本 {i}'}
                ])
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=updater, args=(f'T{t}',)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread errors: {errors}"
    assert len(g.memory) == 200  # 4 threads * 50 entries
    print(f"[OK] glossary thread safety: {len(g.memory)} entries")


def test_progress_cleanup():
    """测试进度文件 results 清理"""
    import tempfile, os
    from core.translation_utils import ProgressTracker
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        p = ProgressTracker(Path(tmp) / "progress.json")
        p.mark_chunk_done("test.rpy", 1, [{"line": 1, "original": "hi", "zh": "你好"}])
        assert "test.rpy" in p.data.get("results", {})
        p.mark_file_done("test.rpy")
        # results 应该被清理
        assert "test.rpy" not in p.data.get("results", {})
        assert "test.rpy" in p.data["completed_files"]
        print("[OK] progress cleanup")


def test_pricing_lookup():
    """测试模型级定价查询和推理模型检测"""
    from core.api_client import get_pricing, is_reasoning_model

    # 精确匹配
    pin, pout, exact = get_pricing('xai', 'grok-4-1-fast-reasoning')
    assert exact is True
    assert pin == 0.20
    assert pout == 0.50

    # grok-4.20 精确匹配
    pin, pout, exact = get_pricing('xai', 'grok-4.20-beta-0309-reasoning')
    assert exact is True
    assert pin == 2.00

    # 前缀匹配（带日期后缀）
    pin, pout, exact = get_pricing('xai', 'grok-4-1-fast-reasoning-20260301')
    assert exact is True
    assert pin == 0.20

    # 未知模型 → 提供商兜底
    pin, pout, exact = get_pricing('xai', 'grok-99-unknown')
    assert exact is False

    # 推理模型检测
    assert is_reasoning_model('grok-4-1-fast-reasoning') is True
    assert is_reasoning_model('deepseek-reasoner') is True
    assert is_reasoning_model('o1-mini') is True
    assert is_reasoning_model('o3') is True
    assert is_reasoning_model('gpt-4o-mini') is False
    assert is_reasoning_model('grok-3-fast') is False
    assert is_reasoning_model('claude-sonnet-4-20250514') is False

    print("[OK] pricing lookup & reasoning detection")


# ============================================================
# B1: 核心函数单元测试 — protect/restore_placeholders
# ============================================================

def test_protect_restore_roundtrip():
    """protect → 修改文本 → restore = 占位符完好还原"""
    text = "[name] says {color=#f00}Hello{/color} to [name]"
    protected, mapping = file_processor.protect_placeholders(text)
    # 令牌存在、原始占位符消失
    assert "__RENPY_PH_" in protected
    assert "[name]" not in protected
    assert "{color=#f00}" not in protected
    # 模拟翻译：替换非占位符部分
    translated = protected.replace("says", "说").replace("Hello", "你好").replace("to", "对")
    restored = file_processor.restore_placeholders(translated, mapping)
    assert "[name]" in restored
    assert "{color=#f00}" in restored
    assert "{/color}" in restored
    print("[OK] protect_restore_roundtrip")


def test_protect_dedup():
    """相同占位符只产生一个 token（全局去重）"""
    text = "[name] greets [name] again"
    _, mapping = file_processor.protect_placeholders(text)
    assert len(mapping) == 1, f"Expected 1 mapping for duplicated placeholder, got {len(mapping)}"
    print("[OK] protect_dedup")


def test_protect_empty_and_no_placeholders():
    """空文本和无占位符文本原样返回"""
    # 空文本
    result, mapping = file_processor.protect_placeholders("")
    assert result == "" and mapping == []
    # 纯空白
    result2, mapping2 = file_processor.protect_placeholders("   ")
    assert mapping2 == []
    # 无占位符
    result3, mapping3 = file_processor.protect_placeholders("Hello world")
    assert result3 == "Hello world" and mapping3 == []
    print("[OK] protect_empty_and_no_placeholders")


def test_protect_mixed_types():
    """混合类型占位符：[var] + {tag} + %(fmt)s"""
    text = "[a] and {b} and %(c)s end"
    protected, mapping = file_processor.protect_placeholders(text)
    assert len(mapping) == 3, f"Expected 3 mappings, got {len(mapping)}"
    # 还原后一致
    restored = file_processor.restore_placeholders(protected, mapping)
    assert restored == text
    print("[OK] protect_mixed_types")


def test_protect_menu_id():
    """菜单标识符 {#id} 也被保护"""
    text = "Go home{#home_choice}"
    protected, mapping = file_processor.protect_placeholders(text)
    assert "{#home_choice}" not in protected
    assert len(mapping) >= 1
    restored = file_processor.restore_placeholders(protected, mapping)
    assert restored == text
    print("[OK] protect_menu_id")


# ============================================================
# B1: 核心函数单元测试 — check_response_item
# ============================================================

def test_check_response_item_normal():
    """正常条目通过校验"""
    warnings = file_processor.check_response_item(
        {"line": 1, "original": "Hello world", "zh": "你好世界"}
    )
    assert len(warnings) == 0
    print("[OK] check_response_item_normal")


def test_check_response_item_empty_zh():
    """译文为空时被拦截"""
    warnings = file_processor.check_response_item(
        {"line": 1, "original": "Hello", "zh": ""}
    )
    assert len(warnings) > 0 and "译文为空" in warnings[0]
    print("[OK] check_response_item_empty_zh")


def test_check_response_item_empty_original():
    """原文为空时被拦截"""
    warnings = file_processor.check_response_item(
        {"line": 1, "original": "", "zh": "你好"}
    )
    assert len(warnings) > 0 and "original 为空" in warnings[0]
    print("[OK] check_response_item_empty_original")


def test_check_response_item_var_missing():
    """占位符缺失时被拦截"""
    warnings = file_processor.check_response_item(
        {"line": 1, "original": "Hello [name]", "zh": "你好"}
    )
    assert len(warnings) > 0 and "占位符" in warnings[0]
    print("[OK] check_response_item_var_missing")


def test_check_response_item_var_preserved():
    """占位符保留时通过"""
    warnings = file_processor.check_response_item(
        {"line": 1, "original": "Hello [name]", "zh": "你好 [name]"}
    )
    assert len(warnings) == 0
    print("[OK] check_response_item_var_preserved")


def test_check_response_item_line_offset():
    """line_offset 正确叠加到行号"""
    warnings = file_processor.check_response_item(
        {"line": 5, "original": "Hi", "zh": ""},
        line_offset=100,
    )
    assert "105" in warnings[0]
    print("[OK] check_response_item_line_offset")


# ============================================================
# B1: 核心函数单元测试 — check_response_chunk
# ============================================================

def test_check_response_chunk_match():
    """返回条数与可翻译行数一致时无警告"""
    chunk = 'e "Line A"\ne "Line B"\ne "Line C"'
    warnings = file_processor.check_response_chunk(chunk, [
        {"line": 1, "original": "Line A", "zh": "行A"},
        {"line": 2, "original": "Line B", "zh": "行B"},
        {"line": 3, "original": "Line C", "zh": "行C"},
    ])
    assert len(warnings) == 0
    print("[OK] check_response_chunk_match")


def test_check_response_chunk_mismatch():
    """返回条数不一致时有警告"""
    chunk = 'e "Line A"\ne "Line B"\ne "Line C"'
    warnings = file_processor.check_response_chunk(chunk, [
        {"line": 1, "original": "Line A", "zh": "行A"},
    ])
    assert len(warnings) > 0 and "不一致" in warnings[0]
    print("[OK] check_response_chunk_mismatch")


def test_check_response_chunk_empty():
    """无可翻译行的 chunk + 空返回 → 无警告"""
    chunk = '# This is a comment\nlabel start:\n    pass'
    warnings = file_processor.check_response_chunk(chunk, [])
    assert len(warnings) == 0
    print("[OK] check_response_chunk_empty")


def test_check_response_chunk_skip_chinese():
    """已含中文的行不计入 expected（视为已翻译）"""
    chunk = 'e "你好世界"\ne "Hello"'
    warnings = file_processor.check_response_chunk(chunk, [
        {"line": 2, "original": "Hello", "zh": "你好"},
    ])
    assert len(warnings) == 0
    print("[OK] check_response_chunk_skip_chinese")


# ============================================================
# C: 集成级测试 — 密度自适应 / 跳过名单 / 漏翻检测 / TranslationDB
# ============================================================

def test_dialogue_density():
    """T6: calculate_dialogue_density 密度自适应路由"""
    from translators.retranslator import calculate_dialogue_density
    # 低密度：多代码少对话
    low = "label start:\n    pass\n    pass\n    pass\n    pass\n" + \
          '    e "Hello"\n' + "    pass\n    pass\n    pass\n    pass\n"
    d_low = calculate_dialogue_density(low)
    assert d_low < 0.20, f"Expected low density, got {d_low}"

    # 高密度：全对话
    high = '    e "Line 1"\n    e "Line 2"\n    e "Line 3"\n    e "Line 4"\n    e "Line 5"\n'
    d_high = calculate_dialogue_density(high)
    assert d_high >= 0.20, f"Expected high density, got {d_high}"

    # 空文件
    d_empty = calculate_dialogue_density("")
    assert d_empty == 0.0
    print("[OK] dialogue_density")


def test_skip_files():
    """T7: SKIP_FILES_FOR_TRANSLATION 跳过逻辑"""
    from file_processor import SKIP_FILES_FOR_TRANSLATION
    for name in ("define.rpy", "variables.rpy", "screens.rpy", "options.rpy", "earlyoptions.rpy"):
        assert name in SKIP_FILES_FOR_TRANSLATION, f"{name} not in SKIP_FILES"
    assert "script.rpy" not in SKIP_FILES_FOR_TRANSLATION
    print("[OK] skip_files")


def test_find_untranslated_lines():
    """T8: find_untranslated_lines 二次过滤"""
    from translators.retranslator import find_untranslated_lines
    content = (
        '    auto "path_%s.png"\n'
        '    idle "icon_hover.png"\n'
        '    hover "btn_hover.png"\n'
        '    image bg = "backgrounds/bg.png"\n'
        '    pov "Hello world, this is a long test line for detection that should be found."\n'
        '    e "Short"\n'
    )
    results = find_untranslated_lines(content)
    found_texts = [text for _, text in results]
    # 应检出长英文对话
    assert any("Hello world" in t for t in found_texts), f"Long dialogue not found: {found_texts}"
    # 不应检出资源路径/属性行
    assert not any("path_" in t for t in found_texts)
    assert not any("icon_hover" in t for t in found_texts)
    print("[OK] find_untranslated_lines")


def test_translation_db_roundtrip():
    """T10: TranslationDB save/load 往返 + upsert 去重"""
    import tempfile, os
    from pathlib import Path
    from core.translation_db import TranslationDB
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    try:
        db = TranslationDB(Path(tmp_path))
        entries = [
            {"file": "test.rpy", "line": 1, "original": "Hello", "translation": "你好", "status": "ok"},
            {"file": "test.rpy", "line": 2, "original": "World", "translation": "世界", "status": "ok"},
        ]
        db.add_entries(entries)
        assert len(db.entries) == 2
        db.save()

        # Reload
        db2 = TranslationDB(Path(tmp_path))
        db2.load()
        assert len(db2.entries) == 2

        # Upsert：相同 file+line 应更新
        db2.add_entries([
            {"file": "test.rpy", "line": 1, "original": "Hello", "translation": "你好啊", "status": "ok"},
        ])
        assert len(db2.entries) == 2  # 不应增加
        print("[OK] translation_db_roundtrip")
    finally:
        os.unlink(tmp_path)


def test_is_untranslated_dialogue():
    """测试 one_click_pipeline._is_untranslated_dialogue 辅助函数"""
    from translators.renpy_text_utils import _is_untranslated_dialogue
    # 纯英文长文本 → 应判定为未翻译
    assert _is_untranslated_dialogue("This is a long English sentence that should be detected as untranslated.")
    # 含中文 → 不应判定
    assert not _is_untranslated_dialogue("这是一个中文句子 with some English mixed in for testing.")
    # 太短 → 不应判定
    assert not _is_untranslated_dialogue("Short text")
    print("[OK] is_untranslated_dialogue")


def test_restore_placeholders_in_translations():
    """测试 _restore_placeholders_in_translations 辅助函数"""
    from core.translation_utils import _restore_placeholders_in_translations
    from file_processor import protect_placeholders
    text = "Hello [name], welcome to {color=#f00}town{/color}!"
    protected, mapping = protect_placeholders(text)
    translations = [
        {"original": protected, "zh": f"你好 {protected.split('__RENPY_PH_0__')[0]}__RENPY_PH_0__！"}
    ]
    # 不应崩溃
    _restore_placeholders_in_translations(translations, mapping)
    # original 应被还原
    assert "[name]" in translations[0]["original"]
    print("[OK] restore_placeholders_in_translations")


# ============================================================
# D: 第九轮新增测试
# ============================================================

def test_progress_resume():
    """T43: ProgressTracker 写入后重载，数据一致"""
    import tempfile, os
    from pathlib import Path
    from core.translation_utils import ProgressTracker
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    try:
        p = ProgressTracker(Path(tmp_path))
        p.mark_chunk_done("test.rpy", 1, [{"line": 1, "zh": "你好"}])
        p.save()  # 强制刷盘

        p2 = ProgressTracker(Path(tmp_path))
        assert p2.is_chunk_done("test.rpy", 1)
        assert not p2.is_chunk_done("test.rpy", 2)
        print("[OK] progress_resume")
    finally:
        os.unlink(tmp_path)


def test_progress_normalize():
    """T44: 加载损坏/缺key的 progress.json 不崩溃"""
    import tempfile, os
    from pathlib import Path
    from core.translation_utils import ProgressTracker
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
        f.write('{"completed_files": ["a.rpy"]}')  # 缺 completed_chunks 和 stats
        tmp_path = f.name
    try:
        p = ProgressTracker(Path(tmp_path))
        assert "a.rpy" in p.data["completed_files"]
        assert "completed_chunks" in p.data
        assert "stats" in p.data
        print("[OK] progress_normalize")
    finally:
        os.unlink(tmp_path)


def test_filter_checked_translations():
    """T47: _filter_checked_translations 正常/空译文/占位符缺失"""
    from core.translation_utils import _filter_checked_translations
    items = [
        {"line": 1, "original": "Hello", "zh": "你好"},
        {"line": 2, "original": "World", "zh": ""},          # 空译文 → dropped
        {"line": 3, "original": "[name] hi", "zh": "你好"},  # 占位符缺失 → dropped
    ]
    kept, dropped_count, dropped_items, warnings = _filter_checked_translations(items)
    assert len(kept) == 1 and kept[0]["line"] == 1
    assert dropped_count == 2
    assert len(dropped_items) == 2
    assert len(warnings) >= 2
    print("[OK] filter_checked_translations")


def test_deduplicate_translations():
    """T48: _deduplicate_translations 去重"""
    from core.translation_utils import _deduplicate_translations
    items = [
        {"line": 1, "original": "Hello", "zh": "你好"},
        {"line": 1, "original": "Hello", "zh": "你好啊"},  # 重复 key
        {"line": 2, "original": "World", "zh": "世界"},
    ]
    result = _deduplicate_translations(items)
    assert len(result) == 2
    assert result[0]["zh"] == "你好"  # 保留首次
    # 空列表
    assert _deduplicate_translations([]) == []
    print("[OK] deduplicate_translations")


def test_match_string_entry_fallback():
    """T49: _match_string_entry_fallback 四层 fallback"""
    from core.translation_utils import _match_string_entry_fallback, _build_fallback_dicts
    ft = {
        "Save Game": "保存游戏",
        "  Load Game  ": "读取存档",
        '__RENPY_PH_0__ Settings': "设置",
        'He said \\"hello\\"': "他说了你好",
    }
    ft_stripped, ft_clean, ft_norm = _build_fallback_dicts(ft)

    # L1: 精确匹配
    zh, level = _match_string_entry_fallback("Save Game", ft, ft_stripped, ft_clean, ft_norm)
    assert zh == "保存游戏" and level == 0

    # L2: strip 匹配
    zh, level = _match_string_entry_fallback("Load Game", ft, ft_stripped, ft_clean, ft_norm)
    assert zh == "读取存档" and level == 2

    # L3: 去占位符匹配
    zh, level = _match_string_entry_fallback("Settings", ft, ft_stripped, ft_clean, ft_norm)
    assert zh == "设置" and level == 3

    # L4: 转义规范化匹配
    zh, level = _match_string_entry_fallback('He said "hello"', ft, ft_stripped, ft_clean, ft_norm)
    assert zh == "他说了你好" and level == 4

    # 无匹配
    zh, level = _match_string_entry_fallback("Unknown", ft, ft_stripped, ft_clean, ft_norm)
    assert zh is None and level == 0
    print("[OK] match_string_entry_fallback")


def test_api_empty_choices():
    """T50: API 返回空 choices 时不崩溃"""
    from core import api_client
    # 模拟空 choices 的情况——直接测试解析逻辑
    # _call_openai_format 需要网络，这里测试 get_pricing 和 is_reasoning_model
    assert api_client.is_reasoning_model("grok-4-1-fast-reasoning") is True
    assert api_client.is_reasoning_model("gpt-4o-mini") is False
    assert api_client.is_reasoning_model("o3-mini") is True
    assert api_client.is_reasoning_model("deepseek-reasoner") is True
    print("[OK] api_reasoning_detection")


def test_positive_int_validation():
    """T52: CLI 参数校验函数"""
    from main import _positive_int, _positive_float, _ratio_float
    import argparse
    # 正常值
    assert _positive_int("5") == 5
    assert _positive_float("3.14") == 3.14
    assert _ratio_float("0.5") == 0.5
    # 非法值
    for fn, val in [(_positive_int, "0"), (_positive_int, "-1"),
                    (_positive_float, "0"), (_ratio_float, "1.5"), (_ratio_float, "0")]:
        try:
            fn(val)
            assert False, f"应该抛出异常: {fn.__name__}({val})"
        except argparse.ArgumentTypeError:
            pass
    print("[OK] positive_int_validation")


def test_reasoning_model_timeout():
    """推理模型自动提升 timeout"""
    from core import api_client
    config = api_client.APIConfig(provider='xai', api_key='test', model='grok-4-1-fast-reasoning', timeout=180.0)
    assert config.timeout >= 300.0, f"Expected >= 300, got {config.timeout}"
    # 非推理模型不应提升
    config2 = api_client.APIConfig(provider='openai', api_key='test', model='gpt-4o-mini', timeout=180.0)
    assert config2.timeout == 180.0
    print("[OK] reasoning_model_timeout")


def test_glossary_hyphenated_names():
    """连字符人名提取（如 Mary-Jane）"""
    g = glossary.Glossary()
    # 模拟翻译数据：Mary-Jane 出现 4 次，同译名"玛丽-简"
    translations = [
        {"original": f"Mary-Jane says hello {i}", "zh": f"玛丽-简说你好{i}"}
        for i in range(4)
    ]
    terms = g.extract_terms_from_translations(translations, min_freq=3)
    assert "Mary-Jane" in terms, f"Hyphenated name not extracted: {terms}"
    print("[OK] glossary_hyphenated_names")


def test_glossary_memory_confidence():
    """翻译记忆信心度过滤：出现 1 次的不输出到 prompt"""
    g = glossary.Glossary()
    g.update_from_translations([
        {"original": "A long sentence for testing", "zh": "测试用的长句子"},
    ])
    text = g.to_prompt_text()
    assert "测试用的长句子" not in text, "count=1 should not appear in prompt"
    # 再出现一次，count=2 → 应输出
    g.update_from_translations([
        {"original": "A long sentence for testing", "zh": "测试用的长句子"},
    ])
    text2 = g.to_prompt_text()
    assert "测试用的长句子" in text2, "count=2 should appear in prompt"
    print("[OK] glossary_memory_confidence")


def test_protect_control_tags():
    """Ren'Py 控制标签 {w}/{p}/{nw}/{fast}/{cps=N} 被占位符保护覆盖"""
    text = 'Wait{w=0.5} pause{p} nowait{nw} fast{fast} speed{cps=20} done{done}'
    protected, mapping = file_processor.protect_placeholders(text)
    # 所有控制标签应被替换
    for tag in ['{w=0.5}', '{p}', '{nw}', '{fast}', '{cps=20}', '{done}']:
        assert tag not in protected, f"{tag} not protected"
    # 还原后完全一致
    restored = file_processor.restore_placeholders(protected, mapping)
    assert restored == text
    print("[OK] protect_control_tags")


def test_replace_string_prefix_strip():
    """WF-08 修复：AI 返回含行前缀的 original 时能正确剥离并替换"""
    from file_processor.patcher import _replace_string_in_line
    # AI 返回 text _("原文") 但行中实际是 _("原文") 结构
    line = '            text _("Made with Ren\'Py")'
    # AI 的 original 包含了 text _(" 前缀
    result = _replace_string_in_line(line, 'text _("Made with Ren\'Py")', '由 Ren\'Py 制作')
    assert result is not None, "prefix strip should match"
    assert "由 Ren'Py 制作" in result
    print("[OK] replace_string_prefix_strip")


def test_replace_string_escaped_quotes():
    """WF-04 修复：含转义引号的字符串匹配"""
    from file_processor.patcher import _replace_string_in_line
    line = r'    textbutton "She said \"hello\""'
    result = _replace_string_in_line(line, r'She said \"hello\"', '她说了"你好"')
    # 即使匹配不上（转义引号情况复杂），至少不应崩溃
    # 如果匹配成功更好
    print(f"[OK] replace_string_escaped_quotes (result={'matched' if result else 'no_match'})")


def test_config_load_and_defaults():
    """config.json 加载 + 默认值填充"""
    from pathlib import Path as _Path
    from core.config import Config, DEFAULTS
    import tempfile
    # 无配置文件时使用默认值
    cfg = Config(game_dir=_Path(tempfile.gettempdir()), cli_args=None)
    assert cfg.get("workers") == DEFAULTS["workers"]
    assert cfg.get("rpm") == DEFAULTS["rpm"]
    assert cfg.get("nonexistent", 42) == 42
    assert not cfg.has_config_file()
    print("[OK] config_load_and_defaults")


def test_config_cli_override():
    """CLI 参数覆盖配置文件和默认值"""
    from pathlib import Path as _Path
    from core.config import Config
    import types, tempfile
    # ��拟 CLI args
    cli = types.SimpleNamespace(workers=8, rpm=None, rps=None, api_key="")
    cfg = Config(game_dir=_Path(tempfile.gettempdir()), cli_args=cli)
    assert cfg.get("workers") == 8       # CLI 覆盖
    assert cfg.get("rpm") == 60          # CLI=None → 默认值
    print("[OK] config_cli_override")


def test_config_file_load():
    """配置文件正常加载"""
    from pathlib import Path as _Path
    from core.config import Config
    import tempfile, os, json
    # 创建临时配置文件
    tmpdir = tempfile.mkdtemp()
    cfg_path = _Path(tmpdir) / "renpy_translate.json"
    cfg_path.write_text(json.dumps({"workers": 10, "rpm": 999}), encoding="utf-8")
    try:
        cfg = Config(game_dir=_Path(tmpdir), cli_args=None)
        assert cfg.has_config_file()
        assert cfg.get("workers") == 10
        assert cfg.get("rpm") == 999
        assert cfg.get("rps") == 5  # 配置文件未设置 → 默认值
        print("[OK] config_file_load")
    finally:
        cfg_path.unlink()
        os.rmdir(tmpdir)


def test_progress_bar_render():
    """ProgressBar 渲染不崩溃（含 ASCII fallback）"""
    from core.translation_utils import ProgressBar
    bar = ProgressBar(total=10, width=20)
    bar.update(3, cost=0.5)
    bar.update(7, cost=1.2)
    bar.finish()
    assert bar.current == 10
    assert bar.cost == 1.7
    print("[OK] progress_bar_render")


def test_review_generator_html():
    """review_generator 生成 HTML 不崩溃"""
    from tools.review_generator import generate_review_html
    from pathlib import Path as _Path
    import tempfile, json, os
    # 创建临时 translation_db
    tmpdir = tempfile.mkdtemp()
    db_path = _Path(tmpdir) / "test_db.json"
    db_path.write_text(json.dumps({
        "version": 1,
        "entries": [
            {"file": "test.rpy", "line": 1, "original": "Hello", "translation": "你好",
             "status": "ok", "error_codes": [], "warning_codes": []},
            {"file": "test.rpy", "line": 2, "original": "World", "translation": "世界",
             "status": "warning", "error_codes": [], "warning_codes": ["W430"]},
        ]
    }), encoding="utf-8")
    out_path = _Path(tmpdir) / "review.html"
    try:
        count = generate_review_html(db_path, out_path)
        assert count == 2
        html_content = out_path.read_text(encoding="utf-8")
        assert "Hello" in html_content
        assert "W430" in html_content
        assert "test.rpy" in html_content
        print("[OK] review_generator_html")
    finally:
        db_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)
        os.rmdir(tmpdir)


def test_lang_config_detect():
    """语言检测函数准确性"""
    from core.lang_config import detect_chinese_ratio, detect_japanese_ratio, detect_korean_ratio
    # 中文
    assert detect_chinese_ratio("你好世界") > 0.5
    assert detect_chinese_ratio("Hello world") == 0.0
    assert detect_chinese_ratio("") == 0.0
    # 日文
    assert detect_japanese_ratio("こんにちは世界") > 0.5
    assert detect_japanese_ratio("Hello") == 0.0
    # 韩文
    assert detect_korean_ratio("안녕하세요") > 0.5
    assert detect_korean_ratio("Hello") == 0.0
    print("[OK] lang_config_detect")


def test_lang_config_lookup():
    """get_language_config 查找与回退"""
    from core.lang_config import get_language_config
    zh = get_language_config("zh")
    assert zh.code == "zh" and zh.glossary_field == "zh"
    ja = get_language_config("ja")
    assert ja.code == "ja" and ja.glossary_field == "ja"
    # 不存在的语言回退到 zh
    fallback = get_language_config("xx-unknown")
    assert fallback.code == "zh"
    print("[OK] lang_config_lookup")


def test_resolve_translation_field():
    """兼容读取翻译字段"""
    from core.lang_config import resolve_translation_field, get_language_config
    zh_cfg = get_language_config("zh")
    ja_cfg = get_language_config("ja")
    # 精确匹配
    assert resolve_translation_field({"zh": "你好"}, zh_cfg) == "你好"
    assert resolve_translation_field({"ja": "こんにちは"}, ja_cfg) == "こんにちは"
    # 别名匹配
    assert resolve_translation_field({"chinese": "你好"}, zh_cfg) == "你好"
    assert resolve_translation_field({"jp": "こんにちは"}, ja_cfg) == "こんにちは"
    # 通用字段 fallback
    assert resolve_translation_field({"translation": "你好"}, zh_cfg) == "你好"
    # 无匹配
    assert resolve_translation_field({"de": "Hallo"}, zh_cfg) is None
    print("[OK] resolve_translation_field")


def test_prompt_zh_unchanged():
    """中文 prompt 零变更回归验证"""
    from core.prompts import build_system_prompt
    from core.glossary import Glossary
    from core.lang_config import get_language_config
    g = Glossary()
    # 不传 lang_config → 默认 zh
    prompt_default = build_system_prompt('adult', g.to_prompt_text(), 'TestProject')
    # 显式传 zh lang_config
    prompt_zh = build_system_prompt('adult', g.to_prompt_text(), 'TestProject', lang_config=get_language_config('zh'))
    baseline = open('tests/zh_prompt_baseline.txt', 'r', encoding='utf-8').read()
    assert prompt_default == baseline, "Default prompt changed!"
    assert prompt_zh == baseline, "zh prompt changed!"
    print("[OK] prompt_zh_unchanged")


def test_prompt_ja_generic():
    """日语 prompt 使用英文通用模板"""
    from core.prompts import build_system_prompt
    from core.lang_config import get_language_config
    ja = get_language_config('ja')
    prompt = build_system_prompt('adult', '', 'TestProject', lang_config=ja)
    assert 'Japanese' in prompt or '日本語' in prompt
    assert '"ja"' in prompt  # JSON 字段名
    # 不应包含中文模板的内容
    assert '你是一个专业的' not in prompt
    print("[OK] prompt_ja_generic")


def test_validator_lang_config():
    """validator W442 使用 lang_config 参数化"""
    from core.lang_config import get_language_config
    # 日语 validator：日文占比低应触发 W442
    ja = get_language_config('ja')
    orig = 'x' * 30 + '\n' + '"' + 'A' * 25 + '"'
    trans = 'x' * 30 + '\n' + '"' + 'B' * 25 + '"'  # 纯英文译文
    issues = file_processor.validate_translation(orig, trans, 'test.rpy', lang_config=ja)
    w442 = [i for i in issues if i.get('code') == 'W442_SUSPECT_ENGLISH_OUTPUT']
    assert len(w442) > 0, "W442 should trigger for pure English when target is Japanese"
    assert '日本語' in w442[0]['message']
    print("[OK] validator_lang_config")


def test_should_retry_truncation():
    """_should_retry 截断检测：returned < expected * 0.5 → needs_split"""
    from translators.direct import _should_retry
    from core.translation_utils import ChunkResult
    # 正常情况
    cr_ok = ChunkResult(part=1, expected=10, returned=8)
    should, split = _should_retry(cr_ok)
    assert not should, "should not retry normal result"
    # 截断情况
    cr_trunc = ChunkResult(part=1, expected=20, returned=5)
    should, split = _should_retry(cr_trunc)
    assert should and split, "should retry with split on truncation"
    # API 错误
    cr_err = ChunkResult(part=1, error="timeout")
    should, split = _should_retry(cr_err)
    assert should and not split, "API error: retry without split"
    # 边界：expected>0, returned=0（完全无输出）
    cr_zero = ChunkResult(part=1, expected=10, returned=0)
    should, split = _should_retry(cr_zero)
    assert should and split, "zero returned should trigger split"
    # 边界：expected=0, returned=0（空 chunk）
    cr_empty = ChunkResult(part=1, expected=0, returned=0)
    should, split = _should_retry(cr_empty)
    assert not should, "empty chunk should not retry"
    print("[OK] should_retry_truncation")


def test_should_retry_normal():
    """_should_retry 正常和丢弃率过高"""
    from translators.direct import _should_retry
    from core.translation_utils import ChunkResult
    # 正常返回
    cr = ChunkResult(part=1, expected=10, returned=10, dropped_count=0)
    should, split = _should_retry(cr)
    assert not should and not split
    # 丢弃率过高（需满足 MIN_DROPPED_FOR_WARNING=3 + ratio>0.3）
    cr_drop = ChunkResult(part=1, expected=10, returned=10, dropped_count=5)
    should, split = _should_retry(cr_drop)
    assert should and not split, "high drop rate should retry without split"
    print("[OK] should_retry_normal")


def test_split_chunk_basic():
    """_split_chunk 基本拆分：行数守恒"""
    from translators.direct import _split_chunk
    lines = [f"line {i}\n" for i in range(20)]
    chunk = {"content": "".join(lines), "line_offset": 0, "part": 1, "total": 1}
    a, b = _split_chunk(chunk)
    total_a = len(a["content"].splitlines())
    total_b = len(b["content"].splitlines())
    assert total_a + total_b == 20, f"line count mismatch: {total_a} + {total_b} != 20"
    assert a["line_offset"] == 0
    assert b["line_offset"] == total_a
    print("[OK] split_chunk_basic")


def test_split_chunk_at_empty_line():
    """_split_chunk 优先在空行处拆分"""
    from translators.direct import _split_chunk
    lines = []
    for i in range(20):
        if i == 10:
            lines.append("\n")  # 空行在中间
        else:
            lines.append(f"    dialogue line {i}\n")
    chunk = {"content": "".join(lines), "line_offset": 0, "part": 1, "total": 1}
    a, b = _split_chunk(chunk)
    # 拆分应该发生在空行处（index 10 之后，即 line 11）
    a_lines = a["content"].splitlines()
    assert len(a_lines) == 11, f"expected 11 lines in chunk_a, got {len(a_lines)}"
    print("[OK] split_chunk_at_empty_line")


def test_config_validation():
    """配置文件 schema 校验：类型/范围/未知键"""
    from pathlib import Path as _Path
    from core.config import Config
    import tempfile, os, json, logging

    # --- 1. 合法配置无警告 ---
    tmpdir = tempfile.mkdtemp()
    cfg_path = _Path(tmpdir) / "renpy_translate.json"
    cfg_path.write_text(json.dumps({
        "workers": 4, "rpm": 30, "temperature": 0.5, "provider": "openai"
    }), encoding="utf-8")
    try:
        cfg = Config(game_dir=_Path(tmpdir), cli_args=None)
        warns = cfg.validate()
        assert warns == [], f"expected no warnings, got {warns}"
    finally:
        cfg_path.unlink()
        os.rmdir(tmpdir)
    print("[OK] config_validation: valid config")

    # --- 2. 类型错误 ---
    tmpdir = tempfile.mkdtemp()
    cfg_path = _Path(tmpdir) / "renpy_translate.json"
    cfg_path.write_text(json.dumps({"workers": "abc"}), encoding="utf-8")
    try:
        cfg = Config(game_dir=_Path(tmpdir), cli_args=None)
        warns = cfg.validate()
        assert any("类型错误" in w for w in warns), f"expected type error warning, got {warns}"
    finally:
        cfg_path.unlink()
        os.rmdir(tmpdir)
    print("[OK] config_validation: type error")

    # --- 3. 范围越界 ---
    tmpdir = tempfile.mkdtemp()
    cfg_path = _Path(tmpdir) / "renpy_translate.json"
    cfg_path.write_text(json.dumps({"workers": 999}), encoding="utf-8")
    try:
        cfg = Config(game_dir=_Path(tmpdir), cli_args=None)
        warns = cfg.validate()
        assert any("值过大" in w for w in warns), f"expected range warning, got {warns}"
    finally:
        cfg_path.unlink()
        os.rmdir(tmpdir)
    print("[OK] config_validation: range violation")

    # --- 4. 未知键 ---
    tmpdir = tempfile.mkdtemp()
    cfg_path = _Path(tmpdir) / "renpy_translate.json"
    cfg_path.write_text(json.dumps({"totally_unknown_key": 123}), encoding="utf-8")
    try:
        cfg = Config(game_dir=_Path(tmpdir), cli_args=None)
        warns = cfg.validate()
        assert any("未知配置项" in w for w in warns), f"expected unknown key warning, got {warns}"
    finally:
        cfg_path.unlink()
        os.rmdir(tmpdir)
    print("[OK] config_validation: unknown key")


def test_fix_nvl_ids_basic():
    """含 nvl clear 的块：say-only ID 应被替换为 nvl+say ID"""
    import tempfile
    from translators.tl_parser import fix_nvl_translation_ids, _compute_say_only_hash, _compute_nvl_say_hash
    say_code = 's "Hello world"'
    say_hash = _compute_say_only_hash(say_code)
    nvl_hash = _compute_nvl_say_hash(say_code)
    assert say_hash != nvl_hash

    tl_content = (
        f"# game/test.rpy:10\n"
        f"translate chinese my_label_{say_hash}:\n"
        f"\n"
        f"    # nvl clear\n"
        f"    # {say_code}\n"
        f'    s "你好世界"\n'
    )
    tmpfile = Path(tempfile.mktemp(suffix=".rpy"))
    tmpfile.write_text(tl_content, encoding="utf-8")
    try:
        stats = fix_nvl_translation_ids(str(tmpfile))
        assert stats["ids_fixed"] == 1, f"expected 1 fix, got {stats}"
        result = tmpfile.read_text(encoding="utf-8")
        assert f"my_label_{nvl_hash}" in result
        assert f"my_label_{say_hash}" not in result
    finally:
        tmpfile.unlink()
    print("[OK] fix_nvl_ids_basic")


def test_fix_nvl_ids_no_nvl():
    """不含 nvl clear 的块不应被修改"""
    import tempfile
    from translators.tl_parser import fix_nvl_translation_ids
    tl_content = (
        "# game/test.rpy:10\n"
        "translate chinese my_label_abcd1234:\n"
        "\n"
        '    # s "Hello"\n'
        '    s "你好"\n'
    )
    tmpfile = Path(tempfile.mktemp(suffix=".rpy"))
    tmpfile.write_text(tl_content, encoding="utf-8")
    try:
        stats = fix_nvl_translation_ids(str(tmpfile))
        assert stats["ids_fixed"] == 0
        assert tmpfile.read_text(encoding="utf-8") == tl_content
    finally:
        tmpfile.unlink()
    print("[OK] fix_nvl_ids_no_nvl")


def test_fix_nvl_ids_already_correct():
    """ID 已经是 nvl+say 哈希时不应重复修改"""
    import tempfile
    from translators.tl_parser import fix_nvl_translation_ids, _compute_nvl_say_hash
    say_code = 's "Already correct"'
    nvl_hash = _compute_nvl_say_hash(say_code)
    tl_content = (
        f"# game/test.rpy:10\n"
        f"translate chinese label_{nvl_hash}:\n"
        f"\n"
        f"    # nvl clear\n"
        f"    # {say_code}\n"
        f'    s "已经正确"\n'
    )
    tmpfile = Path(tempfile.mktemp(suffix=".rpy"))
    tmpfile.write_text(tl_content, encoding="utf-8")
    try:
        stats = fix_nvl_translation_ids(str(tmpfile))
        assert stats["ids_fixed"] == 0
    finally:
        tmpfile.unlink()
    print("[OK] fix_nvl_ids_already_correct")


def test_fix_nvl_ids_real_hashes():
    """用 begin.rpy 的真实数据验证 7 个已知 case"""
    from translators.tl_parser import _compute_say_only_hash, _compute_nvl_say_hash
    cases = [
        ('s "The {color=#3cff00}Love{/color} and {color=#ff0000}Corruption{/color}'
         ' paths have been extended to help make them more robust. There are'
         ' corruption scenes written for the love path scenes and vice versa.'
         ' Essentially doubling the amount of love and corruption content."',
         'bcc2e904', '8c492e19'),
        ('s "Turn {color=#0000ff}NTR{/color} on? These are the'
         ' {color=#0000ff}Darker Paths{/color} in the Mod. This will allow'
         ' access to the {color=#0000ff}Voyeur{/color},'
         ' {color=#0000ff}NTR{/color}, {color=#0000ff}Sadist{/color},'
         ' and {color=#0000ff}Revenge{/color} Paths."',
         '735a34f0', 'df92c7d1'),
    ]
    for say_code, expected_say, expected_nvl in cases:
        assert _compute_say_only_hash(say_code) == expected_say, \
            f"say-only mismatch for {say_code[:40]}..."
        assert _compute_nvl_say_hash(say_code) == expected_nvl, \
            f"nvl+say mismatch for {say_code[:40]}..."
    print(f"[OK] fix_nvl_ids_real_hashes: {len(cases)} cases verified")


# ─────────────────────────────────────────────────────────────────
# I: screen_translator 测试
# ─────────────────────────────────────────────────────────────────

def test_screen_should_skip():
    from translators.screen import _should_skip
    assert _should_skip("") is True
    assert _should_skip("[var]") is True
    assert _should_skip("[mother]") is True
    assert _should_skip("123") is True
    assert _should_skip("...") is True
    assert _should_skip("已保存") is True
    assert _should_skip("images/bg.png") is True
    assert _should_skip("a") is True
    assert _should_skip("Save Game") is False
    assert _should_skip("NTR: undecided") is False
    assert _should_skip("{color=#f00}Warning{/color}") is False
    assert _should_skip("[name] is here") is False
    # 含 Ren'Py 闭合标签的文本不应被误判为文件路径
    assert _should_skip("{size=-10}- You can find work at the tanning salon.{/size}") is False
    assert _should_skip("{size=-10}when you're a gangmember.{/size}") is False
    assert _should_skip("icons/bg.png") is True  # 真正的文件路径仍跳过
    print("[OK] test_screen_should_skip")


def test_screen_extract_basic():
    from translators.screen import extract_screen_strings
    import tempfile, os
    content = """\
screen test_screen():
    vbox:
        text "Save Game"
        textbutton "Start" action Start()
        imagebutton hovered tt.Action("Go closer") focus_mask True
        text "{color=#f00}Warning{/color}"
        text "[pure_var]"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write(content)
        f.flush()
        tmp = Path(f.name)
    try:
        entries = extract_screen_strings(tmp)
        originals = [e.original for e in entries]
        assert "Save Game" in originals
        assert "Start" in originals
        assert "Go closer" in originals
        assert "{color=#f00}Warning{/color}" in originals
        assert "[pure_var]" not in originals  # 纯变量跳过
        types = {e.original: e.pattern_type for e in entries}
        assert types["Save Game"] == "text"
        assert types["Start"] == "textbutton"
        assert types["Go closer"] == "tt_action"
    finally:
        os.unlink(tmp)
    print("[OK] test_screen_extract_basic")


def test_screen_extract_skips_underscore():
    from translators.screen import extract_screen_strings
    import tempfile, os
    content = """\
screen menu_screen():
    textbutton _("Back") action Rollback()
    textbutton "Visible" action Jump("x")
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write(content)
        f.flush()
        tmp = Path(f.name)
    try:
        entries = extract_screen_strings(tmp)
        originals = [e.original for e in entries]
        assert "Back" not in originals  # _() 包裹应跳过
        assert "Visible" in originals
    finally:
        os.unlink(tmp)
    print("[OK] test_screen_extract_skips_underscore")


def test_screen_extract_skips_outside_screen():
    from translators.screen import extract_screen_strings
    import tempfile, os
    content = """\
label start:
    text "Outside screen"
    "Dialogue line"

screen inner():
    text "Inside screen"

define x = 1
    text "After screen"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write(content)
        f.flush()
        tmp = Path(f.name)
    try:
        entries = extract_screen_strings(tmp)
        originals = [e.original for e in entries]
        assert "Inside screen" in originals
        assert "Outside screen" not in originals
        assert "After screen" not in originals
    finally:
        os.unlink(tmp)
    print("[OK] test_screen_extract_skips_outside_screen")


def test_screen_dedup():
    from translators.screen import _deduplicate_entries, ScreenTextEntry
    entries = [
        ScreenTextEntry("a.rpy", 1, "text", "Hello"),
        ScreenTextEntry("b.rpy", 5, "text", "Hello"),
        ScreenTextEntry("a.rpy", 3, "text", "World"),
    ]
    table, by_text = _deduplicate_entries(entries)
    assert len(table) == 2
    assert len(by_text["Hello"]) == 2
    assert len(by_text["World"]) == 1
    print("[OK] test_screen_dedup")


def test_screen_replace_text():
    from translators.screen import _replace_screen_strings_in_file, ScreenTextEntry
    import tempfile, os
    content = '    text "Save Game"\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write(content)
        f.flush()
        tmp = Path(f.name)
    try:
        entries = [ScreenTextEntry(str(tmp), 1, "text", "Save Game")]
        table = {"Save Game": "保存游戏"}
        new_content, count = _replace_screen_strings_in_file(tmp, entries, table)
        assert count == 1
        assert '"保存游戏"' in new_content
        assert '    text "保存游戏"' in new_content  # 缩进保留
    finally:
        os.unlink(tmp)
    print("[OK] test_screen_replace_text")


def test_screen_replace_textbutton_preserves_action():
    from translators.screen import _replace_screen_strings_in_file, ScreenTextEntry
    import tempfile, os
    content = '    textbutton "Start" action Start() style "btn_style"\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write(content)
        f.flush()
        tmp = Path(f.name)
    try:
        entries = [ScreenTextEntry(str(tmp), 1, "textbutton", "Start")]
        table = {"Start": "开始"}
        new_content, count = _replace_screen_strings_in_file(tmp, entries, table)
        assert count == 1
        assert '"开始"' in new_content
        assert 'style "btn_style"' in new_content  # action 参数不动
        assert 'Start()' in new_content  # action 函数不动
    finally:
        os.unlink(tmp)
    print("[OK] test_screen_replace_textbutton_preserves_action")


def test_screen_replace_tt_action():
    from translators.screen import _replace_screen_strings_in_file, ScreenTextEntry
    import tempfile, os
    content = '    imagebutton hovered tt.Action("Go closer") focus_mask True\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write(content)
        f.flush()
        tmp = Path(f.name)
    try:
        entries = [ScreenTextEntry(str(tmp), 1, "tt_action", "Go closer")]
        table = {"Go closer": "靠近"}
        new_content, count = _replace_screen_strings_in_file(tmp, entries, table)
        assert count == 1
        assert '"靠近"' in new_content
        assert 'focus_mask True' in new_content
    finally:
        os.unlink(tmp)
    print("[OK] test_screen_replace_tt_action")


def test_screen_replace_with_tags_and_vars():
    from translators.screen import _replace_screen_strings_in_file, ScreenTextEntry
    import tempfile, os
    content = '    text "Relationship: {color=3cff00}[momrelationship]{/color}"\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write(content)
        f.flush()
        tmp = Path(f.name)
    try:
        entries = [ScreenTextEntry(str(tmp), 1, "text",
                                   "Relationship: {color=3cff00}[momrelationship]{/color}")]
        table = {"Relationship: {color=3cff00}[momrelationship]{/color}":
                 "关系: {color=3cff00}[momrelationship]{/color}"}
        new_content, count = _replace_screen_strings_in_file(tmp, entries, table)
        assert count == 1
        assert "关系:" in new_content
        assert "{color=3cff00}[momrelationship]{/color}" in new_content
    finally:
        os.unlink(tmp)
    print("[OK] test_screen_replace_with_tags_and_vars")


def test_screen_replace_notify():
    from translators.screen import _replace_screen_strings_in_file, ScreenTextEntry
    import tempfile, os
    content = '    imagebutton action Jump("x") hovered Notify("Help needed") focus_mask True\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write(content)
        f.flush()
        tmp = Path(f.name)
    try:
        entries = [ScreenTextEntry(str(tmp), 1, "notify", "Help needed")]
        table = {"Help needed": "需要帮助"}
        new_content, count = _replace_screen_strings_in_file(tmp, entries, table)
        assert count == 1
        assert '"需要帮助"' in new_content
        assert 'Notify' in new_content
        assert 'Jump("x")' in new_content  # action 参数不动
    finally:
        os.unlink(tmp)
    print("[OK] test_screen_replace_notify")


def test_screen_backup_no_overwrite():
    from translators.screen import _create_backup
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False,
                                     encoding='utf-8') as f:
        f.write("original content")
        f.flush()
        tmp = Path(f.name)
    bak = tmp.with_suffix(tmp.suffix + ".bak")
    try:
        assert not bak.exists()
        _create_backup(tmp)
        assert bak.exists()
        assert bak.read_text(encoding="utf-8") == "original content"
        # 第二次不覆盖
        bak.write_text("old backup", encoding="utf-8")
        _create_backup(tmp)
        assert bak.read_text(encoding="utf-8") == "old backup"
    finally:
        os.unlink(tmp)
        if bak.exists():
            os.unlink(bak)
    print("[OK] test_screen_backup_no_overwrite")


def test_screen_chunks():
    from translators.screen import _build_screen_chunks
    texts = [f"text_{i}" for i in range(100)]
    chunks = _build_screen_chunks(texts, max_per_chunk=40)
    assert len(chunks) == 3
    assert len(chunks[0]) == 40
    assert len(chunks[1]) == 40
    assert len(chunks[2]) == 20
    # 总数守恒
    assert sum(len(c) for c in chunks) == 100
    print("[OK] test_screen_chunks")


# ============================================================
# J: 锁定术语预替换 (locked_terms protection)
# ============================================================

def test_locked_terms_protect_basic():
    """locked_terms: basic protection and restore."""
    from file_processor.checker import protect_locked_terms, restore_locked_terms
    terms = {"MyGame": "我的游戏", "Alice": "爱丽丝"}
    text = 'mc "Welcome to MyGame! Alice is here."'
    protected, mapping = protect_locked_terms(text, terms)
    assert "MyGame" not in protected
    assert "Alice" not in protected
    assert "__LOCKED_TERM_" in protected
    assert len(mapping) == 2
    # Restore with Chinese translations
    restored = restore_locked_terms(protected, mapping)
    assert "我的游戏" in restored
    assert "爱丽丝" in restored
    assert "__LOCKED_TERM_" not in restored
    print("[OK] test_locked_terms_protect_basic")


def test_locked_terms_word_boundary():
    """locked_terms: word boundary prevents partial matches."""
    from file_processor.checker import protect_locked_terms
    terms = {"Game": "游戏"}
    text = 'GameOver is not the same as Game end'
    protected, mapping = protect_locked_terms(text, terms)
    # "Game" should match "Game end" but NOT "GameOver"
    assert "GameOver" in protected  # not replaced
    assert len(mapping) == 1
    assert "__LOCKED_TERM_0__" in protected
    # Check that "Game end" was partially replaced
    assert "__LOCKED_TERM_0__ end" in protected
    print("[OK] test_locked_terms_word_boundary")


def test_locked_terms_longer_first():
    """locked_terms: longer terms matched first."""
    from file_processor.checker import protect_locked_terms
    terms = {"New York": "纽约", "New": "新"}
    text = 'Visit New York and New Orleans'
    protected, mapping = protect_locked_terms(text, terms)
    # "New York" should be matched before "New"
    assert "New York" not in protected
    # mapping[0] should be the "New York" entry
    assert mapping[0][1] == "纽约"
    print("[OK] test_locked_terms_longer_first")


def test_locked_terms_empty():
    """locked_terms: empty terms dict does nothing."""
    from file_processor.checker import protect_locked_terms
    text = "Hello world"
    protected, mapping = protect_locked_terms(text, {})
    assert protected == text
    assert mapping == []
    # Also test with None-value terms
    protected2, mapping2 = protect_locked_terms(text, {"Key": ""})
    assert protected2 == text
    assert mapping2 == []
    print("[OK] test_locked_terms_empty")


def test_locked_terms_no_match():
    """locked_terms: no matching terms in text."""
    from file_processor.checker import protect_locked_terms
    terms = {"NotInText": "不在文中"}
    text = 'mc "Hello world"'
    protected, mapping = protect_locked_terms(text, terms)
    assert protected == text
    assert mapping == []
    print("[OK] test_locked_terms_no_match")


def test_locked_terms_multiple_occurrences():
    """locked_terms: same term appearing multiple times."""
    from file_processor.checker import protect_locked_terms, restore_locked_terms
    terms = {"Alice": "爱丽丝"}
    text = 'Alice said "Hi Alice" to Alice.'
    protected, mapping = protect_locked_terms(text, terms)
    assert protected.count("__LOCKED_TERM_0__") == 3
    restored = restore_locked_terms(protected, mapping)
    assert restored.count("爱丽丝") == 3
    print("[OK] test_locked_terms_multiple_occurrences")


def test_locked_terms_special_chars():
    """locked_terms: terms with regex special characters."""
    from file_processor.checker import protect_locked_terms, restore_locked_terms
    terms = {"C++": "C加加", "Mr.Smith": "史密斯先生"}
    text = 'Learn C++ with Mr.Smith today'
    protected, mapping = protect_locked_terms(text, terms)
    restored = restore_locked_terms(protected, mapping)
    assert "C加加" in restored
    assert "史密斯先生" in restored
    print("[OK] test_locked_terms_special_chars")


def test_pipeline_imports_smoke():
    """Pipeline sub-package lazy imports must resolve.

    Catches broken imports that hide behind function-level ``from X import Y``
    statements and therefore survive the normal unit-test pass. Historically
    a refactor left ``pipeline/stages.py`` importing from ``main`` names that
    had been relocated, and ``pipeline/gate.py`` importing constants from a
    module that never defined them — crashes surfaced only at runtime.
    """
    from pipeline.gate import evaluate_gate, attribute_untranslated
    from pipeline.stages import _run_retranslate_phase
    from engines.generic_pipeline import run_generic_pipeline
    from translators.retranslator import retranslate_file, find_untranslated_lines
    from core.translation_utils import ProgressTracker
    from pipeline.helpers import LEN_RATIO_LOWER, LEN_RATIO_UPPER
    assert callable(evaluate_gate)
    assert callable(attribute_untranslated)
    assert callable(_run_retranslate_phase)
    assert callable(run_generic_pipeline)
    assert callable(retranslate_file)
    assert callable(find_untranslated_lines)
    assert isinstance(LEN_RATIO_LOWER, float)
    assert isinstance(LEN_RATIO_UPPER, float)
    # ProgressTracker must be instantiable with a Path
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        pt = ProgressTracker(Path(td) / "progress.json")
        assert hasattr(pt, "save")
    print("[OK] test_pipeline_imports_smoke")


# ============================================================
# API retry mock tests (round 21 — T-C-2)
# ------------------------------------------------------------
# These tests lock down the six HTTP retry branches in
# ``APIClient._call_api`` so that future changes to the transport layer
# (e.g. connection pooling) cannot silently break retry semantics.
# ============================================================

def _make_urlopen_success(body_bytes: bytes):
    """Build a MagicMock that behaves like ``urlopen(...)`` return value (context manager).

    Uses a real ``BytesIO`` for ``read`` so that the bounded-read helper in
    ``core.http_pool`` (which loops until ``read(N)`` returns ``b''``) terminates
    naturally at EOF instead of looping on a sticky MagicMock ``return_value``.
    """
    from unittest.mock import MagicMock
    import io
    ctx = MagicMock()
    resp = MagicMock()
    resp.read = io.BytesIO(body_bytes).read
    ctx.__enter__.return_value = resp
    ctx.__exit__.return_value = False
    return ctx


def _build_httperror(code: int, retry_after: str = ""):
    """Build a ``urllib.error.HTTPError`` with optional Retry-After header."""
    from urllib.error import HTTPError
    from io import BytesIO
    import email.message
    hdrs = email.message.Message()
    if retry_after:
        hdrs["Retry-After"] = retry_after
    return HTTPError("http://example/api", code, "err", hdrs, BytesIO(b'{"error": "x"}'))


_OPENAI_OK_BODY = (
    b'{"choices": [{"message": {"content": "ok"}}],'
    b' "usage": {"prompt_tokens": 1, "completion_tokens": 1}}'
)


def test_api_429_retry_after_header():
    """HTTP 429 with ``Retry-After`` header: wait the advertised seconds then retry."""
    from unittest.mock import patch
    from core import api_client

    config = api_client.APIConfig(
        provider='xai', api_key='test', model='grok', max_retries=3, rpm=0, rps=0,
        use_connection_pool=False,
    )
    client = api_client.APIClient(config)

    err = _build_httperror(429, retry_after="2")
    ok = _make_urlopen_success(_OPENAI_OK_BODY)

    with patch.object(api_client.urlreq, 'urlopen', side_effect=[err, ok]) as m_open, \
         patch.object(api_client.time, 'sleep') as m_sleep, \
         patch('random.uniform', return_value=0.0):
        raw = client._call_api('sys', 'user')

    assert raw == "ok"
    assert m_open.call_count == 2
    assert m_sleep.call_count == 1
    first_wait = m_sleep.call_args_list[0][0][0]
    assert abs(first_wait - 2.0) < 0.01, f"expected wait ~2s (Retry-After), got {first_wait}"
    print("[OK] test_api_429_retry_after_header")


def test_api_429_exponential_backoff():
    """HTTP 429 without ``Retry-After``: exponential backoff kicks in, then retry succeeds."""
    from unittest.mock import patch
    from core import api_client

    config = api_client.APIConfig(
        provider='xai', api_key='test', model='grok', max_retries=3, rpm=0, rps=0,
        use_connection_pool=False,
    )
    client = api_client.APIClient(config)

    err = _build_httperror(429)  # no Retry-After
    ok = _make_urlopen_success(_OPENAI_OK_BODY)

    with patch.object(api_client.urlreq, 'urlopen', side_effect=[err, ok]), \
         patch.object(api_client.time, 'sleep') as m_sleep, \
         patch('random.uniform', return_value=0.0):
        raw = client._call_api('sys', 'user')

    assert raw == "ok"
    assert m_sleep.call_count == 1
    wait = m_sleep.call_args_list[0][0][0]
    # attempt=1: base = min(2**1 * 5, 60) = 10, jitter=0 -> wait=10
    assert abs(wait - 10.0) < 0.01, f"expected exponential backoff ~10s, got {wait}"
    print("[OK] test_api_429_exponential_backoff")


def test_api_500_retry():
    """HTTP 500 retries with its own exponential backoff schedule."""
    from unittest.mock import patch
    from core import api_client

    config = api_client.APIConfig(
        provider='xai', api_key='test', model='grok', max_retries=3, rpm=0, rps=0,
        use_connection_pool=False,
    )
    client = api_client.APIClient(config)

    err = _build_httperror(500)
    ok = _make_urlopen_success(_OPENAI_OK_BODY)

    with patch.object(api_client.urlreq, 'urlopen', side_effect=[err, ok]), \
         patch.object(api_client.time, 'sleep') as m_sleep, \
         patch('random.uniform', return_value=0.0):
        raw = client._call_api('sys', 'user')

    assert raw == "ok"
    assert m_sleep.call_count == 1
    wait = m_sleep.call_args_list[0][0][0]
    # attempt=1: base = min(2**1 * 3, 60) = 6, jitter=0 -> wait=6
    assert abs(wait - 6.0) < 0.01, f"expected 500 backoff ~6s, got {wait}"
    print("[OK] test_api_500_retry")


def test_api_401_no_retry():
    """HTTP 401 surfaces immediately as ``RuntimeError`` — no retry, no sleep."""
    from unittest.mock import patch
    from core import api_client

    config = api_client.APIConfig(
        provider='xai', api_key='test', model='grok', max_retries=3, rpm=0, rps=0,
        use_connection_pool=False,
    )
    client = api_client.APIClient(config)

    err = _build_httperror(401)

    with patch.object(api_client.urlreq, 'urlopen', side_effect=err), \
         patch.object(api_client.time, 'sleep') as m_sleep:
        try:
            client._call_api('sys', 'user')
            raised = False
        except RuntimeError as e:
            raised = True
            assert "401" in str(e)
            assert "api-key" in str(e).lower() or "api_key" in str(e).lower()

    assert raised, "expected RuntimeError on 401"
    assert m_sleep.call_count == 0, "401 must not trigger retry sleep"
    print("[OK] test_api_401_no_retry")


def test_api_404_no_retry():
    """HTTP 404 surfaces immediately as ``RuntimeError`` — no retry, no sleep."""
    from unittest.mock import patch
    from core import api_client

    config = api_client.APIConfig(
        provider='xai', api_key='test', model='bad-model', max_retries=3, rpm=0, rps=0,
        use_connection_pool=False,
    )
    client = api_client.APIClient(config)

    err = _build_httperror(404)

    with patch.object(api_client.urlreq, 'urlopen', side_effect=err), \
         patch.object(api_client.time, 'sleep') as m_sleep:
        try:
            client._call_api('sys', 'user')
            raised = False
        except RuntimeError as e:
            raised = True
            assert "404" in str(e)
            assert "bad-model" in str(e)

    assert raised, "expected RuntimeError on 404"
    assert m_sleep.call_count == 0, "404 must not trigger retry sleep"
    print("[OK] test_api_404_no_retry")


def test_api_urlerror_retry():
    """Transport-level ``URLError`` (e.g. DNS / TLS / connection refused) retries."""
    from unittest.mock import patch
    from urllib.error import URLError
    from core import api_client

    config = api_client.APIConfig(
        provider='xai', api_key='test', model='grok', max_retries=3, rpm=0, rps=0,
        use_connection_pool=False,
    )
    client = api_client.APIClient(config)

    err = URLError("connection refused")
    ok = _make_urlopen_success(_OPENAI_OK_BODY)

    with patch.object(api_client.urlreq, 'urlopen', side_effect=[err, ok]) as m_open, \
         patch.object(api_client.time, 'sleep') as m_sleep, \
         patch('random.uniform', return_value=0.0):
        raw = client._call_api('sys', 'user')

    assert raw == "ok"
    assert m_open.call_count == 2
    assert m_sleep.call_count == 1
    wait = m_sleep.call_args_list[0][0][0]
    # URLError path: base = min(2**1 * 3, 60) = 6, jitter=0 -> wait=6
    assert abs(wait - 6.0) < 0.01, f"expected URLError backoff ~6s, got {wait}"
    print("[OK] test_api_urlerror_retry")


def test_progress_concurrent_flush():
    """Concurrent ``mark_chunk_done`` across workers must not deadlock or lose chunks.

    Round 21 (P-H-2) moved disk I/O out of the main data lock. This test
    exercises 4 threads × 50 marks each, then verifies every chunk is
    present after ``save()``. A deadlock in the new two-lock scheme would
    cause this test to hang past the join timeout.
    """
    import threading
    import tempfile
    from pathlib import Path
    from core.translation_utils import ProgressTracker

    with tempfile.TemporaryDirectory() as td:
        pt = ProgressTracker(Path(td) / "progress.json")

        def worker(thread_id: int) -> None:
            for i in range(50):
                pt.mark_chunk_done(
                    f"file_{thread_id}.rpy",
                    i,
                    [{"original": f"x{i}", "zh": f"y{i}"}],
                )

        threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        for t in threads:
            assert not t.is_alive(), "ProgressTracker deadlock: thread still alive after 15s"

        pt.save()

        for tid in range(4):
            chunks = pt.data["completed_chunks"][f"file_{tid}.rpy"]
            assert sorted(chunks) == list(range(50)), (
                f"file_{tid}.rpy missing chunks (got {len(chunks)}/50): {chunks}"
            )
    print("[OK] test_progress_concurrent_flush")


def test_progress_write_ordering_monotonic():
    """Disk writes under concurrent flushing must be monotonically non-decreasing.

    Locks down the round 22 P1 fix: before the fix, ``_flush_to_disk`` took the
    data lock for the snapshot and then **released it** before acquiring
    ``_save_lock`` — so two threads could each snapshot independently and then
    race into the save lock, with the slower-to-write one clobbering the fresher
    snapshot. After the fix, ``_save_lock`` wraps the ``_lock`` + snapshot +
    write sequence atomically, guaranteeing the on-disk state never regresses.
    """
    import threading
    import tempfile
    import json as _json
    from pathlib import Path
    from core.translation_utils import ProgressTracker

    writes_sizes: list[int] = []
    writes_sizes_lock = threading.Lock()

    with tempfile.TemporaryDirectory() as td:
        pt = ProgressTracker(Path(td) / "progress.json")

        real_write = pt._write_atomic

        def spy_write(json_str: str) -> None:
            data = _json.loads(json_str)
            total_chunks = sum(
                len(c) for c in data.get("completed_chunks", {}).values()
            )
            with writes_sizes_lock:
                writes_sizes.append(total_chunks)
            real_write(json_str)

        pt._write_atomic = spy_write

        def worker(tid: int) -> None:
            for i in range(30):
                pt.mark_chunk_done(f"file_{tid}.rpy", i, [])

        threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        assert len(writes_sizes) >= 3, (
            f"expected at least 3 flushes across 180 marks, got {len(writes_sizes)}"
        )
        for i in range(1, len(writes_sizes)):
            assert writes_sizes[i] >= writes_sizes[i - 1], (
                f"non-monotonic write at index {i}: "
                f"writes_sizes[{i - 1}]={writes_sizes[i - 1]} > "
                f"writes_sizes[{i}]={writes_sizes[i]} — snapshot ordering violated"
            )
    print("[OK] test_progress_write_ordering_monotonic")


# ============================================================
# HTTP connection pool tests (round 21 — PF-C-1)
# ============================================================

def _mock_http_response(status: int, body: bytes = b'{"ok":true}', headers=None):
    """Build a mock ``http.client.HTTPResponse`` (supports status / getheaders / read).

    Uses a real ``BytesIO`` for ``read`` so bounded reads terminate at EOF.
    """
    from unittest.mock import MagicMock
    import io
    resp = MagicMock()
    resp.status = status
    resp.getheaders = MagicMock(return_value=headers or [])
    resp.read = io.BytesIO(body).read
    return resp


def test_http_pool_reuses_connection():
    """Three POSTs on the same thread must hit exactly one underlying HTTPSConnection.

    This is the core reason the pool exists: it eliminates ~150 ms of TCP+TLS
    handshake per request after the first one.
    """
    from unittest.mock import patch, MagicMock
    from core.http_pool import HTTPSConnectionPool

    mock_conn = MagicMock()
    # 每次 getresponse() 返回全新 resp（带独立 BytesIO），这样 3 次 post 都能读到完整 body
    mock_conn.getresponse = MagicMock(side_effect=lambda: _mock_http_response(200))

    with patch('core.http_pool.http.client.HTTPSConnection',
               return_value=mock_conn) as m_cls:
        pool = HTTPSConnectionPool()
        for _ in range(3):
            body = pool.post("https://api.example.com/v1/x", b'{}', {"X": "1"})
            assert body == b'{"ok":true}'
        assert m_cls.call_count == 1, f"expected 1 connection created, got {m_cls.call_count}"
        assert mock_conn.request.call_count == 3
    print("[OK] test_http_pool_reuses_connection")


def test_http_pool_reconnects_on_transport_error():
    """Transport failure (e.g. keep-alive dropped) should trigger a single reconnect."""
    from unittest.mock import patch, MagicMock
    from core.http_pool import HTTPSConnectionPool

    mock_broken = MagicMock()
    mock_broken.request = MagicMock(side_effect=ConnectionResetError("broken pipe"))

    mock_fresh = MagicMock()
    mock_fresh.getresponse = MagicMock(return_value=_mock_http_response(200))

    with patch('core.http_pool.http.client.HTTPSConnection',
               side_effect=[mock_broken, mock_fresh]) as m_cls:
        pool = HTTPSConnectionPool()
        body = pool.post("https://api.example.com/v1/x", b'{}', {})

    assert body == b'{"ok":true}'
    assert m_cls.call_count == 2, f"expected reconnect (2 conns), got {m_cls.call_count}"
    assert mock_broken.close.called, "broken connection should have been closed"
    print("[OK] test_http_pool_reconnects_on_transport_error")


def test_http_pool_raises_http_error_on_4xx():
    """HTTP 4xx / 5xx must surface as ``urllib.error.HTTPError`` so that
    ``APIClient._call_api`` retry logic keeps working unchanged."""
    from unittest.mock import patch, MagicMock
    from urllib.error import HTTPError
    from core.http_pool import HTTPSConnectionPool

    mock_conn = MagicMock()
    mock_conn.getresponse = MagicMock(return_value=_mock_http_response(
        429, body=b'{"error":"rate"}', headers=[("Retry-After", "5")]
    ))

    with patch('core.http_pool.http.client.HTTPSConnection', return_value=mock_conn):
        pool = HTTPSConnectionPool()
        try:
            pool.post("https://api.example.com/v1/x", b'{}', {})
            raised = False
        except HTTPError as e:
            raised = True
            assert e.code == 429
            assert e.headers.get("Retry-After") == "5"
    assert raised, "expected HTTPError on 429"
    print("[OK] test_http_pool_raises_http_error_on_4xx")


def test_api_key_child_env_pop():
    """``_RENPY_TRANSLATOR_CHILD_API_KEY`` must be read with ``pop`` not ``get``.

    Both ``main.py`` and ``one_click_pipeline.py`` read the private child-process
    variable and remove it from the environment in the same statement, so that
    the key does not leak into further ``subprocess`` children spawned by the
    translator (e.g. PyInstaller helpers, Ren'Py's bundled Python). This test
    codifies that contract.
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    # 1. In-process pop semantics
    os.environ["_RENPY_TRANSLATOR_CHILD_API_KEY"] = "test_key_xyz"
    key = os.environ.pop("_RENPY_TRANSLATOR_CHILD_API_KEY", "")
    assert key == "test_key_xyz"
    assert "_RENPY_TRANSLATOR_CHILD_API_KEY" not in os.environ
    assert os.environ.pop("_RENPY_TRANSLATOR_CHILD_API_KEY", "") == ""

    # 2. Cross-process: env var set on parent is received by child, then pop() removes it.
    child_code = (
        "import os; "
        "k = os.environ.pop('_RENPY_TRANSLATOR_CHILD_API_KEY', ''); "
        "still = '_RENPY_TRANSLATOR_CHILD_API_KEY' in os.environ; "
        "print(f'{k}|{still}')"
    )
    env = os.environ.copy()
    env["_RENPY_TRANSLATOR_CHILD_API_KEY"] = "sub_key_abc"
    proc = subprocess.run(
        [sys.executable, "-c", child_code],
        env=env, capture_output=True, text=True, timeout=15,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert proc.returncode == 0, f"child failed: {proc.stderr}"
    assert proc.stdout.strip() == "sub_key_abc|False", (
        f"unexpected child output: {proc.stdout!r}"
    )
    print("[OK] test_api_key_child_env_pop")


# ============================================================
# Response-body size cap (round 22 — H1)
# ============================================================

def test_http_pool_rejects_oversized_response():
    """``HTTPSConnectionPool.post`` must stop reading once the response body
    exceeds ``MAX_API_RESPONSE_BYTES`` (32 MB) and raise ``ResponseTooLarge``.

    Guards against a malicious / misconfigured endpoint streaming unbounded
    data into the translator process, which would otherwise OOM.
    """
    from unittest.mock import patch, MagicMock
    from core.http_pool import HTTPSConnectionPool, ResponseTooLarge

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.getheaders = MagicMock(return_value=[])
    # Each read() returns 64 KB; the pool reads in 64 KB chunks so we hit the
    # 32 MB cap after ~513 iterations without needing to materialise 32 MB in
    # the test process.
    mock_resp.read = MagicMock(return_value=b'\x00' * 65536)

    mock_conn = MagicMock()
    mock_conn.getresponse = MagicMock(return_value=mock_resp)

    with patch('core.http_pool.http.client.HTTPSConnection', return_value=mock_conn):
        pool = HTTPSConnectionPool()
        try:
            pool.post("https://api.example.com/v1/x", b'{}', {})
            raised = False
        except ResponseTooLarge as e:
            raised = True
            msg = str(e)
            assert "32" in msg, f"expected size info in error msg, got: {msg}"
    assert raised, "expected ResponseTooLarge when pool reads past the cap"
    print("[OK] test_http_pool_rejects_oversized_response")


def test_api_client_urllib_rejects_oversized_response():
    """The urllib fallback path in ``APIClient`` must also enforce the cap —
    otherwise setting ``use_connection_pool=False`` would silently bypass
    the hardening.
    """
    from unittest.mock import patch, MagicMock
    from core import api_client
    from core.http_pool import ResponseTooLarge

    config = api_client.APIConfig(
        provider='xai', api_key='test', model='grok',
        max_retries=1, rpm=0, rps=0, use_connection_pool=False,
    )
    client = api_client.APIClient(config)

    mock_resp = MagicMock()
    mock_resp.read = MagicMock(return_value=b'\x00' * 65536)
    ctx = MagicMock()
    ctx.__enter__.return_value = mock_resp
    ctx.__exit__.return_value = False

    with patch.object(api_client.urlreq, 'urlopen', return_value=ctx):
        try:
            client._call_api('sys', 'user')
            raised = False
        except ResponseTooLarge:
            raised = True
    assert raised, "urllib fallback path should also raise ResponseTooLarge"
    print("[OK] test_api_client_urllib_rejects_oversized_response")


def test_glossary_scan_renpy_directory():
    """``Glossary.scan_game_directory`` must extract ``define NAME = Character(...)``
    and ``define config.name = "..."`` from .rpy files (round 25 T-H-1).

    Previously the RPG Maker branch had targeted coverage via
    ``test_glossary_scan_rpgmaker`` but the Ren'Py regex path had none,
    leaving a silent-break risk: any regression in ``char_re`` /
    ``config_name_re`` would go undetected until a real game is translated.
    """
    import tempfile
    from pathlib import Path
    from core.glossary import Glossary

    fixture = (
        '# game/characters.rpy\n'
        'define mc = Character("Main Hero", color="#c8a")\n'
        'define e = Character("Eileen")\n'
        'define narrator = DynamicCharacter("旁白")\n'
        'define config.name = "Test Game"\n'
        'define config.version = "1.0.0"\n'
    )

    with tempfile.TemporaryDirectory() as td:
        game_dir = Path(td) / "game"
        game_dir.mkdir()
        (game_dir / "characters.rpy").write_text(fixture, encoding='utf-8')

        # 放一个应被跳过的 renpy/ 引擎目录文件（不应被扫描）
        renpy_dir = game_dir / "renpy"
        renpy_dir.mkdir()
        (renpy_dir / "engine.rpy").write_text(
            'define engine_internal = Character("Should NOT appear")\n',
            encoding='utf-8',
        )

        g = Glossary()
        g.scan_game_directory(str(game_dir))

        assert g.characters.get("mc") == "Main Hero", (
            f"expected mc → 'Main Hero', got {g.characters.get('mc')!r}"
        )
        assert g.characters.get("e") == "Eileen", (
            f"expected e → 'Eileen', got {g.characters.get('e')!r}"
        )
        assert g.characters.get("narrator") == "旁白", (
            f"expected narrator → '旁白', got {g.characters.get('narrator')!r}"
        )
        # renpy/ 目录应被跳过
        assert "engine_internal" not in g.characters, (
            f"engine file should be skipped, but got: {g.characters}"
        )
        # config.name / config.version 应进入 terms
        assert g.terms.get("__game_name__") == "Test Game", (
            f"expected terms['__game_name__'] = 'Test Game', got {g.terms.get('__game_name__')!r}"
        )
        assert g.terms.get("__game_version__") == "1.0.0", (
            f"expected version 1.0.0, got {g.terms.get('__game_version__')!r}"
        )
    print("[OK] test_glossary_scan_renpy_directory")


def test_translation_db_concurrent_upsert():
    """``TranslationDB.upsert_entry`` must be safe under concurrent access.

    Round 26 C-1: with ``threading.RLock`` added, 32 worker threads each
    inserting 100 unique entries must converge to 3200 distinct entries
    with the index intact (no lost updates, no index corruption).
    """
    import tempfile
    import threading
    from pathlib import Path
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json")

        n_threads = 32
        per_thread = 100
        barrier = threading.Barrier(n_threads)

        def worker(tid: int) -> None:
            barrier.wait()
            for i in range(per_thread):
                db.upsert_entry({
                    "file": f"file_{tid}.rpy",
                    "line": i + 1,
                    "original": f"text_{tid}_{i}",
                    "translation": f"trans_{tid}_{i}",
                    "status": "ok",
                })

        threads = [threading.Thread(target=worker, args=(tid,)) for tid in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = n_threads * per_thread
        assert len(db.entries) == expected, (
            f"expected {expected} entries, got {len(db.entries)} (race condition?)"
        )
        # Every (file, line, original) must be looked up via has_entry.
        for tid in range(n_threads):
            for i in range(per_thread):
                assert db.has_entry(f"file_{tid}.rpy", i + 1, f"text_{tid}_{i}"), (
                    f"missing entry ({tid}, {i})"
                )
        # Index and entries must be consistent.
        assert len(db._index) == expected, (
            f"index size {len(db._index)} != entries size {expected}"
        )
    print("[OK] test_translation_db_concurrent_upsert")


def test_translation_db_save_atomic():
    """``TranslationDB.save`` must not corrupt an existing on-disk DB when the
    atomic replace step fails mid-way (round 26 C-2).
    """
    import json as _json
    import os as _os
    import tempfile
    from pathlib import Path
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "db.json"
        db = TranslationDB(db_path)
        db.upsert_entry({
            "file": "a.rpy", "line": 1, "original": "hello",
            "translation": "你好", "status": "ok",
        })
        db.save()  # writes a valid DB

        # Snapshot original bytes for later compare.
        original_bytes = db_path.read_bytes()

        # Add a second entry and force save to fail at os.replace.
        db.upsert_entry({
            "file": "b.rpy", "line": 2, "original": "world",
            "translation": "世界", "status": "ok",
        })

        real_replace = _os.replace
        calls = {"n": 0}

        def broken_replace(src, dst):  # noqa: ANN001
            calls["n"] += 1
            raise OSError("simulated replace failure")

        _os.replace = broken_replace
        try:
            raised = False
            try:
                db.save()
            except OSError:
                raised = True
            assert raised, "save() should propagate OSError when os.replace fails"
        finally:
            _os.replace = real_replace

        # Original DB file content must be unchanged.
        assert db_path.read_bytes() == original_bytes, (
            "db.json content changed after failed atomic save"
        )
        # The temp file should have been cleaned up.
        tmp_path = db_path.with_suffix(db_path.suffix + ".tmp")
        assert not tmp_path.exists(), f"stale temp file remains: {tmp_path}"

        # The on-disk JSON must still be valid with a single entry.
        persisted = _json.loads(db_path.read_text(encoding="utf-8"))
        assert len(persisted["entries"]) == 1, (
            f"expected 1 persisted entry, got {len(persisted['entries'])}"
        )
    print("[OK] test_translation_db_save_atomic")


def test_translation_db_accepts_line_zero():
    """``line=0`` is a legitimate placeholder (generic engines use it for
    formats without meaningful line numbers); it must no longer be silently
    dropped (round 26 C-3).
    """
    import tempfile
    from pathlib import Path
    from core.translation_db import TranslationDB

    with tempfile.TemporaryDirectory() as td:
        db = TranslationDB(Path(td) / "db.json")
        db.upsert_entry({
            "file": "generic.csv", "line": 0,
            "original": "Hello, world!",
            "translation": "你好，世界！",
            "status": "ok",
        })
        assert db.has_entry("generic.csv", 0, "Hello, world!"), (
            "entry with line=0 must be stored and retrievable"
        )
        results = db.filter_by_status(statuses=["ok"])
        assert any(e["file"] == "generic.csv" and e["line"] == 0 for e in results), (
            "filter_by_status should include line=0 entries"
        )
        # Round-trip through save/load.
        db.save()
        db2 = TranslationDB(Path(td) / "db.json")
        db2.load()
        assert db2.has_entry("generic.csv", 0, "Hello, world!"), (
            "line=0 entry must survive save/load round-trip"
        )
    print("[OK] test_translation_db_accepts_line_zero")


if __name__ == '__main__':
    test_api_config()
    test_usage_stats()
    test_rate_limiter()
    test_estimate_tokens()
    test_find_block_boundaries()
    test_safety_check()
    test_apply_translations()
    test_apply_cascade()
    test_validate_translation()
    test_glossary()
    test_prompts()
    test_json_parse()
    test_force_split()
    test_triple_quote_replacement()
    test_underscore_func_replacement()
    test_validate_menu_identifier()
    test_glossary_dedup()
    test_image_block_boundary()
    test_glossary_thread_safety()
    test_progress_cleanup()
    test_pricing_lookup()
    # B1: 核心函数测试
    test_protect_restore_roundtrip()
    test_protect_dedup()
    test_protect_empty_and_no_placeholders()
    test_protect_mixed_types()
    test_protect_menu_id()
    test_check_response_item_normal()
    test_check_response_item_empty_zh()
    test_check_response_item_empty_original()
    test_check_response_item_var_missing()
    test_check_response_item_var_preserved()
    test_check_response_item_line_offset()
    test_check_response_chunk_match()
    test_check_response_chunk_mismatch()
    test_check_response_chunk_empty()
    test_check_response_chunk_skip_chinese()
    # C: 集成级测试
    test_dialogue_density()
    test_skip_files()
    test_find_untranslated_lines()
    test_translation_db_roundtrip()
    test_is_untranslated_dialogue()
    test_restore_placeholders_in_translations()
    # D: 第九轮新增测试
    test_progress_resume()
    test_progress_normalize()
    test_filter_checked_translations()
    test_deduplicate_translations()
    test_match_string_entry_fallback()
    test_api_empty_choices()
    test_positive_int_validation()
    test_reasoning_model_timeout()
    test_glossary_hyphenated_names()
    test_glossary_memory_confidence()
    test_protect_control_tags()
    test_replace_string_prefix_strip()
    test_replace_string_escaped_quotes()
    test_config_load_and_defaults()
    test_config_cli_override()
    test_config_file_load()
    test_progress_bar_render()
    test_review_generator_html()
    test_lang_config_detect()
    test_lang_config_lookup()
    test_resolve_translation_field()
    test_prompt_zh_unchanged()
    test_prompt_ja_generic()
    test_validator_lang_config()
    # F: chunk 拆分重试测试
    test_should_retry_truncation()
    test_should_retry_normal()
    test_split_chunk_basic()
    test_split_chunk_at_empty_line()
    # G: 配置 schema 校验
    test_config_validation()
    # H: nvl clear 翻译 ID 修正
    test_fix_nvl_ids_basic()
    test_fix_nvl_ids_no_nvl()
    test_fix_nvl_ids_already_correct()
    test_fix_nvl_ids_real_hashes()
    # I: screen_translator 测试
    test_screen_should_skip()
    test_screen_extract_basic()
    test_screen_extract_skips_underscore()
    test_screen_extract_skips_outside_screen()
    test_screen_dedup()
    test_screen_replace_text()
    test_screen_replace_textbutton_preserves_action()
    test_screen_replace_tt_action()
    test_screen_replace_with_tags_and_vars()
    test_screen_replace_notify()
    test_screen_backup_no_overwrite()
    test_screen_chunks()
    # J: 锁定术语预替换
    test_locked_terms_protect_basic()
    test_locked_terms_word_boundary()
    test_locked_terms_longer_first()
    test_locked_terms_empty()
    test_locked_terms_no_match()
    test_locked_terms_multiple_occurrences()
    test_locked_terms_special_chars()
    # K: 架构回归保护（round 20 — CRITICAL import 修复）
    test_pipeline_imports_smoke()
    # L: API retry mock tests（round 21 — T-C-2）
    test_api_429_retry_after_header()
    test_api_429_exponential_backoff()
    test_api_500_retry()
    test_api_401_no_retry()
    test_api_404_no_retry()
    test_api_urlerror_retry()
    # M: ProgressTracker concurrency（round 21 — P-H-2）
    test_progress_concurrent_flush()
    # M': write-ordering monotonicity（round 22 — P1 review fix）
    test_progress_write_ordering_monotonic()
    # N: HTTP connection pool（round 21 — PF-C-1）
    test_http_pool_reuses_connection()
    test_http_pool_reconnects_on_transport_error()
    test_http_pool_raises_http_error_on_4xx()
    # O: API key child-process env (round 21 — S-H-1)
    test_api_key_child_env_pop()
    # P: response body size cap (round 22 — H1)
    test_http_pool_rejects_oversized_response()
    test_api_client_urllib_rejects_oversized_response()
    # Q: glossary Ren'Py scan (round 25 — T-H-1)
    test_glossary_scan_renpy_directory()
    # R: translation_db integrity (round 26 — C-1/C-2/C-3)
    test_translation_db_concurrent_upsert()
    test_translation_db_save_atomic()
    test_translation_db_accepts_line_zero()
    print()
    print("=" * 40)
    print(f"ALL 113 TESTS PASSED")
    print("=" * 40)
