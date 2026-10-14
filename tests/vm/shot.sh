#!/bin/bash
# kullanım: shot.sh <ad>  -> vmtest/shots/<ad>.png (1280x800)
V=$(cd "$(dirname "$0")" && pwd); mkdir -p $V/shots
python3 $V/mon.py $V/mon.sock "screendump $V/shots/$1.ppm"; sleep 1
python3 -c "from PIL import Image;Image.open('$V/shots/$1.ppm').save('$V/shots/$1.png')" && rm -f $V/shots/$1.ppm
