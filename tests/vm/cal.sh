#!/bin/bash
# Calamares'i XWayland (xcb) üzerinde, ayrıntılı kayıtla başlatır (xdotool ile sürülebilsin diye)
pkill -x calamares; sleep 1
GS=$(pgrep -u user -x gnome-shell | head -1)
XA=$(ls /run/user/1000/.mutter-Xwaylandauth.* | head -1)
env -i HOME=/root PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=tr_TR.UTF-8 DISPLAY=:0 XAUTHORITY=$XA \
  XDG_RUNTIME_DIR=/run/user/0 QT_QPA_PLATFORM=xcb setsid calamares -D6 >/tmp/cal.log 2>&1 < /dev/null &
sleep 12; pgrep -c -x calamares
