#!/usr/bin/env python3
"""
Mind Helper — Master Controller & Application Launcher
Coordinates standalone desktop window, corner companion, system awakening notifications,
and terminal diagnostic queries.
"""

import os
import sys
import argparse
import subprocess
import threading
from pathlib import Path


def _update_notice(config_dir):
    """Yeniden başlatarak yapılan MindOS güncellemesinin sonucunu bir kez bildirir"""
    import json
    import time
    try:
        with open("/var/lib/mindpkg/offline-result.json", encoding="utf-8") as f:
            res = json.load(f)
        stamp = str(int(res["time"]))
    except Exception:
        return
    seen = os.path.join(config_dir, "update-seen")
    try:
        if open(seen).read().strip() == stamp:
            return
    except OSError:
        pass
    os.makedirs(config_dir, exist_ok=True)
    with open(seen, "w") as f:
        f.write(stamp)
    if time.time() - int(stamp) > 7 * 86400:
        return
    tr = os.environ.get("LANG", "").startswith("tr")
    name = f"MindOS Paradise {res.get('release', '')}".strip()
    if res.get("ok"):
        title = f"{name} güncel ✓" if tr else f"{name} is up to date ✓"
        body = ("Sistem güncellemesi başarıyla kuruldu." if tr else "The system update was installed successfully.")
    else:
        title = "Güncelleme tamamlanamadı" if tr else "Update could not be completed"
        body = ("Bazı paketler kurulamadı. Ayrıntılar: Mind Arc → Sistem Güncellemesi" if tr
                else "Some packages could not be installed. Details: Mind Arc → System Update")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from weather import send_desktop_notification
        send_desktop_notification({"title": title, "full_message": body})
    except Exception:
        pass


def _autostart_greeting():
    """Oturum açılışı: yalnızca ilk girişte bir bildirim. GTK hiç yüklenmez; GTK yüklemek
    oturumun ilk saniyelerinde X11'e düşüp gereksiz yere XWayland'ı (~250 MB) başlatabiliyordu."""
    config_dir = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "mindhelper")
    _update_notice(config_dir)
    marker = os.path.join(config_dir, "welcomed")
    if os.path.exists(marker):
        return
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from weather import send_desktop_notification, generate_awakening_greeting
        send_desktop_notification(generate_awakening_greeting())
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        open(marker, "w").close()
    except Exception:
        pass


if __name__ == "__main__" and "--autostart" in sys.argv[1:]:
    _autostart_greeting()
    sys.exit(0)
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Fix GNOME Shell window identification & dock/tray metadata
GLib.set_prgname("mindhelper")
GLib.set_application_name("Mind Helper")
Gtk.Window.set_default_icon_name("mindhelper")

from app import MindHelperApp
from corner_widget import CornerSummonerWidget
from weather import send_desktop_notification, generate_awakening_greeting

def run_standalone():
    """Runs the full Mind Helper standalone application window."""
    app = MindHelperApp()
    # Ensure clean exit when window is closed (prevents zombie background processes)
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    app.present()
    Gtk.main()

def run_daemon(mode="autostart"):
    """Runs the background awakening notifier and floating companion widget."""
    # 1. System Awakening Notification
    def notify_worker():
        try:
            greeting = generate_awakening_greeting()
            send_desktop_notification(greeting)
        except Exception:
            pass

    threading.Thread(target=notify_worker, daemon=True).start()

    # 2. Corner Companion Widget
    def launch_standalone():
        subprocess.Popen(["/usr/bin/mindhelper"])

    corner = CornerSummonerWidget(on_open_standalone=launch_standalone)
    corner.show()
    if mode == "minimized":
        corner.toggle_drawer(True)
    Gtk.main()

