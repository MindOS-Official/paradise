#!/bin/bash
# kullanım: x.sh <xdotool argümanları...>  (VM içindeki /tmp/x aracılığıyla)
V=$(cd "$(dirname "$0")" && pwd)
python3 $V/sh.py $V/ser.sock "/tmp/x $*" 20 >/dev/null
