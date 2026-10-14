#!/usr/bin/env python3
"""
Mind Helper — MindOS Celestial & Pixel Inspired Cairo Animation Components
Provides:
1. MindSentinelStar: 8-Point Faceted Crystal Diamond Star (Emerald to Sapphire gradient).
   Replaces the Google Gemini 4-point astroid star with a distinctive MindOS faceted crystal star.
2. GeminiGlowBar: Slim flowing iridescent aurora shimmer bar.
3. AuroraCanvas: Living, breathing sinusoidal aurora mesh ribbons with twinkling stars.
4. PixelAuroraBanner: Full interactive Hero Banner inspired by Google Pixel Tips / My Pixel.
"""

import math
import time
import random
import datetime
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import cairo

class MindSentinelStar(Gtk.DrawingArea):
    """
    Renders the MindOS 8-Point Faceted Crystal Diamond Star in vector Cairo.
    Replaces the Google Gemini 4-point astroid star. Features emerald-to-sapphire
    gradient fill matching the Mind Helper leaf logo, faceted rays, radiant diamond core,
    gentle cosmic breathing pulse, and orbiting stardust.
    """
    def __init__(self, size=36, animated=True):
        super().__init__()
        self.size = size
        self.animated = animated
        self.angle = 0.0
        self.pulse = 1.0
        self.timer_id = None
        self.set_size_request(size, size)
        self.connect("draw", self._on_draw)

        if self.animated:
            self.start_animation()

    def start_animation(self):
        if self.timer_id is None:
            self.timer_id = GLib.timeout_add(33, self._on_tick)  # ~30 FPS

    def stop_animation(self):
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
        self.queue_draw()

    def _on_tick(self):
        t = time.time()
        self.angle = (t * 0.35) % (2 * math.pi)
        self.pulse = 1.0 + 0.08 * math.sin(t * 2.2)
        self.queue_draw()
        return True

    def _on_draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        cx, cy = width / 2.0, height / 2.0

        cr.save()
        cr.translate(cx, cy)
        if self.animated and self.timer_id is not None:
            cr.rotate(self.angle * 0.20)
            scale_factor = self.pulse
        else:
            scale_factor = 1.0
        cr.scale(scale_factor, scale_factor)

        r_outer = min(cx, cy) * 0.85
        r_diag = r_outer * 0.54
        r_inner = r_outer * 0.24

        # 1. 8-Point Faceted Crystal Star Perimeter
        cr.new_path()
        for i in range(8):
            ang_outer = i * (math.pi / 4.0) - (math.pi / 2.0)
            r_pt = r_outer if (i % 2 == 0) else r_diag
            xo = r_pt * math.cos(ang_outer)
            yo = r_pt * math.sin(ang_outer)

            ang_inner = ang_outer + (math.pi / 8.0)
            xi = r_inner * math.cos(ang_inner)
            yi = r_inner * math.sin(ang_inner)

            if i == 0:
                cr.move_to(xo, yo)
            else:
                cr.line_to(xo, yo)
            cr.line_to(xi, yi)
        cr.close_path()

        # 2. Dual-Tone Emerald to Sapphire Gradient (matching Mind Helper wsp.png)
        pat = cairo.LinearGradient(-r_outer, -r_outer, r_outer, r_outer)
        pat.add_color_stop_rgba(0.0, 0.06, 0.72, 0.51, 1.0)  # Emerald #10b981
        pat.add_color_stop_rgba(0.5, 0.13, 0.77, 0.96, 1.0)  # Cyan #22d3ee
        pat.add_color_stop_rgba(1.0, 0.15, 0.39, 0.92, 1.0)  # Sapphire #2563eb
        cr.set_source(pat)
        cr.fill_preserve()

        # 3. Outer Crystal Facet Stroke
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.45)
        cr.set_line_width(1.0)
        cr.stroke()

        # 4. Internal Facet Lines (Geometric Diamond Structure)
        for i in range(8):
            ang = i * (math.pi / 4.0) - (math.pi / 2.0)
            r_pt = r_outer if (i % 2 == 0) else r_diag
            cr.move_to(0, 0)
            cr.line_to(r_pt * math.cos(ang), r_pt * math.sin(ang))
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.30)
        cr.set_line_width(0.8)
        cr.stroke()

        # 5. Central Diamond Starburst Core
        cr.arc(0, 0, max(2.5, r_inner * 0.45), 0, 2 * math.pi)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.95)
        cr.fill()

        # 6. Orbiting Stardust Particles
        if self.animated and self.timer_id is not None:
            t = time.time()
            for i in range(4):
                sparkle_angle = t * 1.5 + (i * (math.pi / 2.0))
                dist = r_outer * (0.95 + 0.15 * math.sin(t * 3.0 + i))
                sx = dist * math.cos(sparkle_angle)
                sy = dist * math.sin(sparkle_angle)
                sparkle_r = 1.4 + 0.7 * math.sin(t * 4.0 + i)
                cr.arc(sx, sy, max(0.8, sparkle_r), 0, 2 * math.pi)
                cr.set_source_rgba(0.85, 0.95, 1.0, 0.85)
                cr.fill()

        cr.restore()
        return False

