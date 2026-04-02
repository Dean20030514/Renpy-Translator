#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多引擎游戏汉化工具 — Tkinter 图形界面启动器。

用法: python gui.py

通过 subprocess 调用现有 CLI（main.py / one_click_pipeline.py / renpy_upgrade_tool.py），
不修改任何现有代码。纯 tkinter + ttk 标准库，零第三方依赖。
"""

from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

# DPI 适配（Windows）
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent

# 提供商默认模型
_PROVIDER_DEFAULTS = {
    "xai": "grok-4-1-fast-reasoning",
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
    "claude": "claude-sonnet-4",
    "gemini": "gemini-2.5-flash",
}

_PROVIDERS = list(_PROVIDER_DEFAULTS.keys())
_ENGINES = ["auto", "renpy", "rpgmaker", "csv", "jsonl"]
_GENRES = ["adult", "visual_novel", "rpg", "general"]

# 进度日志匹配模式，例如 [3/50] (6%) 或 [3/50]
_RE_PROGRESS = re.compile(r'\[(\d+)/(\d+)\](?:\s*\((\d+)%\))?')

# 日志裁剪阈值
MAX_LOG_LINES = 5000
TRIM_TO = 3000


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("多引擎游戏汉化工具")
        self.root.geometry("920x720")
        self.root.minsize(750, 550)

        self.process: subprocess.Popen | None = None
        self._log_queue: queue.Queue = queue.Queue()
        self._start_time: float = 0.0

        self._build_menu()
        self._build_notebook()
        self._build_bottom()
        self._poll_log()

        # 初始化引擎面板
        self._on_engine_change()

    # ============================================================
    # 菜单栏
    # ============================================================

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        tool_menu = tk.Menu(menubar, tearoff=0, font=("", 10))
        tool_menu.add_command(label="  仅扫描估费（Dry-run，无需 API Key）  ", command=self._run_dry_run)
        tool_menu.add_separator()
        tool_menu.add_command(label="  Ren'Py 7→8 升级扫描（检测旧 API 问题）  ", command=self._run_upgrade_scan)
        menubar.add_cascade(label=" \u2630 工具 ", menu=tool_menu)
        self.root.config(menu=menubar)

    # ============================================================
    # Notebook（3 个 Tab）
    # ============================================================

    def _build_notebook(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=False, padx=8, pady=(8, 0))

        self._build_tab_basic()
        self._build_tab_translate()
        self._build_tab_advanced()

    # ── Tab 1: 基本设置 ──

    def _build_tab_basic(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="基本设置")
        row = 0

        # 游戏目录
        ttk.Label(tab, text="游戏目录:").grid(row=row, column=0, sticky="e", pady=3)
        self.var_game_dir = tk.StringVar()
        ttk.Entry(tab, textvariable=self.var_game_dir, width=55).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(tab, text="浏览", command=lambda: self._browse_dir(self.var_game_dir)).grid(row=row, column=2, padx=4)
        row += 1

        # 输出目录
        ttk.Label(tab, text="输出目录:").grid(row=row, column=0, sticky="e", pady=3)
        self.var_output_dir = tk.StringVar(value="output")
        ttk.Entry(tab, textvariable=self.var_output_dir, width=55).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(tab, text="浏览", command=lambda: self._browse_dir(self.var_output_dir)).grid(row=row, column=2, padx=4)
        row += 1

        # 引擎
        ttk.Label(tab, text="引擎:").grid(row=row, column=0, sticky="e", pady=3)
        self.var_engine = tk.StringVar(value="auto")
        cb = ttk.Combobox(tab, textvariable=self.var_engine, values=_ENGINES, state="readonly", width=15)
        cb.grid(row=row, column=1, sticky="w", pady=3)
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_engine_change())
        row += 1

        # 提供商
        ttk.Label(tab, text="API 提供商:").grid(row=row, column=0, sticky="e", pady=3)
        self.var_provider = tk.StringVar(value="xai")
        cb_prov = ttk.Combobox(tab, textvariable=self.var_provider, values=_PROVIDERS, state="readonly", width=15)
        cb_prov.grid(row=row, column=1, sticky="w", pady=3)
        cb_prov.bind("<<ComboboxSelected>>", lambda e: self._on_provider_change())
        row += 1

        # API 密钥
        ttk.Label(tab, text="API 密钥:").grid(row=row, column=0, sticky="e", pady=3)
        self.var_api_key = tk.StringVar()
        ttk.Entry(tab, textvariable=self.var_api_key, show="*", width=55).grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        # 模型
        ttk.Label(tab, text="模型:").grid(row=row, column=0, sticky="e", pady=3)
        self.var_model = tk.StringVar(value=_PROVIDER_DEFAULTS["xai"])
        ttk.Entry(tab, textvariable=self.var_model, width=35).grid(row=row, column=1, sticky="w", pady=3)
        row += 1

        # 并发 / RPM / RPS
        frame_perf = ttk.Frame(tab)
        frame_perf.grid(row=row, column=0, columnspan=3, sticky="w", pady=3)
        ttk.Label(frame_perf, text="并发线程:").pack(side=tk.LEFT)
        self.var_workers = tk.StringVar(value="3")
        ttk.Spinbox(frame_perf, from_=1, to=20, textvariable=self.var_workers, width=4).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(frame_perf, text="RPM:").pack(side=tk.LEFT)
        self.var_rpm = tk.StringVar(value="600")
        ttk.Spinbox(frame_perf, from_=1, to=9999, textvariable=self.var_rpm, width=6).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(frame_perf, text="RPS:").pack(side=tk.LEFT)
        self.var_rps = tk.StringVar(value="10")
        ttk.Spinbox(frame_perf, from_=1, to=999, textvariable=self.var_rps, width=4).pack(side=tk.LEFT)

        tab.columnconfigure(1, weight=1)

    # ── Tab 2: 翻译设置（根据引擎动态切换）──

    def _build_tab_translate(self) -> None:
        self.tab_translate = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_translate, text="翻译设置")

        # 引擎状态标签
        self.lbl_engine_hint = ttk.Label(self.tab_translate, text="当前引擎: auto", font=("", 10, "bold"))
        self.lbl_engine_hint.pack(anchor="w")

        # 动态面板容器
        self.panel_container = ttk.Frame(self.tab_translate)
        self.panel_container.pack(fill=tk.BOTH, expand=True, pady=5)

        # 预建各引擎面板（hidden by default）
        self._build_renpy_panel()
        self._build_rpgmaker_panel()
        self._build_csv_panel()

    def _build_renpy_panel(self) -> None:
        self.panel_renpy = ttk.Frame(self.panel_container)

        # 翻译模式
        ttk.Label(self.panel_renpy, text="翻译模式:").grid(row=0, column=0, sticky="w", pady=3)
        self.var_renpy_mode = tk.StringVar(value="direct")
        modes = [("direct-mode（整文件翻译）", "direct"), ("tl-mode（tl 框架翻译）", "tl"),
                 ("retranslate（补翻残留英文）", "retranslate"), ("一键流水线（试跑+闸门+全量+补翻）", "pipeline")]
        for i, (text, val) in enumerate(modes):
            ttk.Radiobutton(self.panel_renpy, text=text, variable=self.var_renpy_mode,
                            value=val, command=self._on_renpy_mode_change).grid(row=1 + i, column=0, columnspan=2, sticky="w")

        row = 5
        # tl 语言
        ttk.Label(self.panel_renpy, text="tl 语言目录:").grid(row=row, column=0, sticky="e", pady=3)
        self.var_tl_lang = tk.StringVar(value="chinese")
        self.entry_tl_lang = ttk.Entry(self.panel_renpy, textvariable=self.var_tl_lang, width=20)
        self.entry_tl_lang.grid(row=row, column=1, sticky="w", pady=3)
        row += 1

        # 断点续传
        self.var_resume = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.panel_renpy, text="断点续传（--resume）", variable=self.var_resume).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3)
        row += 1

        # 风格
        ttk.Label(self.panel_renpy, text="翻译风格:").grid(row=row, column=0, sticky="e", pady=3)
        self.var_genre = tk.StringVar(value="adult")
        ttk.Combobox(self.panel_renpy, textvariable=self.var_genre, values=_GENRES,
                      state="readonly", width=15).grid(row=row, column=1, sticky="w", pady=3)
        row += 1

        # 流水线参数
        self.frame_pipeline = ttk.LabelFrame(self.panel_renpy, text="流水线参数", padding=5)
        self.frame_pipeline.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(self.frame_pipeline, text="试跑文件数:").grid(row=0, column=0, sticky="e")
        self.var_pilot_count = tk.StringVar(value="20")
        ttk.Spinbox(self.frame_pipeline, from_=1, to=100, textvariable=self.var_pilot_count, width=5).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(self.frame_pipeline, text="闸门最大漏翻比:").grid(row=0, column=2, sticky="e", padx=(10, 0))
        self.var_gate_ratio = tk.StringVar(value="0.08")
        ttk.Entry(self.frame_pipeline, textvariable=self.var_gate_ratio, width=8).grid(row=0, column=3, sticky="w", padx=5)

    def _build_rpgmaker_panel(self) -> None:
        self.panel_rpgmaker = ttk.Frame(self.panel_container)
        ttk.Label(self.panel_rpgmaker, text="RPG Maker MV/MZ 引擎").pack(anchor="w", pady=3)
        ttk.Label(self.panel_rpgmaker, text="使用基本设置中的共享参数。\n翻译完成后会提示手动安装中文字体。",
                  foreground="gray").pack(anchor="w", pady=3)
        self.var_rpgm_genre = tk.StringVar(value="rpg")
        f = ttk.Frame(self.panel_rpgmaker)
        f.pack(anchor="w", pady=3)
        ttk.Label(f, text="翻译风格:").pack(side=tk.LEFT)
        ttk.Combobox(f, textvariable=self.var_rpgm_genre, values=_GENRES,
                      state="readonly", width=15).pack(side=tk.LEFT, padx=5)

    def _build_csv_panel(self) -> None:
        self.panel_csv = ttk.Frame(self.panel_container)
        ttk.Label(self.panel_csv, text="CSV/JSONL 通用格式引擎").pack(anchor="w", pady=3)
        ttk.Label(self.panel_csv, text="支持 CSV、TSV、JSONL、JSON 数组。\n列名自动匹配（original/source/text/en 等）。",
                  foreground="gray").pack(anchor="w", pady=3)

    def _on_engine_change(self) -> None:
        engine = self.var_engine.get()
        self.lbl_engine_hint.config(text=f"当前引擎: {engine}")
        # 隐藏所有面板
        for p in (self.panel_renpy, self.panel_rpgmaker, self.panel_csv):
            p.pack_forget()
        # 显示对应面板
        if engine in ("auto", "renpy"):
            self.panel_renpy.pack(fill=tk.BOTH, expand=True)
            self._on_renpy_mode_change()
        elif engine == "rpgmaker":
            self.panel_rpgmaker.pack(fill=tk.BOTH, expand=True)
        elif engine in ("csv", "jsonl"):
            self.panel_csv.pack(fill=tk.BOTH, expand=True)
        self._update_preview()

    def _on_renpy_mode_change(self) -> None:
        mode = self.var_renpy_mode.get()
        is_tl = mode in ("tl", "pipeline")
        self.entry_tl_lang.config(state="normal" if is_tl else "disabled")
        if mode == "pipeline":
            self.frame_pipeline.grid()
        else:
            self.frame_pipeline.grid_remove()
        self._update_preview()

    def _on_provider_change(self) -> None:
        provider = self.var_provider.get()
        default_model = _PROVIDER_DEFAULTS.get(provider, "")
        self.var_model.set(default_model)
        self._update_preview()

    # ── Tab 3: 高级设置 ──

    def _build_tab_advanced(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="高级设置")

        fields = [
            ("timeout (秒):", "var_timeout", "180"),
            ("temperature:", "var_temperature", "0.1"),
            ("max-chunk-tokens:", "var_max_chunk", "4000"),
            ("max-response-tokens:", "var_max_response", "32768"),
            ("最小对话密度:", "var_min_density", "0.20"),
            ("排除模式 (glob):", "var_exclude", ""),
            ("外部词典 (分号分隔):", "var_dict", ""),
            ("日志文件路径:", "var_log_file", ""),
        ]
        for i, (label, attr, default) in enumerate(fields):
            ttk.Label(tab, text=label).grid(row=i, column=0, sticky="e", pady=2)
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            ttk.Entry(tab, textvariable=var, width=45).grid(row=i, column=1, sticky="ew", pady=2)

        row = len(fields)
        # 字体补丁
        self.var_patch_font = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="启用自动字体补丁（--patch-font）", variable=self.var_patch_font).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=2)
        row += 1
        self.var_no_clean_rpyc = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="不清理 .rpyc 缓存（--no-clean-rpyc）", variable=self.var_no_clean_rpyc).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=2)
        row += 1
        self.var_tl_screen = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="翻译 screen 裸英文（--tl-screen）", variable=self.var_tl_screen).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=2)
        row += 1

        # verbose / quiet
        ttk.Label(tab, text="日志级别:").grid(row=row, column=0, sticky="e", pady=2)
        self.var_log_level = tk.StringVar(value="normal")
        f = ttk.Frame(tab)
        f.grid(row=row, column=1, sticky="w", pady=2)
        for text, val in [("普通", "normal"), ("详细 (--verbose)", "verbose"), ("安静 (--quiet)", "quiet")]:
            ttk.Radiobutton(f, text=text, variable=self.var_log_level, value=val).pack(side=tk.LEFT, padx=5)
        row += 1

        # 配置文件
        sep = ttk.Separator(tab, orient="horizontal")
        sep.grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1
        ttk.Label(tab, text="配置文件:").grid(row=row, column=0, sticky="e", pady=2)
        self.var_config_path = tk.StringVar()
        ttk.Entry(tab, textvariable=self.var_config_path, width=35).grid(row=row, column=1, sticky="ew", pady=2)
        f2 = ttk.Frame(tab)
        f2.grid(row=row, column=2, padx=4)
        ttk.Button(f2, text="加载", command=self._load_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(f2, text="保存", command=self._save_config).pack(side=tk.LEFT, padx=2)

        tab.columnconfigure(1, weight=1)

    # ============================================================
    # 底部区域
    # ============================================================

    def _build_bottom(self) -> None:
        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill=tk.BOTH, expand=True)

        # 命令预览
        prev_frame = ttk.Frame(bottom)
        prev_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(prev_frame, text="命令预览:").pack(side=tk.LEFT)
        self.var_preview = tk.StringVar()
        self.entry_preview = ttk.Entry(prev_frame, textvariable=self.var_preview, state="readonly")
        self.entry_preview.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 按钮栏
        btn_frame = ttk.Frame(bottom)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        self.btn_start = ttk.Button(btn_frame, text="开始翻译", command=self._start)
        self.btn_start.pack(side=tk.LEFT, padx=3)
        self.btn_stop = ttk.Button(btn_frame, text="停止", command=self._stop, state="disabled")
        self.btn_stop.pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="清空日志", command=self._clear_log).pack(side=tk.LEFT, padx=3)
        self.lbl_status = ttk.Label(btn_frame, text="状态: 空闲", foreground="gray")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # 进度条
        self.progress_frame = ttk.Frame(bottom)
        self.progress_frame.pack(fill=tk.X, padx=8, pady=2)

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 8))

        self.lbl_progress = ttk.Label(self.progress_frame, text="")
        self.lbl_progress.pack(side=tk.RIGHT)

        # 日志
        self.log_text = scrolledtext.ScrolledText(bottom, height=12, state="disabled",
                                                   wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ============================================================
    # 命令构建
    # ============================================================

    def _build_command(self, dry_run: bool = False) -> list[str]:
        py = sys.executable
        engine = self.var_engine.get()
        game_dir = self.var_game_dir.get().strip()
        output_dir = self.var_output_dir.get().strip() or "output"
        provider = self.var_provider.get()
        api_key = self.var_api_key.get().strip()
        model = self.var_model.get().strip()
        workers = self.var_workers.get().strip() or "3"
        rpm = self.var_rpm.get().strip() or "600"
        rps = self.var_rps.get().strip() or "10"

        # Ren'Py 一键流水线模式
        if engine in ("auto", "renpy") and self.var_renpy_mode.get() == "pipeline":
            genre = self.var_genre.get()
            cmd = [
                py, "-u", "one_click_pipeline.py",
                "--game-dir", game_dir, "--output-dir", output_dir,
                "--provider", provider, "--api-key", api_key,
                "--model", model, "--genre", genre,
                "--workers", workers, "--rpm", rpm, "--rps", rps,
                "--clean-output",
                "--pilot-count", self.var_pilot_count.get().strip() or "20",
                "--gate-max-untranslated-ratio", self.var_gate_ratio.get().strip() or "0.08",
            ]
            if self.var_renpy_mode.get() == "pipeline" and self.var_tl_lang.get().strip():
                # 检查是否用 tl-mode 流水线（暂不提供，流水线默认 direct-mode）
                pass
            return cmd

        # Ren'Py 7→8 升级扫描
        # （通过菜单触发，不在这里）

        # 通用命令
        cmd = [py, "-u", "main.py", "--game-dir", game_dir, "--output-dir", output_dir,
               "--provider", provider, "--model", model,
               "--workers", workers, "--rpm", rpm, "--rps", rps]

        if not dry_run and api_key:
            cmd += ["--api-key", api_key]
        if dry_run:
            cmd.append("--dry-run")

        # 引擎
        if engine not in ("auto", "renpy"):
            cmd += ["--engine", engine]

        # Ren'Py 特有参数
        if engine in ("auto", "renpy"):
            mode = self.var_renpy_mode.get()
            genre = self.var_genre.get()
            cmd += ["--genre", genre]
            if mode == "tl":
                cmd += ["--tl-mode", "--tl-lang", self.var_tl_lang.get().strip() or "chinese"]
            elif mode == "retranslate":
                cmd.append("--retranslate")
            if self.var_resume.get():
                cmd.append("--resume")
        elif engine == "rpgmaker":
            cmd += ["--genre", self.var_rpgm_genre.get()]

        # 高级参数
        timeout = self.var_timeout.get().strip()
        if timeout and timeout != "180":
            cmd += ["--timeout", timeout]
        temp = self.var_temperature.get().strip()
        if temp and temp != "0.1":
            cmd += ["--temperature", temp]
        chunk = self.var_max_chunk.get().strip()
        if chunk and chunk != "4000":
            cmd += ["--max-chunk-tokens", chunk]
        resp = self.var_max_response.get().strip()
        if resp and resp != "32768":
            cmd += ["--max-response-tokens", resp]
        density = self.var_min_density.get().strip()
        if density and density != "0.20":
            cmd += ["--min-dialogue-density", density]
        exclude = self.var_exclude.get().strip()
        if exclude:
            cmd += ["--exclude"] + [x.strip() for x in exclude.split(";") if x.strip()]
        dict_paths = self.var_dict.get().strip()
        if dict_paths:
            cmd += ["--dict"] + [x.strip() for x in dict_paths.split(";") if x.strip()]
        log_file = self.var_log_file.get().strip()
        if log_file:
            cmd += ["--log-file", log_file]
        if self.var_patch_font.get():
            cmd.append("--patch-font")
        if self.var_no_clean_rpyc.get():
            cmd.append("--no-clean-rpyc")
        if self.var_tl_screen.get():
            cmd.append("--tl-screen")
        if self.var_log_level.get() == "verbose":
            cmd.append("--verbose")
        elif self.var_log_level.get() == "quiet":
            cmd.append("--quiet")

        return cmd

    def _mask_api_key(self, cmd: list[str]) -> str:
        """命令预览中隐藏 API key。"""
        display = []
        skip = False
        for arg in cmd:
            if skip:
                display.append("****")
                skip = False
            elif arg == "--api-key":
                display.append(arg)
                skip = True
            else:
                display.append(arg)
        return " ".join(display)

    def _update_preview(self, *_args) -> None:
        try:
            cmd = self._build_command()
            self.var_preview.set(self._mask_api_key(cmd))
        except (ValueError, TypeError, AttributeError):
            self.var_preview.set("")

    # ============================================================
    # 执行与日志
    # ============================================================

    def _start(self) -> None:
        game_dir = self.var_game_dir.get().strip()
        if not game_dir:
            messagebox.showwarning("缺少参数", "请填写游戏目录路径")
            return
        api_key = self.var_api_key.get().strip()
        if not api_key:
            messagebox.showwarning("缺少参数", "请填写 API 密钥")
            return

        cmd = self._build_command()
        self._run_command(cmd)

    def _run_command(self, cmd: list[str]) -> None:
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="状态: 运行中...", foreground="blue")
        self._start_time = time.time()
        self._append_log(f">>> {self._mask_api_key(cmd)}\n\n")

        def worker():
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, cwd=str(PROJECT_ROOT),
                )
                self.process = proc
                for line in proc.stdout:
                    self._log_queue.put(line)
                proc.wait()
                self._log_queue.put(("__RC__", proc.returncode))
            except Exception as e:
                self._log_queue.put(f"\n[ERROR] {e}\n")
                self._log_queue.put(("__RC__", -1))

        threading.Thread(target=worker, daemon=True).start()

    def _parse_progress(self, text: str) -> None:
        """从日志行中解析进度信息并更新进度条。"""
        m = _RE_PROGRESS.search(text)
        if m:
            current, total = int(m.group(1)), int(m.group(2))
            if m.group(3):
                pct = int(m.group(3))
            else:
                pct = int(current / total * 100) if total > 0 else 0
            self.progress_bar['value'] = pct
            self.lbl_progress.config(text=f"{current}/{total} ({pct}%)")

    def _append_log(self, text: str) -> None:
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text)
        # 日志裁剪：超过阈值时删除早期行
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > MAX_LOG_LINES:
            trim_end = line_count - TRIM_TO
            self.log_text.delete("1.0", f"{trim_end}.0")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _on_finished(self, returncode: int) -> None:
        elapsed = time.time() - self._start_time
        self.process = None
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        if returncode == 0:
            self.lbl_status.config(text=f"状态: 完成 ({elapsed:.1f}s)", foreground="green")
            self._append_log(f"\n[完成] 耗时 {elapsed:.1f} 秒\n")
            self.progress_bar['value'] = 100
            self.lbl_progress.config(text="完成")
        else:
            self.lbl_status.config(text=f"状态: 错误 (code={returncode})", foreground="red")
            self._append_log(f"\n[错误] 退出码 {returncode}，耗时 {elapsed:.1f} 秒\n")

    def _stop(self) -> None:
        if self.process:
            try:
                # Windows: 发送 CTRL_C_EVENT 让子进程的 KeyboardInterrupt 触发进度保存
                import signal
                if hasattr(signal, 'CTRL_C_EVENT'):
                    self.process.send_signal(signal.CTRL_C_EVENT)
                else:
                    self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except OSError:
                pass
            self.lbl_status.config(text="状态: 已停止", foreground="orange")
            self._append_log("\n[已停止] 进程被终止（已尝试保存进度）\n")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.lbl_progress.config(text="已停止")

    def _clear_log(self) -> None:
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    # ============================================================
    # 工具菜单
    # ============================================================

    def _run_dry_run(self) -> None:
        game_dir = self.var_game_dir.get().strip()
        if not game_dir:
            messagebox.showwarning("缺少参数", "请先在「基本设置」中填写游戏目录")
            return
        cmd = self._build_command(dry_run=True)
        self._dry_run_cmd = cmd
        self._dry_run_output = []

        # 使用特殊日志收集
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="状态: 扫描中...", foreground="blue")
        self._start_time = time.time()
        self._append_log(f">>> {self._mask_api_key(cmd)}\n\n")

        def worker():
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, cwd=str(PROJECT_ROOT),
                )
                self.process = proc
                lines = []
                for line in proc.stdout:
                    self._log_queue.put(line)
                    lines.append(line)
                proc.wait()
                self._log_queue.put(("__DRYRUN__", lines, proc.returncode))
            except Exception as e:
                self._log_queue.put(f"\n[ERROR] {e}\n")
                self._log_queue.put(("__RC__", -1))

        threading.Thread(target=worker, daemon=True).start()

    def _run_upgrade_scan(self) -> None:
        """工具菜单入口：弹出目录选择对话框后执行升级扫描。"""
        scan_dir = filedialog.askdirectory(title="选择游戏 game 目录")
        if not scan_dir:
            return
        self._run_upgrade_scan_on_game_dir(scan_dir)

    def _run_upgrade_scan_on_game_dir(self, scan_dir: str) -> None:
        """执行 Ren'Py 7→8 升级扫描（工具菜单和翻译模式共用）。"""
        do_fix = messagebox.askyesno("自动修复", "是否自动修复发现的问题？\n（会创建 .bak 备份）")

        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="状态: 升级扫描中...", foreground="blue")
        self._start_time = time.time()

        def worker():
            try:
                import io
                import contextlib
                from renpy_upgrade_tool import run_scan
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    results, file_count = run_scan(
                        scan_dir, fix=do_fix, backup=True,
                    )
                output = buf.getvalue()
                for line in output.splitlines(keepends=True):
                    self._log_queue.put(line)
                self._log_queue.put(("__RC__", 0))
            except Exception as e:
                self._log_queue.put(f"\n[ERROR] {e}\n")
                self._log_queue.put(("__RC__", 1))

        threading.Thread(target=worker, daemon=True).start()

    # ============================================================
    # 配置加载 / 保存
    # ============================================================

    def _load_config(self) -> None:
        path = self.var_config_path.get().strip()
        if not path:
            path = filedialog.askopenfilename(
                title="选择配置文件", filetypes=[("JSON", "*.json"), ("所有文件", "*.*")])
            if not path:
                return
            self.var_config_path.set(path)
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            mapping = {
                "provider": self.var_provider, "model": self.var_model,
                "genre": self.var_genre, "rpm": self.var_rpm, "rps": self.var_rps,
                "workers": self.var_workers, "timeout": self.var_timeout,
                "temperature": self.var_temperature, "max_chunk_tokens": self.var_max_chunk,
                "max_response_tokens": self.var_max_response, "target_lang": None,
                "tl_lang": self.var_tl_lang, "min_dialogue_density": self.var_min_density,
                "output_dir": self.var_output_dir,
            }
            for key, var in mapping.items():
                if var and key in data and data[key]:
                    var.set(str(data[key]))
            messagebox.showinfo("加载成功", f"已加载配置: {Path(path).name}")
        except Exception as e:
            messagebox.showerror("加载失败", str(e))

    def _save_config(self) -> None:
        path = self.var_config_path.get().strip()
        if not path:
            path = filedialog.asksaveasfilename(
                title="保存配置", defaultextension=".json",
                filetypes=[("JSON", "*.json")])
            if not path:
                return
            self.var_config_path.set(path)
        data = {
            "provider": self.var_provider.get(),
            "model": self.var_model.get(),
            "genre": self.var_genre.get(),
            "rpm": int(self.var_rpm.get() or 600),
            "rps": int(self.var_rps.get() or 10),
            "workers": int(self.var_workers.get() or 3),
            "timeout": float(self.var_timeout.get() or 180),
            "temperature": float(self.var_temperature.get() or 0.1),
            "max_chunk_tokens": int(self.var_max_chunk.get() or 4000),
            "max_response_tokens": int(self.var_max_response.get() or 32768),
            "tl_lang": self.var_tl_lang.get(),
            "min_dialogue_density": float(self.var_min_density.get() or 0.20),
            "output_dir": self.var_output_dir.get(),
        }
        try:
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("保存成功", f"配置已保存: {Path(path).name}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    # ============================================================
    # 辅助
    # ============================================================

    def _browse_dir(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            var.set(path)
            self._update_preview()

    def run(self) -> None:
        self.root.mainloop()
    def _poll_log(self) -> None:
        got_data = False
        for _ in range(50):
            try:
                item = self._log_queue.get_nowait()
                got_data = True
                if isinstance(item, tuple):
                    if item[0] == "__RC__":
                        self._on_finished(item[1])
                        continue
                    elif item[0] == "__DRYRUN__":
                        lines, rc = item[1], item[2]
                        self._on_finished(rc)
                        if rc == 0:
                            summary = []
                            for line in lines:
                                if any(k in line for k in ("剩余文件", "估计费用", "API 调用", "估计输入")):
                                    summary.append(line.strip())
                            if summary:
                                messagebox.showinfo("Dry-run 摘要", "\n".join(summary))
                        continue
                if isinstance(item, str):
                    self._parse_progress(item)
                self._append_log(item)
            except queue.Empty:
                break
        interval = 50 if got_data else 200
        self._poll_id = self.root.after(interval, self._poll_log)


def main() -> None:
    app = App()
    app.root.mainloop()


if __name__ == "__main__":
    main()
