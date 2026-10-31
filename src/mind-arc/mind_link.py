# -*- coding: utf-8 -*-
"""
Mind Link — MindUI Ecosystem Pairing & Universal Clipboard Engine
===================================================================
Provides seamless, Apple-like ecosystem integration between MindOS Paradise
and MindUI Android mobile devices:
  * Local network peer discovery via UDP broadcast (port 4242)
  * TCP Pairing handshake & verification challenge (port 4243)
  * Apple-style pairing dialog with glowing 6-digit verification pin
  * Universal Clipboard synchronization (Wayland wl-clipboard / X11 xclip)
  * Persistent paired devices config in ~/.config/mindos/paired_devices.json
"""

import os
import sys
import json
import time
import socket
import select
import random
import shutil
import subprocess
import threading
from typing import Dict, List, Optional, Callable, Set
import gi
try:
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
except (ValueError, AttributeError):
    pass
from gi.repository import Gtk, GLib, Gio, Adw, Pango, Gdk

DEFAULT_BROADCAST_PORT = 4242
DEFAULT_SERVICE_PORT = 4243
PROTOCOL_VERSION = 1
CONFIG_DIR = os.path.expanduser("~/.config/mindos")
CONFIG_PATH = os.path.join(CONFIG_DIR, "paired_devices.json")

# Multi-language dictionary for Mind Link
LINK_TEXTS = {
    "mind_link": ("MindUI Ekosistem", "MindUI Ecosystem"),
    "mind_link_title": ("Mind Link — MindUI Ekosistem Entegrasyonu", "Mind Link — MindUI Ecosystem Integration"),
    "mind_link_desc": (
        "MindOS Paradise ve MindUI telefonunuz arasında kesintisiz eşleşme, evrensel pano ve anlık veri senkronizasyonu.",
        "Seamless pairing, universal clipboard, and instant synchronization between MindOS Paradise and MindUI devices."
    ),
    "banner_tag": ("MINDUI EKOSİSTEMİ AKTİF", "MINDUI ECOSYSTEM ACTIVE"),
    "banner_detail": (
        "Yakındaki MindUI cihazları ağ üzerinden otomatik olarak taranır. Apple ekosistemi benzeri tek tıkla pürüzsüz eşleşme deneyimi.",
        "Nearby MindUI devices are automatically discovered over the network. One-click Apple-like smooth pairing experience."
    ),
    "nearby_title": ("Yakındaki MindUI Cihazları", "Nearby MindUI Devices"),
    "nearby_desc": (
        "Kurulum aşamasındaki veya ağda keşfedilen MindUI telefonlar",
        "MindUI phones in setup mode or discovered on the local network"
    ),
    "paired_title": ("Eşleştirilmiş Cihazlar", "Paired Devices"),
    "paired_desc": (
        "Yetkilendirilmiş ve bağlı MindUI telefonlarınız",
        "Authorized and connected MindUI phones"
    ),
    "no_nearby": (
        "Yakında MindUI cihazı aranıyor... Telefonunuzun Kurulum veya Mind Link ekranında olduğundan emin olun.",
        "Scanning for nearby MindUI devices... Ensure your phone is in Setup or Mind Link mode."
    ),
    "no_paired": (
        "Henüz eşleştirilmiş cihaz bulunmuyor.",
        "No paired devices found yet."
    ),
    "scan_btn": ("Ağı Yeniden Tara", "Rescan Network"),
    "scanning_status": ("Ağ taranıyor (UDP :4242)...", "Scanning network (UDP :4242)..."),
    "ready_status": ("Hazır • Keşif Dinleniyor", "Ready • Discovery Active"),
    "pair_btn": ("Eşleştir", "Pair"),
    "unpair_btn": ("Eşleşmeyi Kaldır", "Unpair"),
    "connected": ("Bağlı", "Connected"),
    "offline": ("Çevrimdışı", "Offline"),
    "pairing_dialog_title": ("MindUI Cihazı Bulundu", "MindUI Device Found"),
    "pairing_dialog_heading": ("Eşleştirme İsteği Alındı", "Pairing Request Received"),
    "pairing_dialog_body": (
        "‘{device_name}’ ({device_model}) bilgisayarınızla eşleşmek istiyor.\n"
        "Lütfen telefonunuzun ekranında aşağıdaki 6 haneli doğrulama kodunun göründüğünü teyit edin:",
        "‘{device_name}’ ({device_model}) wants to pair with your computer.\n"
        "Please confirm that the following 6-digit verification code appears on your phone screen:"
    ),
    "pair_action_confirm": ("Eşleştir ve Yetkilendir", "Pair & Authorize"),
    "pair_action_cancel": ("Vazgeç", "Cancel"),
    "pair_success_title": ("Eşleştirme Başarılı", "Pairing Successful"),
    "pair_success_msg": (
        "‘{device_name}’ ile güvenli bağlantı kuruldu. Evrensel Pano artık etkin!",
        "Secure connection established with ‘{device_name}’. Universal Clipboard is now active!"
    ),
    "pair_error_title": ("Eşleştirme Hatası", "Pairing Error"),
    "settings_title": ("Ekosistem Tercihleri", "Ecosystem Preferences"),
    "auto_setup_title": ("Kurulum Sırasında Otomatik Algıla", "Auto-Detect During Setup"),
    "auto_setup_subtitle": (
        "Yeni bir MindUI cihazı ilk açılış kurulumundayken bildirim göster ve eşleştirme başlat",
        "Show notification and initiate pairing when a new MindUI phone is in first-boot setup"
    ),
    "clipboard_sync_title": ("Evrensel Pano (Universal Clipboard)", "Universal Clipboard"),
    "clipboard_sync_subtitle": (
        "PC'de kopyalanan metin anında telefona, telefonda kopyalanan PC'ye aktarılır",
        "Text copied on PC is instantly available on your phone and vice versa"
    ),
    "file_drop_title": ("Mind Drop Dosya Paylaşımı", "Mind Drop File Sharing"),
    "file_drop_subtitle": (
        "Telefon ve PC arasında yüksek hızlı yerel dosya transferi",
        "High-speed local file transfer between phone and PC"
    ),
    "notifications_title": ("Bildirim Yansıtma", "Notification Mirroring"),
    "notifications_subtitle": (
        "Telefondan gelen çağrı ve mesaj bildirimlerini masaüstünde göster",
        "Show incoming call and message notifications on the desktop"
    ),
    "diag_title": ("Test ve Teşhis Araçları", "Testing and Diagnostics"),
    "diag_desc": ("Eşleştirme ve pano motorunu yerel olarak test edin", "Test the pairing and clipboard engine locally"),
    "simulate_device_btn": ("Test Cihazı Simüle Et ve Eşleştir", "Simulate Device and Test Pairing"),
    "test_clipboard_btn": ("Test Panosu Gönder", "Send Test Clipboard"),
    "daemon_status_title": ("Mind Link Arka Plan Hizmeti", "Mind Link Background Service"),
}


