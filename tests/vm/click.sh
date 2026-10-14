#!/bin/bash
# kullanım: click.sh <x> <y>  (1280x800 ekran koordinatı; QEMU usb-tablet mutlak fare)
V=$(cd "$(dirname "$0")" && pwd)
M="python3 $V/mon.py $V/mon.sock"
$M "mouse_move $(( $1 * 32767 / 1280 )) $(( $2 * 32767 / 800 ))"; sleep 0.3
$M "mouse_button 1"; sleep 0.15; $M "mouse_button 0"
