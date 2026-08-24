"""Internationalization (i18n) definitions for How to Fish Trainer."""

TRANSLATIONS = {
    "zh": {
        "header_title": "[*] 渔力全开 (How to Fish) - 内存修改器 / 辅助工具\n",
        "header_subtitle": "Unity Mono 引擎 | FishNet 多人联机支持 | JIT 补丁框架\n",
        "attached_info": "[bold green][已连接][/bold green] [white]目标进程:[/white] [cyan]{process_name}[/cyan] (PID: {pid}) | [white]Mono 域:[/white] [yellow]0x{mono_domain:X}[/yellow]",
        "waiting_info": "[bold yellow][等待中][/bold yellow] [white]正在搜索目标进程:[/white] [cyan]{process_name}[/cyan]...",
        "table_title": "[bold white]功能列表[/bold white]",
        "col_hotkey": "快捷键",
        "col_feature": "功能名称",
        "col_status": "状态",
        "col_description": "功能说明",
        "status_active": "[bold green]已开启[/bold green]",
        "status_disabled": "[dim red]已关闭[/dim red]",
        "status_ready": "[bold cyan]就绪 (按键触发)[/bold cyan]",
        "controls_title": "\n[操作说明] ",
        "controls_hotkey_tip": "按下对应快捷键切换功能 | ",
        "controls_lang_tip": "[F12] 切换中英文 (Language) | ",
        "controls_exit_tip": "按 [F10] 或 [Ctrl+C] 安全退出。\n",
        "status_label": "[当前状态] ",
        "starting": "正在启动...",
        "waiting_process": "等待目标进程 {process_name} 启动...",
        "found_process": "找到进程 {process_name}，正在初始化 Mono 桥接...",
        "attached_ready": "已成功连接游戏！就绪。请按 F1 / F2 / F3 / F4 / F5 / F6 开启功能。",
        "game_closed": "游戏已关闭，等待重新连接...",
        "shutting_down": "正在安全关闭修改器...",
        "stopped_clean": "修改器已安全退出，所有内存补丁与原始游戏逻辑均已恢复。",
        "lang_switched": "语言已切换为中文 (ZH)。",
    },
    "en": {
        "header_title": "[*] HOW TO FISH - EXTERNAL MEMORY TRAINER\n",
        "header_subtitle": "Unity Mono Engine | FishNet Multiplayer Support | JIT Patch Framework\n",
        "attached_info": "[bold green][ATTACHED][/bold green] [white]Process:[/white] [cyan]{process_name}[/cyan] (PID: {pid}) | [white]Mono Domain:[/white] [yellow]0x{mono_domain:X}[/yellow]",
        "waiting_info": "[bold yellow][WAITING][/bold yellow] [white]Searching for process:[/white] [cyan]{process_name}[/cyan]...",
        "table_title": "[bold white]AVAILABLE CHEATS[/bold white]",
        "col_hotkey": "Hotkey",
        "col_feature": "Feature",
        "col_status": "Status",
        "col_description": "Description",
        "status_active": "[bold green]ACTIVE[/bold green]",
        "status_disabled": "[dim red]DISABLED[/dim red]",
        "status_ready": "[bold cyan]READY[/bold cyan]",
        "controls_title": "\n[Controls] ",
        "controls_hotkey_tip": "Press designated hotkeys to toggle cheats | ",
        "controls_lang_tip": "[F12] Switch Language (中/EN) | ",
        "controls_exit_tip": "Press [F10] or [Ctrl+C] to exit safely.\n",
        "status_label": "[Status] ",
        "starting": "Starting...",
        "waiting_process": "Waiting for {process_name} to launch...",
        "found_process": "Found {process_name}. Initializing Mono bridge...",
        "attached_ready": "Successfully attached! Ready. Press F1 / F2 / F3 / F4 / F5 / F6.",
        "game_closed": "Game closed. Waiting to reconnect...",
        "shutting_down": "Shutting down trainer...",
        "stopped_clean": "Trainer stopped cleanly. All memory patches and original game logic restored.",
        "lang_switched": "Language switched to English (EN).",
    },
}


def tr(key: str, lang: str = "zh", **kwargs) -> str:
    """Translates a message key to the specified language with format arguments."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
