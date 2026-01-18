"""
SOTA Console Interface for Hampter Link.
Uses PromptToolkit for the REPL and Rich for beautiful output.
"""
import asyncio
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style as PtStyle

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.table import Table
from rich import box

# Force width to avoid wrapping issues in standard terminals
console = RichConsole(width=100)

class SotaConsole:
    """
    State-of-the-Art CLI for Hampter Link.
    """
    
    def __init__(self):
        self.running = False
        self._commands: Dict[str, Callable] = {}
        self._status_provider: Optional[Callable] = None
        self._message_handler: Optional[Callable] = None
        
        # PromptToolkit Session
        self.session = PromptSession()
        
        self._commands = {
            '/help': self._cmd_help,
            '/status': self._cmd_status,
            '/quit': self._cmd_quit,
            '/fan': self._pass,
            '/link': self._pass,
        }
        self._fan_handler = None
        self._link_handler = None

    def set_status_provider(self, provider): self._status_provider = provider
    def set_message_handler(self, handler): self._message_handler = handler
    def set_fan_handler(self, handler): self._fan_handler = handler
    def set_link_handler(self, handler): self._link_handler = handler

    def _pass(self, args): pass

    def _get_bottom_toolbar(self):
        if not self._status_provider:
            return HTML(' <b><style bg="red" fg="white"> OFFLINE </style></b>')
        
        stats = self._status_provider()
        cpu = f"{stats.get('cpu_percent', 0):.0f}%"
        temp = f"{stats.get('temp', 0):.1f}C"
        rssi = f"{stats.get('rssi', -99)}dBm"
        
        return HTML(
            f' CPU: {cpu} | Temp: {temp} | WiFi: {rssi} | '
            f'<b>Type /help</b>'
        )

    async def run(self):
        self.running = True
        
        console.print(Panel(
            "[bold cyan]HAMPTER LINK v2.0[/bold cyan]\n[dim]Secure. Off-Grid. Connected.[/dim]",
            border_style="blue", box=box.ROUNDED, expand=False
        ))
        
        with patch_stdout():
            while self.running:
                try:
                    command = await self.session.prompt_async(
                        HTML('<style fg="#00ffff"><b>[link]</b></style> > '),
                        bottom_toolbar=self._get_bottom_toolbar,
                        refresh_interval=1.0,
                    )
                    if not command.strip(): continue
                    await self._process_command(command)
                except (EOFError, KeyboardInterrupt):
                    self.running = False
                    
        console.print("[yellow]Console stopped.[/yellow]")

    async def _process_command(self, text: str):
        text = text.strip()
        if text.startswith('/'):
            parts = text.split()
            cmd = parts[0].lower()
            args = parts[1:]
            
            if cmd == '/quit': self.running = False
            elif cmd == '/help': await self._cmd_help(args)
            elif cmd == '/status': await self._cmd_status(args)
            elif cmd == '/fan': await self._cmd_fan_proxy(args)
            elif cmd == '/link': await self._cmd_link_proxy(args)
            else:
                console.print(f"[red]Unknown: {cmd}[/red]")
        else:
            if self._message_handler:
                self._message_handler(text)
                ts = datetime.now().strftime("%H:%M")
                console.print(f"[green]Me:[/green] {text}")

    async def _cmd_help(self, args):
        t = Table(show_header=False, box=box.SIMPLE, expand=False)
        t.add_column("Cmd", style="cyan bold")
        t.add_column("Desc")
        t.add_row("/status", "System telemetry")
        t.add_row("/fan", "Set fan speed")
        t.add_row("/quit", "Exit")
        console.print(t)

    async def _cmd_status(self, args):
        if not self._status_provider: return
        s = self._status_provider()
        
        t = Table(show_header=False, box=box.ROUNDED)
        t.add_row(f"[bold]CPU:[/bold] {s.get('cpu_percent')}%", f"[bold]Temp:[/bold] {s.get('temp'):.1f}C")
        t.add_row(f"[bold]WiFi:[/bold] {s.get('rssi')}dBm", f"[bold]Bat:[/bold] {s.get('battery')}%")
        
        console.print(Panel(t, title="Status", border_style="blue", expand=False))

    async def _cmd_fan_proxy(self, args):
        if self._fan_handler and args:
            try:
                val = int(args[0])
                self._fan_handler(val)
                console.print(f"[green]Fan -> {val}%[/green]")
            except:
                console.print("[red]Invalid speed[/red]")
        elif self._fan_handler:
             self._fan_handler(-1)
             console.print("[green]Fan -> Auto[/green]")

    async def _cmd_link_proxy(self, args):
        if self._link_handler:
            self._link_handler()

    async def _cmd_quit(self, args):
        # Explicit quit handler for command map
        self.running = False

    def stop(self):
        self.running = False
