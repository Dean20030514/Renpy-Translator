"""
安全的文件回填器

基于 MTool 架构思路的改进：
- 自动备份（失败可回滚）
- 语法验证（避免生成错误文件）
- 增量处理（只更新变更文件）
"""

import shutil
import time
from pathlib import Path
from typing import Optional, Callable
import sys

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.renpy_tools.utils.logger import logger


class SafePatcher:
    """安全的文件回填器"""
    
    def __init__(self, backup_dir: Path, verify: bool = True):
        """
        初始化回填器
        
        Args:
            backup_dir: 备份目录
            verify: 是否验证语法
        """
        self.backup_dir = backup_dir
        self.verify = verify
        self.patched_files = []
    
    def patch_with_rollback(
        self,
        target_dir: Path,
        trans_data: dict,
        patch_fn: Optional[Callable] = None
    ) -> dict:
        """
        安全回填（支持回滚）
        
        Args:
            target_dir: 目标目录
            trans_data: 翻译数据 {相对路径: 翻译内容}
            patch_fn: 自定义回填函数 (原文本, 翻译数据) -> 新文本
        
        Returns:
            {
                'success': 成功文件列表,
                'failed': 失败文件列表,
                'rollback': 回滚函数
            }
        """
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        success = []
        failed = []
        
        for rel_path, trans in trans_data.items():
            target_file = target_dir / rel_path
            
            if not target_file.exists():
                logger.warning(f"Target file not found: {target_file}")
                failed.append({'file': str(rel_path), 'error': 'File not found'})
                continue
            
            try:
                # 1. 备份
                backup_file = self.backup_dir / rel_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target_file, backup_file)
                
                # 2. 读取原文
                original = target_file.read_text(encoding='utf-8')
                
                # 3. 回填
                if patch_fn:
                    patched = patch_fn(original, trans)
                else:
                    patched = self._default_patch(original, trans)
                
                # 4. 验证（可选）
                if self.verify:
                    self._verify_syntax(patched, target_file.suffix)
                
                # 5. 写入
                target_file.write_text(patched, encoding='utf-8')
                
                success.append(str(rel_path))
                self.patched_files.append((target_file, backup_file))
                logger.info(f"Patched: {rel_path}")
                
            except Exception as e:
                logger.error(f"Failed to patch {rel_path}: {e}")
                failed.append({'file': str(rel_path), 'error': str(e)})
        
        return {
            'success': success,
            'failed': failed,
            'rollback': self._create_rollback_fn()
        }
    
    def _default_patch(self, original: str, trans: dict) -> str:
        """
        默认回填策略（简单替换）
        
        Args:
            original: 原文本
            trans: 翻译数据 {id: 翻译文本}
        
        Returns:
            回填后的文本
        """
        # 这是一个占位实现，实际应该根据文件格式解析
        # 这里假设 trans 是 {行号: 翻译} 的格式
        lines = original.splitlines()
        
        for line_id, translation in trans.items():
            if isinstance(line_id, int) and 0 <= line_id < len(lines):
                lines[line_id] = translation
        
        return '\n'.join(lines)
    
    def _verify_syntax(self, text: str, ext: str):
        """
        验证文件语法
        
        Args:
            text: 文件内容
            ext: 文件扩展名
        
        Raises:
            SyntaxError: 语法错误
        """
        if ext == '.rpy':
            self._verify_renpy_syntax(text)
        elif ext == '.py':
            self._verify_python_syntax(text)
    
    def _verify_renpy_syntax(self, text: str):
        """验证 Ren'Py 语法"""
        lines = text.splitlines()
        
        for i, line in enumerate(lines, 1):
            # 检查缩进（4 的倍数）
            indent = len(line) - len(line.lstrip())
            if indent % 4 != 0:
                raise SyntaxError(
                    f"Line {i}: Invalid indentation ({indent} spaces)"
                )
            
            # 检查引号匹配
            if line.count('"') % 2 != 0 and line.count("'") % 2 != 0:
                raise SyntaxError(f"Line {i}: Unmatched quotes")
    
    def _verify_python_syntax(self, text: str):
        """验证 Python 语法"""
        try:
            compile(text, '<string>', 'exec')
        except SyntaxError as e:
            raise SyntaxError(f"Python syntax error: {e}")
    
    def _create_rollback_fn(self):
        """创建回滚函数"""
        patched = list(self.patched_files)
        
        def rollback():
            """回滚所有已回填的文件"""
            rollback_count = 0
            for target, backup in patched:
                try:
                    shutil.copy2(backup, target)
                    rollback_count += 1
                    logger.info(f"Rolled back: {target}")
                except Exception as e:
                    logger.error(f"Failed to rollback {target}: {e}")
            
            logger.info(f"Rolled back {rollback_count}/{len(patched)} files")
        
        return rollback


