#!/usr/bin/env python3
"""
Mind Helper — AI Brain, Linux Tutor & Appropriateness Engine
Combines deep Linux knowledge, polite demeanor, live system awareness,
real-time research, and safety filtering for user interactions and feedback inspection.
"""

import re
import json
import random
import urllib.parse
import requests
from system_facts import get_live_telemetry

# Safety Blocklist / Guardrails for inappropriate queries & feedback
INAPPROPRIATE_PATTERNS = [
    r'\b(fuck|shit|bitch|asshole|cunt|dick|pussy|whore|slut|bastard|fag|nigger|retard)\b',
    r'\b(porn|nsfw|sex|nude|hentai|erotic|blowjob)\b',
    r'\b(kill\s+yourself|suicide|make\s+a\s+bomb|ddos\s+attack|ransomware)\b',
    r'\b(destroy\s+all\s+files|rm\s+-rf\s+/\s*--no-preserve-root)\b',
    r'\b(hate\s+speech|white\s+supremacy|terrorist)\b'
]

GREETINGS = [
    "Here is the practical explanation and command usage for your query:",
    "Here are the relevant details from the Linux knowledge base:",
    "Here is the recommended workflow and guidance:",
    "Linux system guidance for your inquiry:",
    "Here is how this works in Linux and MindOS Paradise:"
]

CLOSINGS = [
    "\n\n*Tip: Use 'man <command>' in terminal to view the complete flag reference and manual.*",
    "\n\n*Feel free to ask for specific flags, options, or troubleshooting steps.*",
    "\n\n*You can also search the Articles tab for comprehensive guides and cheatsheets.*",
    "\n\n*Mind Helper is ready to answer any further Linux administration questions.*"
]

