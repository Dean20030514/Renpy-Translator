"""Bilingual user interface utilities for Chinese-English output."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


class BilingualMessage:
    """Display messages in both Chinese and English."""
    
    @staticmethod
    def info(zh: str, en: str, title_zh: str = "信息", title_en: str = "Info") -> None:
        """Show info message."""
        text = Text()
        text.append(f"{zh}\n", style="cyan")
        text.append(en, style="dim cyan")
        console.print(Panel(text, title=f"{title_zh} / {title_en}", border_style="cyan"))
    
    @staticmethod
    def success(zh: str, en: str, title_zh: str = "成功", title_en: str = "Success") -> None:
        """Show success message."""
        text = Text()
        text.append(f"✅ {zh}\n", style="green")
        text.append(f"✅ {en}", style="dim green")
        console.print(Panel(text, title=f"{title_zh} / {title_en}", border_style="green"))
    
    @staticmethod
    def warning(zh: str, en: str, title_zh: str = "警告", title_en: str = "Warning") -> None:
        """Show warning message."""
        text = Text()
        text.append(f"⚠️  {zh}\n", style="yellow")
        text.append(f"⚠️  {en}", style="dim yellow")
        console.print(Panel(text, title=f"{title_zh} / {title_en}", border_style="yellow"))
    
    @staticmethod
    def error(zh: str, en: str, title_zh: str = "错误", title_en: str = "Error") -> None:
        """Show error message."""
        text = Text()
        text.append(f"❌ {zh}\n", style="red")
        text.append(f"❌ {en}", style="dim red")
        console.print(Panel(text, title=f"{title_zh} / {title_en}", border_style="red"))
    
    @staticmethod
    def progress(step: int, total: int, zh: str, en: str) -> None:
        """Show progress step."""
        console.print(f"[cyan]【{step}/{total}】[/cyan] {zh}")
        console.print(f"[dim cyan]   [{step}/{total}] {en}[/dim cyan]")


def confirm_operation(
    question_zh: str,
    question_en: str,
    default: bool = False
) -> bool:
    """
    Ask user for confirmation with bilingual prompt.
    
    Args:
        question_zh: Question in Chinese
        question_en: Question in English
        default: Default answer if user just presses Enter
    
    Returns:
        True if user confirms, False otherwise
    """
    default_hint = "Y/n" if default else "y/N"
    
    console.print()
    console.print(f"[yellow]{question_zh}[/yellow]")
    console.print(f"[dim yellow]{question_en}[/dim yellow]")
    
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
    """Display system environment information."""
    import platform
    import shutil
    
    console.print("\n[bold cyan]系统信息 / System Information[/bold cyan]")
    console.print("─" * 60)
    
    # OS info
    console.print(f"操作系统 / OS: {platform.system()} {platform.release()}")
    console.print(f"架构 / Arch: {platform.machine()}")
    
    # Python version
    console.print(f"Python: {platform.python_version()}")
    
    # Check GPU
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
                console.print(f"GPU: {gpu_info}")
            else:
                console.print("GPU: [dim]未检测到 / Not detected[/dim]")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            console.print("GPU: [dim]检测失败 / Detection failed[/dim]")
    else:
        console.print("GPU: [dim]未检测到 / Not detected[/dim]")
    
    console.print("─" * 60 + "\n")


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
