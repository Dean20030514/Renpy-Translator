"""
多级别质量检查器

基于 MTool 架构思路的改进：
- 分级检查（Critical / Warning / Info）
- 自动修复（占位符、换行符、重复标点）
- HTML 可视化报告
- 新增：标签配对检查、术语一致性、英文残留检测
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional
from collections import Counter

from ..utils.placeholder import ph_multiset
from ..utils.common import PH_RE

# 获取模块级 logger
logger = logging.getLogger(__name__)


class MultiLevelValidator:
    """多级别质量检查器"""
    
    # 检查规则配置（扩展版）
    DEFAULT_CHECKS = {
        'placeholder': {'level': 'critical', 'autofix': True},
        'newline': {'level': 'critical', 'autofix': True},
        'length_ratio': {'level': 'warning', 'autofix': False},
        'untranslated': {'level': 'warning', 'autofix': False},
        'duplicate_punct': {'level': 'info', 'autofix': True},
        'empty': {'level': 'critical', 'autofix': False},
        # 新增检查规则
        'tag_mismatch': {'level': 'critical', 'autofix': True},
        'english_leakage': {'level': 'warning', 'autofix': False},
        'number_mismatch': {'level': 'warning', 'autofix': False},
        'term_consistency': {'level': 'info', 'autofix': False},
    }
    
    # Ren'Py 标签正则
    _TAG_OPEN_RE = re.compile(r'\{(i|b|u|color|a|size|font|alpha)(?:=[^}]*)?\}')
    _TAG_CLOSE_RE = re.compile(r'\{/(i|b|u|color|a|size|font|alpha)\}')
    
    # 英文单词检测（排除常见缩写）
    _ENGLISH_WORD_RE = re.compile(r'\b[a-zA-Z]{3,}\b')
    _ALLOWED_ENGLISH = frozenset({
        'ok', 'pc', 'cpu', 'gpu', 'ui', 'api', 'app', 'id', 'ip', 'url',
        'dna', 'rna', 'vip', 'npc', 'rpg', 'fps', 'hp', 'mp', 'sp', 'exp',
        'xxx', 'www', 'http', 'https', 'wifi', 'gps', 'usb', 'pdf', 'jpg', 'png',
    })
    
    # 数字检测
    _NUMBER_RE = re.compile(r'\d+(?:\.\d+)?')
    
    def __init__(self, config: Optional[dict] = None):
        """
        初始化验证器
        
        Args:
            config: 检查规则配置（不提供则使用默认配置）
        """
        self.config = config or self.DEFAULT_CHECKS
        self.issues = {'critical': [], 'warning': [], 'info': []}
        self._term_dict: dict[str, str] = {}  # 术语字典
    
    def set_term_dict(self, term_dict: dict[str, str]) -> None:
        """设置术语字典用于一致性检查
        
        Args:
            term_dict: {英文术语: 中文翻译}
        """
        self._term_dict = {k.lower(): v for k, v in term_dict.items()}
    
    def reset(self):
        """重置问题列表"""
        self.issues = {'critical': [], 'warning': [], 'info': []}

    def validate_with_autofix(
        self,
        source: list[dict],
        target: list[dict]
    ) -> tuple[list[dict], dict]:
        """
        验证并自动修复

        Args:
            source: 原文列表 [{'id': ..., 'en': ...}, ...]
            target: 译文列表 [{'id': ..., 'zh': ...}, ...]

        Returns:
            (fixed_target, issues_report)
        """
        # 重置问题列表，避免累积
        self.reset()
        fixed = []

        # 创建 source 字典以便快速查找
        source_dict = {item['id']: item for item in source}
        
        for tgt in target:
            tgt_id = tgt['id']
            
            # 找到对应的原文
            if tgt_id not in source_dict:
                logger.warning(f"Target ID {tgt_id} not found in source")
                fixed.append(tgt)
                continue
            
            src = source_dict[tgt_id]
            fixes_applied = []
            
            # 1. 空翻译检查
            if self._should_check('empty'):
                issue = self._check_empty(src, tgt)
                if issue:
                    self._add_issue(issue)
            
            # 2. 占位符检查
            if self._should_check('placeholder'):
                issue = self._check_placeholder(src, tgt)
                if issue:
                    self._add_issue(issue)
                    if self._can_autofix('placeholder'):
                        tgt, fix = self._autofix_placeholder(src, tgt)
                        fixes_applied.append(fix)
            
            # 3. 换行符检查
            if self._should_check('newline'):
                issue = self._check_newline(src, tgt)
                if issue:
                    self._add_issue(issue)
                    if self._can_autofix('newline'):
                        tgt, fix = self._autofix_newline(src, tgt)
                        fixes_applied.append(fix)
            
            # 4. 长度比例检查
            if self._should_check('length_ratio'):
                issue = self._check_length_ratio(src, tgt)
                if issue:
                    self._add_issue(issue)
            
            # 5. 未翻译检查
            if self._should_check('untranslated'):
                issue = self._check_untranslated(tgt)
                if issue:
                    self._add_issue(issue)
            
            # 6. 重复标点检查
            if self._should_check('duplicate_punct'):
                issue = self._check_duplicate_punct(tgt)
                if issue:
                    self._add_issue(issue)
                    if self._can_autofix('duplicate_punct'):
                        tgt, fix = self._autofix_duplicate_punct(tgt)
                        fixes_applied.append(fix)
            
            # 7. 标签配对检查 (新增)
            if self._should_check('tag_mismatch'):
                issue = self._check_tag_mismatch(src, tgt)
                if issue:
                    self._add_issue(issue)
                    if self._can_autofix('tag_mismatch'):
                        tgt, fix = self._autofix_tag_mismatch(src, tgt)
                        fixes_applied.append(fix)
            
            # 8. 英文泄露检查 (新增)
            if self._should_check('english_leakage'):
                issue = self._check_english_leakage(tgt)
                if issue:
                    self._add_issue(issue)
            
            # 9. 数字一致性检查 (新增)
            if self._should_check('number_mismatch'):
                issue = self._check_number_mismatch(src, tgt)
                if issue:
                    self._add_issue(issue)
            
            # 10. 术语一致性检查 (新增)
            if self._should_check('term_consistency'):
                issue = self._check_term_consistency(tgt)
                if issue:
                    self._add_issue(issue)
            
            # 记录修复
            if fixes_applied:
                tgt['_autofix'] = fixes_applied
            
            fixed.append(tgt)
        
        return fixed, self.issues
    
    def _should_check(self, check_name: str) -> bool:
        """是否应该执行此检查"""
        return check_name in self.config and self.config[check_name].get('level')
    
    def _can_autofix(self, check_name: str) -> bool:
        """是否可以自动修复"""
        return self.config.get(check_name, {}).get('autofix', False)
    
    def _add_issue(self, issue: dict):
        """添加问题到对应级别"""
        level = issue.get('level', 'info')
        self.issues[level].append(issue)
    
    def _check_empty(self, src: dict, tgt: dict) -> Optional[dict]:
        """检查空翻译"""
        if not tgt.get('zh', '').strip():
            return {
                'level': 'critical',
                'id': tgt['id'],
                'type': 'empty',
                'message': 'Empty translation'
            }
        return None
    
    def _check_placeholder(self, src: dict, tgt: dict) -> Optional[dict]:
        """检查占位符"""
        src_ph = Counter(ph_multiset(src.get('en', '')))
        tgt_ph = Counter(ph_multiset(tgt.get('zh', '')))
        
        if src_ph != tgt_ph:
            missing = src_ph - tgt_ph
            extra = tgt_ph - src_ph
            
            msg = "Placeholder mismatch"
            if missing:
                msg += f" (missing: {dict(missing)})"
            if extra:
                msg += f" (extra: {dict(extra)})"
            
            return {
                'level': 'critical',
                'id': tgt['id'],
                'type': 'placeholder',
                'message': msg,
                'details': {'source': dict(src_ph), 'target': dict(tgt_ph)}
            }
        return None
    
    def _check_newline(self, src: dict, tgt: dict) -> Optional[dict]:
        """检查换行符"""
        src_lines = src.get('en', '').count('\n')
        tgt_lines = tgt.get('zh', '').count('\n')
        
        if src_lines != tgt_lines:
            return {
                'level': 'critical',
                'id': tgt['id'],
                'type': 'newline',
                'message': f"Line count mismatch ({src_lines} vs {tgt_lines})"
            }
        return None
    
    def _check_length_ratio(self, src: dict, tgt: dict) -> Optional[dict]:
        """检查长度比例"""
        src_len = len(src.get('en', ''))
        tgt_len = len(tgt.get('zh', ''))
        
        if src_len == 0:
            return None
        
        ratio = tgt_len / src_len
        
        if ratio < 0.3:
            return {
                'level': 'warning',
                'id': tgt['id'],
                'type': 'length_ratio',
                'message': f"Translation too short (ratio: {ratio:.2f})"
            }
        elif ratio > 3.0:
            return {
                'level': 'warning',
                'id': tgt['id'],
                'type': 'length_ratio',
                'message': f"Translation too long (ratio: {ratio:.2f})"
            }
        
        return None
    
    # 编译一次正则表达式，避免重复编译
    _COMMON_ENGLISH_PATTERN = re.compile(
        r'\b(the|and|you|are|have|what|where|when|who|how)\b',
        re.IGNORECASE
    )

    def _check_untranslated(self, tgt: dict) -> Optional[dict]:
        """检查未翻译（保留英文单词）"""
        text = tgt.get('zh', '')
        if not text:
            return None

        # 使用正则表达式匹配单词边界
        matches = self._COMMON_ENGLISH_PATTERN.findall(text)

        if matches:
            # 去重并保持顺序
            unique_words = list(dict.fromkeys(word.lower() for word in matches))
            return {
                'level': 'warning',
                'id': tgt['id'],
                'type': 'untranslated',
                'message': f"Contains untranslated words: {unique_words}"
            }

        return None
    
    def _check_duplicate_punct(self, tgt: dict) -> Optional[dict]:
        """检查重复标点"""
        text = tgt.get('zh', '')
        
        # 检查常见重复标点
        duplicates = []
        patterns = ['。。', '，，', '！！', '？？', '  ']  # 两个空格
        
        for pattern in patterns:
            if pattern in text:
                duplicates.append(pattern)
        
        if duplicates:
            return {
                'level': 'info',
                'id': tgt['id'],
                'type': 'duplicate_punct',
                'message': f"Duplicate punctuation: {duplicates}"
            }
        
        return None
    
    def _autofix_placeholder(self, src: dict, tgt: dict) -> tuple[dict, str]:
        """自动修复占位符"""
        src_ph = Counter(ph_multiset(src.get('en', '')))
        tgt_ph = Counter(ph_multiset(tgt.get('zh', '')))
        
        # 找到缺失的占位符
        missing = src_ph - tgt_ph
        
        # 在末尾添加缺失占位符
        zh_text = tgt.get('zh', '')
        for ph, count in missing.items():
            for _ in range(count):
                zh_text += f" {ph}"
        
        tgt['zh'] = zh_text
        return tgt, f"Added missing placeholders: {dict(missing)}"
    
    def _autofix_newline(self, src: dict, tgt: dict) -> tuple[dict, str]:
        """自动修复换行符"""
        src_lines = src.get('en', '').count('\n')
        tgt_lines = tgt.get('zh', '').count('\n')

        zh_text = tgt.get('zh', '')

        if src_lines > tgt_lines:
            # 需要添加换行符
            diff = src_lines - tgt_lines
            # 简单策略：在句号后添加换行
            parts = zh_text.split('。')
            num_parts = len(parts)

            if num_parts > 1 and diff > 0:
                # 计算间隔，确保均匀分布
                interval = max(1, (num_parts - 1) // (diff + 1))
                added = 0
                for i in range(interval, num_parts - 1, interval):
                    if added >= diff:
                        break
                    # 在部分末尾添加换行（重组时会在句号后）
                    parts[i] = parts[i] + '\n'
                    added += 1
                zh_text = '。'.join(parts)

        elif src_lines < tgt_lines:
            # 需要删除换行符
            diff = tgt_lines - src_lines
            for _ in range(diff):
                zh_text = zh_text.replace('\n', '', 1)

        tgt['zh'] = zh_text
        return tgt, f"Fixed newline count: {src_lines} vs {tgt_lines}"
    
    def _autofix_duplicate_punct(self, tgt: dict) -> tuple[dict, str]:
        """自动修复重复标点"""
        zh_text = tgt.get('zh', '')

        # 使用正则表达式一次性替换连续的重复标点
        # 比 while 循环更高效，O(n) vs O(n²)
        zh_text = re.sub(r'。{2,}', '。', zh_text)
        zh_text = re.sub(r'，{2,}', '，', zh_text)
        zh_text = re.sub(r'！{2,}', '！', zh_text)
        zh_text = re.sub(r'？{2,}', '？', zh_text)
        zh_text = re.sub(r' {2,}', ' ', zh_text)  # 多个空格

        tgt['zh'] = zh_text
        return tgt, "Removed duplicate punctuation"
    
    # ========== 新增检查方法 ==========
    
    def _check_tag_mismatch(self, src: dict, tgt: dict) -> Optional[dict]:
        """检查 Ren'Py 标签配对是否正确"""
        zh_text = tgt.get('zh', '')
        if not zh_text:
            return None
        
        # 提取开标签和闭标签
        open_tags = self._TAG_OPEN_RE.findall(zh_text)
        close_tags = self._TAG_CLOSE_RE.findall(zh_text)
        
        # 统计配对
        open_counter = Counter(open_tags)
        close_counter = Counter(close_tags)
        
        mismatches = []
        all_tags = set(open_counter.keys()) | set(close_counter.keys())
        
        for tag in all_tags:
            open_count = open_counter.get(tag, 0)
            close_count = close_counter.get(tag, 0)
            if open_count != close_count:
                mismatches.append(f"{tag}({open_count} open, {close_count} close)")
        
        if mismatches:
            return {
                'level': 'critical',
                'id': tgt['id'],
                'type': 'tag_mismatch',
                'message': f"Tag mismatch: {', '.join(mismatches)}"
            }
        
        return None
    
    def _check_english_leakage(self, tgt: dict) -> Optional[dict]:
        """检查英文泄露（大量未翻译的英文单词）"""
        zh_text = tgt.get('zh', '')
        if not zh_text:
            return None
        
        # 移除占位符后再检查
        clean_text = PH_RE.sub('', zh_text)
        
        # 提取所有英文单词
        words = self._ENGLISH_WORD_RE.findall(clean_text)
        
        # 过滤允许的单词
        suspicious = [w for w in words if w.lower() not in self._ALLOWED_ENGLISH]
        
        # 如果超过3个可疑英文单词，报警告
        if len(suspicious) > 3:
            return {
                'level': 'warning',
                'id': tgt['id'],
                'type': 'english_leakage',
                'message': f"Possible untranslated content: {suspicious[:5]}..."
            }
        
        return None
    
    def _check_number_mismatch(self, src: dict, tgt: dict) -> Optional[dict]:
        """检查数字是否保持一致"""
        en_text = src.get('en', '')
        zh_text = tgt.get('zh', '')
        
        if not en_text or not zh_text:
            return None
        
        # 提取数字
        en_numbers = set(self._NUMBER_RE.findall(en_text))
        zh_numbers = set(self._NUMBER_RE.findall(zh_text))
        
        # 检查是否一致
        missing = en_numbers - zh_numbers
        extra = zh_numbers - en_numbers
        
        if missing or extra:
            msg_parts = []
            if missing:
                msg_parts.append(f"missing: {missing}")
            if extra:
                msg_parts.append(f"extra: {extra}")
            return {
                'level': 'warning',
                'id': tgt['id'],
                'type': 'number_mismatch',
                'message': f"Number mismatch - {', '.join(msg_parts)}"
            }
        
        return None
    
    def _check_term_consistency(self, tgt: dict) -> Optional[dict]:
        """检查术语一致性"""
        if not self._term_dict:
            return None
        
        zh_text = tgt.get('zh', '')
        if not zh_text:
            return None
        
        inconsistent = []
        for en_term, expected_zh in self._term_dict.items():
            # 如果译文中应该有某个术语的翻译但用了不同的翻译
            # 这里简单检查：如果原文有术语，译文应该包含对应翻译
            en_text = tgt.get('en', '')
            if en_term.lower() in en_text.lower():
                if expected_zh not in zh_text:
                    inconsistent.append(f"'{en_term}' should be '{expected_zh}'")
        
        if inconsistent:
            return {
                'level': 'info',
                'id': tgt['id'],
                'type': 'term_inconsistent',
                'message': f"Term inconsistency: {', '.join(inconsistent[:3])}"
            }
        
        return None
    
    def _autofix_tag_mismatch(self, src: dict, tgt: dict) -> tuple[dict, str]:
        """自动修复标签不匹配"""
        en_text = src.get('en', '')
        zh_text = tgt.get('zh', '')
        
        # 从原文提取标签结构
        en_open = self._TAG_OPEN_RE.findall(en_text)
        en_close = self._TAG_CLOSE_RE.findall(en_text)
        
        # 从译文提取标签
        zh_open = self._TAG_OPEN_RE.findall(zh_text)
        zh_close = self._TAG_CLOSE_RE.findall(zh_text)
        
        fixed = False
        
        # 检查缺失的闭标签
        zh_open_counter = Counter(zh_open)
        zh_close_counter = Counter(zh_close)
        
        for tag, count in zh_open_counter.items():
            close_count = zh_close_counter.get(tag, 0)
            if count > close_count:
                # 缺少闭标签，在末尾添加
                for _ in range(count - close_count):
                    zh_text += f"{{/{tag}}}"
                    fixed = True
        
        tgt['zh'] = zh_text
        msg = "Added missing close tags" if fixed else "No fix needed"
        return tgt, msg
    
    # ========== 结束新增方法 ==========
    
    def generate_report(self, format: str = 'html', output_path: Optional[str] = None) -> str:
        """
        生成质量报告
        
        Args:
            format: 报告格式（'html', 'json', 'tsv'）
            output_path: 输出路径（如果提供，会写入文件）
        
        Returns:
            报告内容
        """
        if format == 'html':
            report = self._generate_html_report()
        elif format == 'json':
            report = json.dumps(self.issues, indent=2, ensure_ascii=False)
        elif format == 'tsv':
            report = self._generate_tsv_report()
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # 写入文件
        if output_path:
            Path(output_path).write_text(report, encoding='utf-8')
            logger.info(f"Report saved to {output_path}")
        
        return report
    
    def _generate_html_report(self) -> str:
        """生成 HTML 质量报告"""
        critical_count = len(self.issues['critical'])
        warning_count = len(self.issues['warning'])
        info_count = len(self.issues['info'])
        
        # 格式化问题行
        rows = []
        for level in ['critical', 'warning', 'info']:
            for issue in self.issues[level]:
                rows.append(
                    f"<tr>"
                    f"<td class='{level}'>{level.upper()}</td>"
                    f"<td>{issue.get('id', 'N/A')}</td>"
                    f"<td>{issue.get('type', 'N/A')}</td>"
                    f"<td>{issue.get('message', 'N/A')}</td>"
                    f"</tr>"
                )
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Translation Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .critical {{ color: #d32f2f; font-weight: bold; }}
        .warning {{ color: #f57c00; }}
        .info {{ color: #0288d1; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }}
        .stat-card h3 {{ margin-top: 0; }}
        .stat-card p {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>Translation Quality Report</h1>
    <div class="stats">
        <div class="stat-card">
            <h3 class="critical">Critical Issues</h3>
            <p>{critical_count}</p>
        </div>
        <div class="stat-card">
            <h3 class="warning">Warnings</h3>
            <p>{warning_count}</p>
        </div>
        <div class="stat-card">
            <h3 class="info">Info</h3>
            <p>{info_count}</p>
        </div>
    </div>
    <h2>Issues</h2>
    <table>
        <tr>
            <th>Level</th>
            <th>ID</th>
            <th>Type</th>
            <th>Message</th>
        </tr>
        {''.join(rows)}
    </table>
</body>
</html>"""
        return html
    
    def _generate_tsv_report(self) -> str:
        """生成 TSV 质量报告"""
        lines = ['Level\tID\tType\tMessage']
        
        for level in ['critical', 'warning', 'info']:
            for issue in self.issues[level]:
                lines.append(
                    f"{level}\t"
                    f"{issue.get('id', 'N/A')}\t"
                    f"{issue.get('type', 'N/A')}\t"
                    f"{issue.get('message', 'N/A')}"
                )
        
        return '\n'.join(lines)
    
    def get_summary(self) -> dict:
        """
        获取问题摘要
        
        Returns:
            {'critical': 数量, 'warning': 数量, 'info': 数量, 'total': 总数}
        """
        return {
            'critical': len(self.issues['critical']),
            'warning': len(self.issues['warning']),
            'info': len(self.issues['info']),
            'total': sum(len(v) for v in self.issues.values())
        }
