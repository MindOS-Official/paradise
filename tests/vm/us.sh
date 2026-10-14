#!/bin/bash
# kullanım: us.sh "<canlı kullanıcı olarak komut>"  (seri kabuk üzerinden, base64 ile)
B=$(printf '%s' "$1" | base64 -w0)
V=$(cd "$(dirname "$0")" && pwd)
python3 $V/sh.py $V/ser.sock "echo $B | base64 -d > /tmp/u.sh; runuser -u user -- env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000 bash /tmp/u.sh" ${2:-20}