LINUX_KNOWLEDGE = {
    "mindpkg": {
        "title": "MindOS Paket Yöneticisi (`mindpkg`)",
        "keywords": ["mindpkg", "paket", "package", "install", "kur", "yükle", "uygulama", "kaldır",
                     "remove", "chrome", "vscode", ".mind", "program", "indir", "upgrade", "yükselt"],
        "content": (
            "`mindpkg`, MindOS'un paket yöneticisidir. Önce üreticinin resmi deposuna, sonra Debian "
            "deposuna, en son MindOS .mind deposuna bakar ve paketi tek komutla kurar.\n\n"
            "**Sık kullanılan komutlar:**\n"
            "• `sudo mindpkg install chrome` — Google Chrome (resmi Google deposu).\n"
            "• `sudo mindpkg install vscode` — Visual Studio Code.\n"
            "• `sudo mindpkg install <paket>` — Herhangi bir uygulama (ör. `vlc`, `gimp`, `obs-studio`).\n"
            "• `sudo mindpkg remove <paket>` — Kaldırır.\n"
            "• `mindpkg search <kelime>` — MindOS deposunda arar.\n"
            "• `sudo mindpkg update` — Depo indeksini günceller.\n"
            "• `sudo mindpkg upgrade` — Her şeyi yükseltir: önce mindpkg'nin kendisi (yeni sürüm varsa), "
            "sonra .mind paketleri, sonra Chrome/VS Code gibi sistem uygulamaları.\n\n"
            "Güvenlik güncellemeleri kurulu sistemde arka planda otomatik yapılır "
            "(Mind-Arc → Sistem Bakımı'ndan kapatılabilir).\n\n"
            "Grafik arayüz için: **Mind-Arc Kontrol Merkezi → Paket Merkezi** (`mind-arc --page packages`)."
        )
    },
    "mind-arc": {
        "title": "Mind-Arc Kontrol Merkezi",
        "keywords": ["mind-arc", "mindarc", "kontrol merkezi", "control center", "ayarlar", "bakım",
                     "maintenance", "güncelle", "update system"],
        "content": (
            "Mind-Arc, MindOS'un sistem yönetim uygulamasıdır.\n\n"
            "• **Paket Merkezi** — Arama, popüler uygulamalar, tek tıkla kur/kaldır (`mind-arc --page packages`).\n"
            "• **Sistem Bakımı** — RAM/zram durumu, disk kullanımı, sistem güncelleme ve temizlik "
            "(`mind-arc --page maintenance`).\n"
            "• **Performans** — CPU modu, önbellek temizleme ve ağ ayarları.\n"
            "• **Donanım ve Çevre Birimleri** — CPU/GPU/RAM bilgileri, USB ve giriş aygıtları."
        )
    },
    "zram": {
        "title": "Sıkıştırılmış Bellek (`zram`)",
        "keywords": ["zram", "swap", "takas", "ram", "bellek", "memory"],
        "content": (
            "MindOS, RAM'in yarısı kadar (en fazla 8 GB) zstd ile sıkıştırılmış zram takas alanı kullanır.\n\n"
            "• `swapon --show` — Etkin takas alanlarını gösterir.\n"
            "• `zramctl` — zram boyutu, kullanımı ve sıkıştırma oranı.\n"
            "• Ayar dosyası: `/etc/systemd/zram-generator.conf`."
        )
    },
    "systemctl": {
        "title": "systemd Service Architecture (`systemctl`)",
        "keywords": ["systemctl", "service", "systemd", "daemon", "restart service", "start service", "stop service", "enable service"],
        "content": (
            "`systemctl` is the central command for governing systemd units, managing background daemons, system targets, and hardware sockets.\n\n"
            "**Key Commands:**\n"
            "• `systemctl status <unit>` — Inspect running state, active PID, memory consumption, and recent log bursts.\n"
            "• `sudo systemctl start|stop|restart <unit>` — Start, stop, or restart a service immediately.\n"
            "• `sudo systemctl enable --now <unit>` — Enable the daemon at system boot AND start it now.\n"
            "• `sudo systemctl daemon-reload` — Force systemd to re-parse configuration changes on disk.\n"
            "• `systemctl list-failed` — Reveal any crashed units that encountered errors during startup."
        )
    },
    "journalctl": {
        "title": "Systemd Journal Logs (`journalctl`)",
        "keywords": ["journalctl", "logs", "view logs", "system logs", "errors", "service log"],
        "content": (
            "`journalctl` queries the centralized binary logs captured from kernel rings, services, and stdout/stderr streams.\n\n"
            "**Key Invocations:**\n"
            "• `journalctl -xeu <service>` — Review deep diagnostic errors of a failed daemon with full context.\n"
            "• `journalctl -u <service> -f` — Stream real-time log events as they occur.\n"
            "• `journalctl -b` — Read exclusively from the current boot cycle.\n"
            "• `sudo journalctl --vacuum-size=200M` — Reclaim disk storage by purging aged logs exceeding 200MB."
        )
    },
    "chmod": {
        "title": "File Permission Modes (`chmod`)",
        "keywords": ["chmod", "permission", "permissions", "access denied", "read write", "executable"],
        "content": (
            "`chmod` configures read (`r=4`), write (`w=2`), and execute (`x=1`) access permissions for Owner, Group, and Others.\n\n"
            "**Standard Recipes:**\n"
            "• `chmod +x <file>` — Grant execution rights to a shell script or binary.\n"
            "• `chmod 644 <file>` — Standard mode for files: Owner reads/writes; everyone else reads only.\n"
            "• `chmod 755 <directory>` — Standard mode for directories: Owner full control; others can browse and execute.\n"
            "• `chmod 600 <key>` — Standard security for SSH private keys; the system will refuse open permissions."
        )
    },
    "chown": {
        "title": "File & Directory Ownership (`chown`)",
        "keywords": ["chown", "owner", "ownership", "group"],
        "content": (
            "`chown` transfers user and group ownership of a file or directory.\n\n"
            "**Standard Usage:**\n"
            "• `sudo chown user:group filename` — Reassign both user and primary group ownership.\n"
            "• `sudo chown -R noodle:noodle /opt/directory` — Recursively claim ownership of an entire directory tree."
        )
    },
    "memory": {
        "title": "RAM, Caches & System Memory Management",
        "keywords": ["ram", "memory", "free memory", "swap", "oom", "cache", "buffer"],
        "content": (
            "Linux manages memory dynamically through virtual address pages, page caches, and swap space.\n\n"
            "**Core Principle:** Unused RAM is wasted RAM. The Linux kernel aggressively uses spare memory to cache disk reads. When applications need memory, cached pages are freed instantaneously.\n\n"
            "**Inspection Commands:**\n"
            "• `free -h` — Inspect total, used, free, buff/cache, and available physical memory.\n"
            "• `vmstat 1` — Observe memory swapping and context switching in live intervals.\n"
            "• `cat /proc/meminfo` — Detailed kernel statistics on physical page allocations."
        )
    },
    "apt": {
        "title": "Package Management (`apt`)",
        "keywords": ["apt", "install", "update", "upgrade", "package", "dpkg", "repository"],
        "content": (
            "`apt` interfaces with distribution repositories to resolve dependencies, verify cryptographic signatures, and install software.\n\n"
            "**Key Maintenance Commands:**\n"
            "• `sudo apt update` — Synchronize package metadata from remote archive mirrors.\n"
            "• `sudo apt upgrade -y` — Upgrade all installed packages to their latest secure release.\n"
            "• `sudo apt autoremove --purge -y` — Remove orphaned dependencies left behind by uninstalled software.\n"
            "• `sudo apt clean` — Purge downloaded `.deb` installer caches in `/var/cache/apt/archives`."
        )
    },
    "disk": {
        "title": "Storage Volumes & Disk Capacity",
        "keywords": ["disk", "storage", "full", "space", "df", "du", "lsblk", "mount"],
        "content": (
            "Linux storage represents filesystems mounted at unified directory paths rather than separate drives.\n\n"
            "**Diagnostic Tools:**\n"
            "• `df -h` — Display disk free capacity across all mounted storage points.\n"
            "• `lsblk -f` — View storage devices, partitions, filesystem types (ext4, btrfs), and mount destinations.\n"
            "• `sudo du -sh /* 2>/dev/null | sort -h` — Find the heaviest directories consuming storage capacity."
        )
    },
    "process": {
        "title": "Process Lifecycle & Resource Monitoring",
        "keywords": ["process", "ps", "top", "htop", "kill", "pid", "cpu usage"],
        "content": (
            "Every running program exists as a process identified by a unique PID (Process ID) tracked in `/proc`.\n\n"
            "**Process Commands:**\n"
            "• `ps aux | grep <name>` — Locate the PID and command arguments of a specific process.\n"
            "• `kill -15 <PID>` — Send `SIGTERM` for polite, graceful application termination.\n"
            "• `kill -9 <PID>` — Send `SIGKILL` for immediate, forceful kernel termination.\n"
            "• `top` or `htop` — Live interactive monitoring of CPU, RAM, and process consumption."
        )
    },
    "network": {
        "title": "Network Sockets & Port Discovery",
        "keywords": ["network", "port", "ip", "ss", "ping", "socket", "dns", "connection"],
        "content": (
            "Modern Linux manages networking using the `iproute2` suite.\n\n"
            "**Key Commands:**\n"
            "• `ip a` — Inspect IP addresses and interface states.\n"
            "• `ss -tulpn` — Display all listening TCP and UDP sockets along with their owning process names.\n"
            "• `ping -c 4 1.1.1.1` — Measure network reachability and packet latency.\n"
            "• `curl -I https://debian.org` — Inspect HTTP response headers directly."
        )
    }
}

