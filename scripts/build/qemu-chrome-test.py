#!/usr/bin/env python3
"""Canlı ISO'da uçtan uca test: masaüstü açılır, 'mindpkg install chrome' çalıştırılır,
Chrome canlı kullanıcının oturumunda açılır ve ekran görüntüsü alınır.

kullanım: qemu-chrome-test.py <iso> <vmlinuz> <initrd> <çıktı_öneki>
"""
import os
import socket
import subprocess
import sys
import time

iso, kernel, initrd, prefix = sys.argv[1:5]
ser_path, mon_path = f"{prefix}.ser.sock", f"{prefix}.mon.sock"
for p in (ser_path, mon_path):
    if os.path.exists(p):
        os.unlink(p)

append = ("boot=live components quiet splash plymouth.theme=mindos "
          "console=tty0 console=ttyS0,115200 systemd.debug_shell=ttyS0")
qemu = subprocess.Popen([
    "qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-m", "6144", "-smp", "4",
    "-vga", "virtio", "-display", "none", "-nic", "user,model=virtio-net-pci",
    "-kernel", kernel, "-initrd", initrd, "-append", append,
    "-drive", f"file={iso},media=cdrom,readonly=on",
    "-serial", f"unix:{ser_path},server,nowait",
    "-monitor", f"unix:{mon_path},server,nowait",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            buf += chunk
            log.write(chunk)
        except socket.timeout:
            pass
    return buf.decode(errors="replace")


def run(cmd, timeout=60):
    marker = f"DONE_{time.time_ns()}"
    ser.sendall(f"{cmd}; echo {marker}_$((1+1))\n".encode())
    out, end = "", time.time() + timeout
    while time.time() < end and f"{marker}_2" not in out:
        out += read_for(2)
    return out


def monitor(cmd):
    m = socket.socket(socket.AF_UNIX)
    m.connect(mon_path)
    m.sendall((cmd + "\n").encode())
    time.sleep(0.5)
    m.close()


t0 = time.time()
while time.time() - t0 < 300:
    ser.sendall(b"\n")
    if "#" in read_for(3):
        break
while time.time() - t0 < 400:
    if "GS_UP_2" in run("pgrep -x gnome-shell >/dev/null && echo GS_UP_$((1+1))", 10):
        break
    time.sleep(3)
print(f"masaüstü: {round(time.time() - t0)} sn")
time.sleep(25)

t1 = time.time()
out = run("LANG=C mindpkg install chrome 2>&1 | grep -E '==>|Tamamland|Hata|E:' ; google-chrome-stable --version", 900)
print(f"mindpkg install chrome ({round(time.time() - t1)} sn):")
print("\n".join(l for l in out.splitlines() if any(k in l for k in ("==>", "Tamamland", "Hata", "E:", "Google Chrome")))[-1500:])

uid_line = run("id -u $(loginctl list-users --no-legend | awk 'NR==1{print $2}')", 10)
uid = next((w for w in uid_line.split() if w.isdigit() and w != "0"), "1000")
run(f"runuser -u $(id -nu {uid}) -- env XDG_RUNTIME_DIR=/run/user/{uid} WAYLAND_DISPLAY=wayland-0 "
    f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus "
    "google-chrome-stable --no-first-run --no-default-browser-check "
    "https://mindos-official.github.io/mindos_/ >/tmp/chrome.log 2>&1 & true", 10)
time.sleep(30)
print(run("pgrep -c -f google-chrome; tail -3 /tmp/chrome.log", 10)[-600:])
monitor(f"screendump {prefix}-chrome.ppm")
time.sleep(1)
monitor("quit")
qemu.wait(timeout=30)
