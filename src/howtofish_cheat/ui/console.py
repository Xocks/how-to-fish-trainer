"""Rich-based console UI dashboard for How to Fish Trainer."""

from typing import List, Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from ..features.base import CheatFeature
from ..i18n import tr


class TrainerUI:
    """Renders the live terminal dashboard for the trainer."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def generate_dashboard(
        self,
        is_attached: bool,
        process_name: str,
        pid: int,
        mono_domain: int,
        features: List[CheatFeature],
        status_message: str = "Ready",
        language: str = "zh",
    ) -> Panel:
        """Constructs the complete trainer dashboard renderable."""
        # Top Header & Info
        header_text = Text()
        header_text.append(tr("header_title", language), style="bold cyan")
        header_text.append(tr("header_subtitle", language), style="dim italic")

        # Connection Status Line
        if is_attached:
            conn_info = Text.from_markup(
                tr(
                    "attached_info",
                    language,
                    process_name=process_name,
                    pid=pid,
                    mono_domain=mono_domain,
                )
            )
        else:
            conn_info = Text.from_markup(
                tr("waiting_info", language, process_name=process_name)
            )

        # Cheats Table
        table = Table(title=tr("table_title", language), expand=True, show_lines=True)
        table.add_column(tr("col_hotkey", language), style="bold cyan", justify="center", width=10)
        table.add_column(tr("col_feature", language), style="bold white", width=30)
        table.add_column(tr("col_status", language), justify="center", width=18)
        table.add_column(tr("col_description", language), style="dim")

        for f in features:
            if hasattr(f, "get_status_badge"):
                try:
                    status_badge = f.get_status_badge(language=language)
                except TypeError:
                    status_badge = f.get_status_badge()
            else:
                if f.is_enabled:
                    status_badge = tr("status_active", language)
                else:
                    status_badge = tr("status_disabled", language)

            name = f.get_name(language) if hasattr(f, "get_name") else f.name
            desc = f.get_description(language) if hasattr(f, "get_description") else f.description
            table.add_row(f.hotkey, name, status_badge, desc)

        # Controls & Footer
        footer_text = Text()
        footer_text.append(tr("controls_title", language), style="bold yellow")
        footer_text.append(tr("controls_hotkey_tip", language))
        footer_text.append(tr("controls_lang_tip", language), style="bold cyan")
        footer_text.append(tr("controls_exit_tip", language), style="bold magenta")
        footer_text.append(
            f"{tr('status_label', language)}{status_message}",
            style="italic green" if is_attached else "italic yellow",
        )

        content = Group(
            header_text,
            conn_info,
            Text(""),
            table,
            footer_text,
        )

        return Panel(
            content,
            border_style="cyan" if is_attached else "yellow",
            padding=(1, 2),
        )
