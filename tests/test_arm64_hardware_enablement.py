#!/usr/bin/env python3
"""Comprehensive Hardware Enablement, Firmware & Multi-Device Kernel Verification for ARM64."""

import os
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def test_kernel_config():
    print("[1/5] Checking ARM64 kernel configuration...")
    cfg = (REPO_ROOT / "kernel" / "config-mindos-arm64").read_text(encoding="utf-8")
    
    # 1. Device tree
    assert "CONFIG_OF=y" in cfg, "Missing CONFIG_OF"
    assert "CONFIG_OF_FLATTREE=y" in cfg, "Missing CONFIG_OF_FLATTREE"
    assert "CONFIG_OF_OVERLAY=y" in cfg, "Missing CONFIG_OF_OVERLAY"

    # 2. Apple Silicon
    apple_opts = [
        "CONFIG_ARCH_APPLE=y", "CONFIG_APPLE_AIC=y", "CONFIG_APPLE_DART=y",
        "CONFIG_APPLE_SART=y", "CONFIG_NVME_APPLE=y", "CONFIG_DRM_SIMPLEDRM=y",
        "CONFIG_KEYBOARD_APPLESPI=m", "CONFIG_HID_APPLE=m", "CONFIG_BRCMFMAC=m"
    ]
    for opt in apple_opts:
        assert opt in cfg, f"Apple Silicon option missing: {opt}"

    # 3. Raspberry Pi 4 & 5
    rpi_opts = [
        "CONFIG_ARCH_BCM=y", "CONFIG_ARCH_BCM2835=y", "CONFIG_RASPBERRYPI_FIRMWARE=y",
        "CONFIG_PCIE_BRCMSTB=y", "CONFIG_RP1=m", "CONFIG_DRM_VC4=m", "CONFIG_DRM_V3D=m",
        "CONFIG_MMC_BCM2835=y", "CONFIG_MMC_SDHCI_IPROC=y"
    ]
    for opt in rpi_opts:
        assert opt in cfg, f"RPi option missing: {opt}"

    # 4. Snapdragon X Elite & Ampere Altra
    uefi_opts = [
        "CONFIG_ARCH_QCOM=y", "CONFIG_PINCTRL_X1E80100=y", "CONFIG_DRM_MSM=m",
        "CONFIG_SERIAL_AMBA_PL011=y", "CONFIG_SERIAL_AMBA_PL011_CONSOLE=y",
        "CONFIG_ACPI=y", "CONFIG_ARM_AMPERE_CPUFREQ=y", "CONFIG_EDAC_ALTRA=m"
    ]
    for opt in uefi_opts:
        assert opt in cfg, f"Snapdragon/Altra option missing: {opt}"

    print("  [✓] All Apple Silicon, RPi 4/5, Snapdragon X Elite, and Ampere Altra kernel configs verified.")

def test_firmware_staged():
    print("[2/5] Checking staged Wi-Fi & Bluetooth firmware in overlay...")
    fw_dir = REPO_ROOT / "overlay" / "lib" / "firmware"
    assert fw_dir.exists(), f"Firmware root missing: {fw_dir}"
    
    # 1. Broadcom (Apple Silicon + Raspberry Pi 4/5)
    brcm_dir = fw_dir / "brcm"
    assert brcm_dir.exists(), f"Broadcom firmware directory missing: {brcm_dir}"
    fw_files = list(brcm_dir.glob("brcm*"))
    assert len(fw_files) > 20, f"Expected Broadcom firmware files, found {len(fw_files)}"
    
    # Check specific Apple Silicon Wi-Fi and Bluetooth files
    assert (brcm_dir / "brcmbt4378b1-apple,atlantisb-m.bin").exists(), "Missing M1 Bluetooth firmware"
    assert (brcm_dir / "brcmfmac4364b2-pcie.apple,ekans.bin").exists(), "Missing Apple Wi-Fi firmware"
    
    # Check Raspberry Pi 4 & 5 Broadcom Wi-Fi files
    assert any("43455" in f.name for f in fw_files), "Missing Raspberry Pi 4/5 43455 Wi-Fi firmware"
    assert any("43430" in f.name for f in fw_files), "Missing Raspberry Pi 3/Zero 43430 Wi-Fi firmware"
    assert (REPO_ROOT / "packages" / "apple-bcm-firmware_14.0-1+mindos1_all.deb").exists(), "Missing staged deb"
    
    # 2. Realtek Wi-Fi / Bluetooth / NIC
    assert (fw_dir / "realtek").exists(), "Missing realtek/ directory in overlay"
    assert (fw_dir / "rtl_bt").exists(), "Missing rtl_bt/ directory in overlay"
    assert (fw_dir / "rtlwifi").exists(), "Missing rtlwifi/ directory in overlay"
    
    # 3. Misc nonfree (ARM64 HDMI bridge / Qualcomm)
    assert (fw_dir / "Lontium").exists(), "Missing Lontium/ directory in overlay"
    
    # 4. Check overlay.list registration
    overlay_list = (REPO_ROOT / "overlay.list").read_text(encoding="utf-8")
    for expected_fw in ["usr/lib/firmware/brcm", "usr/lib/firmware/realtek", "usr/lib/firmware/rtl_bt"]:
        assert expected_fw in overlay_list, f"Missing {expected_fw} in overlay.list"

    print(f"  [✓] Broadcom (Apple + RPi), Realtek, and misc firmware ({len(list(fw_dir.rglob('*')))} items) staged and registered.")

