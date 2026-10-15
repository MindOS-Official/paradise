# -*- coding: utf-8 -*-
"""
Mind-Arc ek sayfaları:
  * mindpkg Paket Merkezi  - arama, popüler uygulamalar, kurulu .mind paketleri
  * Sistem Bakımı          - RAM/zram durumu, disk kullanımı, güncelleme ve temizlik
  * Sistem Güncellemesi    - MindOS Paradise sürümü, "Yeniden Başlat ve Güncelle"

Uzun süren işlemler (kurulum, güncelleme) arka plan iş parçacığında pkexec ile
çalışır; çıktı canlı olarak "İşlem Çıktısı" panelinde gösterilir.
"""

import glob
import json
import os
import re
import shutil
import subprocess
import threading

from gi.repository import Gtk, GLib, Adw, Pango

try:
    import mindos_prefs  # ortak MindOS tercihleri (mindos-apps: /usr/lib/python3/dist-packages)
except ImportError:
    mindos_prefs = None

MINDPKG = "/usr/local/bin/mindpkg"
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

# (komut adı, sistem paket adı, görünen ad, açıklama anahtarı, simge)
POPULAR_APPS = [
    ("chrome", "google-chrome-stable", "Google Chrome", "app_chrome", "🌐"),
    ("vscode", "code", "Visual Studio Code", "app_vscode", "🧑‍💻"),
    ("steam", "steam-launcher", "Steam", "app_steam", "🎮"),
    ("discord", "discord", "Discord", "app_discord", "💬"),
    ("vlc", "vlc", "VLC", "app_vlc", "🎬"),
    ("gimp", "gimp", "GIMP", "app_gimp", "🎨"),
    ("obs-studio", "obs-studio", "OBS Studio", "app_obs", "🎥"),
    ("inkscape", "inkscape", "Inkscape", "app_inkscape", "✒️"),
    ("audacity", "audacity", "Audacity", "app_audacity", "🎙️"),
    ("telegram-desktop", "telegram-desktop", "Telegram", "app_telegram", "✈️"),
    ("htop", "htop", "htop", "app_htop", "📊"),
]

