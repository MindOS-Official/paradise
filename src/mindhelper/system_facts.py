#!/usr/bin/env python3
"""
Mind Helper — System Telemetry & Linux Insights
Gathers live metrics: RAM consumption, CPU utilization, system uptime, and storage usage.
Provides practical Linux system facts and useful terminal shortcuts.
"""

import os
import time
import random
import platform
import psutil

def format_uptime(seconds: float) -> str:
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if not parts or secs > 0:
        parts.append(f"{secs}s")
    return " ".join(parts)

def get_live_telemetry() -> dict:
    """Collects real-time hardware telemetry and kernel vitals."""
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time

    # Memory
    mem = psutil.virtual_memory()
    mem_used_gb = mem.used / (1024 ** 3)
    mem_total_gb = mem.total / (1024 ** 3)
    mem_percent = mem.percent

    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count(logical=True)
    load1, load5, load15 = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)

    # Disk
    disk = psutil.disk_usage('/')
    disk_used_gb = disk.used / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)
    disk_percent = disk.percent

    # Process count
    try:
        proc_count = len(psutil.pids())
    except Exception:
        proc_count = 0

    # OS / Kernel
    kernel = platform.release()
    node = platform.node()
    os_name = "MindOS Paradise"

    return {
        "uptime_str": format_uptime(uptime_seconds),
        "uptime_sec": int(uptime_seconds),
        "mem_used_gb": round(mem_used_gb, 2),
        "mem_total_gb": round(mem_total_gb, 2),
        "mem_percent": mem_percent,
        "cpu_percent": cpu_percent,
        "cpu_count": cpu_count,
        "load_avg": f"{load1:.2f}, {load5:.2f}, {load15:.2f}",
        "disk_used_gb": round(disk_used_gb, 1),
        "disk_total_gb": round(disk_total_gb, 1),
        "disk_percent": disk_percent,
        "proc_count": proc_count,
        "kernel": kernel,
        "node": node,
        "os_name": os_name
    }

SYSTEM_INSIGHTS = [
    (
        "System Uptime: {uptime_str} • Kernel: {kernel} on {node}. "
        "System vitals are healthy and all core services are running smoothly."
    ),
    (
        "Memory Telemetry: {mem_used_gb} GiB / {mem_total_gb} GiB in use ({mem_percent}%). "
        "Linux automatically allocates unused RAM to buffer and cache disk reads for optimal speed."
    ),
    (
        "Process Activity: {proc_count} active processes across {cpu_count} CPU cores. "
        "Current load average: {load_avg}. Use 'htop' to inspect live process resource allocation."
    ),
    (
        "Root Storage: {disk_used_gb} GiB of {disk_total_gb} GiB used ({disk_percent}%). "
        "Keep your root partition clean by running 'sudo apt clean' and 'sudo apt autoremove'."
    ),
    (
        "CPU Utilization: {cpu_percent}% across {cpu_count} processor cores. "
        "Use 'ps aux --sort=-%cpu | head' to view top CPU consumers anytime."
    ),
    (
        "Pro Tip: Press 'Ctrl + R' in any terminal window to interactively search your command history.",
    ),
    (
        "Pro Tip: Use 'sudo ss -tulpn' to see which applications are listening on open network ports.",
    ),
    (
        "Pro Tip: Run 'journalctl -u <service> -f' to stream live service logs in real time."
    )
]

QUICK_LINUX_TIPS = [
    "Tip: Use 'Ctrl + R' in bash to interactively search your command history.",
    "Tip: Run 'sudo !!' to re-execute your previous command with root privileges.",
    "Tip: 'ss -tulpn' reveals all listening TCP/UDP sockets and their owning process IDs.",
    "Tip: 'journalctl -xeu <service>' inspects the diagnostic logs of a failing daemon.",
    "Tip: Append '2>&1' to redirect standard error directly into standard output.",
    "Tip: 'lsof -i :8080' instantly unmasks whichever process holds port 8080.",
    "Tip: 'df -h' and 'ncdu' swiftly uncover which directory is using storage space.",
    "Tip: Use 'kill -15 <PID>' for polite graceful termination before resorting to 'kill -9'."
]

def get_chilling_fact() -> str:
    """Generates a dynamic system telemetry summary or practical Linux insight."""
    telemetry = get_live_telemetry()
    tmpl = random.choice(SYSTEM_INSIGHTS)
    if isinstance(tmpl, tuple):
        tmpl = tmpl[0]
    return tmpl.format(**telemetry)

def get_quick_tip() -> str:
    """Returns a practical Linux mastery tip."""
    return random.choice(QUICK_LINUX_TIPS)

if __name__ == "__main__":
    t = get_live_telemetry()
    print("Telemetry:", t)
    print("Insight:", get_chilling_fact())
    print("Tip:", get_quick_tip())
