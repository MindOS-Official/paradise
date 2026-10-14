#!/usr/bin/env python3
"""Seri hata ayıklama kabuğunda komut çalıştırır. kullanım: sh.py <soket> <komut> [zaman_aşımı]"""
import re, socket, sys, time
ser = socket.socket(socket.AF_UNIX); ser.connect(sys.argv[1]); ser.settimeout(1)
cmd = sys.argv[2]; to = float(sys.argv[3]) if len(sys.argv) > 3 else 30
mk = f"END{time.time_ns()}"
ser.sendall(f"{cmd}\necho {mk}_$((2+3))\n".encode())
out, end = "", time.time() + to
while time.time() < end and f"{mk}_5" not in out:
    try:
        out += ser.recv(65536).decode(errors="replace")
    except socket.timeout:
        pass
out = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", out)
lines = [l for l in out.splitlines() if mk not in l]
print("\n".join(lines[-80:]))
