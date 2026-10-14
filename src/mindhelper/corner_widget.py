#!/usr/bin/env python3
"""
Mind Helper — Minimized Companion & Corner Summoner Widget
Floats on the screen border with a sleek celestial pill.
Summons the flyout drawer showing live RAM, Weather, System Uptime,
rotating Linux tips, and an inline question bar that answers queries until reset.
Includes a dedicated toggle to launch the full standalone application.
"""

import os
import sys
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

from gemini_anim import GeminiSparkle, GeminiGlowBar
from ai_brain import MindHelperBrain
from system_facts import get_live_telemetry, get_chilling_fact, get_quick_tip
from weather import get_atmospheric_status

class CornerSummonerWidget:
    def __init__(self, on_open_standalone=None):
        self.on_open_standalone = on_open_standalone
        self.brain = MindHelperBrain()
        self.is_drawer_open = False
        self.current_mode = "vitals" # "vitals" or "qa"
        self.telemetry_timer = None

        self._load_css()
        self._build_pill_window()
        self._build_drawer_window()
        self._start_telemetry_loop()

    def _load_css(self):
        css_provider = Gtk.CssProvider()
        css_path = os.path.join(os.path.dirname(__file__), "style.css")
        if not os.path.exists(css_path):
            css_path = "/usr/share/mindhelper/style.css"
        if os.path.exists(css_path):
            try:
                css_provider.load_from_path(css_path)
                Gtk.StyleContext.add_provider_for_screen(
                    Gdk.Screen.get_default(),
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception:
                pass

    def _build_pill_window(self):
        """Compact floating pill widget docked to the screen border."""
        self.pill_win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.pill_win.set_title("Mind Helper")
        self.pill_win.set_wmclass("mindhelper", "mindhelper")
        self.pill_win.set_icon_name("mindhelper")
        self.pill_win.set_decorated(False)
        self.pill_win.set_keep_above(True)
        self.pill_win.set_skip_taskbar_hint(True)
        self.pill_win.set_skip_pager_hint(True)
        self.pill_win.set_app_paintable(True)
        self.pill_win.get_style_context().add_class("corner-dock-window")

        pill_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pill_box.get_style_context().add_class("dock-pill-frame")

        arrow_lbl = Gtk.Label(label="◀")
        arrow_lbl.get_style_context().add_class("dock-arrow")
        pill_box.pack_start(arrow_lbl, False, False, 0)

        # Gemini animated sparkle star
        self.pill_sparkle = GeminiSparkle(size=20, animated=True)
        pill_box.pack_start(self.pill_sparkle, False, False, 0)

        name_lbl = Gtk.Label(label="Mind Helper")
        name_lbl.get_style_context().add_class("telemetry-pill")
        pill_box.pack_start(name_lbl, False, False, 0)

        event_box = Gtk.EventBox()
        event_box.add(pill_box)
        event_box.connect("button-press-event", self._on_pill_clicked)
        event_box.set_tooltip_text("Open Mind Helper Minimized Companion")

        self.pill_win.add(event_box)

        # Screen position: right edge
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geom = monitor.get_geometry()
        x = geom.x + geom.width - 150
        y = geom.y + int(geom.height * 0.45)
        self.pill_win.move(x, y)

    def _build_drawer_window(self):
        """Flyout drawer containing Vitals & Inline Linux Q&A."""
        self.drawer_win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.drawer_win.set_title("Mind Helper")
        self.drawer_win.set_wmclass("mindhelper", "mindhelper")
        self.drawer_win.set_icon_name("mindhelper")
        self.drawer_win.set_decorated(False)
        self.drawer_win.set_keep_above(True)
        self.drawer_win.set_skip_taskbar_hint(True)
        self.drawer_win.set_skip_pager_hint(True)
        self.drawer_win.set_default_size(390, 560)
        self.drawer_win.get_style_context().add_class("flyout-drawer-window")

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.drawer_win.add(main_box)

        # 1. Top Header Row
        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.drawer_sparkle = GeminiSparkle(size=28, animated=True)
        header_row.pack_start(self.drawer_sparkle, False, False, 0)

        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        t_lbl = Gtk.Label()
        t_lbl.set_markup("<span weight='bold' size='medium' color='#f8fafc'>Mind Helper</span>")
        t_lbl.set_xalign(0)
        title_vbox.pack_start(t_lbl, False, False, 0)

        sub_lbl = Gtk.Label()
        sub_lbl.set_markup("<span size='small' color='#94a3b8'>Minimized Companion</span>")
        sub_lbl.set_xalign(0)
        title_vbox.pack_start(sub_lbl, False, False, 0)
        header_row.pack_start(title_vbox, True, True, 0)

        # Toggle Button: Launch Standalone App
        launch_btn = Gtk.Button(label="⤢ Standalone")
        launch_btn.get_style_context().add_class("btn-secondary")
        launch_btn.set_tooltip_text("Launch Standalone Application")
        launch_btn.connect("clicked", self._on_launch_standalone_clicked)
        header_row.pack_start(launch_btn, False, False, 0)

        # Close / Collapse Button
        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("btn-secondary")
        close_btn.connect("clicked", lambda b: self.toggle_drawer(False))
        header_row.pack_start(close_btn, False, False, 0)

        main_box.pack_start(header_row, False, False, 0)

        # 2. Gemini Shimmer Glow Bar
        self.glow_bar = GeminiGlowBar(height=3)
        main_box.pack_start(self.glow_bar, False, False, 0)

        # 3. Dynamic Content Stack (Vitals View vs Q&A View)
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.content_stack.set_transition_duration(200)
        main_box.pack_start(self.content_stack, True, True, 0)

        # --- Sub-page A: Vitals View (RAM, Weather, Uptime, Tips) ---
        self.vitals_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content_stack.add_named(self.vitals_box, "vitals")

        # RAM Usage Card
        self.ram_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.ram_card.get_style_context().add_class("stat-box")
        ram_lbl = Gtk.Label(label="Memory Usage (RAM)")
        ram_lbl.get_style_context().add_class("stat-label")
        ram_lbl.set_xalign(0)
        self.ram_card.pack_start(ram_lbl, False, False, 0)

        self.ram_val_lbl = Gtk.Label()
        self.ram_val_lbl.get_style_context().add_class("stat-val")
        self.ram_val_lbl.set_xalign(0)
        self.ram_card.pack_start(self.ram_val_lbl, False, False, 0)

        self.ram_progress = Gtk.ProgressBar()
        self.ram_card.pack_start(self.ram_progress, False, False, 2)
        self.vitals_box.pack_start(self.ram_card, False, False, 0)

        # Weather & Uptime Twin Cards
        mid_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Weather Card
        weather_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        weather_card.get_style_context().add_class("stat-box")
        w_title = Gtk.Label(label="Atmosphere")
        w_title.get_style_context().add_class("stat-label")
        w_title.set_xalign(0)
        weather_card.pack_start(w_title, False, False, 0)

        self.weather_val_lbl = Gtk.Label()
        self.weather_val_lbl.set_markup("<span size='medium' weight='bold' color='#a5b4fc'>Loading...</span>")
        self.weather_val_lbl.set_xalign(0)
        weather_card.pack_start(self.weather_val_lbl, False, False, 0)
        mid_row.pack_start(weather_card, True, True, 0)

        # Uptime Card
        uptime_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        uptime_card.get_style_context().add_class("stat-box")
        u_title = Gtk.Label(label="System Uptime")
        u_title.get_style_context().add_class("stat-label")
        u_title.set_xalign(0)
        uptime_card.pack_start(u_title, False, False, 0)

        self.uptime_val_lbl = Gtk.Label()
        self.uptime_val_lbl.get_style_context().add_class("stat-val")
        self.uptime_val_lbl.set_xalign(0)
        uptime_card.pack_start(self.uptime_val_lbl, False, False, 0)
        mid_row.pack_start(uptime_card, True, True, 0)

        self.vitals_box.pack_start(mid_row, False, False, 0)

        # CPU & Kernel Card
        cpu_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cpu_card.get_style_context().add_class("stat-box")
        self.cpu_lbl = Gtk.Label()
        self.cpu_lbl.set_xalign(0)
        cpu_card.pack_start(self.cpu_lbl, True, True, 0)
        self.vitals_box.pack_start(cpu_card, False, False, 0)

        # Helpful Chilling Fact / Linux Tip Box
        self.tip_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.tip_card.get_style_context().add_class("chilling-quote-box")
        tip_header = Gtk.Label(label="✧ Sentinel Whisper")
        tip_header.get_style_context().add_class("stat-label")
        tip_header.set_xalign(0)
        self.tip_card.pack_start(tip_header, False, False, 0)

        self.tip_text = Gtk.Label()
        self.tip_text.set_line_wrap(True)
        self.tip_text.set_xalign(0)
        self.tip_card.pack_start(self.tip_text, False, False, 0)
        self.vitals_box.pack_start(self.tip_card, True, True, 0)

        # --- Sub-page B: Q&A View (Active after a question is asked) ---
        self.qa_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content_stack.add_named(self.qa_box, "qa")

        qa_top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        qa_title = Gtk.Label()
        qa_title.set_markup("<span weight='bold' size='small' color='#38bdf8'>✧ Mind Helper Inquiry</span>")
        qa_title.set_xalign(0)
        qa_top_bar.pack_start(qa_title, True, True, 0)

        back_btn = Gtk.Button(label="↩ Return to Vitals")
        back_btn.get_style_context().add_class("btn-secondary")
        back_btn.connect("clicked", lambda b: self._switch_to_vitals())
        qa_top_bar.pack_start(back_btn, False, False, 0)
        self.qa_box.pack_start(qa_top_bar, False, False, 0)

        # Scrollable area for question and response
        qa_scroll = Gtk.ScrolledWindow()
        qa_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        qa_scroll.get_style_context().add_class("chat-scroll-area")

        self.qa_text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.qa_text_box.set_margin_top(8)
        self.qa_text_box.set_margin_bottom(8)

        self.user_query_lbl = Gtk.Label()
        self.user_query_lbl.get_style_context().add_class("user-bubble")
        self.user_query_lbl.set_line_wrap(True)
        self.user_query_lbl.set_xalign(0)
        self.qa_text_box.pack_start(self.user_query_lbl, False, False, 0)

        self.ai_answer_lbl = Gtk.Label()
        self.ai_answer_lbl.get_style_context().add_class("ai-bubble")
        self.ai_answer_lbl.set_line_wrap(True)
        self.ai_answer_lbl.set_xalign(0)
        self.qa_text_box.pack_start(self.ai_answer_lbl, False, False, 0)

        qa_scroll.add(self.qa_text_box)
        self.qa_box.pack_start(qa_scroll, True, True, 0)

        # 4. Bottom Inline Question Bar
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.prompt_entry = Gtk.Entry()
        self.prompt_entry.set_placeholder_text("Ask Mind Helper about Linux...")
        self.prompt_entry.get_style_context().add_class("prompt-entry")
        self.prompt_entry.connect("activate", self._on_ask_clicked)
        bottom_bar.pack_start(self.prompt_entry, True, True, 0)

        ask_btn = Gtk.Button(label="✧ Ask")
        ask_btn.get_style_context().add_class("btn-gemini-sparkle")
        ask_btn.connect("clicked", self._on_ask_clicked)
        bottom_bar.pack_start(ask_btn, False, False, 0)

        main_box.pack_start(bottom_bar, False, False, 0)

    def _start_telemetry_loop(self):
        """Refreshes live vitals every 3 seconds."""
        self._refresh_vitals()
        self.telemetry_timer = GLib.timeout_add_seconds(3, self._refresh_vitals)

    def _refresh_vitals(self):
        try:
            t = get_live_telemetry()
            # RAM
            self.ram_val_lbl.set_text(f"{t['mem_used_gb']} GiB / {t['mem_total_gb']} GiB ({t['mem_percent']}%)")
            self.ram_progress.set_fraction(t['mem_percent'] / 100.0)

            # Uptime
            self.uptime_val_lbl.set_text(t['uptime_str'])

            # CPU & Processes
            self.cpu_lbl.set_markup(
                f"<span size='small' color='#94a3b8'>CPU:</span> <span weight='bold' color='#38bdf8'>{t['cpu_percent']}%</span>  "
                f"<span size='small' color='#94a3b8'>Procs:</span> <span weight='bold' color='#cbd5e1'>{t['proc_count']}</span>"
            )

            # Tip / Chilling Reflection (only if in vitals mode)
            if self.current_mode == "vitals":
                tip = get_quick_tip()
                self.tip_text.set_text(tip)

            # Weather (async background fetch once)
            def weather_worker():
                w = get_atmospheric_status()
                if w["available"]:
                    text = f"<b>{w['temp_c']}°C</b> • {w['condition']}\n<small>{w['city']}</small>"
                else:
                    text = "<small>Silent Void</small>"
                GLib.idle_add(lambda: self.weather_val_lbl.set_markup(text))

            threading.Thread(target=weather_worker, daemon=True).start()
        except Exception:
            pass
        return True

    def _on_pill_clicked(self, widget, event):
        self.toggle_drawer(not self.is_drawer_open)

    def toggle_drawer(self, show: bool):
        self.is_drawer_open = show
        if show:
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor() or display.get_monitor(0)
            geom = monitor.get_geometry()
            drawer_w, drawer_h = 390, 560
            x = geom.x + geom.width - drawer_w - 6
            y = geom.y + int((geom.height - drawer_h) / 2)

            self.drawer_win.move(x, y)
            self.drawer_win.show_all()
            self.drawer_sparkle.start_animation()
            self._refresh_vitals()
        else:
            self.drawer_sparkle.stop_animation()
            self.drawer_win.hide()

    def _on_launch_standalone_clicked(self, button):
        self.toggle_drawer(False)
        if self.on_open_standalone:
            self.on_open_standalone()
        else:
            import subprocess
            subprocess.Popen(["/usr/bin/mindhelper"])

    def _switch_to_vitals(self):
        self.current_mode = "vitals"
        self.content_stack.set_visible_child_name("vitals")
        self.prompt_entry.set_text("")
        self._refresh_vitals()

    def _on_ask_clicked(self, widget):
        query = self.prompt_entry.get_text().strip()
        if not query:
            return

        # Switch to Q&A View
        self.current_mode = "qa"
        self.content_stack.set_visible_child_name("qa")
        self.user_query_lbl.set_text(query)
        self.ai_answer_lbl.set_text("Thinking with Gemini intelligence...")
        self.glow_bar.start()

        def worker():
            answer = self.brain.answer_query(query)
            GLib.idle_add(lambda: self._display_answer(answer))

        threading.Thread(target=worker, daemon=True).start()

    def _display_answer(self, answer: str):
        self.glow_bar.stop()
        self.ai_answer_lbl.set_text(answer)

    def show(self):
        self.pill_win.show_all()