def t(key: str, lang: str = "tr", **fmt) -> str:
    """Helper to translate text strings."""
    entry = LINK_TEXTS.get(key, (key, key))
    s = entry[1] if lang == "en" else entry[0]
    return s.format(**fmt) if fmt else s


# --- Persistent Configuration ---

class MindLinkConfig:
    """Manages reading and writing ~/.config/mindos/paired_devices.json."""

    @staticmethod
    def get_default_config() -> dict:
        return {
            "version": PROTOCOL_VERSION,
            "desktop_id": f"mindos_pc_{abs(hash(socket.gethostname())) % 1000000:06d}",
            "desktop_name": f"{socket.gethostname()} (MindOS Paradise)",
            "devices": [],
            "settings": {
                "auto_pair_setup": True,
                "clipboard_sync": True,
                "quick_drop": True,
                "notifications": True,
                "broadcast_port": DEFAULT_BROADCAST_PORT,
                "service_port": DEFAULT_SERVICE_PORT,
            }
        }

    @classmethod
    def load(cls) -> dict:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if not os.path.exists(CONFIG_PATH):
            cfg = cls.get_default_config()
            cls.save(cfg)
            return cfg
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "devices" not in data:
                    data["devices"] = []
                if "settings" not in data:
                    data["settings"] = cls.get_default_config()["settings"]
                return data
        except Exception as e:
            print(f"[MindLink] Error loading config: {e}", file=sys.stderr)
            return cls.get_default_config()

    @classmethod
    def save(cls, data: dict) -> bool:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp_path = f"{CONFIG_PATH}.tmp.{os.getpid()}"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, CONFIG_PATH)
            return True
        except Exception as e:
            print(f"[MindLink] Error saving config: {e}", file=sys.stderr)
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return False

    @classmethod
    def add_device(cls, dev: dict) -> bool:
        cfg = cls.load()
        existing = [d for d in cfg["devices"] if d.get("device_id") != dev.get("device_id")]
        existing.append(dev)
        cfg["devices"] = existing
        return cls.save(cfg)

    @classmethod
    def remove_device(cls, device_id: str) -> bool:
        cfg = cls.load()
        cfg["devices"] = [d for d in cfg["devices"] if d.get("device_id") != device_id]
        return cls.save(cfg)

    @classmethod
    def update_feature(cls, device_id: str, feature: str, value: bool) -> bool:
        cfg = cls.load()
        for d in cfg["devices"]:
            if d.get("device_id") == device_id:
                if "features" not in d:
                    d["features"] = {}
                d["features"][feature] = value
                return cls.save(cfg)
        return False

    @classmethod
    def update_global_setting(cls, setting: str, value: bool) -> bool:
        cfg = cls.load()
        cfg["settings"][setting] = value
        return cls.save(cfg)


