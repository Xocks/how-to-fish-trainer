"""Rich-based console UI dashboard for How to Fish Trainer."""

from typing import List, Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from ..features import CheatFeature, SpawnableItem, get_default_features
from .selector import ItemSelectorState
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
        features: Optional[List[CheatFeature]] = None,
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

        display_features = features if features else get_default_features()

        for f in display_features:
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

    def generate_item_selector(
        self,
        catalog: List[SpawnableItem],
        state: ItemSelectorState,
        language: str = "zh",
        column_count: int = 4,
    ) -> Panel:
        """Renders one page of the item catalog and the numeric prompt."""
        if column_count <= 0:
            raise ValueError("column_count must be greater than zero")
        state.clamp_page(len(catalog))
        start = state.page * state.page_size
        visible_items = catalog[start : start + state.page_size]

        table = Table(
            expand=True,
            show_lines=False,
            box=None,
            pad_edge=False,
            padding=(0, 1),
        )
        for _ in range(column_count):
            table.add_column("ID", justify="right", style="bold cyan", width=4)
            table.add_column(
                tr("selector_item_name", language),
                style="bold white",
                ratio=1,
                no_wrap=True,
                overflow="ellipsis",
            )

        cell_count = column_count * 2
        for row_start in range(0, len(visible_items), column_count):
            cells = []
            for item in visible_items[row_start : row_start + column_count]:
                item_name = Text(item.display_name)
                if item.requires_confirmation:
                    item_name.append(" !", style="bold red")
                cells.extend((str(item.id), item_name))

            while len(cells) < cell_count:
                cells.extend(("", ""))
            table.add_row(*cells)

        total_pages = state.total_pages(len(catalog))
        footer = Text()
        footer.append(
            tr(
                "selector_page",
                language,
                current=state.page + 1,
                total=total_pages,
                count=len(catalog),
            ),
            style="dim",
        )
        footer.append("\n")

        if state.pending_confirmation:
            item = state.pending_confirmation
            footer.append(
                tr(
                    "selector_confirm_special",
                    language,
                    item_id=item.id,
                    item_name=item.display_name,
                ),
                style="bold red",
            )
        else:
            footer.append(tr("selector_prompt", language), style="bold yellow")
            footer.append(state.input_buffer or "_", style="bold cyan")
            footer.append("\n")
            footer.append(tr("selector_controls", language), style="dim")

        if state.message_key:
            footer.append("\n")
            footer.append(
                tr(state.message_key, language, **state.message_kwargs),
                style="bold red",
            )

        return Panel(
            Group(table, Text(""), footer),
            title=tr("selector_title", language),
            border_style="magenta",
            padding=(1, 2),
        )