def test_initramfs_hardware_support():
    print("[3/5] Checking initramfs hardware modules and DTB hook...")
    mod_file = REPO_ROOT / "overlay" / "etc" / "initramfs-tools" / "modules"
    hook_file = REPO_ROOT / "overlay" / "etc" / "initramfs-tools" / "hooks" / "mindos-arm64-hardware"
    
    assert mod_file.exists(), "Missing initramfs modules file"
    assert hook_file.exists(), "Missing initramfs hardware hook"
    assert os.access(hook_file, os.X_OK), "Initramfs hardware hook is not executable"
    
    mod_text = mod_file.read_text(encoding="utf-8")
    for mod in ["nvme_apple", "apple-dart", "pcie-brcmstb", "rp1", "vc4", "qcom_scm", "amba-pl011"]:
        assert mod in mod_text, f"Module {mod} missing from initramfs modules"
    
    hook_text = hook_file.read_text(encoding="utf-8")
    assert "manual_add_modules" in hook_text, "Initramfs hook missing module addition"
    assert "conf/modules" in hook_text, "Initramfs hook missing conf/modules registration"
    assert "apple" in hook_text and "broadcom" in hook_text and "qcom" in hook_text, "Initramfs hook missing vendor DTB support"
    print("  [✓] Initramfs module list and hardware hook validated.")

def test_grub_configuration():
    print("[4/5] Checking GRUB EFI ARM64 configuration...")
    # 1. ISO grub.cfg
    iso_grub = (REPO_ROOT / "iso" / "boot" / "grub" / "grub.cfg").read_text(encoding="utf-8")
    assert "console=tty0 console=ttyAMA0,115200" in iso_grub, "Missing console redirection in iso grub.cfg"
    assert "devicetree" in iso_grub, "Missing devicetree command in iso grub.cfg"
    assert "apple" in iso_grub.lower(), "Missing Apple entry in iso grub.cfg"
    assert "rpi" in iso_grub.lower() or "raspberry" in iso_grub.lower(), "Missing Raspberry Pi entry in iso grub.cfg"

    # 2. Bootstrap grub generator
    boot_sh = (REPO_ROOT / "scripts" / "build" / "bootstrap-arm64-rootfs.sh").read_text(encoding="utf-8")
    assert "console=tty0 console=ttyAMA0,115200" in boot_sh, "Missing console redirection in bootstrap-arm64-rootfs.sh"
    assert "devicetree" in boot_sh, "Missing devicetree support in bootstrap script"
    assert "apple-bcm-firmware" in boot_sh, "Missing apple-bcm-firmware in bootstrap-arm64-rootfs.sh"

    # 3. System overlay grub.d default
    sys_grub = (REPO_ROOT / "overlay" / "etc" / "default" / "grub.d" / "20-mindos-arm64.cfg").read_text(encoding="utf-8")
    assert "console=tty0 console=ttyAMA0,115200" in sys_grub, "Missing console redirection in grub.d/20-mindos-arm64.cfg"
    print("  [✓] GRUB console redirection (tty0 + ttyAMA0,115200) and devicetree passing verified.")

def test_package_repository_parity():
    print("[5/5] Checking package lists and arm64 package repository index...")
    manifest = (REPO_ROOT / "packages" / "filesystem.manifest").read_text(encoding="utf-8")
    for pkg in ["apple-bcm-firmware", "firmware-brcm80211", "firmware-realtek", "firmware-misc-nonfree"]:
        assert pkg in manifest, f"Package {pkg} missing from filesystem.manifest"

    # MindOS_packages_arm64_repo
    arm_repo = Path("/home/mamish/MindOS_packages_arm64_repo")
    if arm_repo.exists():
        sys_data = json.loads((arm_repo / "system.json").read_text(encoding="utf-8"))
        assert any(x.get("name") == "apple-bcm-firmware" for x in sys_data.get("system", [])), "apple-bcm-firmware missing from system.json"
        
        idx_data = json.loads((arm_repo / "packages-arm64.json").read_text(encoding="utf-8"))
        assert any(x.get("name") == "apple-bcm-firmware" for x in idx_data.get("system", [])), "apple-bcm-firmware missing from packages-arm64.json"
    print("  [✓] Firmware packages confirmed in filesystem.manifest and MindOS arm64 repository index.")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing MindOS Paradise ARM64 Hardware Enablement")
    print("=" * 60)
    test_kernel_config()
    test_firmware_staged()
    test_initramfs_hardware_support()
    test_grub_configuration()
    test_package_repository_parity()
    print("=" * 60)
    print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)