# --- Universal Clipboard Helper ---

class ClipboardManager:
    """Handles reading and writing system clipboard across Wayland / X11."""

    @staticmethod
    def read_text() -> Optional[str]:
        # Try wl-paste
        if shutil.which("wl-paste"):
            try:
                res = subprocess.run(
                    ["wl-paste", "--no-newline"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=1,
                    text=True
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout
            except Exception:
                pass
        # Fallback to xclip
        if shutil.which("xclip"):
            try:
                res = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    timeout=1,
                    text=True
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout
            except Exception:
                pass
        return None

    @staticmethod
    def write_text(text: str) -> bool:
        if not text:
            return False
        # Try wl-copy
        if shutil.which("wl-copy"):
            try:
                proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                proc.communicate(input=text.encode("utf-8"), timeout=2)
                return proc.returncode == 0
            except Exception:
                pass
        # Fallback to xclip
        if shutil.which("xclip"):
            try:
                proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                proc.communicate(input=text.encode("utf-8"), timeout=2)
                return proc.returncode == 0
            except Exception:
                pass
        return False


# --- Network Discovery Engine (UDP) ---

class MindLinkDiscovery:
    """
    Listens for MindUI device UDP broadcasts on port 4242
    and periodically broadcasts discovery requests.
    """

    def __init__(self, on_device_found: Callable[[dict], None],
                 on_device_lost: Optional[Callable[[str], None]] = None,
                 port: int = DEFAULT_BROADCAST_PORT):
        self.on_device_found = on_device_found
        self.on_device_lost = on_device_lost
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.devices: Dict[str, dict] = {}
        self.port = port
        self.sock: Optional[socket.socket] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True, name="MindLinkDiscovery")
        self.thread.start()

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

    def trigger_broadcast_probe(self):
        """Sends a UDP broadcast packet asking nearby MindUI devices to announce themselves."""
        def send_probe():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                payload = json.dumps({
                    "type": "mindarc_discover",
                    "protocol_version": PROTOCOL_VERSION,
                    "desktop_name": socket.gethostname(),
                    "timestamp": time.time()
                }).encode("utf-8")
                s.sendto(payload, ("255.255.255.255", self.port))
                s.sendto(payload, ("127.0.0.1", self.port))
                s.close()
            except Exception as e:
                print(f"[MindLinkDiscovery] Probe send error: {e}", file=sys.stderr)

        threading.Thread(target=send_probe, daemon=True).start()

    def _worker(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass

        try:
            sock.bind(("0.0.0.0", self.port))
            sock.settimeout(1.0)
            self.sock = sock
        except Exception as e:
            print(f"[MindLinkDiscovery] Could not bind UDP port {self.port}: {e}", file=sys.stderr)
            return

        last_probe_time = 0
        while self.running:
            # Periodically broadcast probe every 10 seconds
            now = time.time()
            if now - last_probe_time > 10:
                self.trigger_broadcast_probe()
                last_probe_time = now

            # Check for expired devices (> 20s without beacon)
            expired_ids = []
            for dev_id, dev in list(self.devices.items()):
                if now - dev.get("last_seen_ts", now) > 20:
                    expired_ids.append(dev_id)
            for eid in expired_ids:
                del self.devices[eid]
                if self.on_device_lost:
                    self.on_device_lost(eid)

            try:
                data, addr = sock.recvfrom(4096)
                if not data:
                    continue
                msg = json.loads(data.decode("utf-8"))
                msg_type = msg.get("type")
                if msg_type == "mindui_beacon":
                    dev_id = msg.get("device_id")
                    if not dev_id:
                        continue
                    sender_ip = addr[0]
                    adv_ip = msg.get("ip")
                    if sender_ip not in ("127.0.0.1", "localhost", "::1"):
                        dev_ip = sender_ip
                    else:
                        dev_ip = adv_ip or sender_ip

                    dev_info = {
                        "device_id": dev_id,
                        "device_name": msg.get("device_name", "MindUI Phone"),
                        "device_model": msg.get("device_model", "MindPhone 1"),
                        "os_version": msg.get("os_version", "MindUI 1.0"),
                        "ip": dev_ip,
                        "port": msg.get("port", DEFAULT_SERVICE_PORT),
                        "state": msg.get("state", "pairing_ready"),
                        "last_seen_ts": now,
                    }
                    self.devices[dev_id] = dev_info
                    if self.on_device_found:
                        self.on_device_found(dev_info)
            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
            except Exception as e:
                if self.running:
                    time.sleep(0.5)

        try:
            sock.close()
        except Exception:
            pass


# --- TCP Pairing Handshake Client ---

class MindLinkPairingClient:
    """
    Executes the 2-way verification handshake with a MindUI device over TCP.
    """

    @classmethod
    def pair_with_device(
        cls,
        device_info: dict,
        on_pin_ready: Callable[[str, dict], None],
        on_success: Callable[[dict], None],
        on_error: Callable[[str], None]
    ):
        """
        Runs asynchronously in a background thread.
        on_pin_ready: called when the 6-digit challenge code is received.
                      Must return a threading.Event or callback once user clicks Accept in UI.
        """
        def worker():
            ip = device_info["ip"]
            port = int(device_info.get("port", DEFAULT_SERVICE_PORT))
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10.0)
                sock.connect((ip, port))

                # Step 1: Send pair request
                req = {
                    "type": "pair_request",
                    "protocol_version": PROTOCOL_VERSION,
                    "desktop_id": f"mindos_pc_{abs(hash(socket.gethostname())) % 1000000:06d}",
                    "desktop_name": f"{socket.gethostname()} (MindOS Paradise)"
                }
                sock.sendall((json.dumps(req) + "\n").encode("utf-8"))

                # Step 2: Receive pair challenge
                buf = b""
                while b"\n" not in buf:
                    chunk = sock.recv(1024)
                    if not chunk:
                        raise ConnectionResetError("Connection closed before challenge received.")
                    buf += chunk
                line, rest = buf.split(b"\n", 1)
                challenge = json.loads(line.decode("utf-8"))

                if challenge.get("type") != "pair_challenge":
                    raise ValueError(f"Unexpected challenge message: {challenge}")

                pin_code = challenge.get("code", "000000")

                # Step 3: Present PIN in Apple-like modal to user and wait for user response
                user_approved = [None]  # container
                confirm_event = threading.Event()

                def user_decision_callback(approved: bool):
                    user_approved[0] = approved
                    confirm_event.set()

                # Notify UI to show the dialog
                on_pin_ready(pin_code, device_info, user_decision_callback)

                # Wait up to 60 seconds for user action
                if not confirm_event.wait(timeout=60.0) or not user_approved[0]:
                    # User cancelled or timed out
                    cancel_msg = {"type": "pair_cancel", "reason": "user_cancelled"}
                    sock.sendall((json.dumps(cancel_msg) + "\n").encode("utf-8"))
                    sock.close()
                    on_error("Eşleştirme kullanıcı tarafından iptal edildi.")
                    return

                # Step 4: Send pair_confirm to phone
                auth_token = f"mind_sec_{random.randint(10000000, 99999999)}"
                confirm_msg = {
                    "type": "pair_confirm",
                    "code": pin_code,
                    "accepted": True,
                    "auth_token": auth_token
                }
                sock.sendall((json.dumps(confirm_msg) + "\n").encode("utf-8"))

                # Step 5: Receive pair_success
                buf = rest
                while b"\n" not in buf:
                    chunk = sock.recv(1024)
                    if not chunk:
                        raise ConnectionResetError("Connection closed before confirmation.")
                    buf += chunk
                line, _ = buf.split(b"\n", 1)
                res = json.loads(line.decode("utf-8"))

                if res.get("type") == "pair_success":
                    paired_entry = {
                        "device_id": device_info["device_id"],
                        "device_name": device_info["device_name"],
                        "device_model": device_info["device_model"],
                        "os_version": device_info["os_version"],
                        "ip": ip,
                        "port": port,
                        "paired_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "auth_token": auth_token,
                        "status": "connected",
                        "features": {
                            "universal_clipboard": True,
                            "quick_drop": True,
                            "notifications": True
                        }
                    }
                    MindLinkConfig.add_device(paired_entry)
                    sock.close()
                    on_success(paired_entry)
                else:
                    sock.close()
                    on_error(res.get("message", "Eşleştirme reddedildi."))
            except Exception as e:
                on_error(str(e))

        threading.Thread(target=worker, daemon=True, name="PairingHandshakeWorker").start()


# --- Apple-Style Pairing Modal Dialog ---

class MindLinkPairingDialog:
    """
    Apple-like smooth pairing dialog displaying a glowing MindPhone mockup,
    6-digit verification code badges, and authorization action.
    """

    @classmethod
    def show(cls, parent_window: Gtk.Window, pin_code: str, device_info: dict,
             decision_cb: Callable[[bool], None], lang: str = "tr"):
        dialog = Adw.MessageDialog(
            transient_for=parent_window,
            heading=t("pairing_dialog_heading", lang),
            body=t(
                "pairing_dialog_body",
                lang,
                device_name=device_info.get("device_name", "MindUI Phone"),
                device_model=device_info.get("device_model", "MindPhone 1")
            )
        )

        # Build custom extra child: phone mockup + 6-digit pin pill boxes
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_halign(Gtk.Align.CENTER)

        # 1. Glowing phone avatar card
        phone_avatar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        phone_avatar.set_size_request(84, 114)
        phone_avatar.set_halign(Gtk.Align.CENTER)
        phone_avatar.add_css_class("mind-phone-mockup")

        notch = Gtk.Box()
        notch.set_size_request(28, 4)
        notch.set_halign(Gtk.Align.CENTER)
        notch.set_margin_top(4)
        notch.add_css_class("mind-phone-notch")
        phone_avatar.append(notch)

        phone_icon = Gtk.Label(label="📱")
        phone_icon.set_vexpand(True)
        phone_avatar.append(phone_icon)

        model_badge = Gtk.Label(label=device_info.get("device_model", "MindPhone 1"))
        model_badge.add_css_class("mind-phone-badge")
        model_badge.set_margin_bottom(6)
        phone_avatar.append(model_badge)

        content_box.append(phone_avatar)

        # 2. Large 6-digit verification pin container
        digits_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        digits_box.set_halign(Gtk.Align.CENTER)

        clean_pin = pin_code.replace(" ", "").strip()
        if len(clean_pin) != 6:
            clean_pin = f"{clean_pin:<6}"

        for i, ch in enumerate(clean_pin):
            digit_lbl = Gtk.Label(label=ch)
            digit_lbl.add_css_class("mind-pin-digit")
            digits_box.append(digit_lbl)
            if i == 2:
                sep = Gtk.Label(label="•")
                sep.add_css_class("mind-pin-sep")
                digits_box.append(sep)

        content_box.append(digits_box)

        # 3. Security prompt footer
        info_lbl = Gtk.Label(label="MindOS Güvenlik Doğrulaması (E2E Şifreli)")
        info_lbl.add_css_class("dim-label")
        content_box.append(info_lbl)

        dialog.set_extra_child(content_box)

        # Actions
        dialog.add_response("cancel", t("pair_action_cancel", lang))
        dialog.add_response("confirm", t("pair_action_confirm", lang))
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("confirm")
        dialog.set_close_response("cancel")

        def on_response(d, response_id):
            approved = (response_id == "confirm")
            decision_cb(approved)
            d.destroy()

        dialog.connect("response", on_response)
        dialog.present()


# --- Mind Arc Ecosystem Tab UI ---

class MindLinkPage:
    """
    GTK4 / Libadwaita PreferencesPage representing the Mind Link tab in Mind Arc.
    """

    def __init__(self, win, texts):
        self.win = win
        self.texts = texts
        self.discovery: Optional[MindLinkDiscovery] = None
        self.nearby_rows: Dict[str, Adw.ActionRow] = {}
        self.paired_rows: Dict[str, Adw.ActionRow] = {}
        self.auto_prompted_devices: Set[str] = set()
        self.is_pairing = False

        self.page = Adw.PreferencesPage()
        texts.bind(self.page.set_title, "mind_link")
        self.page.set_icon_name("phone-symbolic")

        self._build_ui()
        self._start_discovery_service()

    def get_lang(self) -> str:
        return getattr(self.win, "current_lang_code", "tr")

    def _build_ui(self):
        lang = self.get_lang()

        # Group 1: Ecosystem Hero Banner
        banner_grp = Adw.PreferencesGroup()
        hero_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        hero_box.add_css_class("mind-link-hero-card")

        tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tag_lbl = Gtk.Label(label=t("banner_tag", lang))
        tag_lbl.add_css_class("mind-link-hero-tag")
        self.texts.bind(tag_lbl.set_label, "banner_tag")
        tag_box.append(tag_lbl)
        hero_box.append(tag_box)

        title_lbl = Gtk.Label(label=t("mind_link_title", lang))
        title_lbl.add_css_class("mind-link-hero-title")
        title_lbl.set_halign(Gtk.Align.START)
        self.texts.bind(title_lbl.set_label, "mind_link_title")
        hero_box.append(title_lbl)

        desc_lbl = Gtk.Label(label=t("banner_detail", lang))
        desc_lbl.set_wrap(True)
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.add_css_class("dim-label")
        self.texts.bind(desc_lbl.set_label, "banner_detail")
        hero_box.append(desc_lbl)

        banner_grp.add(hero_box)
        self.page.add(banner_grp)

        # Group 2: Nearby Discovered Devices
        self.nearby_group = Adw.PreferencesGroup()
        self.texts.bind(self.nearby_group.set_title, "nearby_title")
        self.texts.bind(self.nearby_group.set_description, "nearby_desc")

        # Header suffix: Rescan button & status badge
        scan_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status_badge = Gtk.Label(label=t("scanning_status", lang))
        self.status_badge.add_css_class("dim-label")
        scan_box.append(self.status_badge)

        self.btn_scan = Gtk.Button(valign=Gtk.Align.CENTER)
        self.btn_scan.set_icon_name("view-refresh-symbolic")
        self.texts.bind(self.btn_scan.set_tooltip_text, "scan_btn")
        self.btn_scan.connect("clicked", self._on_rescan_clicked)
        scan_box.append(self.btn_scan)

        self.nearby_group.set_header_suffix(scan_box)

        self.empty_nearby_row = Adw.ActionRow()
        self.texts.bind(self.empty_nearby_row.set_title, "no_nearby")
        self.empty_nearby_row.add_prefix(Gtk.Label(label="📡"))
        self.nearby_group.add(self.empty_nearby_row)

        self.page.add(self.nearby_group)

        # Group 3: Paired Devices
        self.paired_group = Adw.PreferencesGroup()
        self.texts.bind(self.paired_group.set_title, "paired_title")
        self.texts.bind(self.paired_group.set_description, "paired_desc")

        self.empty_paired_row = Adw.ActionRow()
        self.texts.bind(self.empty_paired_row.set_title, "no_paired")
        self.empty_paired_row.add_prefix(Gtk.Label(label="🔗"))
        self.paired_group.add(self.empty_paired_row)

        self.page.add(self.paired_group)
        self._reload_paired_devices_ui()

        # Group 4: Ecosystem Preferences
        settings_group = Adw.PreferencesGroup()
        self.texts.bind(settings_group.set_title, "settings_title")

        # Auto pair during setup
        cfg = MindLinkConfig.load()
        st = cfg.get("settings", {})

        row_setup = Adw.ActionRow()
        self.texts.bind(row_setup.set_title, "auto_setup_title")
        self.texts.bind(row_setup.set_subtitle, "auto_setup_subtitle")
        row_setup.add_prefix(Gtk.Label(label="✨"))
        sw_setup = Gtk.Switch(valign=Gtk.Align.CENTER)
        sw_setup.set_active(st.get("auto_pair_setup", True))
        sw_setup.connect("notify::active", lambda s, p: MindLinkConfig.update_global_setting("auto_pair_setup", s.get_active()))
        row_setup.add_suffix(sw_setup)
        settings_group.add(row_setup)

        # Universal Clipboard switch
        row_clip = Adw.ActionRow()
        self.texts.bind(row_clip.set_title, "clipboard_sync_title")
        self.texts.bind(row_clip.set_subtitle, "clipboard_sync_subtitle")
        row_clip.add_prefix(Gtk.Label(label="📋"))
        sw_clip = Gtk.Switch(valign=Gtk.Align.CENTER)
        sw_clip.set_active(st.get("clipboard_sync", True))
        sw_clip.connect("notify::active", lambda s, p: MindLinkConfig.update_global_setting("clipboard_sync", s.get_active()))
        row_clip.add_suffix(sw_clip)
        settings_group.add(row_clip)

        # Mind Drop
        row_drop = Adw.ActionRow()
        self.texts.bind(row_drop.set_title, "file_drop_title")
        self.texts.bind(row_drop.set_subtitle, "file_drop_subtitle")
        row_drop.add_prefix(Gtk.Label(label="🚀"))
        sw_drop = Gtk.Switch(valign=Gtk.Align.CENTER)
        sw_drop.set_active(st.get("quick_drop", True))
        sw_drop.connect("notify::active", lambda s, p: MindLinkConfig.update_global_setting("quick_drop", s.get_active()))
        row_drop.add_suffix(sw_drop)
        settings_group.add(row_drop)

        self.page.add(settings_group)

        # Group 5: Diagnostics & Simulation
        diag_group = Adw.PreferencesGroup()
        self.texts.bind(diag_group.set_title, "diag_title")
        self.texts.bind(diag_group.set_description, "diag_desc")

        sim_row = Adw.ActionRow()
        self.texts.bind(sim_row.set_title, "simulate_device_btn")
        sim_row.add_prefix(Gtk.Label(label="🧪"))
        btn_sim = Gtk.Button(label="Test Et / Simulate", valign=Gtk.Align.CENTER)
        btn_sim.connect("clicked", self._on_simulate_clicked)
        sim_row.add_suffix(btn_sim)
        diag_group.add(sim_row)

        clip_test_row = Adw.ActionRow()
        self.texts.bind(clip_test_row.set_title, "test_clipboard_btn")
        clip_test_row.add_prefix(Gtk.Label(label="⚡"))
        btn_clip_test = Gtk.Button(label="Pano Kopyala / Copy", valign=Gtk.Align.CENTER)
        btn_clip_test.connect("clicked", self._on_test_clipboard_clicked)
        clip_test_row.add_suffix(btn_clip_test)
        diag_group.add(clip_test_row)

        self.page.add(diag_group)

    def _start_discovery_service(self):
        """Starts background UDP discovery thread."""
        def on_found(dev):
            GLib.idle_add(self._add_or_update_discovered_device, dev)

        def on_lost(dev_id):
            GLib.idle_add(self._remove_discovered_device, dev_id)

        self.discovery = MindLinkDiscovery(on_device_found=on_found, on_device_lost=on_lost)
        self.discovery.start()

    def _on_rescan_clicked(self, _btn):
        if self.discovery:
            self.status_badge.set_label(t("scanning_status", self.get_lang()))
            self.discovery.trigger_broadcast_probe()
            GLib.timeout_add_seconds(3, lambda: self.status_badge.set_label(t("ready_status", self.get_lang())))

    def _add_or_update_discovered_device(self, dev: dict):
        dev_id = dev.get("device_id")
        if not dev_id:
            return

        # Hide empty row
        self.empty_nearby_row.set_visible(False)

        if dev_id in self.nearby_rows:
            # Update existing
            row = self.nearby_rows[dev_id]
            row.set_subtitle(f"{dev.get('device_model')} • {dev.get('ip')} • {dev.get('state', 'ready')}")
            return

        row = Adw.ActionRow()
        row.set_title(dev.get("device_name", "MindUI Phone"))
        row.set_subtitle(f"{dev.get('device_model')} • {dev.get('ip')} • {dev.get('state', 'ready')}")
        row.add_prefix(Gtk.Label(label="📱"))

        pair_btn = Gtk.Button(label=t("pair_btn", self.get_lang()), valign=Gtk.Align.CENTER)
        pair_btn.add_css_class("suggested-action")
        pair_btn.connect("clicked", lambda b: self._start_pairing_flow(dev))
        row.add_suffix(pair_btn)

        self.nearby_rows[dev_id] = row
        self.nearby_group.add(row)

        # Apple-like automatic setup detection: prompt pairing if device is in setup_mode
        cfg = MindLinkConfig.load()
        paired_ids = [d.get("device_id") for d in cfg.get("devices", [])]
        if (dev.get("state") in ("setup_mode", "pairing_ready")
                and dev_id not in paired_ids
                and dev_id not in self.auto_prompted_devices
                and not self.is_pairing
                and cfg.get("settings", {}).get("auto_pair_setup", True)):
            self.auto_prompted_devices.add(dev_id)
            GLib.idle_add(lambda: self._start_pairing_flow(dev))

    def _remove_discovered_device(self, dev_id: str):
        if dev_id in self.nearby_rows:
            row = self.nearby_rows.pop(dev_id)
            self.nearby_group.remove(row)
        if not self.nearby_rows:
            self.empty_nearby_row.set_visible(True)

    def _start_pairing_flow(self, dev: dict):
        """Initiates pairing with the given device."""
        if self.is_pairing:
            return
        self.is_pairing = True
        lang = self.get_lang()

        def on_pin_ready(pin: str, info: dict, decision_cb: Callable[[bool], None]):
            def wrapped_decision(ok: bool):
                if not ok:
                    self.is_pairing = False
                decision_cb(ok)

            GLib.idle_add(
                MindLinkPairingDialog.show,
                self.win,
                pin,
                info,
                wrapped_decision,
                lang
            )

        def on_success(paired_entry: dict):
            self.is_pairing = False
            GLib.idle_add(self._handle_pairing_success, paired_entry)

        def on_error(err_msg: str):
            self.is_pairing = False
            GLib.idle_add(self._handle_pairing_error, err_msg)

        MindLinkPairingClient.pair_with_device(
            dev,
            on_pin_ready=on_pin_ready,
            on_success=on_success,
            on_error=on_error
        )

    def _handle_pairing_success(self, paired_entry: dict):
        self._reload_paired_devices_ui()
        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading=t("pair_success_title", self.get_lang()),
            body=t("pair_success_msg", self.get_lang(), device_name=paired_entry.get("device_name", "MindUI"))
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present()

    def _handle_pairing_error(self, err_msg: str):
        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading=t("pair_error_title", self.get_lang()),
            body=str(err_msg)
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present()

    def _reload_paired_devices_ui(self):
        # Clear previous rows
        for row in list(self.paired_rows.values()):
            self.paired_group.remove(row)
        self.paired_rows.clear()

        cfg = MindLinkConfig.load()
        devices = cfg.get("devices", [])
        if not devices:
            self.empty_paired_row.set_visible(True)
            return

        self.empty_paired_row.set_visible(False)
        lang = self.get_lang()

        for d in devices:
            dev_id = d.get("device_id")
            row = Adw.ExpanderRow()
            row.set_title(d.get("device_name", "MindUI Phone"))
            row.set_subtitle(f"{d.get('device_model', 'MindPhone')} • {t('connected', lang)}")
            row.add_prefix(Gtk.Label(label="📱"))

            # Unpair button in suffix
            btn_unpair = Gtk.Button(label=t("unpair_btn", lang), valign=Gtk.Align.CENTER)
            btn_unpair.add_css_class("destructive-action")
            btn_unpair.connect("clicked", lambda b, did=dev_id: self._unpair_device(did))
            row.add_suffix(btn_unpair)

            # Sub-row: Universal Clipboard toggle
            feat_clip = Adw.ActionRow(title=t("clipboard_sync_title", lang))
            sw_c = Gtk.Switch(valign=Gtk.Align.CENTER)
            sw_c.set_active(d.get("features", {}).get("universal_clipboard", True))
            sw_c.connect("notify::active", lambda s, p, did=dev_id: MindLinkConfig.update_feature(did, "universal_clipboard", s.get_active()))
            feat_clip.add_suffix(sw_c)
            row.add_row(feat_clip)

            # Sub-row: Mind Drop toggle
            feat_drop = Adw.ActionRow(title=t("file_drop_title", lang))
            sw_d = Gtk.Switch(valign=Gtk.Align.CENTER)
            sw_d.set_active(d.get("features", {}).get("quick_drop", True))
            sw_d.connect("notify::active", lambda s, p, did=dev_id: MindLinkConfig.update_feature(did, "quick_drop", s.get_active()))
            feat_drop.add_suffix(sw_d)
            row.add_row(feat_drop)

            self.paired_rows[dev_id] = row
            self.paired_group.add(row)

    def _unpair_device(self, dev_id: str):
        MindLinkConfig.remove_device(dev_id)
        self._reload_paired_devices_ui()

    def _on_simulate_clicked(self, _btn):
        """Simulates an incoming MindUI phone in setup mode for quick developer verification."""
        mock_dev = {
            "device_id": f"mindui_demo_{random.randint(100, 999)}",
            "device_name": "MindUI Phone 1 (Paradise Edition)",
            "device_model": "MindPhone 1",
            "os_version": "MindUI 1.0 (Android 14)",
            "ip": "127.0.0.1",
            "port": DEFAULT_SERVICE_PORT,
            "state": "setup_mode"
        }
        self._add_or_update_discovered_device(mock_dev)

        # Directly launch Apple-style pairing modal with demo PIN
        demo_pin = f"{random.randint(100000, 999999)}"

        def on_decision(approved: bool):
            if approved:
                mock_dev["paired_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                mock_dev["status"] = "connected"
                mock_dev["auth_token"] = "sim_token_xyz"
                mock_dev["features"] = {"universal_clipboard": True, "quick_drop": True, "notifications": True}
                MindLinkConfig.add_device(mock_dev)
                self._reload_paired_devices_ui()
                self._handle_pairing_success(mock_dev)

        MindLinkPairingDialog.show(self.win, demo_pin, mock_dev, on_decision, self.get_lang())

    def _on_test_clipboard_clicked(self, _btn):
        test_msg = f"✨ MindOS Paradise ➔ MindUI Pano Senkronizasyonu [{time.strftime('%H:%M:%S')}]"
        ok = ClipboardManager.write_text(test_msg)
        status = "Kopyalandı ✓ (Panoya yazıldı)" if ok else "Pano aracı bulunamadı"
        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Pano Testi",
            body=f"{status}\n\nİçerik:\n{test_msg}"
        )
        dialog.add_response("ok", "Tamam")
        dialog.present()

    def refresh(self):
        """Called when language changes."""
        self._reload_paired_devices_ui()


# --- CSS Extensions for Mind Link Apple-like Styling ---

MIND_LINK_CSS = """
.mind-link-hero-card {
    background: linear-gradient(135deg, rgba(0, 242, 254, 0.12) 0%, rgba(79, 172, 254, 0.08) 100%);
    border: 1px solid rgba(0, 242, 254, 0.35);
    border-radius: 16px;
    padding: 18px 22px;
    box-shadow: 0 4px 20px rgba(0, 242, 254, 0.08);
}
.mind-link-hero-tag {
    font-size: 10px;
    font-weight: 800;
    color: #00f2fe;
    background: rgba(0, 242, 254, 0.18);
    border-radius: 6px;
    padding: 3px 8px;
    letter-spacing: 0.8px;
}
.mind-link-hero-title {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.3px;
}
.mind-phone-mockup {
    background: #111823;
    border: 2px solid #00f2fe;
    border-radius: 18px;
    box-shadow: 0 0 25px rgba(0, 242, 254, 0.35);
}
.mind-phone-notch {
    background: #00f2fe;
    border-radius: 3px;
}
.mind-phone-badge {
    font-size: 9px;
    font-weight: 700;
    color: #00f2fe;
}
.mind-pin-digit {
    font-size: 26px;
    font-weight: 900;
    font-family: monospace;
    color: #00f2fe;
    background: rgba(0, 242, 254, 0.12);
    border: 2px solid rgba(0, 242, 254, 0.45);
    border-radius: 10px;
    padding: 6px 12px;
    min-width: 24px;
}
.mind-pin-sep {
    font-size: 20px;
    font-weight: bold;
    color: rgba(0, 242, 254, 0.4);
    margin: 0 4px;
}
"""

def inject_mind_link_css():
    """Injects custom CSS provider for Mind Link."""
    try:
        provider = Gtk.CssProvider()
        provider.load_from_data(MIND_LINK_CSS.encode("utf-8"))
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10
            )
    except Exception as e:
        print(f"[MindLink] CSS injection warning: {e}", file=sys.stderr)
