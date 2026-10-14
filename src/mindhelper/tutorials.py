#!/usr/bin/env python3
"""
Mind Helper — Linux Academy & Comprehensive Tutorial Library
Curated, high-yield, practical Linux administration and engineering guides.
Contains real-world commands, configuration recipes, and troubleshooting workflows.
"""

TUTORIALS = [
    {
        "id": "shell_navigation",
        "category": "Core Fundamentals",
        "title": "Terminal Navigation & Essential File Operations",
        "subtitle": "Navigating directories, viewing files, standard I/O streams, and shortcuts",
        "read_time": "5 min",
        "content": (
            "THE LINUX FILESYSTEM HIERARCHY\n"
            "In Linux, all files and storage devices branch from a single root directory: '/'.\n"
            "Key top-level directories:\n"
            "  /bin & /usr/bin : Essential user binaries and command utilities\n"
            "  /etc            : System-wide configuration files\n"
            "  /home           : User personal directories and application settings\n"
            "  /var/log        : System and service log files\n"
            "  /tmp            : Temporary storage (cleared upon system reboot)\n\n"
            "CORE NAVIGATION COMMANDS:\n"
            "  pwd             : Print working directory (current path)\n"
            "  ls -lah         : List all files including hidden dotfiles, with file sizes in human units (KB/MB)\n"
            "  cd <path>       : Change working directory\n"
            "  cd ..           : Move up one parent directory level\n"
            "  cd ~ or cd      : Return directly to your home directory (/home/username)\n"
            "  cd -            : Toggle back to the previous working directory\n\n"
            "FILE & DIRECTORY MANIPULATION:\n"
            "  mkdir -p a/b/c  : Create nested directory paths without error if they already exist\n"
            "  cp -r src/ dst/ : Copy files or directories recursively\n"
            "  mv src dst      : Move or rename files and directories\n"
            "  rm -i file      : Interactively prompt before deleting a file\n"
            "  rm -rf dir/     : Force delete directory and contents (use with extreme caution)\n"
            "  touch file.txt  : Create an empty file or update file timestamps\n\n"
            "VIEWING & SEARCHING CONTENT:\n"
            "  cat file.txt    : Print file contents directly to standard output\n"
            "  less file.txt   : Scroll through long files interactively (press 'q' to quit, '/' to search)\n"
            "  head -n 20 file : Display the first 20 lines of a file\n"
            "  tail -f app.log : Follow live log file updates in real time\n"
            "  grep -rn 'txt' .: Search recursively for 'txt' across all files with line numbers\n\n"
            "STANDARD STREAMS & PIPES:\n"
            "Every Linux process operates with three standard file descriptors:\n"
            "  0 : Standard Input  (stdin)\n"
            "  1 : Standard Output (stdout)\n"
            "  2 : Standard Error  (stderr)\n\n"
            "Common I/O redirection patterns:\n"
            "  cmd > file.txt   : Overwrite file with stdout\n"
            "  cmd >> file.txt  : Append stdout to file\n"
            "  cmd 2>&1 file    : Redirect stderr into stdout\n"
            "  cmd1 | cmd2      : Pipe stdout of cmd1 directly into stdin of cmd2\n\n"
            "ESSENTIAL TERMINAL SHORTCUTS:\n"
            "  Ctrl + C : Cancel or terminate the currently running foreground command\n"
            "  Ctrl + Z : Suspend command to background (resume with 'fg' or 'bg')\n"
            "  Ctrl + R : Interactively reverse-search through your bash command history\n"
            "  Ctrl + L : Clear terminal screen (equivalent to typing 'clear')\n"
            "  Ctrl + A : Move cursor to the beginning of the command line\n"
            "  Ctrl + E : Move cursor to the end of the command line\n"
        )
    },
    {
        "id": "permissions_chown",
        "category": "Security & Permissions",
        "title": "Linux Permissions: Numerical Modes, Ownership & Access",
        "subtitle": "Mastering chmod, chown, octal calculations, and directory permissions",
        "read_time": "6 min",
        "content": (
            "THE PERMISSION STRUCTURE:\n"
            "Every file and directory in Linux has permissions assigned to three entities:\n"
            "  1. Owner (u)  : The user who created or owns the file\n"
            "  2. Group (g)  : The group assigned to the file\n"
            "  3. Others (o) : All other users on the operating system\n\n"
            "Each entity has three permission bits:\n"
            "  r (Read)    = 4 : View file content or list directory entries\n"
            "  w (Write)   = 2 : Modify, rename, or delete file; create files in directory\n"
            "  x (Execute) = 1 : Run script/binary; enter directory ('cd')\n\n"
            "OCTAL PERMISSION CALCULATION:\n"
            "Add the values together for each entity (Owner, Group, Others):\n"
            "  7 = 4 + 2 + 1 (Read + Write + Execute)\n"
            "  6 = 4 + 2     (Read + Write)\n"
            "  5 = 4 + 1     (Read + Execute)\n"
            "  4 = 4         (Read only)\n"
            "  0 = None      (No permissions)\n\n"
            "STANDARD PRACTICAL RECIPES:\n"
            "  chmod 644 file.txt      : Owner can read/write; Group & Others can read only\n"
            "                            (Standard security for ordinary configuration & code files)\n"
            "  chmod 755 script.sh     : Owner full rights; Group & Others can read and execute\n"
            "                            (Standard mode for binaries, scripts, and directories)\n"
            "  chmod +x build.sh       : Add execute permission to the current script\n"
            "  chmod 700 ~/.ssh        : Owner read/write/cd; all other users blocked completely\n"
            "  chmod 600 ~/.ssh/id_*   : Owner read/write only; required by SSH for private keys\n\n"
            "CHANGING OWNERSHIP WITH CHOWN:\n"
            "Use 'chown' to assign owner user and group (requires sudo):\n"
            "  sudo chown user:group filename\n"
            "  sudo chown -R noodle:noodle /var/www/html\n"
            "  sudo chown root:root /etc/systemd/system/app.service\n\n"
            "SPECIAL PERMISSION BITS:\n"
            "  SUID (chmod 4755): Runs binary with file owner's privileges (e.g., passwd command)\n"
            "  SGID (chmod 2755): Inherits parent directory's group for all newly created files\n"
            "  Sticky Bit (chmod 1777 /tmp): Users can only delete files they personally own\n"
        )
    },
    {
        "id": "systemd_services",
        "category": "System Administration",
        "title": "Systemd Service Management & journalctl Logs",
        "subtitle": "Controlling daemons, inspecting failures, analyzing boot logs, and writing units",
        "read_time": "7 min",
        "content": (
            "WHAT IS SYSTEMD?\n"
            "systemd is the init system and service manager that initializes the Linux kernel\n"
            "into userspace (running as Process ID 1). It manages background daemons, network sockets,\n"
            "mount points, and system timers.\n\n"
            "ESSENTIAL SYSTEMCTL COMMANDS:\n"
            "  systemctl status <service>       : Check state, PID, memory usage, and recent log lines\n"
            "  sudo systemctl start <service>   : Start a service immediately\n"
            "  sudo systemctl stop <service>    : Gracefully stop a running service\n"
            "  sudo systemctl restart <service> : Restart service (stop then start)\n"
            "  sudo systemctl reload <service>  : Reload config without dropping active connections\n"
            "  sudo systemctl enable <service>  : Configure service to start automatically at system boot\n"
            "  sudo systemctl disable <service> : Prevent service from starting at system boot\n"
            "  sudo systemctl enable --now <svc>: Enable for boot AND start it immediately in one command\n"
            "  systemctl is-active <service>    : Returns 'active' or 'inactive' (ideal for shell scripts)\n"
            "  systemctl list-failed            : Display all services that failed or crashed\n\n"
            "ANALYZING LOGS WITH JOURNALCTL:\n"
            "systemd centralizes all daemon output and kernel events into a high-speed journal.\n"
            "  journalctl -u <service> -f       : Stream logs in real time as they arrive (like 'tail -f')\n"
            "  journalctl -u <service> -n 50    : Display the last 50 log lines for a service\n"
            "  journalctl -xeu <service>        : Deep diagnostic view explaining why a service failed\n"
            "  journalctl -p err -b             : Show only error and fatal messages from the current boot\n"
            "  journalctl --since '30 min ago'  : Show log entries recorded within the last half hour\n"
            "  sudo journalctl --vacuum-size=200M: Trim journal disk usage to under 200MB\n\n"
            "CREATING A CUSTOM SERVICE UNIT:\n"
            "Create file: /etc/systemd/system/myapp.service\n"
            "  [Unit]\n"
            "  Description=My Custom Application\n"
            "  After=network.target\n\n"
            "  [Service]\n"
            "  Type=simple\n"
            "  User=noodle\n"
            "  WorkingDirectory=/opt/myapp\n"
            "  ExecStart=/usr/bin/python3 /opt/myapp/server.py\n"
            "  Restart=on-failure\n"
            "  RestartSec=5s\n\n"
            "  [Install]\n"
            "  WantedBy=multi-user.target\n\n"
            "After editing or adding units, notify systemd:\n"
            "  sudo systemctl daemon-reload\n"
            "  sudo systemctl enable --now myapp.service\n"
        )
    },
    {
        "id": "storage_filesystems",
        "category": "Storage & Filesystems",
        "title": "Disk Space, Filesystems & Permanent Mounts (/etc/fstab)",
        "subtitle": "Diagnosing full disks, inspecting partitions, and configuring /etc/fstab safely",
        "read_time": "6 min",
        "content": (
            "CHECKING DISK SPACE & VOLUMES:\n"
            "  df -h                  : Display filesystem usage in human-readable gigabytes (GB)\n"
            "  lsblk -f               : Show all physical drives, partitions, filesystem types (ext4/btrfs), and mount points\n"
            "  blkid                  : Print permanent UUID identifiers for all partitions\n\n"
            "FINDING HEAVY FILES & DIRECTORIES:\n"
            "When disk space runs low, identify heavy culprits:\n"
            "  sudo du -sh /* 2>/dev/null | sort -h\n"
            "  sudo du -sh /var/log /var/cache /home/* 2>/dev/null | sort -h\n"
            "  find / -type f -size +500M 2>/dev/null\n"
            "  (Searches the entire system for individual files larger than 500MB)\n\n"
            "MOUNTING & UNMOUNTING STORAGE:\n"
            "  sudo mkdir -p /mnt/data\n"
            "  sudo mount /dev/sdb1 /mnt/data\n"
            "  sudo umount /mnt/data\n"
            "  (If unmount fails due to 'device busy', find blocking process with: lsof +D /mnt/data)\n\n"
            "CONFIGURING PERMANENT MOUNTS IN /etc/fstab:\n"
            "To mount disks automatically at system boot, add an entry to /etc/fstab.\n"
            "Always identify drives by permanent UUID rather than transient device names like /dev/sdb1:\n"
            "  1. Run 'sudo blkid' to copy the partition UUID\n"
            "  2. Add entry to /etc/fstab:\n"
            "     UUID=a1b2c3d4-0000-1111-2222-333344445555  /mnt/data  ext4  defaults,noatime  0  2\n\n"
            "CRITICAL SAFETY RULE FOR /etc/fstab:\n"
            "Never reboot after editing /etc/fstab without testing syntax first!\n"
            "  sudo mount -a\n"
            "If 'mount -a' completes with zero output or errors, the syntax is valid and safe.\n"
            "If an error appears, fix it immediately to avoid boot failure into emergency rescue mode.\n"
        )
    },
    {
        "id": "package_management",
        "category": "Software Management",
        "title": "Package Management with APT & Flatpak",
        "subtitle": "Installing, updating, cleaning packages, and resolving broken dependencies",
        "read_time": "5 min",
        "content": (
            "APT ARCHITECTURE (DEBIAN / UBUNTU):\n"
            "APT (Advanced Package Tool) manages software dependencies and coordinates deb packages.\n\n"
            "DAILY MAINTENANCE WORKFLOW:\n"
            "  sudo apt update               : Refresh mirror index of available packages\n"
            "  sudo apt upgrade -y           : Upgrade installed software without removing existing packages\n"
            "  sudo apt full-upgrade         : Comprehensive upgrade that resolves dependency changes (ideal for distribution point updates)\n\n"
            "MANAGING PACKAGES:\n"
            "  sudo apt install <package>    : Download and install package and required dependencies\n"
            "  sudo apt remove <package>     : Uninstall binary package but retain user config files\n"
            "  sudo apt purge <package>      : Uninstall binary package AND delete configuration files\n"
            "  apt search <keyword>          : Search repository for packages matching term\n"
            "  apt show <package>            : Inspect version, license, maintainer, and package description\n"
            "  dpkg -l | grep <name>         : Check if a specific package is currently installed locally\n\n"
            "RECLAIMING DISK SPACE & REPAIRING:\n"
            "  sudo apt autoremove --purge   : Remove unneeded dependencies left behind by uninstalled software\n"
            "  sudo apt clean                : Delete downloaded .deb installer archives in /var/cache/apt/archives/\n"
            "  sudo apt --fix-broken install : Automatically resolve and repair broken package dependencies\n\n"
            "FLATPAK APP MANAGEMENT:\n"
            "Flatpak provides sandboxed applications across Linux distributions:\n"
            "  flatpak list                  : List installed Flatpak applications and runtimes\n"
            "  flatpak update                : Update all installed Flatpaks to newest releases\n"
            "  flatpak install flathub <app> : Install application from Flathub repository\n"
            "  flatpak run <app.id>          : Launch application from terminal\n"
        )
    },
    {
        "id": "network_diagnostics",
        "category": "Networking & Security",
        "title": "Network Diagnostics, Port Inspection & UFW Firewall",
        "subtitle": "Checking IP addresses, routing, open sockets with ss, and firewall configuration",
        "read_time": "6 min",
        "content": (
            "NETWORK INTERFACES & ROUTING:\n"
            "Modern Linux uses the high-performance 'iproute2' toolset:\n"
            "  ip a                     : Show network interfaces, MAC addresses, and assigned IP addresses\n"
            "  ip r                     : Show IP routing table and default internet gateway\n"
            "  ip link set eth0 up/down : Bring interface up or take it offline\n\n"
            "INSPECTING OPEN PORTS & SOCKETS WITH SS:\n"
            "'ss' replaces legacy 'netstat' for examining network connections and listening ports:\n"
            "  sudo ss -tulpn           : List all listening TCP (-t) and UDP (-u) sockets\n"
            "                             with process names (-p) and port numbers (-n)\n"
            "  sudo ss -tulpn | grep :80: Check if port 80 (HTTP) or 443 (HTTPS) is occupied\n"
            "  ss -ta                   : Display all established and waiting TCP connections\n\n"
            "CONNECTIVITY & DNS DIAGNOSTICS:\n"
            "  ping -c 4 1.1.1.1        : Verify raw network reachability and packet latency\n"
            "  resolvectl status        : Inspect systemd-resolved DNS servers and domains\n"
            "  curl -I https://debian.org: Fetch HTTP headers to test web service response codes\n"
            "  traceroute 1.1.1.1       : Trace network hops between system and destination server\n\n"
            "MANAGING UFW (UNCOMPLICATED FIREWALL):\n"
            "UFW manages Linux iptables / nftables packet filtering rules simply and cleanly:\n"
            "  sudo ufw status verbose  : Display firewall state and active port rules\n"
            "  sudo ufw enable          : Enable firewall protection\n"
            "  sudo ufw disable         : Temporarily disable firewall\n"
            "  sudo ufw allow 22/tcp    : Allow incoming SSH traffic\n"
            "  sudo ufw allow 80/tcp    : Allow HTTP web traffic\n"
            "  sudo ufw allow 443/tcp   : Allow HTTPS encrypted web traffic\n"
            "  sudo ufw delete allow 22/tcp: Delete existing firewall rule\n"
        )
    },
    {
        "id": "memory_processes",
        "category": "System Performance",
        "title": "Process Monitoring, Signals & System Memory",
        "subtitle": "Tracking CPU/RAM consumers, load averages, and safely terminating processes",
        "read_time": "6 min",
        "content": (
            "MONITORING RUNNING PROCESSES:\n"
            "  ps aux                   : Print snapshot of every running process on the system\n"
            "  ps aux --sort=-%mem | head -n 10: Display the top 10 highest memory consuming processes\n"
            "  ps aux --sort=-%cpu | head -n 10: Display the top 10 highest CPU consuming processes\n"
            "  pgrep -l nginx           : Find process ID (PID) matching name 'nginx'\n"
            "  htop                     : Interactive, colorized process viewer (F9 to kill, F6 to sort)\n\n"
            "UNDERSTANDING SYSTEM MEMORY & CACHES:\n"
            "Run 'free -h' to inspect memory allocations:\n"
            "  total      : Physical RAM installed in the machine\n"
            "  used       : Memory currently consumed by running applications\n"
            "  free       : Memory completely untouched\n"
            "  buff/cache : Memory utilized by Linux kernel to cache disk I/O\n"
            "  available  : Memory available to launch new applications without swapping\n\n"
            "Note: The Linux kernel uses idle RAM for disk cache. When apps need memory,\n"
            "cached pages are dropped instantly. 'Available' is the true indicator of free capacity.\n\n"
            "UNDERSTANDING SYSTEM LOAD AVERAGE:\n"
            "Shown in 'uptime' as three numbers: (1-minute, 5-minute, 15-minute load averages).\n"
            "Compare the numbers to your CPU core count ('nproc'):\n"
            "  If load average equals CPU core count: System is at 100% full capacity\n"
            "  If load average exceeds CPU core count: Tasks are queued and waiting for CPU time\n\n"
            "PROCESS SIGNALS & SAFE TERMINATION:\n"
            "  kill -15 <PID> (SIGTERM) : Graceful request to stop. The application saves open files,\n"
            "                             closes network sockets, and terminates cleanly.\n"
            "  kill -9 <PID> (SIGKILL)  : Immediate kernel termination. Used when a process is frozen\n"
            "                             and unresponsive to SIGTERM.\n"
            "  killall <process_name>   : Terminate all processes matching application name\n"
            "  pkill -f 'pattern'       : Match against full command line string\n"
        )
    },
    {
        "id": "users_ssh",
        "category": "User Administration",
        "title": "User Accounts, Sudo Privileges & SSH Key Security",
        "subtitle": "Creating users, managing groups, sudoers, and setting up SSH key authentication",
        "read_time": "5 min",
        "content": (
            "MANAGING USERS & GROUPS:\n"
            "  sudo adduser newuser       : Interactively create a new user account with home directory\n"
            "  sudo deluser --remove-home user: Remove user account and wipe their home directory\n"
            "  sudo usermod -aG sudo newuser: Grant sudo administrative privileges to user\n"
            "  groups <username>          : List all groups the specified user belongs to\n"
            "  id                         : Display current user UID, GID, and active groups\n\n"
            "CONFIGURING SUDO PERMISSIONS:\n"
            "Never edit /etc/sudoers directly with standard text editors.\n"
            "Always use the safe syntax-checking editor:\n"
            "  sudo visudo\n"
            "To grant passwordless sudo (standard in live environments):\n"
            "  username ALL=(ALL) NOPASSWD: ALL\n\n"
            "MODERN SSH KEY AUTHENTICATION:\n"
            "SSH keys provide cryptographic authentication superior to passwords.\n"
            "  1. Generate modern Ed25519 keypair on client:\n"
            "     ssh-keygen -t ed25519 -C 'user@mindos'\n"
            "     (Generates private key ~/.ssh/id_ed25519 and public key ~/.ssh/id_ed25519.pub)\n\n"
            "  2. Install public key onto remote machine:\n"
            "     ssh-copy-id -i ~/.ssh/id_ed25519.pub user@remote-ip\n\n"
            "  3. Strict file permission rules (SSH blocks access if permissions are loose):\n"
            "     chmod 700 ~/.ssh\n"
            "     chmod 600 ~/.ssh/id_ed25519\n"
            "     chmod 644 ~/.ssh/id_ed25519.pub\n"
            "     chmod 600 ~/.ssh/authorized_keys\n"
        )
    },
    {
        "id": "mindos_tuning",
        "category": "MindOS Paradise",
        "title": "MindOS Paradise Desktop Shortcuts & System Tips",
        "subtitle": "Mastering GNOME shortcuts, Calamares installer tips, and terminal productivity",
        "read_time": "4 min",
        "content": (
            "MINDOS PARADISE DESKTOP SHORTCUTS:\n"
            "  Super (Windows key)   : Open GNOME Applications Overview and Workspace view\n"
            "  Ctrl + Alt + T        : Open Terminal window immediately\n"
            "  Super + Left / Right  : Snap active window to left or right half of the screen\n"
            "  Super + Up / Down     : Maximize active window or restore / minimize\n"
            "  Super + V             : Open Clipboard History popup\n"
            "  Alt + Tab             : Cycle through running applications\n"
            "  Alt + ` (Backtick)    : Cycle through multiple windows of the same application\n"
            "  Print Screen          : Interactive screenshot and screen recording tool\n\n"
            "LIVE SESSION & INSTALLATION TIPS:\n"
            "  • MindOS Installer (Calamares):\n"
            "    Launch from the dock or desktop to install MindOS Paradise to disk.\n"
            "    Supports guided automatic partitioning and manual partition configuration.\n"
            "  • Default Live User Credentials:\n"
            "    Username : user\n"
            "    Sudo     : Full administrative passwordless sudo access\n\n"
            "MIND HELPER FEATURES:\n"
            "  • Sentinel AI Tab: Ask any Linux question directly to receive instant command recipes\n"
            "  • Articles & Tutorials: In-depth guides covering system management and networking\n"
            "  • Developer Feedback: Direct feedback portal to send suggestions to the development team\n"
            "  • Diagnostic Self-Test: Run 'mindhelper --check' in terminal anytime to verify system vitals\n"
        )
    },
    {
        "id": "mindpkg_guide",
        "category": "MindOS",
        "title": "mindpkg: MindOS Paket Yöneticisi",
        "subtitle": "Tek komutla uygulama kurma, kaldırma, arama ve kendi .mind paketini oluşturma",
        "read_time": "6 min",
        "content": (
            "MINDPKG NEDİR?\n"
            "mindpkg, MindOS'un kendi paket yöneticisidir. Bir uygulamayı nereden bulursa bulsun\n"
            "tek komutla kurar; hangi depoyu kullanacağına kendisi karar verir.\n\n"
            "PAKET HANGİ SIRAYLA ARANIR? (MindOS Paradise)\n"
            "  1. Üreticinin resmi deposu  : chrome, vscode gibi uygulamalar imzalı resmi depodan\n"
            "                                gelir ve sistemle birlikte otomatik güncellenir\n"
            "  2. Debian deposu            : ~70.000 paket, Paradise için derlenmiş doğru sürüm\n"
            "  3. MindOS .mind deposu      : Debian'da olmayan paketler (15.000+ paket)\n\n"
            "TEMEL KOMUTLAR\n"
            "  sudo mindpkg install chrome       : Google Chrome'u kurar\n"
            "  sudo mindpkg install vscode       : Visual Studio Code'u kurar\n"
            "  sudo mindpkg install vlc gimp     : Birden fazla paketi aynı anda kurar\n"
            "  sudo mindpkg remove chrome        : Paketi kaldırır\n"
            "  sudo mindpkg update               : MindOS depo indeksini günceller\n"
            "  sudo mindpkg upgrade              : mindpkg'yi ve tüm paketleri yükseltir\n"
            "  mindpkg search <kelime>           : MindOS deposunda arar\n"
            "  mindpkg info <paket>              : Paket bilgisini gösterir\n"
            "  mindpkg list                      : mindpkg ile kurulan .mind paketlerini listeler\n"
            "  sudo mindpkg clean                : İndirme önbelleğini temizler\n"
            "  sudo mindpkg install ./paket.mind : Yerel bir .mind dosyasını kurar\n\n"
            "TAKMA ADLAR\n"
            "  chrome  -> google-chrome-stable\n"
            "  vscode  -> code\n"
            "  firefox -> firefox-esr\n\n"
            "GÜVENLİK\n"
            "  • Depodan inen her .mind paketi SHA256 ile doğrulanır.\n"
            "  • Bir .mind paketi sistem paketlerine (dpkg) ait bir dosyanın üzerine yazacaksa\n"
            "    kurulum durdurulur. Zorlamak gerekirse: MINDPKG_FORCE=1 sudo mindpkg install ...\n"
            "  • Paket içindeki dosyalar her zaman root sahipliğiyle kurulur; sistem dizinlerinin\n"
            "    sahiplik ve izinleri değiştirilmez.\n\n"
            ".MIND PAKET FORMATI\n"
            "Bir .mind dosyası Zstandard ile sıkıştırılmış bir tar arşividir:\n"
            "  metadata.json   : ad, sürüm, mimari, açıklama, bağımlılıklar\n"
            "  files.tar.zst   : kök dizine (/) açılacak dosyalar\n"
            "  pre_install.sh / post_install.sh / pre_remove.sh / post_remove.sh (isteğe bağlı)\n\n"
            "KENDİ PAKETİNİ OLUŞTUR\n"
            "  mkdir -p uygulamam/rootfs/usr/bin\n"
            "  cp uygulamam.sh uygulamam/rootfs/usr/bin/uygulamam\n"
            "  cat > uygulamam/metadata.json <<'EOF'\n"
            "  {\"name\": \"uygulamam\", \"version\": \"1.0\", \"release\": \"1\",\n"
            "   \"architecture\": \"x86_64\", \"description\": \"Benim uygulamam\"}\n"
            "  EOF\n"
            "  mindpkg build uygulamam            : uygulamam-1.0-1-x86_64.mind oluşturur\n"
            "  sudo mindpkg install uygulamam-1.0-1-x86_64.mind\n\n"
            "Kurulumdan sonra mindpkg şunları otomatik çalıştırır: ldconfig,\n"
            "update-desktop-database, gtk-update-icon-cache, glib-compile-schemas.\n\n"
            "GRAFİK ARAYÜZ\n"
            "Terminal kullanmak istemiyorsan Mind-Arc Kontrol Merkezi → Paket Merkezi\n"
            "sayfasından arama yapabilir, popüler uygulamaları tek tıkla kurabilirsin.\n"
            "Terminalden doğrudan açmak için: mind-arc --page packages\n"
        )
    },
    {
        "id": "mindos_desktop",
        "category": "MindOS",
        "title": "MindOS Masaüstü: ArcMenu, Mind-Arc ve Sistem Araçları",
        "subtitle": "Uygulama menüsü, kontrol merkezi, bellek yönetimi ve terminal araçları",
        "read_time": "4 min",
        "content": (
            "ARCMENU (UYGULAMA MENÜSÜ)\n"
            "  • Sol üstteki MindOS lotus simgesine tıkla veya Super (Windows) tuşuna bas.\n"
            "  • Uygulamalar kategorilere ayrılmıştır; yazmaya başlayınca arama yapılır.\n"
            "  • Ayarlar: menü simgesine sağ tıkla → ArcMenu Settings.\n\n"
            "MIND-ARC KONTROL MERKEZİ\n"
            "  mind-arc                      : Kontrol merkezini açar\n"
            "  mind-arc --page packages      : Paket Merkezi\n"
            "  mind-arc --page maintenance   : Sistem Bakımı (güncelleme, temizlik, RAM/zram)\n"
            "  mind-arc --page performance   : Performans ayarları\n\n"
            "BELLEK (ZRAM)\n"
            "MindOS, RAM'in yarısı kadar (en fazla 8 GB) zstd ile sıkıştırılmış zram takas\n"
            "alanı kullanır. Böylece RAM dolduğunda disk yerine bellek içinde sıkıştırma yapılır.\n"
            "  swapon --show                 : Etkin takas alanları\n"
            "  zramctl                       : zram kullanımı ve sıkıştırma oranı\n\n"
            "SİSTEM BİLGİSİ\n"
            "  fastfetch / neofetch          : MindOS lotus logosuyla sistem özeti\n"
            "  uname -r                      : Kernel sürümü (7.2.x-mindos)\n\n"
            "GÜNCELLEME\n"
            "  sudo apt update && sudo apt full-upgrade : Sistemi günceller\n"
            "  sudo mindpkg update           : MindOS deposunu günceller\n"
            "  sudo mindpkg upgrade          : Her şeyi yükseltir (mindpkg dahil)\n"
        )
    }
]

def search_tutorials(query: str) -> list:
    """Searches tutorials by title, category, or content keywords."""
    if not query or not query.strip():
        return TUTORIALS

    q = query.strip().lower()
    matches = []
    for tut in TUTORIALS:
        score = 0
        if q in tut["title"].lower():
            score += 10
        if q in tut["category"].lower():
            score += 5
        if q in tut["subtitle"].lower():
            score += 3
        if q in tut["content"].lower():
            score += 1

        if score > 0:
            matches.append((score, tut))

    matches.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in matches]

if __name__ == "__main__":
    print(f"Loaded {len(TUTORIALS)} tutorials.")
    for t in TUTORIALS:
        print(f" - [{t['category']}] {t['title']} ({t['read_time']})")
