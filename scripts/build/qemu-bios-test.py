#!/usr/bin/env python3
"""BIOS (isolinux) üzerinden gerçek açılış testi.

isolinux menüsünde TAB ile komut satırına seri debug kabuğu eklenir, ardından
gnome-shell'in başladığı seri porttan doğrulanır ve aralıklarla ekran görüntüsü alınır.

kullanım: qemu-bios-test.py <iso> <çıktı_öneki>
"""
import os
import socket
import subprocess
import sys
import time

iso, prefix = sys.argv[1:3]
ser_path, mon_path = f"{prefix}.ser.sock", f"{prefix}.mon.sock"
for p in (ser_path, mon_path):
    if os.path.exists(p):
        os.unlink(p)

qemu = subprocess.Popen([
    "qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-m", "4096", "-smp", "4",
    "-vga", "virtio", "-display", "none",
    "-drive", f"file={iso},media=cdrom,readonly=on", "-boot", "d",
    "-serial", f"unix:{ser_path},server,nowait",
    "-monitor", f"unix:{mon_path},server,nowait",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

KEYS = {" ": "spc", "=": "equal", ".": "dot", ",": "comma", "/": "slash",
        "_": "shift-minus", "-": "minus"}


def monitor(cmd):
    m = socket.socket(socket.AF_UNIX)
    m.connect(mon_path)
    m.sendall((cmd + "\n").encode())
    time.sleep(0.15)
    m.close()


def typetext(text):
    for ch in text:
        monitor("sendkey " + KEYS.get(ch, ch))


ser = socket.socket(socket.AF_UNIX)
ser.connect(ser_path)
ser.settimeout(1)


def read_for(seconds):
    buf = b""
    end = time.time() + seconds
    while time.time() < end:
        try:
            buf += ser.recv(65536)
        except socket.timeout:
            pass
    return buf.decode(errors="replace")


time.sleep(8)
monitor(f"screendump {prefix}-menu.ppm")
monitor("sendkey tab")
time.sleep(1)
typetext(" console=tty0 console=ttyS0,115200 systemd.debug_shell=ttyS0")
monitor("sendkey ret")
t0 = time.time()

shell_at = None
while time.time() - t0 < 300:
    ser.sendall(b"pgrep -x gnome-shell >/dev/null && echo GS_RUN_$((40+2))\n")
    if "GS_RUN_42" in read_for(4):
        shell_at = round(time.time() - t0)
        break
print("BIOS: gnome-shell", f"{shell_at} sn'de başladı" if shell_at else "BAŞLAMADI")
for i, wait in enumerate((20, 40)):
    time.sleep(wait)
    monitor(f"screendump {prefix}-shot{i}.ppm")
ser.sendall(b"systemctl --failed --no-legend --plain; cat /proc/cmdline\n")
print(read_for(3)[-800:])
monitor("quit")
qemu.wait(timeout=30)
