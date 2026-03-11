"""双语用户界面工具 - 中英文双语输出，支持 Rich 降级。"""

from __future__ import annotations

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# 创建 Console 实例（或回退到纯文本输出）
if RICH_AVAILABLE:
    console = Console()
else:
    console = None  # type: ignore[assignment]


def _print_plain(*args: object) -> None:
    """Rich 不可用时的纯文本输出"""
    print(*args)


class BilingualMessage:
    """中英双语消息显示，Rich 不可用时自动回退为纯文本。"""
    
    @staticmethod
    def info(zh: str, en: str, title_zh: str = "信息", title_en: str = "Info") -> None:
        """显示信息消息。"""
        if RICH_AVAILABLE:
            text = Text()
            text.append(f"{zh}\n", style="cyan")
            text.append(en, style="dim cyan")
            console.print(Panel(text, title=f"{title_zh} / {title_en}", border_style="cyan"))
        else:
            _print_plain(f"[{title_zh}/{title_en}] {zh}")
            _print_plain(f"  {en}")
    
    @staticmethod
    def success(zh: str, en: str, title_zh: str = "成功", title_en: str = "Success") -> None:
        """显示成功消息。"""
        if RICH_AVAILABLE:
            text = Text()
            text.append(f"✅ {zh}\n", style="green")
            text.append(f"✅ {en}", style="dim green")
            console.print(Panel(text, title=f"{title_zh} / {title_en}", border_style="green"))
        else:
            _print_plain(f"[OK] {zh}")
            _print_plain(f"     {en}")
    
    @staticmethod
    def warning(zh: str, en: str, title_zh: str = "警告", title_en: str = "Warning") -> None:
        """显示警告消息。"""
        if RICH_AVAILABLE:
            text = Text()
            text.append(f"⚠️  {zh}\n", style="yellow")
            text.append(f"⚠️  {en}", style="dim yellow")
            console.print(Panel(text, title=f"{title_zh} / {title_en}", border_style="yellow"))
        else:
            _print_plain(f"[WARN] {zh}")
            _print_plain(f"       {en}")
    
    @staticmethod
    def error(zh: str, en: str, title_zh: str = "错误", title_en: str = "Error") -> None:
        """显示错误消息。"""
        if RICH_AVAILABLE:
            text = Text()
            text.append(f"❌ {zh}\n", style="red")
            text.append(f"❌ {en}", style="dim red")
            console.print(Panel(text, title=f"{title_zh} / {title_en}", border_style="red"))
        else:
            _print_plain(f"[ERROR] {zh}")
            _print_plain(f"        {en}")
    
    @staticmethod
    def progress(step: int, total: int, zh: str, en: str) -> None:
        """显示进度步骤。"""
        if RICH_AVAILABLE:
            console.print(f"[cyan]【{step}/{total}】[/cyan] {zh}")
            console.print(f"[dim cyan]   [{step}/{total}] {en}[/dim cyan]")
        else:
            _print_plain(f"[{step}/{total}] {zh}")
            _print_plain(f"  [{step}/{total}] {en}")


def confirm_operation(
    question_zh: str,
    question_en: str,
    default: bool = False
) -> bool:
    """
    双语确认提示。

    Args:
        question_zh: 中文问题
        question_en: 英文问题
        default: 用户直接回车时的默认值

    Returns:
        用户是否确认
    """
    default_hint = "Y/n" if default else "y/N"

    if RICH_AVAILABLE:
        console.print()
        console.print(f"[yellow]{question_zh}[/yellow]")
        console.print(f"[dim yellow]{question_en}[/dim yellow]")
    else:
        print()
        print(question_zh)
        print(question_en)

    response = input(f"[{default_hint}]: ").strip().lower()

    if not response:
        return default

    return response in ('y', 'yes', '是', 'shi', 's')


def check_prerequisites() -> tuple[bool, list[str]]:
    """
    Check if all required tools are installed.
    
    Returns:
        (all_ok, missing_tools) tuple
    """
    import shutil
    
    required_tools = {
        'python': 'Python',
        'pip': 'pip',
        'ollama': 'Ollama'
    }
    
    missing_tools = []
    
    for cmd, name in required_tools.items():
        if not shutil.which(cmd):
            missing_tools.append(name)
    
    return (len(missing_tools) == 0, missing_tools)


def show_system_info() -> None:
    """显示系统环境信息。"""
    import platform
    import shutil

    _out = console.print if RICH_AVAILABLE else _print_plain

    if RICH_AVAILABLE:
        _out("\n[bold cyan]系统信息 / System Information[/bold cyan]")
    else:
        _out("\n系统信息 / System Information")
    _out("─" * 60)

    _out(f"操作系统 / OS: {platform.system()} {platform.release()}")
    _out(f"架构 / Arch: {platform.machine()}")
    _out(f"Python: {platform.python_version()}")

    if shutil.which('nvidia-smi'):
        import subprocess
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            if result.returncode == 0:
                gpu_info = result.stdout.strip()
                _out(f"GPU: {gpu_info}")
            else:
                _out("GPU: 未检测到 / Not detected")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            _out("GPU: 检测失败 / Detection failed")
    else:
        _out("GPU: 未检测到 / Not detected")

    _out("─" * 60 + "\n")


if __name__ == "__main__":
    # Test examples
    show_system_info()
    
    BilingualMessage.info(
        "这是测试信息",
        "This is test information"
    )
    
    BilingualMessage.success(
        "操作成功完成",
        "Operation completed successfully"
    )
    
    BilingualMessage.warning(
        "这是警告信息",
        "This is warning message"
    )
    
    BilingualMessage.error(
        "发生错误",
        "Error occurred"
    )
    
    BilingualMessage.progress(
        3, 5,
        "正在提取文本...",
        "Extracting texts..."
    )
    
    if confirm_operation(
        "是否继续操作？",
        "Continue operation?",
        default=True
    ):
        console.print("[green]用户确认继续 / User confirmed[/green]")
    else:
        console.print("[yellow]用户取消操作 / User cancelled[/yellow]")
    
    ok, missing = check_prerequisites()
    if not ok:
        BilingualMessage.error(
            f"缺少必要工具：{', '.join(missing)}",
            f"Missing required tools: {', '.join(missing)}"
        )
