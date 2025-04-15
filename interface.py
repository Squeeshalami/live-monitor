import time
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich import box
from utils import *
from typing import Tuple, Any

console = Console()


def add_cpu_row(table: Table, cpu_usage: float, cpu_freq, cpu_color: str):
    """Adds the CPU usage row to the *CPU/GPU* table."""
    cpu_bar_width = 40 
    cpu_bar_fill = int((cpu_usage / 100.0) * cpu_bar_width)
    cpu_bar = f"[{cpu_color}]{'█' * cpu_bar_fill}{'-' * (cpu_bar_width - cpu_bar_fill)}[/{cpu_color}]"
    freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
    table.add_row(
        "[bold white]CPU[/bold white]",
        freq_str,
        f"[{cpu_color}]{cpu_usage:.2f}%[/{cpu_color}]",
        cpu_bar
    )

def add_memory_row(table: Table, memory, memory_usage: float, memory_color: str):
    """Adds the Memory usage row to the *Memory/Disk* table."""
    mem_bar_width = 40 
    mem_bar_fill = int((memory_usage / 100.0) * mem_bar_width)
    mem_bar = f"[{memory_color}]{'█' * mem_bar_fill}{'-' * (mem_bar_width - mem_bar_fill)}[/{memory_color}]"
    mem_raw = f"{format_bytes(memory.used)} / {format_bytes(memory.total)}"
    table.add_row(
        "[bold white]System Memory[/bold white]",
        f"{mem_raw}",
        f"[{memory_color}]{memory_usage:.2f}%[/{memory_color}]",
        mem_bar
    )

def add_disk_row(table: Table, disk, disk_usage: float, disk_color: str):
    """Adds the Disk usage row to the *Memory/Disk* table."""
    disk_bar_width = 40 
    disk_bar_fill = int((disk_usage / 100.0) * disk_bar_width)
    disk_bar = f"[{disk_color}]{'█' * disk_bar_fill}{'-' * (disk_bar_width - disk_bar_fill)}[/{disk_color}]"
    disk_raw = f"{format_bytes(disk.used)} / {format_bytes(disk.total)}"
    table.add_row(
        f"[bold white]Disk Usage[/bold white]",
        f"{disk_raw}",
        f"[{disk_color}]{disk_usage:.2f}%[/{disk_color}]",
        disk_bar
    )

def add_network_rows(table: Table, send_rate: float, recv_rate: float):
    """Adds the Network rate rows to the *Network* table, displaying in KB/s."""
    # Convert bytes/s to KB/s
    send_kbps = send_rate / 1024
    recv_kbps = recv_rate / 1024

    # Display formatted KB/s
    table.add_row("[bold white]Upload[/bold white] [bold green]↗[/bold green]", f"{send_kbps:.1f} KB/s")
    table.add_row("[bold white]Download[/bold white] [bold red]↘[/bold red]", f"{recv_kbps:.1f} KB/s")

def add_sensor_rows(table: Table, temps):
    """Adds filtered temperature rows to the *CPU/GPU* table using utils function."""
    try:
        filtered_temps = get_filtered_temperatures(temps)
        for temp_info in filtered_temps:
            # Add row using the structured info from the utility function
            table.add_row(
                f"[bold white]{temp_info['prefix']} {temp_info['label']}[/bold white]",
                f"{temp_info['temp']:.1f}°C", 
                "", 
                ""  
            )
    except Exception as e:
        console.print_exception(show_locals=True)
        table.add_row("Temperatures", "Error reading", "", "")

def generate_output_renderable(last_net_io_prev, last_time_prev) -> Tuple[Group, Any, float]:
    """Generates the renderable output including panels and exit message."""
    current_time = time.time()
    time_delta = current_time - last_time_prev if last_time_prev else 1.0 # Avoid division by zero
    stats = get_system_stats()
    memory_usage = stats["memory"].percent
    disk_usage = stats["disk"].percent

    # Use previous state passed as arguments
    current_net_io = stats["net_io"]
    send_rate, recv_rate = calculate_network_rates(current_net_io, last_net_io_prev, time_delta)

    cpu_color = get_cpu_color(stats["cpu_usage"])
    memory_color = get_memory_color(memory_usage)
    disk_color = get_color_by_value(disk_usage)

    # --- Create Tables --- #
    cpu_gpu_table = Table(show_header=False, header_style="bold red", box=box.SIMPLE, padding=(0, 1))
    cpu_gpu_table.add_column("Metric", style="dim", width=15)
    cpu_gpu_table.add_column("Value", justify="right", style="bold")
    cpu_gpu_table.add_column("Usage (%)", justify="right", style="bold")
    cpu_gpu_table.add_column("Bar", justify="left", width=40)
    add_cpu_row(cpu_gpu_table, stats["cpu_usage"], stats["cpu_freq"], cpu_color)
    add_sensor_rows(cpu_gpu_table, stats["temps"])
    mem_disk_table = Table(show_header=False, header_style="bold yellow", box=box.SIMPLE, padding=(0, 1))
    mem_disk_table.add_column("Metric", style="dim", width=15)
    mem_disk_table.add_column("Raw Usage", justify="right", style="bold")
    mem_disk_table.add_column("Usage (%)", justify="right", style="bold")
    mem_disk_table.add_column("Bar", justify="left", width=40)
    add_memory_row(mem_disk_table, stats["memory"], memory_usage, memory_color)
    add_disk_row(mem_disk_table, stats["disk"], disk_usage, disk_color)
    network_table = Table(show_header=False, header_style="bold blue", box=box.SIMPLE, padding=(0, 1))
    network_table.add_column("Metric", style="dim", width=15)
    network_table.add_column("Rate", justify="right", style="bold")
    add_network_rows(network_table, send_rate, recv_rate)

    # --- Group Tables into Panels --- #
    panel_group = Group(
        Panel(cpu_gpu_table, title="CPU & GPU", border_style="bold red"),
        Panel(mem_disk_table, title="Memory & Disk", border_style="bold yellow"),
        Panel(network_table, title="Network", border_style="bold blue")
    )

    # --- Align the Panel Group --- #
    aligned_panels = Align(panel_group, align="left", width=100)

    # --- Create Exit Message --- #
    exit_message = Text("Press Ctrl+C to exit", justify="left", style="dim")

    # --- Combine Aligned Panels and Exit Message --- #
    final_group = Group(
        aligned_panels,
        exit_message
    )

    # Return the renderable group and the current state for the next iteration
    return final_group, current_net_io, current_time

