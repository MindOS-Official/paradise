#!/usr/bin/env bash
# chroot içinde: purge + autoremove SİMÜLASYONU (-s), hiçbir şey silmez
export LANG=C
apt-get -s purge --autoremove $(cat /tmp/purge.txt) 2>&1 | grep -E "^Purg" | awk '{print $2}' | sort > /tmp/sim-auto.txt
wc -l < /tmp/sim-auto.txt
comm -13 /tmp/sim-purge.txt /tmp/sim-auto.txt
