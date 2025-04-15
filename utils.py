from typing import Tuple, Optional, Dict, Any
import psutil


def get_system_stats() -> Dict[str, Any]:
    """
    Fetches various system statistics using psutil.
    """
    stats = {
        "cpu_usage": psutil.cpu_percent(),
        "cpu_freq": psutil.cpu_freq(),
        "memory": psutil.virtual_memory(),
        "disk": psutil.disk_usage('/'),
        "net_io": psutil.net_io_counters(),
        "temps": None,
    }
    try:
        stats["temps"] = psutil.sensors_temperatures()
    except AttributeError:
        pass # Not available
    return stats


def get_cpu_color(value: float) -> str:
    """
    Get the color code based on CPU usage percentage.
    """
    color = get_color_by_value(value)
    return f"{color}"


def get_memory_color(value: float) -> str:
    """
    Get the color code based on memory usage percentage.
    """
    color = get_color_by_value(value)
    return f"{color}"


def get_color_by_value(value: float) -> str: # Changed type hint to float
    """
    Get a color (green, yellow, red) based on a percentage value.
    """
    if value < 50:
        return "green"
    elif value < 75:
        return "yellow"
    else:
        return "red"


def format_bytes(size: int) -> str:
    """
    Converts bytes to a human-readable string (KB, MB, GB).
    """
    power = 2**10 # 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.1f}{power_labels.get(n, '')}B"


def calculate_network_rates(current_net_io, last_net_io, time_delta: float) -> Tuple[float, float]:
    """
    Calculates network send and receive rates (bytes/sec).
    """
    if time_delta > 0 and last_net_io is not None:
        # Ensure last_net_io is not None for the first calculation
        bytes_sent_delta = current_net_io.bytes_sent - last_net_io.bytes_sent
        bytes_recv_delta = current_net_io.bytes_recv - last_net_io.bytes_recv
        # Prevent negative rates if counters reset (e.g., system suspend)
        send_rate = max(0, bytes_sent_delta / time_delta)
        recv_rate = max(0, bytes_recv_delta / time_delta)
    else:
        send_rate = 0
        recv_rate = 0
    return send_rate, recv_rate


def get_filtered_temperatures(temps: Optional[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """
    Filters psutil sensor temperatures to find preferred CPU and GPU temps.
    """
    filtered_temps = []
    if not temps:
        return filtered_temps

    # Define keywords
    cpu_keywords = {"coretemp", "k10temp", "cpu", "package"}
    gpu_keywords = {"amdgpu", "nvidia", "gpu", "radeon"}
    package_keywords = {"package", "tctl", "tdie"} # Keywords for main CPU package temp

    cpu_temp_added = False
    gpu_temps_added = {} 

    # --- First pass: Prioritize adding 'package' CPU temperature ---
    package_temp_found = False
    for name, entries in temps.items():
        name_lower = name.lower()
        for entry in entries:
            label_lower = (entry.label or "").lower()
            is_cpu_package = any(pkg_kw in label_lower for pkg_kw in package_keywords) or \
                             any(pkg_kw in name_lower for pkg_kw in package_keywords)

            if is_cpu_package and not cpu_temp_added:
                display_label = entry.label or name
                filtered_temps.append({
                    "prefix": "CPU Temp:",
                    "label": display_label,
                    "temp": entry.current
                })
                cpu_temp_added = True
                package_temp_found = True
                break 
        if package_temp_found: break

    # --- Second pass: Add first generic CPU temp (if no package temp found) and GPU temps ---
    for name, entries in temps.items():
        name_lower = name.lower()
        for entry in entries:
            label_lower = (entry.label or "").lower()
            display_label = entry.label or name

            # Check if it's a CPU temp (and no CPU temp has been added yet)
            is_cpu = any(kw in name_lower for kw in cpu_keywords) or \
                     any(kw in label_lower for kw in cpu_keywords)
            if is_cpu and not cpu_temp_added:
                filtered_temps.append({
                    "prefix": "CPU Temp:",
                    "label": display_label,
                    "temp": entry.current
                })
                cpu_temp_added = True
                

            # Check if it's a GPU temp (and this specific one hasn't been added)
            is_gpu = any(kw in name_lower for kw in gpu_keywords) or \
                     any(kw in label_lower for kw in gpu_keywords)
            if is_gpu and display_label not in gpu_temps_added:
                 filtered_temps.append({
                     "prefix": "GPU Temp:",
                     "label": display_label,
                     "temp": entry.current
                 })
                 gpu_temps_added[display_label] = True

    return filtered_temps