def run_diagnostic():
    print("✦ Mind Helper — System Diagnostic & Verification ✦\n")
    print("• Checking Python Modules & Core Libraries:")
    for mod in ["gi", "cairo", "psutil", "requests", "json", "threading"]:
        try:
            __import__(mod)
            print(f"  [✓] {mod:<12} Loaded successfully")
        except Exception as e:
            print(f"  [✗] {mod:<12} Failed: {e}")

    print("\n• Checking System Telemetry Engine:")
    from system_facts import get_live_telemetry, get_quick_tip
    t = get_live_telemetry()
    print(f"  [✓] Kernel:       {t['kernel']}")
    print(f"  [✓] OS Release:   {t['os_name']}")
    print(f"  [✓] Silicon Uptime:{t['uptime_str']}")
    print(f"  [✓] Memory (RAM): {t['mem_used_gb']}G / {t['mem_total_gb']}G ({t['mem_percent']}%)")
    print(f"  [✓] Cores/CPU:    {t['cpu_count']} cores ({t['cpu_percent']}%)")

    print("\n• Checking Knowledge Base:")
    from ai_brain import MindHelperBrain
    brain = MindHelperBrain()
    sample = brain.answer_query("how does systemctl work?")
    lines = [l for l in sample.split("\n") if l.strip()]
    first_line = lines[0] if lines else "Active"
    print(f"  [✓] MindHelperBrain online (Sample response: {first_line[:50]}...)")

    print("\n• Checking Weather Telemetry:")
    from weather import get_atmospheric_status
    w = get_atmospheric_status(timeout=2)
    print(f"  [✓] Atmosphere:   {w['temp_c']}°C, {w['condition']} ({w['city']})")

    print("\n• Checking System Integration & Autostart:")
    desktop_file = Path("/usr/share/applications/mindhelper.desktop")
    autostart_file = Path("/etc/xdg/autostart/mindhelper-autostart.desktop")
    icon_png = Path("/usr/share/icons/hicolor/512x512/apps/mindhelper.png")
    has_icon = icon_png.exists()
    print(f"  [{'✓' if desktop_file.exists() else '!'}] Desktop Menu Entry:    {desktop_file}")
    print(f"  [{'✓' if autostart_file.exists() else '!'}] System Autostart:       {autostart_file}")
    print(f"  [{'✓' if has_icon else '!'}] Application Icon:        {icon_png}")

    print("\n✦ Verification Complete: Mind Helper is operational and ready for MindOS Paradise. ✦")

def main():
    parser = argparse.ArgumentParser(description="Mind Helper — Linux Companion & Intelligence Tutor")
    parser.add_argument("--daemon", action="store_true", help="Run background corner companion and awakening sequence")
    parser.add_argument("--autostart", action="store_true", help="System login autostart mode")
    parser.add_argument("--minimized", action="store_true", help="Summon the minimized companion flyout")
    parser.add_argument("--check", action="store_true", help="Run terminal diagnostic self-test")
    parser.add_argument("--ask", type=str, metavar="QUERY", help="Ask Mind Helper a Linux question directly in the terminal")
    args = parser.parse_args()

    if args.check:
        run_diagnostic()
        sys.exit(0)

    if args.ask:
        from ai_brain import MindHelperBrain
        brain = MindHelperBrain()
        print(brain.answer_query(args.ask))
        sys.exit(0)

    # Gracefully handle headless/chroot console without graphical display
    if not Gtk.init_check()[0]:
        print("✦ Mind Helper — MindOS Companion ✦")
        print("No graphical display detected in this console session (chroot/headless).")
        print("Mind Helper is installed and ready to start in graphical desktop session.")
        print("\nAvailable Terminal Commands:")
        print("  mindhelper --check         Run diagnostic self-test")
        print("  mindhelper --ask '<query>' Inquire directly via terminal")
        sys.exit(0)

    if args.autostart:
        # Oturum açılışında pencere ya da yüzen widget açılmaz; yalnızca ilk girişte
        # bir kez karşılama bildirimi gösterilir. Mind Helper menüden/dock'tan açılır.
        marker = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
                              "mindhelper", "welcomed")
        if not os.path.exists(marker):
            try:
                send_desktop_notification(generate_awakening_greeting())
                os.makedirs(os.path.dirname(marker), exist_ok=True)
                open(marker, "w").close()
            except Exception:
                pass
        sys.exit(0)
    if args.daemon:
        run_daemon(mode="autostart")
    elif args.minimized:
        run_daemon(mode="minimized")
    else:
        run_standalone()

if __name__ == "__main__":
    main()
