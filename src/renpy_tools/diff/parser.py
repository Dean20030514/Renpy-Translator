from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

ENCODINGS = ["utf-8-sig", "utf-8", "cp1252", "latin1"]

EN_MARKERS = ["英", "_en", "-en", ".en", "_ENG", "_English", "English", "_EN", "-EN"]
CN_MARKERS = ["_zh", "-zh", ".zh", "_cn", "-cn", ".cn", "中文", "中", "_ZH", "_CN", "-ZH", "-CN"]

LABEL_RE   = re.compile(r'^\s*label\s+([A-Za-z_]\w*)\s*:\s*$')
SCREEN_RE  = re.compile(r'^\s*screen\s+([A-Za-z_]\w*)\s*(?:\([^\)]*\))?\s*:\s*$')
MENU_RE    = re.compile(r'^\s*menu\s*:\s*$')
CHOICE_RE  = re.compile(r'^\s*"(.+?)"\s*:\s*$')
JUMP_RE    = re.compile(r'^\s*jump\s+([A-Za-z_]\w*)\s*$')
CALL_SCR_RE= re.compile(r'^\s*call\s+screen\s+([A-Za-z_]\w*)\s*$')
CALL_LBL_RE= re.compile(r'^\s*call\s+([A-Za-z_]\w*)\s*$')
SCENE_RE   = re.compile(r'^\s*scene\s+')
SHOW_RE    = re.compile(r'^\s*show\s+')
HIDE_RE    = re.compile(r'^\s*hide\s+')
DEFAULT_RE = re.compile(r'^\s*default\s+')
IMAGEBUTTON_JUMP_RE = re.compile(r"action\s+Jump\(\s*'([^']+)'\s*\)")

SPEAKER_LINE_RE = re.compile(r'^\s*([A-Za-z_]\w*)\s+"(.+?)"\s*$')
NARRATION_LINE_RE = re.compile(r'^\s*"(.+?)"\s*$')
TEXT_WIDGET_RE = re.compile(r'^\s*text\s+"(.+?)"')
COMMENT_LINE_RE = re.compile(r'^\s*#')

@dataclass
class Dialogue:
    kind: str
    speaker: Optional[str]
    text: str
    line_no: int

@dataclass
class Block:
    name: str
    type: str  # 'label' | 'screen'
    start_line: int
    dialogues: List['Dialogue'] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=lambda: {
        "jump":0, "call":0, "call_screen":0, "scene":0, "show":0, "hide":0, "menu":0, "imagebutton_jumps":0
    })
    imagebutton_jumps: List[Tuple[str,int]] = field(default_factory=list)
    menus: List['MenuBlock'] = field(default_factory=list)

@dataclass
class MenuChoice:
    text: str
    target_type: Optional[str]  # 'jump' | 'call' | 'call_screen' | None
    target_name: Optional[str]
    line_no: int

@dataclass
class MenuBlock:
    line_no: int
    choices: List['MenuChoice'] = field(default_factory=list)

@dataclass
class ParsedFile:
    path: str
    raw_lines: int
    norm_lines: int
    labels: Dict[str, 'Block']
    screens: Dict[str, 'Block']
    global_counts: Dict[str, int]


def read_text(path: str) -> List[str]:
    for enc in ENCODINGS:
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                return f.read().splitlines()
        except (UnicodeDecodeError, OSError):
            # 尝试下一种编码
            continue
    # 最后一次显式使用 utf-8 忽略错误，保证有编码且不触发 lint 警告
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def normalize_key(name: str, is_en: bool) -> str:
    base = name
    markers = EN_MARKERS if is_en else CN_MARKERS
    changed = True
    while changed:
        changed = False
        for m in markers:
            if base.endswith(m):
                base = base[: -len(m)]
                changed = True
    return base