TEXTS = {
    "packages": ("Paket Merkezi", "Package Center"),
    "maintenance": ("Sistem Bakımı", "System Maintenance"),
    "mp_title": ("mindpkg Paket Yöneticisi", "mindpkg Package Manager"),
    "mp_desc": ("MindOS'un paket yöneticisi tek komutla kurar: önce üreticinin resmi deposu, sonra Debian deposu, "
                "yoksa MindOS .mind deposu. Terminalde: mindpkg install &lt;paket&gt;",
                "MindOS's package manager installs with one command: vendor repository first, then Debian, "
                "then the MindOS .mind repository. In a terminal: mindpkg install &lt;package&gt;"),
    "mp_version": ("Sürüm", "Version"),
    "mp_repo": ("MindOS deposu", "MindOS repository"),
    "mp_repo_count": ("{n} paket", "{n} packages"),
    "mp_repo_none": ("Henüz eşitlenmedi", "Not synced yet"),
    "mp_update": ("Depoları Güncelle", "Update Repositories"),
    "mp_upgrade": ("Tümünü Yükselt", "Upgrade All"),
    "popular": ("Popüler Uygulamalar", "Popular Apps"),
    "popular_desc": ("Tek tıkla kur veya kaldır", "Install or remove with one click"),
    "install": ("Kur", "Install"),
    "remove": ("Kaldır", "Remove"),
    "installed": ("Kurulu", "Installed"),
    "search": ("Paket Ara", "Search Packages"),
    "search_desc": ("MindOS deposunda arar. Debian'daki her paket de adıyla doğrudan kurulabilir.",
                    "Searches the MindOS repository. Any Debian package can also be installed by name."),
    "search_entry": ("Uygulama ara: steam, discord, vlc...", "Search apps: steam, discord, vlc..."),
    "search_direct": ("“{q}” paketini doğrudan kur", "Install “{q}” directly"),
    "search_direct_sub": ("Üretici deposu → Debian → MindOS sırasıyla aranır",
                          "Looks in vendor → Debian → MindOS repositories"),
    "search_none": ("MindOS deposunda eşleşme yok", "No match in the MindOS repository"),
    "mind_installed": ("Kurulu .mind Paketleri", "Installed .mind Packages"),
    "mind_installed_none": ("mindpkg ile kurulmuş .mind paketi yok", "No .mind packages installed with mindpkg"),
    "output": ("İşlem Çıktısı", "Operation Output"),
    "idle": ("Hazır", "Ready"),
    "running": ("Çalışıyor: {cmd}", "Running: {cmd}"),
    "done_ok": ("Tamamlandı ✓", "Completed ✓"),
    "done_fail": ("Başarısız (çıkış kodu {rc})", "Failed (exit code {rc})"),
    "busy": ("Başka bir işlem sürüyor, lütfen bekleyin.", "Another operation is running, please wait."),
    "app_chrome": ("Google'ın web tarayıcısı (resmi Google deposu)", "Google's web browser (official Google repo)"),
    "app_vscode": ("Microsoft'un kod editörü (resmi Microsoft deposu)", "Microsoft's code editor (official repo)"),
    "app_vlc": ("Her formatı oynatan medya oynatıcı", "Plays every media format"),
    "app_gimp": ("Gelişmiş görüntü düzenleyici", "Advanced image editor"),
    "app_obs": ("Canlı yayın ve ekran kaydı", "Streaming and screen recording"),
    "app_inkscape": ("Vektör çizim programı", "Vector graphics editor"),
    "app_audacity": ("Ses kaydı ve düzenleme", "Audio recording and editing"),
    "app_telegram": ("Hızlı ve güvenli mesajlaşma", "Fast and secure messaging"),
    "app_steam": ("Valve'ın oyun platformu (resmi Valve deposu)", "Valve's gaming platform (official Valve repository)"),
    "app_discord": ("Sesli ve yazılı sohbet", "Voice and text chat"),
    "app_htop": ("Terminal tabanlı sistem izleyici", "Terminal system monitor"),
    "mem_title": ("Bellek ve zram", "Memory and zram"),
    "mem_desc": ("MindOS, RAM'in yarısı kadar sıkıştırılmış zram takas alanı kullanır",
                 "MindOS uses a compressed zram swap of half the RAM"),
    "ram": ("RAM", "RAM"),
    "zram": ("zram (sıkıştırılmış takas)", "zram (compressed swap)"),
    "zram_none": ("Etkin değil", "Not active"),
    "zram_val": ("{orig} veri → {comp} bellekte ({ratio}x sıkıştırma)",
                 "{orig} data → {comp} in memory ({ratio}x compression)"),
    "disk_title": ("Disk Kullanımı", "Disk Usage"),
    "maint_title": ("Bakım İşlemleri", "Maintenance Tasks"),
    "maint_desc": ("Yönetici yetkisi gerektiren işlemler için parola sorulur",
                   "Administrator password is requested for privileged tasks"),
    "m_update": ("Sistemi Güncelle", "Update System"),
    "m_update_sub": ("mindpkg upgrade: önce mindpkg, sonra .mind ve sistem paketleri",
                     "mindpkg upgrade: mindpkg itself, then .mind and system packages"),
    "auto_title": ("Otomatik Güvenlik Güncellemeleri", "Automatic Security Updates"),
    "auto_sub": ("Debian güvenlik yamaları arka planda kendiliğinden kurulur (kurulu sistemde)",
                 "Debian security patches install automatically in the background (installed system)"),
    "m_autoremove": ("Gereksiz Paketleri Kaldır", "Remove Unused Packages"),
    "m_autoremove_sub": ("Artık ihtiyaç duyulmayan bağımlılıkları siler", "Removes dependencies no longer needed"),
    "m_clean": ("Paket Önbelleğini Temizle", "Clean Package Cache"),
    "m_clean_sub": ("apt ve mindpkg indirme önbelleklerini boşaltır", "Empties apt and mindpkg download caches"),
    "m_thumbs": ("Küçük Resim Önbelleğini Temizle", "Clear Thumbnail Cache"),
    "m_thumbs_sub": ("Dosya yöneticisi önizlemelerini siler (yönetici gerekmez)",
                     "Deletes file manager previews (no admin needed)"),
    "run": ("Çalıştır", "Run"),
    "open": ("Aç", "Open"),
    "m_update_sub2": ("Yeniden başlatarak güvenli güncelleme: Sistem Güncellemesi sayfası",
                      "Safe update with a restart: System Update page"),
    "updates": ("Sistem Güncellemesi", "System Update"),
    "u_checking": ("Güncellemeler denetleniyor…", "Checking for updates…"),
    "u_uptodate": ("Sisteminiz güncel", "Your system is up to date"),
    "u_ready": ("{name} hazır", "{name} is available"),
    "u_pending": ("{n} güncelleme hazır", "{n} updates available"),
    "u_scheduled": ("Güncelleme hazırlandı; bilgisayar yeniden başlayınca kurulacak",
                    "Update prepared; it will be installed when the computer restarts"),
    "u_live": ("Canlı oturumdasınız. Güncellemeler MindOS diske kurulduktan sonra yapılabilir.",
               "You are in a live session. Updates are available once MindOS is installed to disk."),
    "u_check_fail": ("Denetlenemedi: {err}", "Could not check: {err}"),
    "u_check": ("Denetle", "Check"),
    "u_install": ("Yeniden Başlat ve Güncelle", "Restart and Update"),
    "u_reboot_now": ("Şimdi Yeniden Başlat", "Restart Now"),
    "u_cancel": ("İptal Et", "Cancel"),
    "u_rebooting": ("Yeniden başlatılıyor…", "Restarting…"),
    "u_new_title": ("Yenilikler", "What's New"),
    "u_items_title": ("Bekleyen Güncellemeler", "Pending Updates"),
    "u_items_desc": ("Hepsi önce indirilip imza ve SHA256 ile doğrulanır; kurulum yeniden başlatınca, "
                     "masaüstü kapalıyken yapılır.",
                     "Everything is downloaded and verified (signature and SHA256) first; installation "
                     "happens after a restart, while the desktop is closed."),
    "u_mindpkg": ("mindpkg paket yöneticisi", "mindpkg package manager"),
    "u_debian": ("Debian paketleri", "Debian packages"),
    "u_debian_n": ("{n} paket: {names}", "{n} packages: {names}"),
    "u_mind": (".mind uygulaması: {name}", ".mind app: {name}"),
    "u_last_title": ("Son Güncelleme", "Last Update"),
    "u_last_ok": ("Başarılı · {when}", "Successful · {when}"),
    "u_last_fail": ("Bazı adımlar başarısız · {when}", "Some steps failed · {when}"),
    "u_last_log": ("Ayrıntılar: {log}", "Details: {log}"),
    "u_confirm_title": ("Yeniden başlatılsın mı?", "Restart now?"),
    "u_confirm_body": ("Güncellemeler indirilip doğrulanacak, ardından bilgisayar yeniden başlayacak ve "
                       "kurulum açılış ekranında yapılacak. Açık çalışmalarınızı kaydedin.",
                       "Updates will be downloaded and verified, then the computer will restart and install "
                       "them on the boot screen. Save any open work."),
    "u_notify": ("Güncelleme Bildirimleri", "Update Notifications"),
    "u_notify_sub": ("Günde bir kez denetlenir; güncelleme varsa bildirim gösterilir",
                     "Checked once a day; a notification appears when updates are available"),
    "u_auto_title": ("Otomatik Denetim", "Automatic Check"),
    "priv_title": ("Gizlilik", "Privacy"),
    "priv_desc": ("İnternete bilgi gönderen özellikler yalnızca siz açarsanız çalışır",
                  "Features that send data over the internet only work if you turn them on"),
    "priv_weather": ("Hava Durumu (Mind Helper)", "Weather (Mind Helper)"),
    "priv_weather_sub": ("Konumunuz IP adresinizden wttr.in tarafından tahmin edilir",
                         "wttr.in estimates your location from your IP address"),
    "priv_search": ("İnternette Arama (Mind Helper)", "Web Search (Mind Helper)"),
    "priv_search_sub": ("Mind Helper'ın yanıtlayamadığı sorular DuckDuckGo'ya gönderilir",
                        "Questions Mind Helper cannot answer are sent to DuckDuckGo"),
    "nv_title": ("NVIDIA Ekran Kartı", "NVIDIA Graphics"),
    "nv_modern": ("NVIDIA'nın en yeni sürücüsü MindOS kernel'iyle kurulur",
                  "NVIDIA's latest driver is installed with the MindOS kernel"),
    "nv_legacy": ("Bu kart NVIDIA 550 sürücüsünü kullanır; bilgisayar Debian'ın 6.12 LTS kernel'ine geçirilir",
                  "This card uses the NVIDIA 550 driver; the computer switches to Debian's 6.12 LTS kernel"),
    "nv_old": ("Bu kart için güncel NVIDIA sürücüsü yok; açık kaynak nouveau sürücüsü kullanılıyor",
               "There is no current NVIDIA driver for this card; the open-source nouveau driver is used"),
    "nv_install": ("NVIDIA Sürücüsünü Kur", "Install NVIDIA Driver"),
    "nv_live": ("Canlı oturumdasınız. Sürücü, MindOS diske kurulduktan sonra kurulabilir.",
                "You are in a live session. The driver can be installed after MindOS is installed to disk."),
    "nv_running": ("NVIDIA sürücüsü çalışıyor: {ver}", "NVIDIA driver is running: {ver}"),
    "nv_reboot": ("Sürücü kuruldu; etkinleşmesi için yeniden başlatın", "Driver installed; restart to activate it"),
    "nv_restart": ("Yeniden Başlat", "Restart"),
    "nv_confirm": ("NVIDIA sürücüsü kurulsun mu?", "Install the NVIDIA driver?"),
    "nv_confirm_body": ("Sürücü internetten indirilip kurulacak (birkaç yüz MB). Secure Boot açıksa yeniden "
                        "başlarken mavi ekranda bir kez onay kodu girmeniz istenecek; kod kurulum çıktısında yazar.",
                        "The driver will be downloaded and installed (a few hundred MB). If Secure Boot is on, "
                        "you will enter a one-time code on a blue screen at the next restart; the code is shown "
                        "in the installation output."),
    "bc_title": ("Broadcom Wi-Fi", "Broadcom Wi-Fi"),
    "bc_need": ("Bu Wi-Fi kartı için Broadcom sürücüsü (wl) gerekiyor. Kurulum için internet gerekir: "
                "kablo ya da telefonla USB internet paylaşımı kullanın.",
                "This Wi-Fi card needs the Broadcom driver (wl). Installation needs internet: use a cable "
                "or USB tethering from your phone."),
    "bc_ok": ("Wi-Fi kartı çalışıyor ({drv})", "Wi-Fi card is working ({drv})"),
    "bc_install": ("Wi-Fi Sürücüsünü Kur", "Install Wi-Fi Driver"),
    "u_preparing": ("Güncellemeler indiriliyor ve doğrulanıyor… Bitince bilgisayar yeniden başlayacak. "
                    "Ayrıntılar aşağıda, İşlem Çıktısı'nda.",
                    "Downloading and verifying updates… The computer will restart when done. "
                    "Details below in Operation Output."),
    "u_prepare_fail": ("Güncelleme hazırlanamadı; ayrıntılar aşağıda.", "The update could not be prepared; see details below."),
    "thumbs_done": ("{n} küçük resim silindi", "{n} thumbnails deleted"),
}


