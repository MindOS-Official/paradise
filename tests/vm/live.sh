#!/bin/bash
# Canlı ISO'yu diske dokunmadan açar; seri hata ayıklama kabuğu ttyS0'da
V=$(cd "$(dirname "$0")" && pwd)
K=${K:-$V/kernel}   # vmlinuz + initrd (ISO içindeki live/ klasöründen)
rm -f $V/ser.sock $V/mon.sock
exec qemu-system-x86_64 -enable-kvm -cpu host -m 4096 -smp 4 -machine q35 -vga virtio -display none \
  -drive file=$HOME/Downloads/MindOS-Paradise.iso,media=cdrom,readonly=on -device qemu-xhci -device usb-tablet \
  -nic user,model=virtio-net-pci -kernel $K/vmlinuz -initrd $K/initrd \
  -append "boot=live components quiet splash locales=tr_TR.UTF-8 keyboard-layouts=tr console=tty0 systemd.debug_shell=ttyS0" \
  -serial unix:$V/ser.sock,server,nowait -monitor unix:$V/mon.sock,server,nowait
