"""
优化的 Ollama 翻译器

基于 MTool 架构思路的改进：
- 连接池化（复用 HTTP 连接）
- 立即质量验证（占位符、行数、长度比例）
- 智能重试（低质量自动重试）
- 统计跟踪（成功率、重试率）
"""

import time
from typing import Optional

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    requests = None
    _HAS_REQUESTS = False

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ..utils.logger import logger
from ..utils.placeholder import ph_multiset


class OllamaTranslator:
    """优化的 Ollama 翻译器"""

    def __init__(
        self,
        host: str,
        model: str,
        max_workers: int = 4,
        quality_threshold: float = 0.7,
        max_retries: int = 3,
        timeout: float = 120.0,
        temperature: float = 0.3
    ):
        """
        初始化翻译器

        Args:
            host: Ollama 服务地址
            model: 模型名称
            max_workers: 最大并发数（用于连接池）
            quality_threshold: 质量阈值（低于此值自动重试）
            max_retries: 最大重试次数
            timeout: HTTP 请求超时时间（秒）
            temperature: 采样温度
        """
        if not _HAS_REQUESTS:
            raise ImportError(
                "requests 库未安装，请运行: pip install requests"
            )

        self.host = host
        self.model = model
        self.quality_threshold = quality_threshold
        self.max_retries = max_retries
        self.timeout = timeout
        self.temperature = temperature

        # 连接池化（减少握手开销）
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers,
            pool_maxsize=max_workers,
            max_retries=0  # 手动处理重试
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'retries': 0,
            'failed': 0,
            'total_time': 0.0,
            'total_quality': 0.0
        }

    def translate_with_validation(
        self,
        text: str,
        context: Optional[dict] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None
    ) -> dict:
        """
        翻译并验证结果

        Args:
            text: 待翻译文本
            context: 上下文信息（type, speaker_name 等）
            system_prompt: 系统提示词
            temperature: 温度参数（None 则使用默认值）
            timeout: 超时时间（None 则使用默认值）

        Returns:
            {
                'success': 是否成功,
                'translation': 翻译文本,
                'text': 翻译文本（兼容旧接口）,
                'quality_score': 质量分数 (0-1),
                'issues': 问题列表,
                'retries': 重试次数,
                'time': 翻译耗时
            }
        """
        self.stats['total'] += 1
        start_time = time.time()

        # 使用实例默认值或传入参数
        actual_temp = temperature if temperature is not None else self.temperature
        actual_timeout = timeout if timeout is not None else self.timeout

        for attempt in range(self.max_retries):
            try:
                # 1. 调用 Ollama 翻译
                result = self._call_ollama(
                    text,
                    system_prompt=system_prompt,
                    temperature=actual_temp,
                    timeout=actual_timeout
                )

                # 2. 立即验证质量
                quality = self._validate_translation(text, result, context)

                # 3. 如果质量达标，返回结果
                if quality['score'] >= self.quality_threshold:
                    elapsed = time.time() - start_time
                    self.stats['success'] += 1
                    self.stats['total_time'] += elapsed
                    self.stats['total_quality'] += quality['score']

                    return {
                        'success': True,
                        'translation': result,
                        'text': result,  # 兼容旧接口
                        'quality_score': quality['score'],
                        'issues': quality['issues'],
                        'retries': attempt,
                        'time': elapsed
                    }

                # 4. 质量不达标，记录并重试
                self.stats['retries'] += 1
                logger.warning(
                    f"Translation quality low ({quality['score']:.2f}), "
                    f"retrying (attempt {attempt + 1}/{self.max_retries})... "
                    f"Issues: {quality['issues']}"
                )

                # 指数退避
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    # 最后一次尝试失败
                    self.stats['failed'] += 1
                    elapsed = time.time() - start_time
                    self.stats['total_time'] += elapsed

                    return {
                        'success': False,
                        'translation': None,
                        'text': None,
                        'quality_score': 0.0,
                        'issues': [str(e)],
                        'retries': attempt + 1,
                        'time': elapsed
                    }

                # 指数退避
                time.sleep(2 ** attempt)

        # 最大重试后仍失败
        elapsed = time.time() - start_time
        self.stats['failed'] += 1
        self.stats['total_time'] += elapsed

        return {
            'success': False,
            'translation': None,
            'text': None,
            'quality_score': 0.0,
            'issues': ['Max retries exceeded with low quality'],
            'retries': self.max_retries,
            'time': elapsed
        }

    def _call_ollama(
        self,
        text: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        timeout: float = 120.0
    ) -> str:
        """
        调用 Ollama API

        Args:
            text: 待翻译文本
            system_prompt: 系统提示词
            temperature: 温度参数
            timeout: 超时时间

        Returns:
            翻译结果
        """
        url = f"{self.host}/api/generate"

        # 构建提示词
        if system_prompt:
            prompt = f"{system_prompt}\n\n{text}"
        else:
            prompt = f"Translate the following English text to Chinese:\n\n{text}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 4096
            }
        }

        response = self.session.post(
            url,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        result = response.json()
        return result.get('response', '').strip()

    def _validate_translation(
        self,
        source: str,
        target: str,
        context: Optional[dict] = None
    ) -> dict:
        """
        翻译质量验证

        检查项：
        - 占位符数量匹配
        - 行数匹配
        - 长度比例合理
        - 未翻译检测

        Args:
            source: 原文
            target: 译文
            context: 上下文信息

        Returns:
            {
                'score': 质量分数 (0-1),
                'issues': 问题列表
            }
        """
        issues = []
        score = 1.0

        # 1. 检查占位符
        src_ph = ph_multiset(source)
        tgt_ph = ph_multiset(target)

        if src_ph != tgt_ph:
            # 计算差异
            missing = {k: src_ph.get(k, 0) - tgt_ph.get(k, 0)
                       for k in set(src_ph) | set(tgt_ph)
                       if src_ph.get(k, 0) > tgt_ph.get(k, 0)}
            extra = {k: tgt_ph.get(k, 0) - src_ph.get(k, 0)
                     for k in set(src_ph) | set(tgt_ph)
                     if tgt_ph.get(k, 0) > src_ph.get(k, 0)}
            msg = "Placeholder mismatch"
            if missing:
                msg += f" (missing: {missing})"
            if extra:
                msg += f" (extra: {extra})"
            issues.append(msg)
            score -= 0.3

        # 2. 检查行数
        src_lines = source.count('\n')
        tgt_lines = target.count('\n')

        if src_lines != tgt_lines:
            issues.append(f"Line count mismatch ({src_lines} vs {tgt_lines})")
            score -= 0.2

        # 3. 检查长度比例
        src_len = len(source)
        tgt_len = len(target)
        ratio = tgt_len / max(src_len, 1)

        if ratio < 0.3:
            issues.append(f"Translation too short (ratio: {ratio:.2f})")
            score -= 0.2
        elif ratio > 3.0:
            issues.append(f"Translation too long (ratio: {ratio:.2f})")
            score -= 0.1

        # 4. 检查未翻译（仅对对话类型）
        if context and context.get('type') == 'dialog':
            common_english = [
                ' the ', ' and ', ' you ', ' are ', ' have ',
                ' what ', ' where ', ' when ', ' who ', ' how '
            ]
            target_lower = f" {target.lower()} "
            untranslated = [word for word in common_english if word in target_lower]

            if untranslated:
                issues.append(f"Contains untranslated words: {untranslated}")
                score -= 0.3

        # 5. 检查空翻译
        if not target.strip():
            issues.append("Empty translation")
            score = 0.0

        return {
            'score': max(0.0, score),
            'issues': issues
        }

    def get_stats(self) -> dict:
        """
        获取翻译统计

        Returns:
            {
                'total': 总翻译数,
                'success': 成功数,
                'retries': 重试数,
                'failed': 失败数,
                'success_rate': 成功率,
                'avg_time': 平均耗时,
                'avg_quality': 平均质量分数
            }
        """
        total = self.stats['total']
        success = self.stats['success']
        avg_time = self.stats['total_time'] / max(total, 1)
        avg_quality = self.stats['total_quality'] / max(success, 1)

        return {
            **self.stats,
            'success_rate': success / max(total, 1),
            'avg_time': avg_time,
            'avg_quality': avg_quality
        }

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出（关闭连接）"""
        self.session.close()
