#!/usr/bin/env python3
"""
Mind Helper — Standalone Application (Material You / Google Pixel Edition)
The comprehensive interactive portal for Mind Helper on MindOS Paradise.
Features:
1. PixelAuroraBanner: Living Cairo aurora canvas with floating star constellations.
2. Ask Mind Helper: Intelligent Linux question bar with Discovery Cards and Gemini glow bar.
3. Linux Academy: Comprehensive, searchable tutorial grimoire.
4. Developer Feedback: 24-hour rate-limited, AI-inspected feedback portal.
"""

import os
import subprocess
import sys
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

from gemini_anim import GeminiSparkle, GeminiGlowBar, PixelAuroraBanner
from ai_brain import MindHelperBrain
from system_facts import get_live_telemetry, get_chilling_fact
from weather import get_atmospheric_status
from tutorials import TUTORIALS, search_tutorials
from feedback import check_rate_limit, submit_feedback

class MindHelperApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Mind Helper")
        self.set_wmclass("mindhelper", "mindhelper")
        self.set_role("mindhelper")
        self.set_default_icon_name("mindhelper")
        self.set_icon_name("mindhelper")

        self.set_default_size(960, 720)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.brain = MindHelperBrain()
        self.connect("destroy", Gtk.main_quit)
        self._load_css()
        self._setup_icon()
        self._build_ui()
        self._start_telemetry_loop()
        GLib.idle_add(self._ask_privacy_once)

    def _ask_privacy_once(self):
        """İnternete kişisel veri gönderen özellikler için bir kez açık onay ister (varsayılan kapalı)"""
        try:
            import mindos_prefs
        except Exception:
            return False
        if mindos_prefs.is_set("weather") and mindos_prefs.is_set("web_search"):
            return False
        tr = os.environ.get("LANG", "").startswith("tr")
        dialog = Gtk.Dialog(title="Gizlilik" if tr else "Privacy", transient_for=self, modal=True)
        dialog.add_button("Kaydet" if tr else "Save", Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(10)
        for side in ("left", "right", "top", "bottom"):
            getattr(box, f"set_margin_{side}")(18)
        intro = Gtk.Label(label=(
            "Mind Helper'ın bazı özellikleri internete bilgi gönderir. Hangilerini açmak istediğinizi seçin; "
            "daha sonra Mind Arc → Genel Ayarlar → Gizlilik'ten değiştirebilirsiniz." if tr else
            "Some Mind Helper features send data over the internet. Choose which ones to turn on; you can "
            "change this later in Mind Arc → General Settings → Privacy."))
        intro.set_line_wrap(True)
        intro.set_xalign(0)
        intro.set_max_width_chars(60)
        box.pack_start(intro, False, False, 0)
        weather = Gtk.CheckButton(label=(
            "Hava durumu: konumunuz IP adresinizden wttr.in tarafından tahmin edilir" if tr else
            "Weather: wttr.in estimates your location from your IP address"))
        search = Gtk.CheckButton(label=(
            "İnternette arama: yanıtı bilinmeyen sorularınız DuckDuckGo'ya gönderilir" if tr else
            "Web search: questions Mind Helper cannot answer are sent to DuckDuckGo"))
        weather.set_active(mindos_prefs.get("weather"))
        search.set_active(mindos_prefs.get("web_search"))
        box.pack_start(weather, False, False, 0)
        box.pack_start(search, False, False, 0)
        dialog.show_all()
        dialog.run()
        mindos_prefs.set("weather", weather.get_active())
        mindos_prefs.set("web_search", search.get_active())
        dialog.destroy()
        return False

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

    def _setup_icon(self):
        self.set_icon_name("mindhelper")
        for candidate in ["mindhelper.png", "mindhelper.svg", "D12logo.png"]:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", candidate)
            if os.path.exists(icon_path):
                try:
                    self.set_icon_from_file(icon_path)
                    return
                except Exception:
                    pass
        for fallback in [
            "/usr/share/mindhelper/assets/mindhelper.png",
            "/usr/share/mindhelper/assets/mindhelper.svg",
            "/usr/share/icons/hicolor/scalable/apps/mindhelper.svg",
            "/usr/share/icons/hicolor/512x512/apps/mindhelper.png"
        ]:
            if os.path.exists(fallback):
                try:
                    self.set_icon_from_file(fallback)
                    return
                except Exception:
                    pass

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.get_style_context().add_class("main-window-box")
        self.add(main_box)

        # 1. Google Pixel Living Aurora Hero Banner
        self.hero_banner = PixelAuroraBanner()
        main_box.pack_start(self.hero_banner, False, False, 0)

        # 2. Flowing Gemini Shimmer Glow Bar
        self.glow_bar = GeminiGlowBar(height=3)
        main_box.pack_start(self.glow_bar, False, False, 0)

        # 3. Main Navigation Notebook (Pixel Pill Segmented Control)
        self.notebook = Gtk.Notebook()
        main_box.pack_start(self.notebook, True, True, 0)

        # Tab 1: Ask Mind Helper
        self.chat_tab = self._build_chat_tab()
        tab1_label = Gtk.Label(label="✧ Linux AI")
        self.notebook.append_page(self.chat_tab, tab1_label)

        # Tab 2: Articles & Guides
        self.tutorials_tab = self._build_tutorials_tab()
        tab2_label = Gtk.Label(label="📖 Articles & Guides")
        self.notebook.append_page(self.tutorials_tab, tab2_label)

        # Tab 3: Developer Feedback
        self.feedback_tab = self._build_feedback_tab()
        tab3_label = Gtk.Label(label="✉ Developer Feedback")
        self.notebook.append_page(self.feedback_tab, tab3_label)

    # --------------------------------------------------------------------------
    # Tab 1: Ask Mind Helper (Chat & Inquiry Interface)
    # --------------------------------------------------------------------------
    def _build_chat_tab(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.set_margin_left(20)
        container.set_margin_right(20)
        container.set_margin_top(12)
        container.set_margin_bottom(14)

        # System telemetry & insights banner
        self.welcome_banner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.welcome_banner.get_style_context().add_class("chilling-quote-box")
        w_title = Gtk.Label(label="✧ System Telemetry & Insights")
        w_title.get_style_context().add_class("stat-label")
        w_title.set_xalign(0)
        self.welcome_banner.pack_start(w_title, False, False, 0)

        self.welcome_text = Gtk.Label()
        self.welcome_text.set_line_wrap(True)
        self.welcome_text.set_xalign(0)
        self.welcome_text.set_text(get_chilling_fact())
        self.welcome_banner.pack_start(self.welcome_text, False, False, 0)
        container.pack_start(self.welcome_banner, False, False, 0)

        # Pixel Discovery Cards (4-column interactive cards)
        cards_grid = Gtk.Grid()
        cards_grid.set_column_spacing(10)
        cards_grid.set_row_spacing(8)
        cards_grid.set_column_homogeneous(True)

        tips = [
            ("⚡", "System Vitals", "Live RAM & silicon telemetry", "How much memory and CPU is currently being used by the system?"),
            ("🛡️", "Permission Rites", "Master chmod & chown bounds", "Explain Linux file permissions, chmod 755 vs 644, and chown"),
            ("⚙️", "Service Control", "systemctl & daemon mastery", "How do I control system services with systemctl status, start, and restart?"),
            ("🌐", "Network Ports", "Scan open sockets with ss", "How do I discover open ports and listening sockets using ss and netstat?"),
            ("📦", "mindpkg", "Tek komutla uygulama kur", "mindpkg ile nasıl uygulama kurarım?"),
            ("🧭", "Paket Merkezi", "Mind-Arc'ta tek tıkla kur", None),
        ]

        for idx, (icon, title, desc, query) in enumerate(tips):
            card = Gtk.Button()
            card.get_style_context().add_class("discovery-card")
            card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

            i_lbl = Gtk.Label(label=icon)
            i_lbl.get_style_context().add_class("discovery-icon")
            i_lbl.set_xalign(0)
            card_box.pack_start(i_lbl, False, False, 0)

            t_lbl = Gtk.Label(label=title)
            t_lbl.get_style_context().add_class("discovery-title")
            t_lbl.set_xalign(0)
            card_box.pack_start(t_lbl, False, False, 0)

            d_lbl = Gtk.Label(label=desc)
            d_lbl.get_style_context().add_class("discovery-desc")
            d_lbl.set_xalign(0)
            card_box.pack_start(d_lbl, False, False, 0)

            card.add(card_box)
            if query is None:
                # Mind-Arc Paket Merkezi'ni doğrudan aç
                card.connect("clicked", lambda b: subprocess.Popen(["mind-arc", "--page", "packages"]))
            else:
                card.connect("clicked", lambda b, q=query: self._submit_prompt(q))
            cards_grid.attach(card, idx % 3, idx // 3, 1, 1)

        container.pack_start(cards_grid, False, False, 0)

        # Scrollable Chat History
        chat_scroll = Gtk.ScrolledWindow()
        chat_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        chat_scroll.get_style_context().add_class("chat-scroll-area")

        self.chat_history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.chat_history_box.set_margin_top(8)
        self.chat_history_box.set_margin_bottom(8)
        chat_scroll.add(self.chat_history_box)
        container.pack_start(chat_scroll, True, True, 0)

        # Initial Bot Greeting in Chat
        self._add_bot_bubble(
            "Welcome to Mind Helper.\n\n"
            "Ask me anything regarding Linux administration, terminal commands, "
            "package management, or system performance. You can also explore the Articles tab for comprehensive guides.\n\n"
            "Uygulama kurmak için: sudo mindpkg install <paket>  (ör. chrome, vscode, vlc)"
        )

        # Bottom Prompt Capsule
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.prompt_entry = Gtk.Entry()
        self.prompt_entry.set_placeholder_text("Ask Mind Helper to explain, teach, or diagnose any Linux topic...")
        self.prompt_entry.get_style_context().add_class("prompt-entry")
        self.prompt_entry.connect("activate", lambda e: self._on_send_prompt())
        bottom_bar.pack_start(self.prompt_entry, True, True, 0)

        send_btn = Gtk.Button(label="✧ Ask")
        send_btn.get_style_context().add_class("btn-gemini-sparkle")
        send_btn.connect("clicked", lambda b: self._on_send_prompt())
        bottom_bar.pack_start(send_btn, False, False, 0)

        container.pack_start(bottom_bar, False, False, 0)
        return container

    def _on_send_prompt(self):
        text = self.prompt_entry.get_text().strip()
        if not text:
            return
        self.prompt_entry.set_text("")
        self._submit_prompt(text)

    def _submit_prompt(self, query: str):
        self._add_user_bubble(query)
        self.glow_bar.start()

        # Add thinking indicator
        thinking_bubble = self._add_bot_bubble("✧ Mind Helper is analyzing the kernel and silicon ether...")

        def worker():
            answer = self.brain.answer_query(query)
            GLib.idle_add(lambda: self._finish_prompt(thinking_bubble, answer))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_prompt(self, thinking_bubble, answer: str):
        self.glow_bar.stop()
        thinking_bubble.set_text(answer)

    def _add_user_bubble(self, text: str):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label=text)
        lbl.set_line_wrap(True)
        lbl.get_style_context().add_class("user-bubble")
        box.pack_end(lbl, False, False, 0)
        self.chat_history_box.pack_start(box, False, False, 0)
        box.show_all()

    def _add_bot_bubble(self, text: str) -> Gtk.Label:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl = Gtk.Label(label=text)
        lbl.set_line_wrap(True)
        lbl.set_selectable(True)
        lbl.get_style_context().add_class("ai-bubble")
        box.pack_start(lbl, True, True, 0)
        self.chat_history_box.pack_start(box, False, False, 0)
        box.show_all()
        return lbl

    # --------------------------------------------------------------------------
    # Tab 2: Linux Academy (Tutorial Texts)
    # --------------------------------------------------------------------------
    def _build_tutorials_tab(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        container.set_margin_left(20)
        container.set_margin_right(20)
        container.set_margin_top(12)
        container.set_margin_bottom(14)

        # Search Bar Capsule
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.tut_search_entry = Gtk.Entry()
        self.tut_search_entry.set_placeholder_text("Search Linux tutorials (e.g. systemd, chmod, memory, network)...")
        self.tut_search_entry.get_style_context().add_class("prompt-entry")
        self.tut_search_entry.connect("changed", self._on_tut_search_changed)
        search_box.pack_start(self.tut_search_entry, True, True, 0)
        container.pack_start(search_box, False, False, 0)

        # Paned Master-Detail Layout
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(330)
        container.pack_start(paned, True, True, 0)

        # Left: Tutorial List
        left_scroll = Gtk.ScrolledWindow()
        left_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.tut_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left_scroll.add(self.tut_list_box)
        paned.pack1(left_scroll, resize=False, shrink=False)

        # Right: Reader Area
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_box.set_margin_left(16)

        reader_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.reader_cat_lbl = Gtk.Label(label="Category")
        self.reader_cat_lbl.get_style_context().add_class("telemetry-pill")
        reader_header.pack_start(self.reader_cat_lbl, False, False, 0)

        self.reader_time_lbl = Gtk.Label(label="5 min read")
        self.reader_time_lbl.get_style_context().add_class("weather-badge")
        reader_header.pack_start(self.reader_time_lbl, False, False, 0)

        ask_about_btn = Gtk.Button(label="✧ Ask Mind Helper About This")
        ask_about_btn.get_style_context().add_class("btn-gemini-sparkle")
        ask_about_btn.connect("clicked", self._on_ask_about_current_tutorial)
        reader_header.pack_end(ask_about_btn, False, False, 0)
        right_box.pack_start(reader_header, False, False, 0)

        self.reader_title_lbl = Gtk.Label()
        self.reader_title_lbl.set_xalign(0)
        right_box.pack_start(self.reader_title_lbl, False, False, 0)

        # Scrollable Content
        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_scroll.get_style_context().add_class("chat-scroll-area")

        self.reader_content_lbl = Gtk.Label()
        self.reader_content_lbl.set_xalign(0)
        self.reader_content_lbl.set_line_wrap(True)
        self.reader_content_lbl.set_selectable(True)
        self.reader_content_lbl.set_margin_left(16)
        self.reader_content_lbl.set_margin_right(16)
        self.reader_content_lbl.set_margin_top(12)
        self.reader_content_lbl.set_margin_bottom(12)
        content_scroll.add(self.reader_content_lbl)
        right_box.pack_start(content_scroll, True, True, 0)

        paned.pack2(right_box, resize=True, shrink=False)

        self.active_tutorial = None
        self._populate_tutorial_list(TUTORIALS)
        if TUTORIALS:
            self._display_tutorial(TUTORIALS[0])

        return container

    def _populate_tutorial_list(self, tutorials):
        for child in self.tut_list_box.get_children():
            self.tut_list_box.remove(child)

        for tut in tutorials:
            card = Gtk.Button()
            card.get_style_context().add_class("tutorial-item-card")

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            c_lbl = Gtk.Label(label=tut["category"])
            c_lbl.get_style_context().add_class("tutorial-category")
            c_lbl.set_xalign(0)
            vbox.pack_start(c_lbl, False, False, 0)

            t_lbl = Gtk.Label(label=tut["title"])
            t_lbl.get_style_context().add_class("tutorial-title")
            t_lbl.set_line_wrap(True)
            t_lbl.set_xalign(0)
            vbox.pack_start(t_lbl, False, False, 0)

            time_lbl = Gtk.Label(label=f"⏱ {tut['read_time']}")
            time_lbl.get_style_context().add_class("tutorial-time")
            time_lbl.set_xalign(0)
            vbox.pack_start(time_lbl, False, False, 0)

            card.add(vbox)
            card.connect("clicked", lambda b, t=tut: self._display_tutorial(t))
            self.tut_list_box.pack_start(card, False, False, 0)

        self.tut_list_box.show_all()

    def _on_tut_search_changed(self, entry):
        query = entry.get_text()
        filtered = search_tutorials(query)
        self._populate_tutorial_list(filtered)

    def _display_tutorial(self, tut):
        self.active_tutorial = tut
        self.reader_cat_lbl.set_text(tut["category"])
        self.reader_time_lbl.set_text(tut["read_time"])
        self.reader_title_lbl.set_markup(f"<span size='large' weight='bold' color='#38bdf8'>{GLib.markup_escape_text(tut['title'])}</span>")
        self.reader_content_lbl.set_text(tut["content"])

    def _on_ask_about_current_tutorial(self, button):
        if self.active_tutorial:
            q = f"Teach me more about {self.active_tutorial['title']}"
            self.notebook.set_current_page(0)
            self._submit_prompt(q)

    # --------------------------------------------------------------------------
    # Tab 3: Developer Feedback (24h rate limit, AI inspected, hidden dev mail)
    # --------------------------------------------------------------------------
    def _build_feedback_tab(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        container.set_margin_left(24)
        container.set_margin_right(24)
        container.set_margin_top(16)
        container.set_margin_bottom(16)

        # Rate Limit Status Card
        self.feedback_status_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.feedback_status_card.get_style_context().add_class("ready-alert")

        self.feedback_status_lbl = Gtk.Label()
        self.feedback_status_lbl.set_line_wrap(True)
        self.feedback_status_lbl.set_xalign(0)
        self.feedback_status_card.pack_start(self.feedback_status_lbl, False, False, 0)
        container.pack_start(self.feedback_status_card, False, False, 0)

        # Form Card
        form_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form_card.get_style_context().add_class("feedback-card")

        # Category and Alias Row
        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        cat_lbl = Gtk.Label(label="Communion Category")
        cat_lbl.get_style_context().add_class("stat-label")
        cat_lbl.set_xalign(0)
        cat_box.pack_start(cat_lbl, False, False, 0)

        self.category_combo = Gtk.ComboBoxText()
        self.category_combo.append_text("Suggestion / Idea")
        self.category_combo.append_text("Bug / System Glitch")
        self.category_combo.append_text("Praise / Thought")
        self.category_combo.append_text("Linux Topic Request")
        self.category_combo.set_active(0)
        cat_box.pack_start(self.category_combo, False, False, 0)
        row1.pack_start(cat_box, True, True, 0)

        alias_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        alias_lbl = Gtk.Label(label="Sender Identity (Optional)")
        alias_lbl.get_style_context().add_class("stat-label")
        alias_lbl.set_xalign(0)
        alias_box.pack_start(alias_lbl, False, False, 0)

        self.alias_entry = Gtk.Entry()
        self.alias_entry.set_placeholder_text("Your mortal alias or callsign")
        self.alias_entry.get_style_context().add_class("prompt-entry")
        alias_box.pack_start(self.alias_entry, True, True, 0)
        row1.pack_start(alias_box, True, True, 0)

        form_card.pack_start(row1, False, False, 0)

        # Subject
        sub_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sub_lbl = Gtk.Label(label="Summary / Subject")
        sub_lbl.get_style_context().add_class("stat-label")
        sub_lbl.set_xalign(0)
        sub_box.pack_start(sub_lbl, False, False, 0)

        self.subject_entry = Gtk.Entry()
        self.subject_entry.set_placeholder_text("Clear, concise subject of your communion")
        self.subject_entry.get_style_context().add_class("prompt-entry")
        sub_box.pack_start(self.subject_entry, False, False, 0)
        form_card.pack_start(sub_box, False, False, 0)

        # Message Body
        body_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        body_lbl = Gtk.Label(label="Feedback Substance (Inspected by Mind Helper)")
        body_lbl.get_style_context().add_class("stat-label")
        body_lbl.set_xalign(0)
        body_box.pack_start(body_lbl, False, False, 0)

        body_scroll = Gtk.ScrolledWindow()
        body_scroll.set_min_content_height(140)
        body_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.body_view = Gtk.TextView()
        self.body_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.body_view.get_style_context().add_class("prompt-entry")
        body_scroll.add(self.body_view)
        body_box.pack_start(body_scroll, True, True, 0)
        form_card.pack_start(body_box, True, True, 0)

        # Privacy: what is sent and where (KVKK/GDPR)
        tr = os.environ.get("LANG", "").startswith("tr")
        self.include_system_chk = Gtk.CheckButton(
            label="Sistem bilgilerini ekle (işletim sistemi, kernel, çalışma süresi, RAM)" if tr
            else "Include system info (OS, kernel, uptime, RAM)")
        self.include_system_chk.set_active(False)
        form_card.pack_start(self.include_system_chk, False, False, 0)
        privacy_lbl = Gtk.Label(
            label=("Mesajınız ve takma adınız formsubmit.co aracılığıyla MindOS geliştiricisinin e-posta "
                   "kutusuna iletilir. Başka hiçbir bilgi gönderilmez." if tr else
                   "Your message and alias are relayed through formsubmit.co to the MindOS developer's "
                   "mailbox. Nothing else is sent."))
        privacy_lbl.set_line_wrap(True)
        privacy_lbl.set_xalign(0)
        privacy_lbl.get_style_context().add_class("stat-label")
        form_card.pack_start(privacy_lbl, False, False, 0)

        # Submit Action
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.submit_btn = Gtk.Button(label="✧ Transmit Communion to Developer")
        self.submit_btn.get_style_context().add_class("btn-gemini-sparkle")
        self.submit_btn.connect("clicked", self._on_submit_feedback)
        action_bar.pack_start(self.submit_btn, False, False, 0)

        form_card.pack_start(action_bar, False, False, 0)
        container.pack_start(form_card, True, True, 0)

        self._refresh_feedback_rate_limit()
        return container

    def _refresh_feedback_rate_limit(self):
        can_submit, msg, _ = check_rate_limit()
        if can_submit:
            self.feedback_status_card.get_style_context().remove_class("cooldown-alert")
            self.feedback_status_card.get_style_context().add_class("ready-alert")
            self.feedback_status_lbl.set_markup(
                f"<span weight='bold'>✧ Daily Communion Open:</span> {msg} "
                "Mind Helper will inspect your feedback for appropriateness before forwarding directly to the developer."
            )
            self.submit_btn.set_sensitive(True)
        else:
            self.feedback_status_card.get_style_context().remove_class("ready-alert")
            self.feedback_status_card.get_style_context().add_class("cooldown-alert")
            self.feedback_status_lbl.set_markup(
                f"<span weight='bold'>⏳ Communion Window Sealed:</span> {msg}"
            )
            self.submit_btn.set_sensitive(False)

    def _on_submit_feedback(self, button):
        category = self.category_combo.get_active_text() or "General"
        alias = self.alias_entry.get_text().strip()
        subject = self.subject_entry.get_text().strip()

        buf = self.body_view.get_buffer()
        start, end = buf.get_bounds()
        message = buf.get_text(start, end, True).strip()

        if not subject or not message:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Incomplete Communion"
            )
            dialog.format_secondary_text("Please provide both a subject and substantive message.")
            dialog.run()
            dialog.destroy()
            return

        include_system = self.include_system_chk.get_active()
        self.submit_btn.set_sensitive(False)
        self.glow_bar.start()

        def worker():
            success, response_msg = submit_feedback(category, subject, message, alias, include_system)
            GLib.idle_add(lambda: self._finish_feedback_submission(success, response_msg))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_feedback_submission(self, success: bool, msg: str):
        self.glow_bar.stop()
        self._refresh_feedback_rate_limit()

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO if success else Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Communion Dispatched" if success else "Communion Declined"
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()

        if success:
            self.subject_entry.set_text("")
            self.body_view.get_buffer().set_text("")

    # --------------------------------------------------------------------------
    # Telemetry Background Refresh
    # --------------------------------------------------------------------------
    def _start_telemetry_loop(self):
        self._update_telemetry()
        GLib.timeout_add_seconds(4, self._update_telemetry)

    def _update_telemetry(self):
        try:
            t = get_live_telemetry()
            ram_str = f"RAM: {t['mem_used_gb']}G / {t['mem_total_gb']}G ({t['mem_percent']}%)"
            uptime_str = f"Uptime: {t['uptime_str']}"

            def weather_worker():
                w = get_atmospheric_status()
                if w["available"]:
                    weather_str = f"{w['temp_c']}°C • {w['condition']}"
                else:
                    weather_str = "Void Synchronized"
                GLib.idle_add(lambda: self.hero_banner.update_telemetry(ram_str, uptime_str, weather_str))

            threading.Thread(target=weather_worker, daemon=True).start()
        except Exception:
            pass
        return True

if __name__ == "__main__":
    app = MindHelperApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