AUTO_UPDATES_FILE = "/etc/apt/apt.conf.d/20auto-upgrades"
AUTO_UPDATES_CMD = ("printf 'APT::Periodic::Update-Package-Lists \"1\";\\nAPT::Periodic::Unattended-Upgrade \"%s\";\\n' "
                    "> " + AUTO_UPDATES_FILE)


def auto_updates_enabled():
    try:
        with open(AUTO_UPDATES_FILE, encoding="utf-8") as f:
            return bool(re.search(r'Unattended-Upgrade\s+"1"', f.read()))
    except OSError:
        return False


def human(nbytes):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if nbytes < 1024 or unit == "TB":
            return f"{nbytes:.1f} {unit}" if unit != "B" else f"{int(nbytes)} B"
        nbytes /= 1024
    return str(nbytes)


def system_installed(pkg):
    try:
        out = subprocess.run(["dpkg-query", "-W", "-f=${db:Status-Abbrev}", pkg],
                             capture_output=True, text=True).stdout
        return out.startswith("ii")
    except Exception:
        return False


def mind_installed(name):
    return os.path.exists(f"/var/lib/mindpkg/installed/{name}.json")


class ExtraTexts:
    """Dil değişince yeniden yazılacak etiketleri tutar"""

    def __init__(self, win):
        self.win = win
        self.items = []

    def t(self, key, **fmt):
        tr, en = TEXTS[key]
        s = en if getattr(self.win, "current_lang_code", "tr") == "en" else tr
        return s.format(**fmt) if fmt else s

    def bind(self, setter, key, **fmt):
        self.items.append((setter, key, fmt))
        setter(self.t(key, **fmt))

    def refresh(self):
        for setter, key, fmt in self.items:
            setter(self.t(key, **fmt))


class OutputPanel:
    """Komut çıktısını canlı gösteren panel; aynı anda tek işlem çalıştırır"""

    def __init__(self, texts):
        self.texts = texts
        self.busy = False
        self.group = Adw.PreferencesGroup()
        self.group.set_visible(False)  # yalnızca bir işlem başlayınca görünür
        texts.bind(self.group.set_title, "output")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        status_box = Gtk.Box(spacing=8)
        self.spinner = Gtk.Spinner()
        self.status = Gtk.Label(xalign=0)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        texts.bind(self.status.set_label, "idle")
        status_box.append(self.spinner)
        status_box.append(self.status)
        box.append(status_box)

        self.buffer = Gtk.TextBuffer()
        view = Gtk.TextView(buffer=self.buffer, editable=False, monospace=True, cursor_visible=False)
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        view.set_top_margin(8)
        view.set_bottom_margin(8)
        view.set_left_margin(8)
        view.set_right_margin(8)
        self.view = view
        scroller = Gtk.ScrolledWindow()
        scroller.set_min_content_height(200)
        scroller.set_child(view)
        scroller.add_css_class("card")
        box.append(scroller)
        self.group.add(box)

    def append(self, text):
        self.buffer.insert(self.buffer.get_end_iter(), text)
        mark = self.buffer.create_mark(None, self.buffer.get_end_iter(), False)
        self.view.scroll_mark_onscreen(mark)
        return False

    def run(self, argv, on_done=None, show=None):
        if self.busy:
            self.append(self.texts.t("busy") + "\n")
            return
        self.busy = True
        self.group.set_visible(True)
        self.buffer.set_text("")
        label = show or " ".join(argv)
        self.status.set_label(self.texts.t("running", cmd=label))
        self.spinner.start()

        def worker():
            rc = -1
            try:
                env = dict(os.environ, LANG=os.environ.get("LANG", "C.UTF-8"))
                proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, bufsize=1, env=env)
                for line in proc.stdout:
                    GLib.idle_add(self.append, ANSI.sub("", line))
                rc = proc.wait()
            except Exception as e:
                GLib.idle_add(self.append, f"{e}\n")
            GLib.idle_add(self._finish, rc, on_done)

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, rc, on_done):
        self.busy = False
        self.spinner.stop()
        self.status.set_label(self.texts.t("done_ok") if rc == 0 else self.texts.t("done_fail", rc=rc))
        if on_done:
            on_done(rc)
        return False