def parse_rpy(path: str) -> ParsedFile:
    lines = read_text(path)
    raw = len(lines)

    norm_lines = 0
    for ln in lines:
        if ln.strip() == "":
            continue
        if COMMENT_LINE_RE.match(ln):
            continue
        norm_lines += 1

    labels: Dict[str, Block] = {}
    screens: Dict[str, Block] = {}
    cur_block: Optional[Block] = None

    def end_block():
        nonlocal cur_block
        cur_block = None

    def indent_level(s: str) -> int:
        # count leading spaces/tabs uniformly
        i = 0
        for ch in s:
            if ch in (' ', '\t'):
                i += 1
            else:
                break
        return i

    def parse_menu(lines: List[str], start_idx: int) -> MenuBlock:
        # start_idx is 1-based line index where 'menu:' appears
        mline = lines[start_idx-1]
        mindent = indent_level(mline)
        mb = MenuBlock(line_no=start_idx)
        j = start_idx + 1
        n = len(lines)
        while j <= n:
            l = lines[j-1]
            if not l.strip() or COMMENT_LINE_RE.match(l):
                j += 1
                continue
            ind = indent_level(l)
            if ind <= mindent:
                break  # menu block ends
            cm = CHOICE_RE.match(l)
            if cm and ind > mindent:
                choice_text = cm.group(1)
                choice_indent = ind
                target_type = None
                target_name = None
                k = j + 1
                while k <= n:
                    ll = lines[k-1]
                    if not ll.strip() or COMMENT_LINE_RE.match(ll):
                        k += 1
                        continue
                    ind2 = indent_level(ll)
                    if ind2 <= choice_indent:
                        break  # end of this choice block
                    # look for first actionable target
                    jm = JUMP_RE.match(ll)
                    if jm:
                        target_type, target_name = 'jump', jm.group(1)
                        break
                    cl = CALL_LBL_RE.match(ll)
                    if cl:
                        target_type, target_name = 'call', cl.group(1)
                        break
                    cs = CALL_SCR_RE.match(ll)
                    if cs:
                        target_type, target_name = 'call_screen', cs.group(1)
                        break
                    k += 1
                mb.choices.append(MenuChoice(text=choice_text, target_type=target_type, target_name=target_name, line_no=j))
            j += 1
        return mb

    for idx, ln in enumerate(lines, start=1):
        m = LABEL_RE.match(ln)
        if m:
            end_block()
            name = m.group(1)
            labels[name] = Block(name=name, type="label", start_line=idx)
            cur_block = labels[name]
            continue

        m = SCREEN_RE.match(ln)
        if m:
            end_block()
            name = m.group(1)
            screens[name] = Block(name=name, type="screen", start_line=idx)
            cur_block = screens[name]
            continue

        if MENU_RE.match(ln):
            if cur_block:
                cur_block.counts["menu"] += 1
                # try to parse choices with targets for this menu block
                try:
                    mb = parse_menu(lines, idx)
                    if mb.choices:
                        cur_block.menus.append(mb)
                except (ValueError, IndexError, RuntimeError):
                    # best-effort parsing; ignore failures
                    pass
            continue

        if JUMP_RE.match(ln):
            if cur_block:
                cur_block.counts["jump"] += 1
            continue

        m = CALL_SCR_RE.match(ln)
        if m:
            if cur_block:
                cur_block.counts["call_screen"] += 1
            continue

        m = CALL_LBL_RE.match(ln)
        if m:
            if cur_block:
                cur_block.counts["call"] += 1
            continue

        if SCENE_RE.match(ln):
            if cur_block:
                cur_block.counts["scene"] += 1
            continue

        if SHOW_RE.match(ln):
            if cur_block:
                cur_block.counts["show"] += 1
            continue

        if HIDE_RE.match(ln):
            if cur_block:
                cur_block.counts["hide"] += 1
            continue

        for jm in IMAGEBUTTON_JUMP_RE.finditer(ln):
            if cur_block:
                cur_block.counts["imagebutton_jumps"] += 1
                cur_block.imagebutton_jumps.append((jm.group(1), idx))

        # 在 screen 块中优先识别 text 小部件，避免被误判为角色说话
        if cur_block and cur_block.type == "screen":
            dm = TEXT_WIDGET_RE.match(ln)
            if dm:
                cur_block.dialogues.append(Dialogue(kind="text", speaker=None, text=dm.group(1), line_no=idx))
                continue

        dm = SPEAKER_LINE_RE.match(ln)
        if dm and cur_block:
            cur_block.dialogues.append(Dialogue(kind="speaker", speaker=dm.group(1), text=dm.group(2), line_no=idx))
            continue

        dm = NARRATION_LINE_RE.match(ln)
        if dm and cur_block:
            cur_block.dialogues.append(Dialogue(kind="narration", speaker=None, text=dm.group(1), line_no=idx))
            continue

        # 非 screen 场景下也尝试匹配 text（有些 label 里也会用 screen-like DSL）
        dm = TEXT_WIDGET_RE.match(ln)
        if dm and cur_block:
            cur_block.dialogues.append(Dialogue(kind="text", speaker=None, text=dm.group(1), line_no=idx))
            continue

    global_counts = {
        "labels": len(labels),
        "screens": len(screens),
        "dialogs": sum(len(b.dialogues) for b in labels.values()) + sum(len(b.dialogues) for b in screens.values()),
        "jumps": sum(b.counts["jump"] for b in list(labels.values()) + list(screens.values())),
        "calls": sum(b.counts["call"] for b in list(labels.values()) + list(screens.values())),
        "call_screens": sum(b.counts["call_screen"] for b in list(labels.values()) + list(screens.values())),
        "scenes": sum(b.counts["scene"] for b in list(labels.values()) + list(screens.values())),
        "shows": sum(b.counts["show"] for b in list(labels.values()) + list(screens.values())),
        "hides": sum(b.counts["hide"] for b in list(labels.values()) + list(screens.values())),
        "imagebutton_jumps": sum(b.counts["imagebutton_jumps"] for b in list(labels.values()) + list(screens.values())),
    }

    return ParsedFile(
        path=path,
        raw_lines=raw,
        norm_lines=norm_lines,
        labels=labels,
        screens=screens,
        global_counts=global_counts,
    )


def align_by_speaker(en_dialogs: List[Dialogue], cn_dialogs: List[Dialogue]):
    from difflib import SequenceMatcher
    en_seq = [ (d.kind, d.speaker or "_") for d in en_dialogs ]
    cn_seq = [ (d.kind, d.speaker or "_") for d in cn_dialogs ]
    sm = SequenceMatcher(None, en_seq, cn_seq, autojunk=False)
    mapping = []
    en_ptr = 0
    cn_ptr = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for _ in range(i2 - i1):
                mapping.append( (en_ptr, cn_ptr) )
                en_ptr += 1
                cn_ptr += 1
        elif tag == "replace":
            span = min(i2 - i1, j2 - j1)
            for _ in range(span):
                mapping.append( (en_ptr, cn_ptr) )
                en_ptr += 1
                cn_ptr += 1
            while en_ptr < i2:
                mapping.append( (en_ptr, None) )
                en_ptr += 1
            cn_ptr = j2
        elif tag == "delete":
            while en_ptr < i2:
                mapping.append( (en_ptr, None) )
                en_ptr += 1
        elif tag == "insert":
            cn_ptr = j2
    while en_ptr < len(en_seq):
        mapping.append( (en_ptr, None) )
        en_ptr += 1
    return mapping
