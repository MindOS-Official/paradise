#!/bin/bash
# Secure Boot açık (Microsoft anahtarlı) UEFI ile ISO'yu açar
V=$(cd "$(dirname "$0")" && pwd)
rm -f $V/mon.sock $V/ser.sock
DISK=()
[ -f $V/disk.qcow2 ] && DISK=(-drive file=$V/disk.qcow2,if=virtio,format=qcow2)
exec qemu-system-x86_64 -enable-kvm -cpu host -m 4096 -smp 4 -machine q35,smm=on -global driver=cfi.pflash01,property=secure,value=on \
  -vga virtio -display none -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd \
  -drive if=pflash,format=raw,unit=1,file=$V/sbvars.fd  \
  -device qemu-xhci -device usb-tablet -nic user,model=virtio-net-pci -serial unix:$V/ser.sock,server,nowait -monitor unix:$V/mon.sock,server,nowait "${DISK[@]}"
