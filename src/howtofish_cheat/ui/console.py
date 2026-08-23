"""Rich-based console UI dashboard for How to Fish Trainer."""

from typing import List
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from ..features.base import CheatFeature


class TrainerUI:
    """Renders the live terminal dashboard for the trainer."""

    def __init__(self, console: Console = None):
        self.console = console or Console()

    def generate_dashboard(
        self,
        is_attached: bool,
        process_name: str,
        pid: int,
        mono_domain: int,
        features: List[CheatFeature],
        status_message: str = "Ready",
    ) -> Panel:
        """Constructs the complete trainer dashboard renderable."""
        # Top Header & Info
        header_text = Text()
        header_text.append("[*] HOW TO FISH - EXTERNAL MEMORY TRAINER\n", style="bold cyan")
        header_text.append("Unity Mono Engine | FishNet Multiplayer Support | JIT Patch Framework\n", style="dim italic")

        # Connection Status Line
        if is_attached:
            conn_info = Text.from_markup(
                f"[bold green][ATTACHED][/bold green] [white]Process:[/white] [cyan]{process_name}[/cyan] (PID: {pid}) | [white]Mono Domain:[/white] [yellow]0x{mono_domain:X}[/yellow]"
            )
        else:
            conn_info = Text.from_markup(
                f"[bold yellow][WAITING][/bold yellow] [white]Searching for process:[/white] [cyan]{process_name}[/cyan]..."
            )

        # Cheats Table
        table = Table(title="[bold white]AVAILABLE CHEATS[/bold white]", expand=True, show_lines=True)
        table.add_column("Hotkey", style="bold cyan", justify="center", width=10)
        table.add_column("Feature", style="bold white", width=30)
        table.add_column("Status", justify="center", width=15)
        table.add_column("Description", style="dim")

        for f in features:
            status_badge = "[bold green]ACTIVE[/bold green]" if f.is_enabled else "[dim red]DISABLED[/dim red]"
            table.add_row(f.hotkey, f.name, status_badge, f.description)

        # Controls & Footer
        footer_text = Text()
        footer_text.append("\n[Controls] ", style="bold yellow")
        footer_text.append("Press designated hotkeys to toggle cheats | ")
        footer_text.append("Press [F10] or [Ctrl+C] to exit safely.\n", style="bold magenta")
        footer_text.append(f"[Status] {status_message}", style="italic green" if is_attached else "italic yellow")

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