class IncrementalBuilder:
    """增量构建器"""
    
    def __init__(self, cache_file: Path = None):
        """
        初始化构建器
        
        Args:
            cache_file: 缓存文件路径（存储文件修改时间）
        """
        self.cache_file = cache_file or Path('.build_cache.json')
        self.cache = self._load_cache()
    
    def build_incremental(
        self,
        source_dir: Path,
        output_dir: Path,
        build_fn: Callable[[Path, Path], None],
        changed_files: Optional[set] = None
    ) -> dict:
        """
        增量构建（只处理变更文件）
        
        Args:
            source_dir: 源目录
            output_dir: 输出目录
            build_fn: 构建函数 (源文件, 输出文件) -> None
            changed_files: 变更文件集合（如果为 None，自动检测）
        
        Returns:
            {
                'rebuilt': 重新构建的文件列表,
                'skipped': 跳过的文件列表,
                'time_saved': 节省的时间（估算）
            }
        """
        if changed_files is None:
            changed_files = self._detect_changes(source_dir)
        
        rebuilt = []
        skipped = []
        start = time.time()
        
        for file in source_dir.rglob('*.rpy'):
            rel_path = file.relative_to(source_dir)
            output_file = output_dir / rel_path
            
            if rel_path in changed_files:
                # 重新构建
                output_file.parent.mkdir(parents=True, exist_ok=True)
                build_fn(file, output_file)
                rebuilt.append(str(rel_path))
                
                # 更新缓存
                self.cache[str(rel_path)] = file.stat().st_mtime
                logger.info(f"Built: {rel_path}")
            else:
                # 跳过
                skipped.append(str(rel_path))
        
        self._save_cache()
        
        elapsed = time.time() - start
        total_files = len(rebuilt) + len(skipped)
        
        # 估算完整构建时间
        if rebuilt:
            estimated_full_time = elapsed * total_files / len(rebuilt)
            time_saved = estimated_full_time - elapsed
        else:
            time_saved = 0
        
        logger.info(
            f"Incremental build complete: "
            f"{len(rebuilt)} rebuilt, {len(skipped)} skipped, "
            f"saved ~{time_saved:.1f}s"
        )
        
        return {
            'rebuilt': rebuilt,
            'skipped': skipped,
            'time_saved': time_saved
        }
    
    def _detect_changes(self, source_dir: Path) -> set:
        """检测变更文件"""
        changed = set()
        
        for file in source_dir.rglob('*.rpy'):
            rel_path = str(file.relative_to(source_dir))
            mtime = file.stat().st_mtime
            
            if rel_path not in self.cache or self.cache[rel_path] != mtime:
                changed.add(Path(rel_path))
        
        return changed
    
    def _load_cache(self) -> dict:
        """加载缓存"""
        if self.cache_file.exists():
            import json
            return json.loads(self.cache_file.read_text(encoding='utf-8'))
        return {}
    
    def _save_cache(self):
        """保存缓存"""
        import json
        self.cache_file.write_text(
            json.dumps(self.cache, indent=2),
            encoding='utf-8'
        )
