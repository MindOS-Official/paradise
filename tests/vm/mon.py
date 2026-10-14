#!/usr/bin/env python3
"""QEMU monitör komutu gönderir. kullanım: mon.py <soket> <komut>"""
import socket, sys, time
m = socket.socket(socket.AF_UNIX); m.connect(sys.argv[1]); m.sendall((sys.argv[2] + "\n").encode()); time.sleep(0.5)