# Backward compatibility alias
GeminiSparkle = MindSentinelStar

class GeminiGlowBar(Gtk.DrawingArea):
    """
    Slim horizontal flowing shimmer bar that animates while Mind Helper is thinking.
    """
    def __init__(self, height=3):
        super().__init__()
        self.bar_height = height
        self.set_size_request(-1, height)
        self.offset = 0.0
        self.is_active = False
        self.timer_id = None
        self.connect("draw", self._on_draw)

    def start(self):
        self.is_active = True
        if self.timer_id is None:
            self.timer_id = GLib.timeout_add(25, self._on_tick)

    def stop(self):
        self.is_active = False
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
        self.queue_draw()

    def _on_tick(self):
        self.offset = (self.offset + 0.02) % 1.0
        self.queue_draw()
        return self.is_active

    def _on_draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        if not self.is_active:
            pat = cairo.LinearGradient(0, 0, width, 0)
            pat.add_color_stop_rgba(0.0, 0.06, 0.72, 0.51, 0.0)
            pat.add_color_stop_rgba(0.5, 0.13, 0.77, 0.96, 0.4)
            pat.add_color_stop_rgba(1.0, 0.15, 0.39, 0.92, 0.0)
            cr.set_source(pat)
            cr.rectangle(0, 0, width, height)
            cr.fill()
            return False

        pat = cairo.LinearGradient(0, 0, width, 0)
        stops = [
            (0.0, (0.06, 0.72, 0.51)),  # Emerald #10b981
            (0.3, (0.13, 0.77, 0.96)),  # Cyan #22d3ee
            (0.6, (0.15, 0.39, 0.92)),  # Sapphire #2563eb
            (0.8, (0.18, 0.83, 0.75)),  # Mint #2dd4bf
            (1.0, (0.06, 0.72, 0.51)),  # Loop
        ]
        for base_pos, (r, g, b) in stops:
            shifted = (base_pos + self.offset) % 1.0
            pat.add_color_stop_rgba(shifted, r, g, b, 0.95)

        cr.set_source(pat)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        return False

class AuroraCanvas(Gtk.DrawingArea):
    """
    Living, undulating sinusoidal aurora background canvas with gentle stardust particles.
    """
    def __init__(self, height=136):
        super().__init__()
        self.set_size_request(-1, height)
        self.particles = []
        for _ in range(26):
            self.particles.append({
                'x': random.uniform(0.0, 1.0),
                'y': random.uniform(0.1, 0.9),
                'r': random.uniform(1.0, 2.5),
                'speed': random.uniform(0.015, 0.04),
                'twinkle_speed': random.uniform(1.8, 3.6),
                'phase': random.uniform(0, 6.28)
            })
        self.timer_id = None
        self.connect("draw", self._on_draw)
        self.start()

    def start(self):
        if self.timer_id is None:
            self.timer_id = GLib.timeout_add(33, self._on_tick)

    def stop(self):
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

    def _on_tick(self):
        self.queue_draw()
        return True

    def _on_draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        t = time.time()

        bg = cairo.LinearGradient(0, 0, w, h)
        bg.add_color_stop_rgb(0.0, 0.03, 0.05, 0.09)
        bg.add_color_stop_rgb(0.5, 0.05, 0.08, 0.16)
        bg.add_color_stop_rgb(1.0, 0.08, 0.12, 0.22)
        cr.set_source(bg)
        cr.paint()

        def draw_aurora_wave(y_mid, amp, freq, phase, r, g, b, alpha):
            cr.new_path()
            cr.move_to(0, h)
            cr.line_to(0, y_mid)
            steps = 22
            dx = w / steps
            for i in range(steps + 1):
                x = i * dx
                y = y_mid + amp * math.sin(x * freq + phase)
                cr.line_to(x, y)
            cr.line_to(w, h)
            cr.close_path()

            grad = cairo.LinearGradient(0, max(0, y_mid - amp), 0, h)
            grad.add_color_stop_rgba(0.0, r, g, b, alpha)
            grad.add_color_stop_rgba(0.5, r, g, b, alpha * 0.45)
            grad.add_color_stop_rgba(1.0, r, g, b, 0.0)
            cr.set_source(grad)
            cr.fill()

        # Waves in Emerald, Cyan, and Sapphire
        draw_aurora_wave(h * 0.42, h * 0.22, 0.005, t * 0.65, 0.06, 0.72, 0.51, 0.32)
        draw_aurora_wave(h * 0.54, h * 0.26, 0.004, -t * 0.50 + 1.2, 0.13, 0.77, 0.96, 0.28)
        draw_aurora_wave(h * 0.66, h * 0.19, 0.007, t * 0.95 + 2.5, 0.15, 0.39, 0.92, 0.22)

        for p in self.particles:
            px = ((p['x'] + t * p['speed'] * 0.04) % 1.0) * w
            py = p['y'] * h
            twinkle = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * p['twinkle_speed'] + p['phase']))

            cr.arc(px, py, p['r'] * 1.8, 0, 2 * math.pi)
            cr.set_source_rgba(0.4, 0.85, 0.7, twinkle * 0.25)
            cr.fill()

            cr.arc(px, py, p['r'], 0, 2 * math.pi)
            cr.set_source_rgba(0.95, 0.98, 1.0, twinkle * 0.9)
            cr.fill()

        cr.move_to(0, h - 1)
        cr.line_to(w, h - 1)
        line_pat = cairo.LinearGradient(0, 0, w, 0)
        line_pat.add_color_stop_rgba(0.0, 0.06, 0.72, 0.51, 0.1)
        line_pat.add_color_stop_rgba(0.5, 0.13, 0.77, 0.96, 0.45)
        line_pat.add_color_stop_rgba(1.0, 0.15, 0.39, 0.92, 0.1)
        cr.set_source(line_pat)
        cr.set_line_width(1.0)
        cr.stroke()

        return False

