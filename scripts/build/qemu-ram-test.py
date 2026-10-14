#!/usr/bin/env python3
"""MindOS Paradise canlı ISO RAM ölçümü (QEMU/KVM).

Aynı koşullarda (RAM, CPU, kernel parametreleri) ISO'yu açar, GNOME masaüstü
yüklendikten sonra seri porttaki debug kabuğundan bellek ölçümü alır ve
ekran görüntüsü kaydeder.

kullanım: qemu-ram-test.py <iso> <vmlinuz> <initrd> <çıktı_öneki> [bekleme_sn]
"""
import os
import socket
import subprocess
import sys
import time

iso, kernel, initrd, prefix = sys.argv[1:5]
settle = int(sys.argv[5]) if len(sys.argv) > 5 else 90
ser_path = f"{prefix}.serial.sock"
mon_path = f"{prefix}.mon.sock"
for p in (ser_path, mon_path):
    if os.path.exists(p):
        os.unlink(p)

append = ("boot=live components quiet splash plymouth.theme=mindos "
          "console=tty0 console=ttyS0,115200 systemd.debug_shell=ttyS0")
qemu = subprocess.Popen([
    "qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-m", "4096", "-smp", "4",
    "-vga", "virtio", "-display", "none",
    "-kernel", kernel, "-initrd", initrd, "-append", append,
    "-drive", f"file={iso},media=cdrom,readonly=on",
    "-serial", f"unix:{ser_path},server,nowait",
    "-monitor", f"unix:{mon_path},server,nowait",
], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

time.sleep(2)
ser = socket.socket(socket.AF_UNIX)
ser.connect(ser_path)
ser.settimeout(1)
log = open(f"{prefix}.serial.log", "wb")


def read_for(seconds):
    buf = b""
    end = time.time() + seconds
    while time.time() < end:
        try:
            chunk = ser.recv(65536)
            if not chunk:
                break
            buf += chunk
            log.write(chunk)
        except socket.timeout:
            pass
    return buf


def run(cmd, wait=4):
    marker = f"__END_{time.time_ns()}__"
    ser.sendall(f"{cmd}; echo {marker}\n".encode())
    out = b""
    end = time.time() + wait + 30
    while time.time() < end and marker.encode() + b"\r\n" not in out and marker.encode() + b"\n" not in out:
        out += read_for(1)
    return out.decode(errors="replace")


def monitor(cmd):
    m = socket.socket(socket.AF_UNIX)
    m.connect(mon_path)
    m.settimeout(2)
    m.sendall((cmd + "\n").encode())
    time.sleep(1)
    m.close()


t0 = time.time()
# debug kabuğunun hazır olmasını bekle
while time.time() - t0 < 300:
    ser.sendall(b"\n")
    if b"#" in read_for(3):
        break
# gnome-shell çalışana kadar bekle (en fazla 6 dk)
shell_up = None
while time.time() - t0 < 360:
    out = run("pgrep -x gnome-shell >/dev/null && echo SHELL_UP_YES", 2)
    if "SHELL_UP_YES" in out.replace("echo SHELL_UP_YES", ""):
        shell_up = time.time() - t0
        break
    time.sleep(3)
print(f"gnome-shell başladı: {shell_up and round(shell_up)} sn")
time.sleep(settle)

report = run(
    "uname -r; free -m; echo; "
    "echo SWAP:; cat /proc/swaps; echo ZSWAP: $(cat /sys/module/zswap/parameters/enabled 2>/dev/null); "
    "grep -E 'MemTotal|MemAvailable|^Shmem:|Buffers|^Cached|AnonPages|Slab' /proc/meminfo; echo; "
    "echo PROC_COUNT: $(ps -e --no-headers | wc -l); "
    "echo TOP_RSS_MB:; ps -eo rss=,comm= --sort=-rss | head -15 | awk '{printf \"%7.1f %s\\n\", $1/1024, $2}'; "
    "echo FAILED:; systemctl --failed --no-legend --plain | head",
    6)
print(report)
monitor(f"screendump {prefix}.ppm")
time.sleep(2)
monitor("quit")
qemu.wait(timeout=30)
log.close()
