#!/bin/bash
# Kurulum testi sanal makinesi: UEFI, 25 GB virtio disk, ISO CD'de, seri hata ayıklama kabuğu
V=$(cd "$(dirname "$0")" && pwd)
ISO=${ISO:-$HOME/Downloads/MindOS-Paradise.iso}
K=${K:-$V/kernel}   # vmlinuz + initrd (ISO içindeki live/ klasöründen)
rm -f $V/ser.sock $V/mon.sock
EXTRA=()
[ "$1" = "live" ] && EXTRA=(-kernel $K/vmlinuz -initrd $K/initrd -append "boot=live components quiet splash locales=tr_TR.UTF-8 keyboard-layouts=tr console=tty0 systemd.debug_shell=ttyS0")
exec qemu-system-x86_64 -enable-kvm -cpu host -m 6144 -smp 4 -machine q35 -vga virtio -display none \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=$V/vars.fd \
  -drive file=$V/disk.qcow2,if=virtio,format=qcow2 -drive file=$ISO,media=cdrom,readonly=on \
  -device qemu-xhci -device usb-tablet -nic user,model=virtio-net-pci \
  -serial unix:$V/ser.sock,server,nowait -monitor unix:$V/mon.sock,server,nowait "${EXTRA[@]}"