class PackageCenter:
    def __init__(self, win, texts):
        self.win = win
        self.texts = texts
        self.index = None
        self.search_rows = []
        self.search_timeout = 0
        self.page = Adw.PreferencesPage()
        texts.bind(self.page.set_title, "packages")
        self.output = OutputPanel(texts)

        # mindpkg bilgisi
        g = Adw.PreferencesGroup()
        texts.bind(g.set_title, "mp_title")
        texts.bind(g.set_description, "mp_desc")
        self.row_version = Adw.ActionRow()
        texts.bind(self.row_version.set_title, "mp_version")
        self.row_version.add_prefix(Gtk.Label(label="📦"))
        g.add(self.row_version)
        self.row_repo = Adw.ActionRow()
        texts.bind(self.row_repo.set_title, "mp_repo")
        self.row_repo.add_prefix(Gtk.Label(label="☁️"))
        btn = Gtk.Button(valign=Gtk.Align.CENTER)
        btn.add_css_class("suggested-action")
        texts.bind(btn.set_label, "mp_update")
        btn.connect("clicked", lambda b: self.output.run(["pkexec", MINDPKG, "update"], self.after_change,
                                                         "mindpkg update"))
        self.row_repo.add_suffix(btn)
        up = Gtk.Button(valign=Gtk.Align.CENTER)
        texts.bind(up.set_label, "mp_upgrade")
        up.connect("clicked", lambda b: self.win.view_stack.set_visible_child_name("updates"))
        self.row_repo.add_suffix(up)
        g.add(self.row_repo)
        self.page.add(g)

        # arama
        g = Adw.PreferencesGroup()
        texts.bind(g.set_title, "search")
        texts.bind(g.set_description, "search_desc")
        self.entry = Adw.EntryRow()
        texts.bind(self.entry.set_title, "search_entry")
        self.entry.connect("changed", self.on_search_changed)
        g.add(self.entry)
        self.search_group = g
        self.page.add(g)

        self.page.add(self.output.group)

        # popüler uygulamalar
        g = Adw.PreferencesGroup()
        texts.bind(g.set_title, "popular")
        texts.bind(g.set_description, "popular_desc")
        self.app_rows = []
        for cmd, sys_pkg, title, desc_key, icon in POPULAR_APPS:
            row = Adw.ActionRow(title=title)
            texts.bind(row.set_subtitle, desc_key)
            row.add_prefix(Gtk.Label(label=icon))
            b = Gtk.Button(valign=Gtk.Align.CENTER)
            b.connect("clicked", self.on_app_clicked, cmd, sys_pkg)
            row.add_suffix(b)
            g.add(row)
            self.app_rows.append((b, cmd, sys_pkg))
        self.page.add(g)

        # kurulu .mind paketleri
        self.mind_group = Adw.PreferencesGroup()
        texts.bind(self.mind_group.set_title, "mind_installed")
        self.mind_rows = []
        self.page.add(self.mind_group)

        self.refresh()

    # --- durum ---
    def refresh(self):
        try:
            head = open(MINDPKG, encoding="utf-8").read(2000)
            ver = re.search(r'VERSION = "([^"]+)"', head)
            self.row_version.set_subtitle(f"mindpkg {ver.group(1) if ver else '?'}")
        except Exception:
            self.row_version.set_subtitle("mindpkg ?")
        count = 0
        for f in glob.glob("/var/lib/mindpkg/repos/*.json"):
            try:
                count += len(json.load(open(f, encoding="utf-8")).get("packages", []))
            except Exception:
                pass
        self.index = None
        if count:
            self.row_repo.set_subtitle(self.texts.t("mp_repo_count", n=f"{count:,}".replace(",", ".")))
        else:
            self.row_repo.set_subtitle(self.texts.t("mp_repo_none"))
        for b, cmd, sys_pkg in self.app_rows:
            inst = system_installed(sys_pkg) or mind_installed(sys_pkg) or mind_installed(cmd)
            b.set_label(self.texts.t("remove" if inst else "install"))
            for cls in ("suggested-action", "destructive-action"):
                b.remove_css_class(cls)
            b.add_css_class("destructive-action" if inst else "suggested-action")
            b.installed = inst
        for r in self.mind_rows:
            self.mind_group.remove(r)
        self.mind_rows = []
        recs = sorted(glob.glob("/var/lib/mindpkg/installed/*.json"))
        if not recs:
            r = Adw.ActionRow()
            r.set_title(self.texts.t("mind_installed_none"))
            self.mind_group.add(r)
            self.mind_rows.append(r)
        for f in recs:
            try:
                meta = json.load(open(f, encoding="utf-8"))
            except Exception:
                continue
            name = meta.get("name", os.path.basename(f)[:-5])
            r = Adw.ActionRow(title=GLib.markup_escape_text(name),
                              subtitle=GLib.markup_escape_text(f"{meta.get('version', '')} · {meta.get('description', '')}"))
            b = Gtk.Button(valign=Gtk.Align.CENTER, label=self.texts.t("remove"))
            b.add_css_class("destructive-action")
            b.connect("clicked", lambda btn, n=name: self.output.run(["pkexec", MINDPKG, "remove", n],
                                                                     self.after_change, f"mindpkg remove {n}"))
            r.add_suffix(b)
            self.mind_group.add(r)
            self.mind_rows.append(r)

    def after_change(self, rc):
        self.refresh()
        if self.entry.get_text().strip():
            self.do_search()

    def on_app_clicked(self, button, cmd, sys_pkg):
        action = "remove" if getattr(button, "installed", False) else "install"
        self.output.run(["pkexec", MINDPKG, action, cmd], self.after_change, f"mindpkg {action} {cmd}")

    # --- arama ---
    def load_index(self):
        pkgs = {}
        for f in glob.glob("/var/lib/mindpkg/repos/*.json"):
            try:
                for p in json.load(open(f, encoding="utf-8")).get("packages", []):
                    if "snap" not in str(p.get("version", "")):
                        pkgs.setdefault(p["name"], p)
            except Exception:
                pass
        self.index = list(pkgs.values())

    def on_search_changed(self, entry):
        if self.search_timeout:
            GLib.source_remove(self.search_timeout)
        self.search_timeout = GLib.timeout_add(350, self.do_search)

    def do_search(self):
        self.search_timeout = 0
        for r in self.search_rows:
            self.search_group.remove(r)
        self.search_rows = []
        q = self.entry.get_text().strip().lower()
        if len(q) < 2:
            return False
        if self.index is None:
            self.load_index()
        featured = [a for a in POPULAR_APPS
                    if q in a[2].lower() or q in a[0] or q in a[1] or a[0] in q]
        hidden = {n for a in featured for n in (a[0], a[1])}
        index = [p for p in self.index if p["name"] not in hidden]
        exact = [p for p in index if p["name"].lower() == q]
        named = [p for p in index if q in p["name"].lower() and p not in exact]
        desc = [p for p in index if q not in p["name"].lower() and q in str(p.get("description", "")).lower()]
        results = (exact + sorted(named, key=lambda p: len(p["name"])) + desc)[:25]

        for cmd, sys_pkg, title, desc_key, icon in featured:
            r = Adw.ActionRow(title=title, subtitle=self.texts.t(desc_key))
            r.add_prefix(Gtk.Label(label=icon))
            if mind_installed(cmd) or system_installed(sys_pkg):
                lbl = Gtk.Label(label=self.texts.t("installed"))
                lbl.add_css_class("dim-label")
                r.add_suffix(lbl)
            else:
                b = Gtk.Button(valign=Gtk.Align.CENTER, label=self.texts.t("install"))
                b.add_css_class("suggested-action")
                b.connect("clicked", lambda btn, c=cmd: self.output.run(["pkexec", MINDPKG, "install", c],
                                                                        self.after_change, f"mindpkg install {c}"))
                r.add_suffix(b)
            self.search_group.add(r)
            self.search_rows.append(r)
        if not featured and re.fullmatch(r"[a-z0-9][a-z0-9.+-]*", q):
            r = Adw.ActionRow(title=self.texts.t("search_direct", q=q), subtitle=self.texts.t("search_direct_sub"))
            r.add_prefix(Gtk.Label(label="⚡"))
            b = Gtk.Button(valign=Gtk.Align.CENTER, label=self.texts.t("install"))
            b.add_css_class("suggested-action")
            b.connect("clicked", lambda btn: self.output.run(["pkexec", MINDPKG, "install", q], self.after_change,
                                                             f"mindpkg install {q}"))
            r.add_suffix(b)
            self.search_group.add(r)
            self.search_rows.append(r)
        if not results and not featured:
            r = Adw.ActionRow(title=self.texts.t("search_none"))
            self.search_group.add(r)
            self.search_rows.append(r)
        for p in results:
            name = p["name"]
            r = Adw.ActionRow(title=GLib.markup_escape_text(name),
                              subtitle=GLib.markup_escape_text(f"{p.get('version', '')} · {p.get('description', '')}"))
            r.set_subtitle_lines(1)
            if mind_installed(name) or system_installed(name):
                lbl = Gtk.Label(label=self.texts.t("installed"))
                lbl.add_css_class("dim-label")
                r.add_suffix(lbl)
            else:
                b = Gtk.Button(valign=Gtk.Align.CENTER, label=self.texts.t("install"))
                b.connect("clicked", lambda btn, n=name: self.output.run(["pkexec", MINDPKG, "install", n],
                                                                         self.after_change, f"mindpkg install {n}"))
                r.add_suffix(b)
            self.search_group.add(r)
            self.search_rows.append(r)
        return False


