#!/bin/bash
# MindOS Paradise ARM64: Canlı ISO'yu QEMU aarch64 ile test eder
V=$(cd "$(dirname "$0")" && pwd)
BIOS=${BIOS:-/usr/share/qemu-efi-aarch64/QEMU_EFI.fd}
[ -f "$BIOS" ] || BIOS=/usr/share/AAVMF/AAVMF_CODE.fd
rm -f "$V/ser-arm64.sock" "$V/mon-arm64.sock"
ISO_FILE="${ISO:-$HOME/Downloads/MindOS-Paradise-arm64.iso}"

QEMU_ARGS=(
  -M virt
  -cpu cortex-a57
  -m 4096
  -smp 4
  -device virtio-gpu-pci
  -display none
  -device qemu-xhci
  -device usb-kbd
  -device usb-tablet
  -nic user,model=virtio-net-pci
  -serial "unix:$V/ser-arm64.sock,server,nowait"
  -monitor "unix:$V/mon-arm64.sock,server,nowait"
)

K=${K:-$V/kernel}
if [ -f "$K/vmlinuz" ] && [ -f "$K/initrd" ]; then
  QEMU_ARGS+=(
    -kernel "$K/vmlinuz"
    -initrd "$K/initrd"
    -append "boot=live components quiet splash locales=tr_TR.UTF-8 keyboard-layouts=tr console=ttyAMA0,115200 console=tty0 systemd.debug_shell=ttyAMA0"
  )
elif [ -f "$BIOS" ]; then
  QEMU_ARGS+=(-bios "$BIOS")
fi

if [ -f "$ISO_FILE" ]; then
  QEMU_ARGS+=(-drive "file=$ISO_FILE,media=cdrom,readonly=on")
fi

exec qemu-system-aarch64 "${QEMU_ARGS[@]}" "$@"