class PixelAuroraBanner(Gtk.Overlay):
    """
    Google Pixel / My Pixel inspired Hero Header.
    Features MindSentinelStar 8-point crystal star instead of Google Gemini.
    """
    def __init__(self):
        super().__init__()
        self.canvas = AuroraCanvas(height=136)
        self.add(self.canvas)

        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        content_box.set_margin_left(22)
        content_box.set_margin_right(22)
        content_box.set_margin_top(18)
        content_box.set_margin_bottom(18)

        # 8-Point Faceted Crystal Diamond Star
        self.star = MindSentinelStar(size=46, animated=True)
        content_box.pack_start(self.star, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.greeting_label = Gtk.Label()
        self.greeting_label.set_markup(self._get_time_greeting())
        self.greeting_label.set_xalign(0)
        vbox.pack_start(self.greeting_label, False, False, 0)

        subtitle_lbl = Gtk.Label()
        subtitle_lbl.set_markup("<span class='brand-subtitle'>MindOS Synthetic Sentinel • Linux Intelligence &amp; Companion</span>")
        subtitle_lbl.set_xalign(0)
        vbox.pack_start(subtitle_lbl, False, False, 0)
        content_box.pack_start(vbox, True, True, 0)

        badges_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        badges_box.set_valign(Gtk.Align.CENTER)

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.ram_badge = Gtk.Label(label="🧠 RAM: --")
        self.ram_badge.get_style_context().add_class("telemetry-pill")
        top_row.pack_start(self.ram_badge, False, False, 0)

        self.uptime_badge = Gtk.Label(label="⚡ Silicon: Nominal")
        self.uptime_badge.get_style_context().add_class("uptime-badge")
        top_row.pack_start(self.uptime_badge, False, False, 0)
        badges_box.pack_start(top_row, False, False, 0)

        self.weather_badge = Gtk.Label(label="⛅ Atmosphere: Probing...")
        self.weather_badge.get_style_context().add_class("weather-badge")
        badges_box.pack_start(self.weather_badge, False, False, 0)

        content_box.pack_start(badges_box, False, False, 0)

        self.add_overlay(content_box)
        self.show_all()

    def _get_time_greeting(self) -> str:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            greet = "Good Morning, Explorer ✧"
        elif 12 <= hour < 18:
            greet = "Good Afternoon, Navigator ✧"
        elif 18 <= hour < 23:
            greet = "Good Evening, Voyager ✧"
        else:
            greet = "Night Sentinel Synchronized ✧"
        return f"<span class='brand-title'>{greet}</span>"

    def update_telemetry(self, ram_text: str, uptime_text: str, weather_text: str):
        self.ram_badge.set_text(f"🧠 {ram_text}")
        self.uptime_badge.set_text(f"⚡ {uptime_text}")
        self.weather_badge.set_text(f"⛅ {weather_text}")