class Maintenance:
    def __init__(self, win, texts):
        self.win = win
        self.texts = texts
        self.page = Adw.PreferencesPage()
        texts.bind(self.page.set_title, "maintenance")
        self.output = OutputPanel(texts)

        g = Adw.PreferencesGroup()
        texts.bind(g.set_title, "mem_title")
        texts.bind(g.set_description, "mem_desc")
        self.row_ram, self.bar_ram = self.level_row(g, "ram", "🧠")
        self.row_zram, self.bar_zram = self.level_row(g, "zram", "🗜️")
        self.page.add(g)

        g = Adw.PreferencesGroup()
        texts.bind(g.set_title, "disk_title")
        self.disk_rows = []
        for mount in ("/", "/home"):
            if mount == "/home" and os.stat("/home").st_dev == os.stat("/").st_dev:
                continue
            row = Adw.ActionRow(title=mount)
            row.add_prefix(Gtk.Label(label="💽"))
            bar = Gtk.LevelBar(min_value=0, max_value=1, valign=Gtk.Align.CENTER)
            bar.set_size_request(160, -1)
            row.add_suffix(bar)
            g.add(row)
            self.disk_rows.append((mount, row, bar))
        self.page.add(g)

        g = Adw.PreferencesGroup()
        texts.bind(g.set_title, "maint_title")
        texts.bind(g.set_description, "maint_desc")
        row = Adw.ActionRow()
        texts.bind(row.set_title, "m_update")
        texts.bind(row.set_subtitle, "m_update_sub2")
        row.add_prefix(Gtk.Label(label="🔄"))
        b = Gtk.Button(valign=Gtk.Align.CENTER)
        texts.bind(b.set_label, "open")
        b.connect("clicked", lambda btn: self.win.view_stack.set_visible_child_name("updates"))
        row.add_suffix(b)
        g.add(row)
        tasks = [
            ("m_autoremove", "🧹", ["pkexec", "env", "DEBIAN_FRONTEND=noninteractive",
                                    "apt-get", "-y", "autoremove", "--purge"]),
            ("m_clean", "🗑️", ["pkexec", "sh", "-c", f"apt-get clean && {MINDPKG} clean"]),
        ]
        if os.path.exists("/usr/bin/unattended-upgrade"):
            self.auto_row = Adw.SwitchRow()
            texts.bind(self.auto_row.set_title, "auto_title")
            texts.bind(self.auto_row.set_subtitle, "auto_sub")
            self.auto_row.add_prefix(Gtk.Label(label="🛡️"))
            self.auto_row.set_active(auto_updates_enabled())
            self.auto_row.connect("notify::active", self.on_auto_toggled)
            g.add(self.auto_row)
        for key, icon, argv in tasks:
            row = Adw.ActionRow()
            texts.bind(row.set_title, key)
            texts.bind(row.set_subtitle, key + "_sub")
            row.add_prefix(Gtk.Label(label=icon))
            b = Gtk.Button(valign=Gtk.Align.CENTER)
            texts.bind(b.set_label, "run")
            b.connect("clicked", lambda btn, a=argv, k=key: self.output.run(a, None, self.texts.t(k)))
            row.add_suffix(b)
            g.add(row)
        row = Adw.ActionRow()
        texts.bind(row.set_title, "m_thumbs")
        texts.bind(row.set_subtitle, "m_thumbs_sub")
        row.add_prefix(Gtk.Label(label="🖼️"))
        b = Gtk.Button(valign=Gtk.Align.CENTER)
        texts.bind(b.set_label, "run")
        b.connect("clicked", self.on_thumbs)
        row.add_suffix(b)
        g.add(row)
        self.page.add(g)
        self.page.add(self.output.group)

        self.update_stats()
        GLib.timeout_add_seconds(2, self.update_stats)

    def on_auto_toggled(self, row, _pspec):
        want = row.get_active()
        if want == auto_updates_enabled():
            return

        def worker():
            rc = subprocess.run(["pkexec", "sh", "-c", AUTO_UPDATES_CMD % ("1" if want else "0")]).returncode
            if rc != 0:  # yetki verilmedi: anahtarı gerçek duruma geri al
                GLib.idle_add(row.set_active, auto_updates_enabled())

        threading.Thread(target=worker, daemon=True).start()

    def level_row(self, group, key, icon):
        row = Adw.ActionRow()
        self.texts.bind(row.set_title, key)
        row.add_prefix(Gtk.Label(label=icon))
        bar = Gtk.LevelBar(min_value=0, max_value=1, valign=Gtk.Align.CENTER)
        bar.set_size_request(160, -1)
        row.add_suffix(bar)
        group.add(row)
        return row, bar

    def update_stats(self):
        if getattr(self.win, "stats_active", True) is False:
            return False
        try:
            mem = {}
            for line in open("/proc/meminfo"):
                k, v = line.split(":", 1)
                mem[k] = int(v.split()[0]) * 1024
            used = mem["MemTotal"] - mem["MemAvailable"]
            self.row_ram.set_subtitle(f"{human(used)} / {human(mem['MemTotal'])}")
            self.bar_ram.set_value(used / mem["MemTotal"])
        except Exception:
            pass
        try:
            stat = open("/sys/block/zram0/mm_stat").read().split()
            orig, comp = int(stat[0]), int(stat[1])
            size = int(open("/sys/block/zram0/disksize").read())
            ratio = f"{orig / comp:.1f}" if comp else "–"
            self.row_zram.set_subtitle(self.texts.t("zram_val", orig=human(orig), comp=human(comp), ratio=ratio))
            self.bar_zram.set_value(orig / size if size else 0)
        except Exception:
            self.row_zram.set_subtitle(self.texts.t("zram_none"))
            self.bar_zram.set_value(0)
        for mount, row, bar in self.disk_rows:
            try:
                du = shutil.disk_usage(mount)
                row.set_subtitle(f"{human(du.used)} / {human(du.total)}")
                bar.set_value(du.used / du.total)
            except Exception:
                pass
        return True

    def on_thumbs(self, button):
        base = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "thumbnails")
        n = 0
        for f in glob.glob(os.path.join(base, "*", "*.png")):
            try:
                os.remove(f)
                n += 1
            except Exception:
                pass
        self.output.buffer.set_text(self.texts.t("thumbs_done", n=n) + "\n")

