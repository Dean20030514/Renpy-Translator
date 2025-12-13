"""
多级别质量检查器

基于 MTool 架构思路的改进：
- 分级检查（Critical / Warning / Info）
- 自动修复（占位符、换行符、重复标点）
- HTML 可视化报告
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional
from collections import Counter

from ..utils.placeholder import ph_multiset

# 获取模块级 logger
logger = logging.getLogger(__name__)


class MultiLevelValidator:
    """多级别质量检查器"""
    
    # 检查规则配置
    DEFAULT_CHECKS = {
        'placeholder': {'level': 'critical', 'autofix': True},
        'newline': {'level': 'critical', 'autofix': True},
        'length_ratio': {'level': 'warning', 'autofix': False},
        'untranslated': {'level': 'warning', 'autofix': False},
        'duplicate_punct': {'level': 'info', 'autofix': True},
        'empty': {'level': 'critical', 'autofix': False},
    }
    
    def __init__(self, config: Optional[dict] = None):
        """
        初始化验证器
        
        Args:
            config: 检查规则配置（不提供则使用默认配置）
        """
        self.config = config or self.DEFAULT_CHECKS
        self.issues = {'critical': [], 'warning': [], 'info': []}
    
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
