#!/bin/bash
# Calamares'i açar ve "Diski sil" ile otomatik kurulum yapar (1280x800 ekran düzeni)
V=$(cd "$(dirname "$0")" && pwd)
X() { $V/x.sh "$@"; }
python3 $V/sh.py $V/ser.sock "/tmp/cal.sh" 40 >/dev/null
NEXT="mousemove 1007 728 click 1"
X $NEXT; sleep 2          # karşılama -> konum
X $NEXT; sleep 2          # konum -> klavye
X $NEXT; sleep 4          # klavye -> bölümleme
X mousemove 334 233 click 1; sleep 3   # Diski sil
X $NEXT; sleep 3          # -> kullanıcı
X mousemove 427 207 click 1; X type --delay 40 Test
X mousemove 427 411 click 1; X type --delay 40 mindos123
X mousemove 633 411 click 1; X type --delay 40 mindos123; sleep 1
X $NEXT; sleep 3          # -> özet
$V/shot.sh summary
X mousemove 1018 775 click 1   # Kur