def pref_switch(texts, key, title, subtitle, icon):
    """mindos_prefs tercihine bağlı bir anahtar satırı"""
    row = Adw.SwitchRow()
    texts.bind(row.set_title, title)
    texts.bind(row.set_subtitle, subtitle)
    row.add_prefix(Gtk.Label(label=icon))
    row.set_active(mindos_prefs.get(key))
    row.connect("notify::active", lambda r, _p: mindos_prefs.set(key, r.get_active()))
    return row


def build_privacy_group(texts):
    g = Adw.PreferencesGroup()
    texts.bind(g.set_title, "priv_title")
    texts.bind(g.set_description, "priv_desc")
    g.add(pref_switch(texts, "weather", "priv_weather", "priv_weather_sub", "🌤️"))
    g.add(pref_switch(texts, "web_search", "priv_search", "priv_search_sub", "🔎"))
    return g


class SystemUpdate:
    """MindOS Paradise sürümü, bekleyen güncellemeler ve "Yeniden Başlat ve Güncelle".

    Denetim yetki istemez (mindpkg check --json). Kurulum 'pkexec mindpkg upgrade --offline' ile
    hazırlanır (indir + doğrula), sonra bilgisayar yeniden başlar ve Plymouth ekranında kurulur."""

    def __init__(self, win, texts):
        self.win = win
        self.texts = texts
        self.info = None
        self.checking = False
        self.page = Adw.PreferencesPage()
        texts.bind(self.page.set_title, "updates")
        self.output = OutputPanel(texts)

        hero = Adw.PreferencesGroup()
        box = Gtk.Box(spacing=18, margin_top=6, margin_bottom=6)
        logo = Gtk.Image(icon_name="mindos-logo", pixel_size=72)
        box.append(logo)
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, valign=Gtk.Align.CENTER, hexpand=True)
        self.lbl_name = Gtk.Label(xalign=0, label="MindOS Paradise")
        self.lbl_name.add_css_class("title-1")
        self.lbl_status = Gtk.Label(xalign=0, wrap=True)
        self.lbl_status.add_css_class("dim-label")
        col.append(self.lbl_name)
        col.append(self.lbl_status)
        box.append(col)
        btns = Gtk.Box(spacing=8, valign=Gtk.Align.CENTER)
        self.spinner = Gtk.Spinner()
        btns.append(self.spinner)
        self.btn_check = Gtk.Button()
        texts.bind(self.btn_check.set_label, "u_check")
        self.btn_check.connect("clicked", lambda b: self.check())
        btns.append(self.btn_check)
        self.btn_cancel = Gtk.Button(visible=False)
        texts.bind(self.btn_cancel.set_label, "u_cancel")
        self.btn_cancel.connect("clicked", self.on_cancel)
        btns.append(self.btn_cancel)
        self.btn_install = Gtk.Button(visible=False)
        self.btn_install.add_css_class("suggested-action")
        self.btn_install.connect("clicked", self.on_install)
        btns.append(self.btn_install)
        box.append(btns)
        hero.add(box)
        self.page.add(hero)

        self.grp_new = Adw.PreferencesGroup(visible=False)
        texts.bind(self.grp_new.set_title, "u_new_title")
        self.page.add(self.grp_new)
        self.grp_items = Adw.PreferencesGroup(visible=False)
        texts.bind(self.grp_items.set_title, "u_items_title")
        texts.bind(self.grp_items.set_description, "u_items_desc")
        self.page.add(self.grp_items)
        self.grp_last = Adw.PreferencesGroup(visible=False)
        texts.bind(self.grp_last.set_title, "u_last_title")
        self.page.add(self.grp_last)
        if mindos_prefs:
            g = Adw.PreferencesGroup()
            texts.bind(g.set_title, "u_auto_title")
            g.add(pref_switch(texts, "update_notify", "u_notify", "u_notify_sub", "🔔"))
            self.page.add(g)
        self.page.add(self.output.group)
        self.dynamic_rows = []
        self.check()

    def clear_rows(self):
        for group, row in self.dynamic_rows:
            group.remove(row)
        self.dynamic_rows = []

    def add_row(self, group, title, subtitle=None, icon=None):
        row = Adw.ActionRow(title=GLib.markup_escape_text(title))
        if subtitle:
            row.set_subtitle(GLib.markup_escape_text(subtitle))
            row.set_subtitle_lines(3)
        if icon:
            row.add_prefix(Gtk.Label(label=icon))
        group.add(row)
        self.dynamic_rows.append((group, row))
        return row

    def check(self):
        if self.checking or self.output.busy:
            return
        self.checking = True
        self.spinner.start()
        self.btn_check.set_sensitive(False)
        self.lbl_status.set_label(self.texts.t("u_checking"))

        def worker():
            try:
                r = subprocess.run([MINDPKG, "check", "--json"], capture_output=True, text=True, timeout=180)
                info = json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else None
                err = None if info else (ANSI.sub("", r.stderr).strip().splitlines() or ["?"])[-1]
            except Exception as e:
                info, err = None, str(e)
            GLib.idle_add(self.show_info, info, err)

        threading.Thread(target=worker, daemon=True).start()

    def lang(self):
        return "en" if getattr(self.win, "current_lang_code", "tr") == "en" else "tr"

    def show_info(self, info, err=None):
        self.checking = False
        self.spinner.stop()
        self.btn_check.set_sensitive(True)
        if info is not None:
            self.info = info
        info = self.info
        if info is None:
            self.lbl_status.set_label(self.texts.t("u_check_fail", err=err or "?"))
            return False
        t = self.texts.t
        rel = info.get("release", {})
        self.lbl_name.set_label(f"MindOS Paradise {rel.get('installed', '')}".strip())
        self.clear_rows()

        latest = rel.get("latest") or {}
        notes = (latest.get("notes") or {}).get(self.lang()) or (latest.get("notes") or {}).get("tr") or []
        self.grp_new.set_visible(bool(rel.get("newer") and notes))
        if rel.get("newer"):
            self.grp_new.set_description(f"{latest.get('name', '')} · {latest.get('date', '')}")
            for n in notes:
                self.add_row(self.grp_new, str(n), icon="✨")

        if info.get("mindpkg", {}).get("newer"):
            mp = info["mindpkg"]
            self.add_row(self.grp_items, t("u_mindpkg"), f"{mp['installed']} → {mp['latest']}", "📦")
        for c in info.get("components", []):
            self.add_row(self.grp_items, c["name"], f"{c.get('installed') or '—'} → {c['version']}", "🪷")
        deb = info.get("debian", {})
        if deb.get("count"):
            names = ", ".join(deb.get("names", [])[:12]) + ("…" if deb["count"] > 12 else "")
            self.add_row(self.grp_items, t("u_debian"), t("u_debian_n", n=deb["count"], names=names), "🧩")
        for m in info.get("mind", []):
            self.add_row(self.grp_items, t("u_mind", name=m["name"]), f"{m['installed']} → {m['version']}", "📦")
        self.grp_items.set_visible(bool(info.get("pending")) and not info.get("scheduled"))

        last = info.get("last")
        self.grp_last.set_visible(bool(last))
        if last:
            import datetime
            when = datetime.datetime.fromtimestamp(last.get("time", 0)).strftime("%d.%m.%Y %H:%M")
            row = self.add_row(self.grp_last, t("u_last_ok" if last.get("ok") else "u_last_fail", when=when),
                               "\n".join(last.get("errors") or []) or None, "✅" if last.get("ok") else "⚠️")
            if not last.get("ok"):
                self.add_row(self.grp_last, t("u_last_log", log=last.get("log", "/var/log/mindos-update.log")))

        self.btn_cancel.set_visible(bool(info.get("scheduled")))
        if info.get("live"):
            self.lbl_status.set_label(t("u_live"))
            self.btn_install.set_visible(False)
        elif info.get("scheduled"):
            self.lbl_status.set_label(t("u_scheduled"))
            self.btn_install.set_label(t("u_reboot_now"))
            self.btn_install.set_visible(True)
        elif info.get("pending"):
            self.lbl_status.set_label(t("u_ready", name=latest.get("name", "")) if rel.get("newer")
                                      else t("u_pending", n=info["pending"]))
            self.btn_install.set_label(t("u_install"))
            self.btn_install.set_visible(True)
        else:
            self.lbl_status.set_label(t("u_uptodate"))
            self.btn_install.set_visible(False)
        return False

    def refresh(self):
        self.btn_install.set_label(self.texts.t("u_reboot_now" if (self.info or {}).get("scheduled") else "u_install"))
        if self.info is not None and not self.checking:
            self.show_info(None)

    def reboot(self):
        self.lbl_status.set_label(self.texts.t("u_rebooting"))
        self.btn_install.set_sensitive(False)
        self.btn_cancel.set_sensitive(False)
        subprocess.Popen(["systemctl", "reboot"])
        return False

    def on_install(self, button):
        if (self.info or {}).get("scheduled"):
            self.reboot()
            return
        t = self.texts.t
        dialog = Adw.MessageDialog(transient_for=self.win, heading=t("u_confirm_title"), body=t("u_confirm_body"))
        dialog.add_response("cancel", t("u_cancel"))
        dialog.add_response("go", t("u_install"))
        dialog.set_response_appearance("go", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("go")
        dialog.connect("response", lambda d, r: r == "go" and self.prepare())
        dialog.present()

    def prepare(self):
        self.btn_install.set_sensitive(False)
        self.btn_check.set_sensitive(False)
        self.lbl_status.set_label(self.texts.t("u_preparing"))
        self.spinner.start()
        # ilerleme sayfanın altında; odak çıktıya verilince sayfa oraya kayar
        GLib.timeout_add(300, lambda: self.output.view.grab_focus() and False)

        def done(rc):
            self.spinner.stop()
            self.btn_install.set_sensitive(True)
            self.btn_check.set_sensitive(True)
            if rc == 0 and os.path.islink("/system-update"):
                GLib.timeout_add_seconds(2, self.reboot)
                self.lbl_status.set_label(self.texts.t("u_rebooting"))
            else:
                if rc != 0:
                    self.lbl_status.set_label(self.texts.t("u_prepare_fail"))
                self.check()

        self.output.run(["pkexec", MINDPKG, "upgrade", "--offline"], done, self.texts.t("u_install"))

    def on_cancel(self, button):
        self.output.run(["pkexec", MINDPKG, "offline-cancel"], lambda rc: self.check(), self.texts.t("u_cancel"))



def nvidia_cards():
    """[(aygıt_no, ad)] NVIDIA ekran kartları"""
    try:
        out = subprocess.run(["lspci", "-nn", "-d", "10de:"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return []
    cards = []
    for line in out.splitlines():
        m = re.search(r"\[10de:([0-9a-f]{4})\]", line)
        if m and re.search(r"\[030[02]\]", line):
            name = re.findall(r"\[([^\]]*GeForce[^\]]*|[^\]]*RTX[^\]]*|[^\]]*Quadro[^\]]*)\]", line)
            cards.append((int(m.group(1), 16), name[0] if name else line.split(": ", 1)[-1]))
    return cards


class NvidiaGroup:
    """Donanım sayfasında NVIDIA kartı ve tek tıkla sürücü kurulumu (mindpkg install nvidia)"""

    def __init__(self, win, texts):
        self.win, self.texts = win, texts
        self.output = OutputPanel(texts)
        self.group = Adw.PreferencesGroup(visible=False)
        texts.bind(self.group.set_title, "nv_title")
        self.row = Adw.ActionRow()
        self.row.add_prefix(Gtk.Label(label="🎮"))
        self.row.set_subtitle_lines(3)
        self.button = Gtk.Button(valign=Gtk.Align.CENTER, visible=False)
        self.button.add_css_class("suggested-action")
        self.button.connect("clicked", self.on_click)
        self.row.add_suffix(self.button)
        self.group.add(self.row)
        self.state = None
        threading.Thread(target=lambda: GLib.idle_add(self.show, nvidia_cards()), daemon=True).start()

    def show(self, cards):
        if not cards:
            return False
        self.cards = cards
        self.group.set_visible(True)
        self.refresh()
        return False

    def refresh(self):
        if not getattr(self, "cards", None):
            return
        t = self.texts.t
        dev, name = self.cards[0]
        self.row.set_title(GLib.markup_escape_text(name))
        gen = "modern" if dev >= 0x1E00 else "legacy" if dev >= 0x1340 else "old"
        try:
            ver = open("/proc/driver/nvidia/version").readline().split("Kernel Module")[-1].split()[0]
        except (OSError, IndexError):
            ver = None
        installed = system_installed("nvidia-driver")
        if ver:
            self.state, sub = "running", t("nv_running", ver=ver)
        elif installed:
            self.state, sub = "reboot", t("nv_reboot")
        elif gen == "old" or os.path.exists("/run/live/medium"):
            self.state, sub = None, t("nv_old") if gen == "old" else t("nv_live")
        else:
            self.state, sub = "install", t("nv_modern" if gen == "modern" else "nv_legacy")
        self.row.set_subtitle(sub)
        self.button.set_visible(self.state in ("install", "reboot"))
        self.button.set_label(t("nv_install") if self.state == "install" else t("nv_restart"))

    def on_click(self, button):
        if self.state == "reboot":
            subprocess.Popen(["systemctl", "reboot"])
            return
        t = self.texts.t
        dialog = Adw.MessageDialog(transient_for=self.win, heading=t("nv_confirm"), body=t("nv_confirm_body"))
        dialog.add_response("cancel", t("u_cancel"))
        dialog.add_response("go", t("nv_install"))
        dialog.set_response_appearance("go", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", lambda d, r: r == "go" and self.install())
        dialog.present()

    def install(self):
        self.button.set_sensitive(False)

        def done(rc):
            self.button.set_sensitive(True)
            self.refresh()

        self.output.run(["pkexec", MINDPKG, "install", "nvidia"], done, self.texts.t("nv_install"))



def broadcom_cards():
    """[(ad, kullanılan sürücü|None)] Broadcom Wi-Fi kartları"""
    try:
        out = subprocess.run(["lspci", "-nnk", "-d", "14e4:"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return []
    cards = []
    for line in out.splitlines():
        if not line.startswith(("\t", " ")):
            if re.search(r"\[028[0-9]\]", line):
                name = re.sub(r"^.*?\]: (Broadcom Inc\. and subsidiaries )?", "", line)
                cards.append([re.sub(r" \[14e4:.*$", "", name), None])
        elif cards and "Kernel driver in use:" in line:
            cards[-1][1] = line.split(":", 1)[1].strip()
    return cards


class BroadcomGroup:
    """Donanım sayfasında, sürücüsü olmayan Broadcom Wi-Fi kartları için tek tıkla 'wl' kurulumu"""

    def __init__(self, win, texts, output):
        self.win, self.texts, self.output = win, texts, output
        self.group = Adw.PreferencesGroup(visible=False)
        texts.bind(self.group.set_title, "bc_title")
        self.row = Adw.ActionRow()
        self.row.add_prefix(Gtk.Label(label="📶"))
        self.row.set_subtitle_lines(3)
        self.button = Gtk.Button(valign=Gtk.Align.CENTER, visible=False)
        self.button.add_css_class("suggested-action")
        self.button.connect("clicked", lambda b: self.install())
        self.row.add_suffix(self.button)
        self.group.add(self.row)
        threading.Thread(target=lambda: GLib.idle_add(self.show, broadcom_cards()), daemon=True).start()

    def show(self, cards):
        self.cards = cards
        self.refresh()
        return False

    def refresh(self):
        if not getattr(self, "cards", None):
            return
        t = self.texts.t
        name, drv = self.cards[0]
        self.group.set_visible(True)
        self.row.set_title(GLib.markup_escape_text(name))
        need = drv is None and not os.path.exists("/run/live/medium")
        self.row.set_subtitle(t("bc_ok", drv=drv) if drv else t("bc_need") if need else t("nv_live"))
        self.button.set_visible(need)
        self.button.set_label(t("bc_install"))

    def install(self):
        self.button.set_sensitive(False)

        def done(rc):
            self.button.set_sensitive(True)
            self.cards = broadcom_cards()
            self.refresh()

        self.output.run(["pkexec", MINDPKG, "install", "broadcom"], done, self.texts.t("bc_install"))


def build_extra_pages(win):
    """Ana pencereye Paket Merkezi ve Sistem Bakımı sayfalarını ekler"""
    win.extra_texts = ExtraTexts(win)
    win.extra_updates = SystemUpdate(win, win.extra_texts)
    win.view_stack.add_named(win.extra_updates.page, "updates")
    win.extra_packages = PackageCenter(win, win.extra_texts)
    win.view_stack.add_named(win.extra_packages.page, "packages")
    win.extra_maintenance = Maintenance(win, win.extra_texts)
    win.view_stack.add_named(win.extra_maintenance.page, "maintenance")
    if hasattr(win, "page_hardware"):  # Donanım → NVIDIA (yalnızca NVIDIA kartı varsa görünür)
        win.extra_nvidia = NvidiaGroup(win, win.extra_texts)
        win.page_hardware.add(win.extra_nvidia.group)
        win.extra_broadcom = BroadcomGroup(win, win.extra_texts, win.extra_nvidia.output)
        win.page_hardware.add(win.extra_broadcom.group)
        win.page_hardware.add(win.extra_nvidia.output.group)
    if mindos_prefs and hasattr(win, "page_appearance"):  # Genel Ayarlar → Gizlilik
        win.page_appearance.add(build_privacy_group(win.extra_texts))


def extra_sidebar_items(win):
    t = win.extra_texts.t if hasattr(win, "extra_texts") else (lambda k: TEXTS[k][0])
    return [("updates", "⬆️", t("updates")), ("packages", "📦", t("packages")),
            ("maintenance", "🛠️", t("maintenance"))]


def update_extra_texts(win):
    if hasattr(win, "extra_texts"):
        win.extra_texts.refresh()
        win.extra_packages.refresh()
        win.extra_updates.refresh()
        if hasattr(win, "extra_nvidia"):
            win.extra_nvidia.refresh()
            win.extra_broadcom.refresh()
