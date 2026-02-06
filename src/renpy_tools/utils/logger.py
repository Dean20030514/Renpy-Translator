"""
Unified logging system for Ren'Py translation tools.

Provides:
- Structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- File and console output
- Rich formatting support
- Performance timing utilities
- Progress tracking integration
- Custom exception hierarchy
"""

from __future__ import annotations

import logging
import sys
import time
import functools
from pathlib import Path
from typing import Optional, Any, Callable, TypeVar
from contextlib import contextmanager

try:
    from rich.logging import RichHandler
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
    _HAS_RICH = True
    _console = Console()
except ImportError:
    _HAS_RICH = False
    _console = None

# 类型变量用于装饰器
F = TypeVar('F', bound=Callable[..., Any])


# ========================================
# 自定义异常层次结构
# ========================================

class RenpyToolsError(Exception):
    """Ren'Py 翻译工具基础异常"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class FileOperationError(RenpyToolsError):
    """文件操作错误（读取、写入、编码等）"""
    
    def __init__(self, message: str, file_path: Optional[Path] = None, **kwargs):
        details = {"file_path": str(file_path) if file_path else None, **kwargs}
        super().__init__(message, details)
        self.file_path = file_path


class ValidationError(RenpyToolsError):
    """验证错误（占位符、格式等）"""
    
    def __init__(self, message: str, item_id: Optional[str] = None, **kwargs):
        details = {"item_id": item_id, **kwargs}
        super().__init__(message, details)
        self.item_id = item_id


class TranslationError(RenpyToolsError):
    """翻译错误（API 调用、质量问题等）"""
    
    def __init__(self, message: str, source_text: Optional[str] = None, **kwargs):
        details = {"source_text": source_text[:100] if source_text else None, **kwargs}
        super().__init__(message, details)
        self.source_text = source_text


class ConfigurationError(RenpyToolsError):
    """配置错误（缺少必要参数、无效值等）"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = {"config_key": config_key, **kwargs}
        super().__init__(message, details)
        self.config_key = config_key


class APIError(RenpyToolsError):
    """API 调用错误（超时、限流、认证等）"""
    
    def __init__(
        self, 
        message: str, 
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        details = {"provider": provider, "status_code": status_code, **kwargs}
        super().__init__(message, details)
        self.provider = provider
        self.status_code = status_code


# ========================================
# 日志类
# ========================================


class TranslationLogger:
    """Logger wrapper with convenience methods."""
    
    def __init__(
        self,
        name: str = "renpy_tools",
        level: int = logging.INFO,
        log_file: Optional[Path] = None,
        use_rich: bool = True
    ):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for log output
            use_rich: Use rich formatting if available
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Clear existing handlers
        
        # Console handler
        if use_rich and _HAS_RICH:
            console_handler = RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_time=True,
                show_path=False
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
        
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)  # Log everything to file
            self.logger.addHandler(file_handler)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(msg, *args, **kwargs)
    
    @contextmanager
    def timer(self, operation: str, level: int = logging.INFO):
        """
        Context manager for timing operations.
        
        Usage:
            with logger.timer("Processing files"):
                # do work
                pass
        """
        start = time.time()
        self.logger.log(level, f"Starting: {operation}")
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.logger.log(level, f"Completed: {operation} (took {elapsed:.2f}s)")
    
    @contextmanager
    def progress(
        self,
        total: int,
        description: str = "Processing",
        disable: bool = False
    ):
        """
        Context manager for progress tracking with Rich.
        
        Usage:
            with logger.progress(100, "Translating") as update:
                for i in range(100):
                    update(1)  # increment by 1
        """
        if _HAS_RICH and not disable:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=_console,
            ) as progress:
                task = progress.add_task(description, total=total)
                
                def update(advance: int = 1):
                    progress.update(task, advance=advance)
                
                yield update
        else:
            # Fallback: simple counter
            count = [0]
            
            def update(advance: int = 1):
                count[0] += advance
                if count[0] % max(1, total // 10) == 0:
                    self.info(f"{description}: {count[0]}/{total}")
            
            yield update


def log_exceptions(
    logger_instance: Optional[TranslationLogger] = None,
    reraise: bool = True,
    default_return: Any = None
) -> Callable[[F], F]:
    """
    装饰器：自动记录函数异常
    
    Usage:
        @log_exceptions()
        def risky_function():
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger_instance or get_logger()
            try:
                return func(*args, **kwargs)
            except RenpyToolsError as e:
                log.error(f"{func.__name__} failed: {e}")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                log.exception(f"{func.__name__} unexpected error: {e}")
                if reraise:
                    raise
                return default_return
        return wrapper  # type: ignore
    return decorator


# Global logger instance
_default_logger: Optional[TranslationLogger] = None


def get_logger(
    name: str = "renpy_tools",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    use_rich: bool = True
) -> TranslationLogger:
    """
    Get or create global logger instance.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        use_rich: Use rich formatting
        
    Returns:
        TranslationLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = TranslationLogger(
            name=name,
            level=level,
            log_file=log_file,
            use_rich=use_rich
        )
    return _default_logger


def setup_logger(
    name: str = "renpy_tools",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    use_rich: bool = True
) -> TranslationLogger:
    """
    Setup and configure global logger.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        use_rich: Use rich formatting
        
    Returns:
        Configured TranslationLogger instance
    """
    global _default_logger
    _default_logger = TranslationLogger(
        name=name,
        level=level,
        log_file=log_file,
        use_rich=use_rich
    )
    return _default_logger


# 创建默认的模块级 logger 实例
logger = get_logger()


if __name__ == "__main__":
    # Test logger
    logger = get_logger(level=logging.DEBUG)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    with logger.timer("Test operation"):
        time.sleep(1)
    
    # Test file logging
    log_file = Path("test.log")
    file_logger = setup_logger(log_file=log_file)
    file_logger.info("This message goes to both console and file")
    
    if log_file.exists():
        print(f"\nLog file contents:\n{log_file.read_text()}")
        log_file.unlink()