class MindHelperBrain:
    def __init__(self):
        pass

    def validate_content(self, text: str) -> tuple[bool, str]:
        """
        Inspects query or feedback content for appropriateness.
        Returns: (is_appropriate: bool, explanation: str)
        """
        if not text or not text.strip():
            return False, "Content is empty."

        clean_text = text.lower().strip()

        # Check safety blocklist
        for pattern in INAPPROPRIATE_PATTERNS:
            if re.search(pattern, clean_text, re.IGNORECASE):
                return False, (
                    "Content contains language or destructive requests "
                    "that do not align with our principles of constructive assistance."
                )

        # Minimum substantive length check
        if len(clean_text) < 4:
            return False, "Content is too brief to convey meaningful thought."

        return True, "Content is polite and appropriate."

    def answer_query(self, user_query: str) -> str:
        """
        Analyzes the user's question, teaches the relevant Linux concept,
        and provides an accurate, practical response.
        """
        is_safe, reason = self.validate_content(user_query)
        if not is_safe:
            return (
                "✦ Mind Helper Response ✦\n\n"
                f"I must decline to process this inquiry.\n\n"
                f"*Reason*: {reason}\n\n"
                "I am here to teach and explain Linux with clarity and mutual respect. "
                "Please rephrase your inquiry."
            )

        q_lower = user_query.lower()

        # Check for live system inquiries
        if any(w in q_lower for w in ["how much ram", "memory usage", "uptime", "how long", "cpu", "kernel", "system status", "telemetry", "my system"]):
            return self._generate_telemetry_response(user_query)

        # Search Linux Knowledge Base
        best_match = None
        highest_score = 0
        for topic_key, topic_data in LINUX_KNOWLEDGE.items():
            score = 0
            for kw in topic_data["keywords"]:
                if kw in q_lower:
                    score += 3
            if topic_key in q_lower:
                score += 5
            if score > highest_score:
                highest_score = score
                best_match = topic_data

        intro = random.choice(GREETINGS)
        outro = random.choice(CLOSINGS)

        if best_match and highest_score >= 3:
            response = (
                f"{intro}\n\n"
                f"### {best_match['title']}\n\n"
                f"{best_match['content']}\n"
                f"{outro}"
            )
            return response

        # General Linux reasoning / online fallback
        web_info = self._attempt_web_research(user_query)
        if web_info:
            return (
                f"{intro}\n\n"
                f"{web_info}\n"
                f"{outro}"
            )

        # Fallback intelligent guidance
        return (
            f"{intro}\n\n"
            f"You inquired regarding: **{user_query.strip()}**\n\n"
            "In Linux, every operational topic can be explored directly through standard system tools:\n\n"
            "1. **Manual Pages**: Run `man <command>` or `man -k <keyword>` to read authoritative documentation.\n"
            "2. **Real-time Diagnostics**: Use `journalctl -xe` to inspect recent system journal events.\n"
            "3. **Process Vitals**: Use `top` or `ps aux` to observe running threads.\n"
            "4. **Articles & Guides**: Check the Articles tab for curated in-depth tutorials.\n\n"
            "If you seek to understand a specific command (such as `chmod`, `systemctl`, `apt`, `ss`, or `df`), "
            "name it directly, and I will explain its syntax, flags, and usage."
            f"{outro}"
        )

    def _generate_telemetry_response(self, query: str) -> str:
        """Generates real-time diagnostic response using actual system stats."""
        t = get_live_telemetry()
        intro = random.choice(GREETINGS)
        outro = random.choice(CLOSINGS)

        return (
            f"{intro}\n\n"
            "### Live System Vitals\n\n"
            f"• **System Uptime**: `{t['uptime_str']}`\n"
            f"• **Memory (RAM)**: `{t['mem_used_gb']} GiB` used of `{t['mem_total_gb']} GiB` ({t['mem_percent']}% utilized)\n"
            f"• **CPU Activity**: `{t['cpu_percent']}%` across `{t['cpu_count']}` logical cores (Load average: `{t['load_avg']}`)\n"
            f"• **Storage (Root)**: `{t['disk_used_gb']} GiB` of `{t['disk_total_gb']} GiB` ({t['disk_percent']}% used)\n"
            f"• **Active Processes**: `{t['proc_count']}` running under Kernel `{t['kernel']}` on node `{t['node']}`\n\n"
            "System telemetry indicates normal operation."
            f"{outro}"
        )

    def _attempt_web_research(self, query: str) -> str:
        """Attempts a quick web lookup via DuckDuckGo Instant Answer API."""
        try:
            import mindos_prefs
            if not mindos_prefs.get("web_search"):  # soru DuckDuckGo'ya gider; yalnızca izinle
                return None
        except Exception:
            return None
        try:
            clean_q = urllib.parse.quote_plus(f"linux {query}")
            url = f"https://api.duckduckgo.com/?q={clean_q}&format=json&no_html=1&skip_disambig=1"
            headers = {"User-Agent": "MindHelper/1.0 (MindOS Paradise; Linux)"}
            resp = requests.get(url, headers=headers, timeout=2.5)
            if resp.status_code == 200:
                data = resp.json()
                abstract = data.get("AbstractText", "")
                if abstract:
                    heading = data.get("Heading", "Linux Architecture")
                    return f"### {heading}\n\n{abstract}"
                related = data.get("RelatedTopics", [])
                if related and "Text" in related[0]:
                    return f"### Linux Telemetry\n\n{related[0]['Text']}"
        except Exception:
            pass
        return None

if __name__ == "__main__":
    brain = MindHelperBrain()
    print("Testing answer on systemctl:")
    print(brain.answer_query("how does systemctl work?"))
