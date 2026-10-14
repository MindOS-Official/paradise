#!/usr/bin/env bash
# chroot içinde: purge listesini SİMÜLE eder (-s), hiçbir şey silmez
export LANG=C
apt-get -s purge $(cat /tmp/purge.txt) 2>&1 | grep -E "^Purg" | awk '{print $2}' | sort > /tmp/sim-purge.txt
wc -l < /tmp/sim-purge.txt
comm -13 <(sort /tmp/purge.txt) /tmp/sim-purge.txt | tr "\n" " "; echo
apt-get -s purge $(cat /tmp/purge.txt) 2>&1 | grep -iE "^E:|broken" | head
