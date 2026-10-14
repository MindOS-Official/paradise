#!/usr/bin/env python3
"""QEMU sendkey ile metin yazar (ABD klavye düzeni). kullanım: type.py <mon.sock> <metin> [--enter]"""
import socket, sys, time
SHIFT = {'!':'1','@':'2','#':'3','$':'4','%':'5','^':'6','&':'7','*':'8','(':'9',')':'0','_':'minus','+':'equal',
         '{':'bracket_left','}':'bracket_right','|':'backslash',':':'semicolon','"':'apostrophe','<':'comma','>':'dot','?':'slash','~':'grave_accent'}
PLAIN = {' ':'spc','-':'minus','=':'equal','[':'bracket_left',']':'bracket_right','\\':'backslash',';':'semicolon',
         "'":'apostrophe',',':'comma','.':'dot','/':'slash','`':'grave_accent','\n':'ret'}
def key(c):
    if c.isalpha():
        return ('shift-' + c.lower()) if c.isupper() else c
    if c.isdigit(): return c
    if c in PLAIN: return PLAIN[c]
    if c in SHIFT: return 'shift-' + SHIFT[c]
    raise ValueError(c)
m = socket.socket(socket.AF_UNIX); m.connect(sys.argv[1])
text = sys.argv[2] + ("\n" if "--enter" in sys.argv else "")
for c in text:
    m.sendall(f"sendkey {key(c)}\n".encode()); time.sleep(0.04)
time.sleep(0.3)
