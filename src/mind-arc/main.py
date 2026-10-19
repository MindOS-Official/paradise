#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MIND-ARC CONTROL CENTER
Gelişmiş GTK4 ve Libadwaita Arayüzlü Sistem Yönetim Uygulaması
Yazar: MindOS Paradise Ekibi
Lisans: GPLv3
"""

import os
import sys
import subprocess
import psutil
import glob
import time
import locale
import gettext
import struct
import platform
import re
import threading
import json
import gi
import warnings

# Deprecation uyarılarını gözardı ederek terminal/günlük çıktılarını temiz tutuyoruz
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Gerekli GTK4 ve Libadwaita kütüphane sürümlerini belirtiyoruz
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gdk, Gio, GLib, Adw, GdkPixbuf

# Gettext yerelleştirme ayarları ve dizin yolları
LOCALE_DIR = "/opt/mind-arc/locale"
if not os.access(os.path.dirname(LOCALE_DIR), os.W_OK):
    # Normal kullanıcı /opt altına yazamaz: derlenen çeviriler kullanıcının önbelleğine yazılır
    LOCALE_DIR = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
                              "mind-arc", "locale")

# Kullanıcının scope eşitlemesi istediği global değişkenler
locale_dir = LOCALE_DIR

gettext.bindtextdomain('mind-arc', LOCALE_DIR)
gettext.textdomain('mind-arc')

# Varsayılan dil çeviri nesnesi
current_translation = gettext.translation('mind-arc', LOCALE_DIR, languages=['tr'], fallback=True)

def _(text):
    global current_translation
    return current_translation.gettext(text)


def compile_po_to_mo(po_path, mo_path):
    """
    po dosyasını binary mo formatına derler.
    """
    messages = {"": "Content-Type: text/plain; charset=UTF-8\n"}
    msgid = None
    
    if not os.path.exists(po_path):
        return
        
    with open(po_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('msgid '):
                msgid = line[6:].strip('"')
            elif line.startswith('msgstr ') and msgid is not None:
                msgstr = line[7:].strip('"')
                if msgid:
                    messages[msgid] = msgstr
                msgid = None
                
    keys = sorted(messages.keys())
    num_strings = len(keys)
    
    original_table = []
    translation_table = []
    original_data = b""
    translation_data = b""
    
    start_original_data_offset = 28 + (8 * num_strings) * 2
    
    current_orig_offset = start_original_data_offset
    for key in keys:
        key_bytes = key.encode('utf-8') + b'\x00'
        original_table.append((len(key_bytes) - 1, current_orig_offset))
        original_data += key_bytes
        current_orig_offset += len(key_bytes)
        
    start_translation_data_offset = current_orig_offset
    current_trans_offset = start_translation_data_offset
    for key in keys:
        val_bytes = messages[key].encode('utf-8') + b'\x00'
        translation_table.append((len(val_bytes) - 1, current_trans_offset))
        translation_data += val_bytes
        current_trans_offset += len(val_bytes)
        
    with open(mo_path, 'wb') as f:
        f.write(struct.pack('<I', 0x950412de))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', num_strings))
        f.write(struct.pack('<I', 28))
        f.write(struct.pack('<I', 28 + 8 * num_strings))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', 0))
        
        for length, offset in original_table:
            f.write(struct.pack('<II', length, offset))
            
        for length, offset in translation_table:
            f.write(struct.pack('<II', length, offset))
            
        f.write(original_data)
        f.write(translation_data)


def setup_translations():
    translations = {
        'tr': {
            'Mind-Arc Control Center': 'Mind-Arc Kontrol Merkezi',
            'System Info': 'Hakkında',
            'OS Name': 'İşletim Sistemi',
            'Kernel Version': 'Kernel Sürümü',
            'Uptime': 'Çalışma Süresi',
            'Internal Hardware': 'Dahili Donanım',
            'CPU Status': 'CPU Durumu',
            'CPU Usage': 'CPU Kullanımı',
            'CPU Temp': 'CPU Sıcaklığı',
            'RAM Status': 'RAM Durumu',
            'RAM Usage': 'RAM Kullanımı',
            'RAM Capacity': 'RAM Kapasitesi',
            'GPU and Fan Control': 'GPU ve Fan Kontrolü',
            'GPU Model': 'GPU Modeli',
            'GPU Usage': 'GPU Kullanımı',
            'GPU Temp': 'GPU Sıcaklığı',
            'GPU Status': 'GPU Durumu',
            'Hardware Control [EXPERIMENTAL]': 'Donanım Kontrolü [DENEYSEL]',
            'Fan Settings': 'Fan Ayarları',
            'Controlled Device': 'Kontrol Edilen Aygıt',
            'GPU Fan Control': 'GPU (Ekran Kartı) Fan Kontrolü',
            'Peripherals': 'Harici Donanım',
            'Connected Devices': 'Bağlı Cihazlar',
            'Mouse Speed': 'Mouse Hızı',
            'Appearance and General Settings': 'Görünüm ve Genel Ayarlar',
            'Dark Mode': 'Karanlık Tema',
            'Wi-Fi': 'Wi-Fi Bağlantısı',
            'Bluetooth': 'Bluetooth Bağlantısı',
            'Performance and Tweak': 'Performans ve Tweak',
            'Clear System Cache': 'Sistem Ön Belleğini Temizle',
            'Language / Dil': 'Dil / Language',
            'WARNING! The settings in this section (Fan control, voltage, etc.) can cause hardware damage to your system. You are playing with settings you shouldn\'t. The MindOS team is not responsible for any damage that may occur.': 'DİKKAT! Bu bölümdeki ayarlar (Fan kontrolü, voltaj vb.) sisteminize donanımsal zarar verebilir. Oynamamanız gereken ayarlarla oynuyorsunuz. Oluşabilecek hasarlardan MindOS ekibi sorumlu değildir.',
            'I Accept': 'Kabul Ediyorum',
            'Cancel': 'İptal',
            'Cache cleared successfully!': 'Sistem ön belleği başarıyla temizlendi!',
            'An error occurred:': 'Bir hata oluştu:',
            'Fan Speed (PWM)': 'Fan Hızı (PWM)',
            'Warning': 'Uyarı',
            'Enabled': 'Aktif',
            'Disabled': 'Pasif',
            'No devices found.': 'Cihaz bulunamadı.',
            'Apply': 'Uygula',
            'Hardware settings require root privileges.': 'Donanım ayarları yetkili kullanıcı (root) izinleri gerektirir.',
            'Error': 'Hata',
            'Info': 'Bilgi',
            'Control external devices and settings': 'Harici cihazları ve ayarları kontrol edin',
            'Optimize system performance': 'Sistem performansını optimize edin',
            'Adjust display and network settings': 'Ekran, ağ ve genel ayarları düzenleyin',
            'Monitor CPU, RAM and GPU metrics': 'CPU, RAM ve GPU ölçümlerini izleyin',
            'Hardware fan and safety configurations': 'Donanım fan ve güvenlik yapılandırmaları',
            'Select application language': 'Uygulama dilini seçin',
            'System overview details': 'Sistem genel bakış detayları',
            'Hostname': 'Ağ Adı (Hostname)',
            'System Architecture': 'Sistem Mimarisi',
            'Display Server': 'Görüntü Sunucusu',
            'Disk Storage': 'Disk Depolama',
            'Mice': 'Bağlı Fareler (Mice)',
            'Keyboards': 'Bağlı Klavyeler',
            'Audio and Headsets': 'Kulaklık ve Ses Cihazları',
            'Bluetooth and Receivers': 'Bluetooth ve Alıcılar',
            'CPU Cores': 'CPU Çekirdek Sayısı',
            'CPU Clock Speed': 'İşlemci Hızı',
            'RAM Speed': 'RAM Frekansı',
            'GPU Driver': 'Grafik Sürücüsü',
            'CPU Model': 'İşlemci Modeli',
            'RAM Optimization': 'RAM Sıkıştırma',
            'Compress system RAM to free up memory': 'Sistem RAM belleklerini sıkıştırarak boşaltır',
            'Performance Mode': 'Yüksek Performans Modu',
            'Set CPU governor to performance mode': 'İşlemci governor modunu en yüksek güce ayarlar',
            'No keyboards detected.': 'Klavye algılanmadı.',
            'No headsets detected.': 'Kulaklık/ses cihazı algılanmadı.',
            'No bluetooth devices detected.': 'Bluetooth cihazı algılanmadı.',
            'No mice detected.': 'Fare algılanmadı.',
            'Optimization applied successfully!': 'Optimizasyon başarıyla uygulandı!',
            'Performance mode changed!': 'Performans modu değiştirildi!',
            'General Settings': 'Genel Ayarlar',
            'Network Connections': 'Ağ Bağlantıları',
            'System Specifications': 'Sistem Özellikleri',
            'Live Metrics': 'Canlı Ölçümler',
            'ZRAM Optimization': 'ZRAM Optimizasyonu',
            'Optimize ZRAM swappiness for responsiveness': 'Sistem tepkiselliği için ZRAM swappiness değerini düzenler',
            'Disable IPv6': 'IPv6\'yı Devre Dışı Bırak',
            'Disable IPv6 protocol to speed up network resolution': 'Ağ çözümlemesini hızlandırmak için IPv6 protokolünü kapatır',
            'System Log Vacuum': 'Sistem Günlük Temizliği',
            'Clean system journal logs older than 1 day': '1 günden eski sistem journal günlüklerini siler',
            'Optimize Swappiness': 'Sanal Bellek Eğilimi (Swappiness)',
            'Set vm.swappiness to 10 for better SSD lifetime': 'SSD ömrü ve sistem hızı için swappiness değerini 10 yapar',
            'Disk Read-Ahead Buffer': 'Disk Okuma Önceliği',
            'Increase read-ahead buffer to speed up disk access': 'Disk erişimini hızlandırmak için önbellek okuma değerini artırır',
            'TCP Window Scaling': 'TCP Pencere Ölçekleme',
            'Enable TCP window scaling for faster network': 'Daha hızlı internet için TCP pencere ölçeklemesini açar',
            'Zombie Process Cleaner': 'Zombi Süreç Temizleyici',
            'Kill zombie and orphan system processes': 'Zombi ve yetim kalmış sistem süreçlerini sonlandırır',
            'Install XFCE Desktop': 'XFCE Masaüstü Ortamını Kur',
            'Install lightweight XFCE desktop environment': 'Sistem kaynaklarını minimum tüketen hafif XFCE masaüstünü yükler',
            'XFCE Installation started in the background.': 'XFCE kurulumu arka planda başlatıldı.',
            'Performans Etkisi: Düşük': 'Performans Etkisi: Düşük',
            'Performans Etkisi: Orta': 'Performans Etkisi: Orta',
            'Performans Etkisi: Yüksek': 'Performans Etkisi: Yüksek',
            'Low': 'Düşük',
            'Medium': 'Orta',
            'High': 'Yüksek',
            'Desktop Environment': 'Masaüstü Ortamı',
            'Welcome to Mind-Arc Control Center': 'Mind-Arc Kontrol Merkezi\'ne Hoş Geldiniz',
            '(TEMPORARILY DISABLED)': '(GEÇİCİ OLARAK DEVRE DIŞI)',
            'System Volume': 'Master Ses Seviyesi',
            'Screen Brightness': 'Ekran Parlaklığı',
            'Screen Timeout': 'Ekran Zaman Aşımı',
            'System Notifications': 'Sistem Bildirimleri',
            '1 Minute': '1 Dakika',
            '5 Minutes': '5 Dakika',
            '15 Minutes': '15 Dakika',
            'Never': 'Asla',
            'Microphone Access': 'Mikrofon Erişimi',
            'Camera Access': 'Kamera Erişimi',
            'Do Not Disturb': 'Rahatsız Etmeyin (DND)',
            
            # USB Installer Çevirileri
            'MindOS USB Installer [EXPERIMENTAL]': 'MindOS USB Kurucu [DENEYSEL]',
            'Automated operating system installation on external USB storage': 'Harici USB depolama birimine otomatik işletim sistemi kurulumu',
            'Target USB Drive': 'Hedef USB Sürücüsü',
            'New Username': 'Yeni Kullanıcı Adı',
            'Sudo Password': 'Sudo Şifresi',
            'Target System Language': 'Hedef Sistem Dili',
            'Keyboard Layout': 'Klavye Düzeni',
            'Start Installation': 'Kurulumu Başlat',
            'Confirm Disk Wipe': 'Diski Sıfırlamayı Onayla',
            'WARNING: All data on the selected USB drive will be permanently erased. Are you sure you want to proceed?': 'UYARI: Seçilen USB sürücüsündeki tüm veriler kalıcı olarak silinecektir. Devam etmek istediğinize emin misiniz?',
            'Installing MindOS...': 'MindOS Yükleniyor...',
            'Please wait while the operating system is installed on your USB drive.': 'İşletim sistemi USB sürücünüze yüklenirken lütfen bekleyin.',
            'Close': 'Kapat',
            'Preparing disk (Partitioning)...': 'Disk hazırlanıyor (Bölümlendirme)...',
            'Formatting partition as ext4...': 'Bölüm ext4 olarak biçimlendiriliyor...',
            'Transferring system files...': 'Sistem dosyaları aktarılıyor...',
            'Configuring user and locale settings...': 'Kullanıcı ve yerel ayarlar yapılandırılıyor...',
            'Installing bootloader and live persistence...': 'Önyükleyici ve canlı kalıcılık kuruluyor...',
            'Installing bootloader (BIOS + UEFI, Secure Boot)...': 'Önyükleyici kuruluyor (BIOS + UEFI, Secure Boot)...',
            'Preparing the system for first boot...': 'Sistem ilk açılış için hazırlanıyor...',
            'Writing changes to the drive (this may take a while)...': 'Değişiklikler diske yazılıyor (biraz sürebilir)...',
            'The drive is too small. At least 12 GB is required.': 'Disk çok küçük. En az 12 GB gerekiyor.',
            'Password must be at least 6 characters.': 'Parola en az 6 karakter olmalı.',
            'Creating the user account failed.': 'Kullanıcı hesabı oluşturulamadı.',
            'Copying system files failed. The drive may be faulty or full.': 'Sistem dosyaları kopyalanamadı. Disk arızalı ya da dolu olabilir.',
            'Installing the bootloader failed.': 'Önyükleyici kurulamadı.',
            'Preparing the system for first boot failed.': 'Sistem ilk açılış için hazırlanamadı.',
            'The selected ISO is not a valid MindOS image.': 'Seçilen ISO geçerli bir MindOS kalıbı değil.',
            'Authorization failed or was cancelled.': 'Yetkilendirme başarısız oldu ya da iptal edildi.',
            'MindOS was installed on the drive as a full system. You can boot any computer from it; it keeps your files and updates like a normal installation.': 'MindOS sürücüye tam sistem olarak kuruldu. Her bilgisayarı bundan açabilirsiniz; dosyalarınızı saklar ve normal bir kurulum gibi güncellenir.',
            'Installs a complete, permanent MindOS on a USB drive or external disk (not a live system)': 'USB belleğe veya harici diske kalıcı, tam bir MindOS kurar (canlı sistem değil)',
            'Installation completed successfully!': 'Kurulum başarıyla tamamlandı!',
            'Installation Completed': 'Kurulum Tamamlandı',
            'Installation Failed': 'Kurulum Başarısız',
            'No USB drives detected.': 'USB sürücü algılanmadı.',
            'Fields cannot be empty.': 'Alanlar boş bırakılamaz.',
            'Beta Warning': 'Beta Uyarısı',
            'This is an experimental beta feature. Your USB drive could be damaged, and all existing data will be permanently erased. The MindOS team is not responsible for any damage or data loss that may occur. Please proceed with caution.': 'Bu deneysel bir beta özelliğidir. USB sürücünüz bozulabilir ve mevcut tüm verileriniz kalıcı olarak silinecektir. Oluşabilecek hasar veya veri kayıplarından MindOS ekibi sorumlu değildir. Lütfen dikkatli devam edin.',
            'Source ISO File': 'Kaynak ISO Dosyası',
            'Select Source ISO File': 'Kaynak ISO Dosyasını Seçin',
            'Select': 'Seç',
            'ISO Images (*.iso)': 'ISO Dosyaları (*.iso)',
            'Please select a valid ISO file.': 'Lütfen geçerli bir ISO dosyası seçin.',
            'Failed to mount source ISO file.': 'Kaynak ISO dosyası bağlanamadı.'
        },
        'en': {
            'Mind-Arc Control Center': 'Mind-Arc Control Center',
            'System Info': 'System Info',
            'OS Name': 'OS Name',
            'Kernel Version': 'Kernel Version',
            'Uptime': 'Uptime',
            'Internal Hardware': 'Internal Hardware',
            'CPU Status': 'CPU Status',
            'CPU Usage': 'CPU Usage',
            'CPU Temperature': 'CPU Temperature',
            'RAM Status': 'RAM Status',
            'RAM Usage': 'RAM Usage',
            'RAM Capacity': 'RAM Capacity',
            'GPU and Fan Control': 'GPU and Fan Control',
            'GPU Model': 'GPU Model',
            'GPU Usage': 'GPU Usage',
            'GPU Temp': 'GPU Temperature',
            'GPU Status': 'GPU Status',
            'Hardware Control [EXPERIMENTAL]': 'Hardware Control [EXPERIMENTAL]',
            'Fan Settings': 'Fan Settings',
            'Controlled Device': 'Controlled Device',
            'GPU Fan Control': 'GPU Fan Control',
            'Peripherals': 'Peripherals',
            'Connected Devices': 'Connected Devices',
            'Mouse Speed': 'Mouse Speed',
            'Appearance and General Settings': 'Appearance and General Settings',
            'Dark Mode': 'Dark Mode',
            'Wi-Fi': 'Wi-Fi',
            'Bluetooth': 'Bluetooth',
            'Performance and Tweak': 'Performance and Tweak',
            'Clear System Cache': 'Clear System Cache',
            'Language / Dil': 'Language / Dil',
            'WARNING! The settings in this section (Fan control, voltage, etc.) can cause hardware damage to your system. You are playing with settings you shouldn\'t. The MindOS team is not responsible for any damage that may occur.': 'WARNING! The settings in this section (Fan control, voltage, etc.) can cause hardware damage to your system. You are playing with settings you shouldn\'t. The MindOS team is not responsible for any damage that may occur.',
            'I Accept': 'I Accept',
            'Cancel': 'Cancel',
            'Cache cleared successfully!': 'System cache cleared successfully!',
            'An error occurred:': 'An error occurred:',
            'Fan Speed (PWM)': 'Fan Speed (PWM)',
            'Warning': 'Warning',
            'Enabled': 'Enabled',
            'Disabled': 'Disabled',
            'No devices found.': 'No devices found.',
            'Apply': 'Apply',
            'Hardware settings require root privileges.': 'Hardware settings require root privileges.',
            'Error': 'Error',
            'Info': 'Info',
            'Control external devices and settings': 'Control external devices and settings',
            'Optimize system performance': 'Optimize system performance',
            'Adjust display and network settings': 'Adjust display, network and general settings',
            'Monitor CPU, RAM and GPU metrics': 'Monitor CPU, RAM and GPU metrics',
            'Hardware fan and safety configurations': 'Hardware fan and safety configurations',
            'Select application language': 'Select application language',
            'System overview details': 'System overview details',
            'Hostname': 'Hostname',
            'System Architecture': 'System Architecture',
            'Display Server': 'Display Server',
            'Disk Storage': 'Disk Storage',
            'Mice': 'Connected Mice',
            'Keyboards': 'Keyboards',
            'Audio and Headsets': 'Audio and Headsets',
            'Bluetooth and Receivers': 'Bluetooth and Receivers',
            'CPU Cores': 'CPU Cores',
            'CPU Clock Speed': 'CPU Clock Speed',
            'RAM Speed': 'RAM Speed',
            'GPU Driver': 'GPU Driver',
            'CPU Model': 'CPU Model',
            'RAM Optimization': 'RAM Optimization',
            'Compress system RAM to free up memory': 'Compresses system RAM to free up memory',
            'Performance Mode': 'High Performance Mode',
            'Set CPU governor to performance mode': 'Sets CPU governor to maximum performance',
            'No keyboards detected.': 'No keyboards detected.',
            'No headsets detected.': 'No headsets detected.',
            'No bluetooth devices detected.': 'No bluetooth devices detected.',
            'No mice detected.': 'No mice detected.',
            'Optimization applied successfully!': 'Optimization applied successfully!',
            'Performance mode changed!': 'Performance mode changed!',
            'General Settings': 'General Settings',
            'Network Connections': 'Network Connections',
            'System Specifications': 'System Specifications',
            'Live Metrics': 'Live Metrics',
            'ZRAM Optimization': 'ZRAM Optimization',
            'Optimize ZRAM swappiness for responsiveness': 'Optimize ZRAM swappiness for responsiveness',
            'Disable IPv6': 'Disable IPv6',
            'Disable IPv6 protocol to speed up network resolution': 'Disables IPv6 protocol to speed up network resolution',
            'System Log Vacuum': 'System Log Vacuum',
            'Clean system journal logs older than 1 day': 'Cleans system journal logs older than 1 day',
            'Optimize Swappiness': 'Optimize Swappiness',
            'Set vm.swappiness to 10 for better SSD lifetime': 'Set vm.swappiness to 10 for better SSD lifetime',
            'Disk Read-Ahead Buffer': 'Disk Read-Ahead Buffer',
            'Increase read-ahead buffer to speed up disk access': 'Increase read-ahead buffer to speed up disk access',
            'TCP Window Scaling': 'TCP Window Scaling',
            'Enable TCP window scaling for faster network': 'Enable TCP window scaling for faster network',
            'Zombie Process Cleaner': 'Zombie Process Cleaner',
            'Kill zombie and orphan system processes': 'Kill zombie and orphan system processes',
            'Install XFCE Desktop': 'Install XFCE Desktop',
            'Install lightweight XFCE desktop environment': 'Install lightweight XFCE desktop environment',
            'XFCE Installation started in the background.': 'XFCE Installation started in the background.',
            'Performans Etkisi: Düşük': 'Performance Impact: Low',
            'Performans Etkisi: Orta': 'Performance Impact: Medium',
            'Performans Etkisi: Yüksek': 'Performance Impact: High',
            'Low': 'Low',
            'Medium': 'Medium',
            'High': 'High',
            'Desktop Environment': 'Desktop Environment',
            'Welcome to Mind-Arc Control Center': 'Welcome to Mind-Arc Control Center',
            '(TEMPORARILY DISABLED)': '(TEMPORARILY DISABLED)',
            'System Volume': 'System Volume',
            'Screen Brightness': 'Screen Brightness',
            'Screen Timeout': 'Screen Timeout',
            'System Notifications': 'System Notifications',
            '1 Minute': '1 Minute',
            '5 Minutes': '5 Minutes',
            '15 Minutes': '15 Minutes',
            'Never': 'Never',
            'Microphone Access': 'Microphone Access',
            'Camera Access': 'Camera Access',
            'Do Not Disturb': 'Do Not Disturb',
            
            # USB Installer Translations
            'MindOS USB Installer [EXPERIMENTAL]': 'MindOS USB Installer [EXPERIMENTAL]',
            'Automated operating system installation on external USB storage': 'Automated operating system installation on external USB storage',
            'Target USB Drive': 'Target USB Drive',
            'New Username': 'New Username',
            'Sudo Password': 'Sudo Password',
            'Target System Language': 'Target System Language',
            'Keyboard Layout': 'Keyboard Layout',
            'Start Installation': 'Start Installation',
            'Confirm Disk Wipe': 'Confirm Disk Wipe',
            'WARNING: All data on the selected USB drive will be permanently erased. Are you sure you want to proceed?': 'WARNING: All data on the selected USB drive will be permanently erased. Are you sure you want to proceed?',
            'Installing MindOS...': 'Installing MindOS...',
            'Please wait while the operating system is installed on your USB drive.': 'Please wait while the operating system is installed on your USB drive.',
            'Close': 'Close',
            'Preparing disk (Partitioning)...': 'Preparing disk (Partitioning)...',
            'Formatting partition as ext4...': 'Formatting partition as ext4...',
            'Transferring system files...': 'Transferring system files...',
            'Configuring user and locale settings...': 'Configuring user and locale settings...',
            'Installing bootloader and live persistence...': 'Installing bootloader and live persistence...',
            'Installing bootloader (BIOS + UEFI, Secure Boot)...': 'Installing bootloader (BIOS + UEFI, Secure Boot)...',
            'Preparing the system for first boot...': 'Preparing the system for first boot...',
            'Writing changes to the drive (this may take a while)...': 'Writing changes to the drive (this may take a while)...',
            'The drive is too small. At least 12 GB is required.': 'The drive is too small. At least 12 GB is required.',
            'Password must be at least 6 characters.': 'Password must be at least 6 characters.',
            'Creating the user account failed.': 'Creating the user account failed.',
            'Copying system files failed. The drive may be faulty or full.': 'Copying system files failed. The drive may be faulty or full.',
            'Installing the bootloader failed.': 'Installing the bootloader failed.',
            'Preparing the system for first boot failed.': 'Preparing the system for first boot failed.',
            'The selected ISO is not a valid MindOS image.': 'The selected ISO is not a valid MindOS image.',
            'Authorization failed or was cancelled.': 'Authorization failed or was cancelled.',
            'MindOS was installed on the drive as a full system. You can boot any computer from it; it keeps your files and updates like a normal installation.': 'MindOS was installed on the drive as a full system. You can boot any computer from it; it keeps your files and updates like a normal installation.',
            'Installs a complete, permanent MindOS on a USB drive or external disk (not a live system)': 'Installs a complete, permanent MindOS on a USB drive or external disk (not a live system)',
            'Installation completed successfully!': 'Installation completed successfully!',
            'Installation Completed': 'Installation Completed',
            'Installation Failed': 'Installation Failed',
            'No USB drives detected.': 'No USB drives detected.',
            'Fields cannot be empty.': 'Fields cannot be empty.',
            'Beta Warning': 'Beta Warning',
            'This is an experimental beta feature. Your USB drive could be damaged, and all existing data will be permanently erased. The MindOS team is not responsible for any damage or data loss that may occur. Please proceed with caution.': 'This is an experimental beta feature. Your USB drive could be damaged, and all existing data will be permanently erased. The MindOS team is not responsible for any damage or data loss that may occur. Please proceed with caution.',
            'Source ISO File': 'Source ISO File',
            'Select Source ISO File': 'Select Source ISO File',
            'Select': 'Select',
            'ISO Images (*.iso)': 'ISO Images (*.iso)',
            'Please select a valid ISO file.': 'Please select a valid ISO file.',
            'Failed to mount source ISO file.': 'Failed to mount source ISO file.'
        }
    }
    
    for lang, msgs in translations.items():
        po_dir = f"{LOCALE_DIR}/{lang}/LC_MESSAGES"
        os.makedirs(po_dir, exist_ok=True)
        po_path = f"{po_dir}/mind-arc.po"
        mo_path = f"{po_dir}/mind-arc.mo"
        
        with open(po_path, 'w', encoding='utf-8') as f:
            f.write('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n')
            for msgid, msgstr in msgs.items():
                safe_msgid = msgid.replace('"', '\\"')
                safe_msgstr = msgstr.replace('"', '\\"')
                f.write(f'msgid "{safe_msgid}"\n')
                f.write(f'msgstr "{safe_msgstr}"\n\n')
                
        compile_po_to_mo(po_path, mo_path)

setup_translations()
current_translation = gettext.translation('mind-arc', LOCALE_DIR, languages=['tr'], fallback=True)

# Ek sayfalar: mindpkg Paket Merkezi ve Sistem Bakımı
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mindarc_extra


# --- GSettings Helper ve Güvenli Erişim Metotları ---

def get_gsettings_bool(schema, key, default=False):
    try:
        settings = Gio.Settings.new(schema)
        return settings.get_boolean(key)
    except Exception:
        try:
            res = subprocess.check_output(["gsettings", "get", schema, key], stderr=subprocess.DEVNULL, text=True).strip()
            return res == "true"
        except Exception:
            return default

def set_gsettings_bool(schema, key, val):
    try:
        settings = Gio.Settings.new(schema)
        settings.set_boolean(key, val)
    except Exception:
        try:
            val_str = "true" if val else "false"
            subprocess.run(["gsettings", "set", schema, key, val_str], stderr=subprocess.DEVNULL)
        except Exception:
            pass


def get_mic_hard_status():
    try:
        res = subprocess.check_output("pactl get-source-mute @DEFAULT_SOURCE@ 2>/dev/null", shell=True, text=True)
        if "Mute: yes" in res:
            return False
    except Exception:
        pass
    return not get_gsettings_bool("org.gnome.desktop.privacy", "disable-microphone", False)

def get_camera_hard_status():
    video_devices = glob.glob("/dev/video*")
    if video_devices:
        try:
            if not os.access(video_devices[0], os.R_OK):
                return False
        except Exception:
            pass
    try:
        with open("/proc/modules", "r") as f:
            modules = f.read()
        if "uvcvideo" not in modules:
            return False
    except Exception:
        pass
    return not get_gsettings_bool("org.gnome.desktop.privacy", "disable-camera", False)


# --- Sistem Verilerini Okuma Yardımcı Fonksiyonları ---

def get_os_name():
    try:
        with open("/etc/mindos-release", "r") as f:  # mindpkg güncel sürümü buraya yazar (ör. MindOS Paradise 1.1)
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "Debian GNU/Linux 12 (bookworm)"


def get_uptime_seconds():
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.readline().split()[0])
    except Exception:
        return 0.0


def run_cmd(args, timeout=3):
    """Komutun çıktısı; hata ya da zaman aşımında "" (donanım okumaları arayüzü asla kilitlemesin)"""
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def get_cpu_model():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if "model name" in line:
                    return line.split(':', 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "—"


def get_cpu_temp():
    """İşlemci sıcaklığı (°C). Sensör bulunamazsa None döner; uydurma bir değer gösterilmez."""
    try:
        temps = psutil.sensors_temperatures()
    except Exception:
        temps = {}
    # AMD: k10temp/zenpower (Tctl), Intel: coretemp (Package id 0), ARM: cpu_thermal
    for name, preferred in (("k10temp", ("Tctl", "Tdie")), ("zenpower", ("Tdie", "Tctl")),
                            ("coretemp", ("Package id 0",)), ("cpu_thermal", ()), ("soc_thermal", ())):
        entries = [e for e in temps.get(name, []) if e.current]
        if entries:
            best = next((e for e in entries if e.label in preferred), entries[0])
            return best.current
    for zone in glob.glob("/sys/class/thermal/thermal_zone*"):
        try:
            with open(os.path.join(zone, "type")) as f:
                if f.read().strip() not in ("x86_pkg_temp", "cpu-thermal", "cpu_thermal"):
                    continue
            with open(os.path.join(zone, "temp")) as f:
                return int(f.read().strip()) / 1000.0
        except Exception:
            pass
    return None


def get_gpu_info():
    gpu_model = "Unknown Graphics"
    gpu_usage = 0
    gpu_temp = 0.0
    
    try:
        gpu_lines = [l for l in run_cmd(["lspci", "-nn"]).splitlines() if re.search(r"VGA|3D|Display", l)]
        if gpu_lines:
            line = gpu_lines[0]
            parts = line.split(":", 2)
            if len(parts) >= 3:
                device_info = parts[2].strip()
                brackets = re.findall(r'\[(.*?)\]', device_info)
                candidates = [b for b in brackets if b not in ["0300", "3D", "Display"] and ":" not in b]
                if candidates:
                    selected_name = candidates[-1]
                    for cand in candidates:
                        if any(k in cand.lower() for k in ["radeon", "geforce", "nvidia", "intel", "arc", "graphics"]):
                            selected_name = cand
                            break
                    gpu_model = selected_name
                else:
                    gpu_model = device_info
            
            gpu_model = gpu_model.replace("Advanced Micro Devices, Inc. [AMD/ATI]", "AMD Radeon").replace("[AMD/ATI]", "").strip()
    except Exception:
        pass
        
    sys_cards = glob.glob("/sys/class/drm/card*/device")
    for card_path in sys_cards:
        try:
            with open(os.path.join(card_path, "vendor"), "r") as f:
                vendor = f.read().strip()
            
            if "0x1002" in vendor:
                busy_path = os.path.join(card_path, "gpu_busy_percent")
                if os.path.exists(busy_path):
                    with open(busy_path, "r") as f:
                        gpu_usage = int(f.read().strip())
                        
                hwmon_glob = glob.glob(os.path.join(card_path, "hwmon", "hwmon*"))
                if not hwmon_glob:
                    hwmon_glob = glob.glob("/sys/class/hwmon/hwmon*")
                for h_dir in hwmon_glob:
                    try:
                        with open(os.path.join(h_dir, "name"), "r") as f:
                            name = f.read().strip()
                        if "amdgpu" in name:
                            temp_path = os.path.join(h_dir, "temp1_input")
                            if os.path.exists(temp_path):
                                with open(temp_path, "r") as f:
                                    gpu_temp = int(f.read().strip()) / 1000.0
                                break
                    except Exception:
                        pass
                break
        except Exception:
            pass
            
    if "NVIDIA" in gpu_model.upper() or gpu_model == "Unknown Graphics":
        try:
            res = run_cmd(["nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu",
                           "--format=csv,noheader,nounits"])
            parts = res.strip().split(",")
            if len(parts) >= 3:
                gpu_model = parts[0].strip()
                gpu_usage = int(parts[1].strip())
                gpu_temp = float(parts[2].strip())
        except Exception:
            pass
            
    return gpu_model, gpu_usage, gpu_temp


def get_gpu_driver():
    for driver_path in sorted(glob.glob("/sys/class/drm/card*/device/driver")):
        try:
            return os.path.basename(os.readlink(driver_path))
        except Exception:
            pass
    return "—"


def get_gpu_pwm_paths():
    card_path = "/sys/class/drm/card0/device"
    hwmon_glob = glob.glob(os.path.join(card_path, "hwmon", "hwmon*"))
    if not hwmon_glob:
        hwmon_glob = glob.glob("/sys/class/hwmon/hwmon*")
    for h_dir in hwmon_glob:
        try:
            with open(os.path.join(h_dir, "name"), "r") as f:
                name = f.read().strip()
            if "amdgpu" in name:
                pwm_path = os.path.join(h_dir, "pwm1")
                pwm_enable_path = os.path.join(h_dir, "pwm1_enable")
                return pwm_path, pwm_enable_path
        except Exception:
            pass
    return None, None


def get_ram_speed():
    """RAM hızı ve tipi, systemd-udevd'nin okuduğu DMI bilgisinden (yetki gerektirmez).
    Kurulu modüllerden en yüksek çalışma hızı gösterilir; okunamazsa "—"."""
    try:
        out = subprocess.run(["udevadm", "info", "-q", "property", "-p", "/devices/virtual/dmi/id"],
                             capture_output=True, text=True, timeout=5).stdout
        props = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
        best = None
        for key, size in props.items():
            m = re.fullmatch(r"MEMORY_DEVICE_(\d+)_SIZE", key)
            if not m or not size.isdigit() or int(size) == 0:
                continue
            i = m.group(1)
            speed = props.get(f"MEMORY_DEVICE_{i}_CONFIGURED_SPEED_MTS") or props.get(f"MEMORY_DEVICE_{i}_SPEED_MTS")
            if speed and speed.isdigit() and int(speed) > 0 and (best is None or int(speed) > best[0]):
                best = (int(speed), props.get(f"MEMORY_DEVICE_{i}_TYPE", ""))
        if best:
            kind = best[1] if best[1] and best[1] not in ("Unknown", "Other") else ""
            return f"{kind} · {best[0]} MT/s" if kind else f"{best[0]} MT/s"
    except Exception:
        pass
    return "—"


def get_disk_usage():
    try:
        usage = psutil.disk_usage('/')
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        return f"{used_gb:.1f} GB / {total_gb:.1f} GB ({usage.percent}%)"
    except Exception:
        return "N/A"


def get_usb_drives():
    drives = []
    try:
        data = json.loads(run_cmd(["lsblk", "-d", "-o", "NAME,SIZE,TRAN,MODEL", "-J"]) or "{}")
        if "blockdevices" in data:
            for dev in data["blockdevices"]:
                if dev.get("tran") == "usb":
                    name = dev.get("name", "")
                    size = dev.get("size", "")
                    model = dev.get("model", "") or "USB Drive"
                    drives.append((f"/dev/{name}", f"/dev/{name} - {model} ({size})"))
    except Exception:
        pass
        
    if not drives:
        for p in glob.glob("/sys/block/sd*"):
            try:
                with open(os.path.join(p, "removable"), "r") as f:
                    if f.read().strip() == "1":
                        dev_name = os.path.basename(p)
                        drives.append((f"/dev/{dev_name}", f"/dev/{dev_name} - USB Drive"))
            except Exception:
                pass
    return drives


def get_categorized_devices():
    categories = {
        'mouse': [],
        'keyboard': [],
        'headset': [],
        'bluetooth': []
    }
    
    if os.path.exists('/proc/bus/input/devices'):
        try:
            with open('/proc/bus/input/devices', 'r') as f:
                content = f.read()
            blocks = content.split('\n\n')
            for block in blocks:
                lines = block.split('\n')
                name = ""
                handlers = ""
                is_mouse = False
                is_kbd = False
                for line in lines:
                    if line.startswith('N: Name='):
                        name = line.split('=', 1)[1].strip('"')
                    elif line.startswith('H: Handlers='):
                        handlers = line.split('=', 1)[1]
                        if 'mouse' in handlers:
                            is_mouse = True
                        if 'kbd' in handlers:
                            is_kbd = True
                if name:
                    # sistem düğmeleri ve hoparlör de "kbd" olarak görünür; dahili klavye (AT Translated) kalır
                    if any(x in name.lower() for x in ["power button", "video bus", "sleep button", "lid switch",
                                                       "pc speaker", "pc spkr"]):
                        continue
                    if name.lower().startswith("at translated set 2 keyboard"):
                        name = "Dahili klavye" if os.environ.get("LANG", "").startswith("tr") else "Built-in keyboard"
                    if is_mouse:
                        categories['mouse'].append(name)
                    elif is_kbd:
                        categories['keyboard'].append(name)
        except Exception:
            pass
            
    try:
        res = run_cmd(["bluetoothctl", "--timeout", "2", "devices", "Connected"]) \
            if glob.glob("/sys/class/bluetooth/hci*") else ""
        for line in res.splitlines():
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                dev_name = parts[2].strip()
                categories['bluetooth'].append(dev_name)
                if any(k in dev_name.lower() for k in ["headphone", "headset", "earbud", "audio", "sound", "speaker", "buds"]):
                    categories['headset'].append(dev_name)
    except Exception:
        pass
        
    try:
        res = run_cmd(["lsusb"])
        for line in res.splitlines():
            if "root hub" not in line.lower() and "hub" not in line.lower():
                parts = line.split(":", 1)
                if len(parts) > 1:
                    dev_name = parts[1].strip()[9:]
                    if any(k in dev_name.lower() for k in ["headset", "headphone", "audio", "mic", "dac", "sound"]):
                        categories['headset'].append(dev_name)
                    elif any(k in dev_name.lower() for k in ["dongle", "receiver", "adapter", "bluetooth", "wireless"]):
                        if dev_name not in categories['bluetooth']:
                            categories['bluetooth'].append(dev_name)
    except Exception:
        pass
        
    for k in categories:
        categories[k] = list(set(categories[k]))
        
    return categories


def get_system_volume():
    try:
        res = run_cmd(["amixer", "get", "Master"])
        match = re.search(r'\[(\d+)%\]', res)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    try:
        res = run_cmd(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
        match = re.search(r'(\d+)%', res)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return 50


def set_system_volume(val):
    try:
        subprocess.run(["amixer", "set", "Master", f"{int(val)}%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{int(val)}%"], stderr=subprocess.DEVNULL)
    except Exception:
        pass


def get_screen_brightness():
    backlights = glob.glob("/sys/class/backlight/*")
    if backlights:
        try:
            b_dir = backlights[0]
            with open(os.path.join(b_dir, "brightness"), "r") as f:
                curr = int(f.read().strip())
            with open(os.path.join(b_dir, "max_brightness"), "r") as f:
                max_b = int(f.read().strip())
            return int((curr / max_b) * 100)
        except Exception:
            pass
    try:
        res = run_cmd(["brightnessctl", "get"])
        max_b = int(run_cmd(["brightnessctl", "max"]))
        return int((int(res.strip()) / max_b) * 100)
    except Exception:
        pass
    return 70


def set_screen_brightness(val):
    try:
        subprocess.run(["brightnessctl", "set", f"{int(val)}%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


# --- Arayüz Sınıfları ---

class MindArcWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(950, 720)
        self.set_title("Mind-Arc Control Center")
        
        # Dil tespiti
        self.current_lang_code = 'tr'
        try:
            sys_lang, dummy_encoding = locale.getlocale()
            if not sys_lang:
                sys_lang = os.environ.get('LANG', 'tr')
            if sys_lang and sys_lang.lower().startswith('en'):
                self.current_lang_code = 'en'
        except Exception:
            pass
            
        self.set_language_translation(self.current_lang_code)

        # Görünüm mimarisi
        self.nav_view = Adw.NavigationView()
        self.set_content(self.nav_view)

        # Sidebar animasyon ve genişlik takipleri
        self.sidebar_expanded = False
        self.current_sidebar_width = 60
        self.sidebar_tick_id = 0
        self.sidebar_items = []
        self.is_updating_sliders = False
        self.usb_drive_data = []
        self.usb_warning_shown = False # DND/Beta uyarısı oturum kontrolü

        # Asenkron çalışan sistem verilerini tutmak için sözlük
        self.latest_stats = {
            "uptime_str": "...",
            "cpu_usage": 0.0,
            "cpu_temp": None,
            "ram_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0,
            "gpu_model": "Unknown",
            "gpu_usage": 0,
            "gpu_temp": 0.0,
            "gpu_driver": "N/A",
            "cpu_model": "…",
            "ram_speed": "…",
            "cpu_logical": 4,
            "cpu_physical": 2,
            "cpu_speed": "N/A",
            "volume": 50,
            "brightness": 70,
            "devices": {'mouse': [], 'keyboard': [], 'headset': [], 'bluetooth': []},
            "usb_drives": []
        }

        # Ana Tercihler Sayfası
        self.main_page = Adw.NavigationPage.new(self.create_main_content(), _("Mind-Arc Control Center"))
        self.main_page.set_tag("main")
        self.nav_view.add(self.main_page)

        # Fan Kontrolü Alt Sayfası
        self.fan_page = Adw.NavigationPage.new(self.create_fan_control_content(), _("Fan Settings"))
        self.fan_page.set_tag("fan_settings")
        self.nav_view.add(self.fan_page)

        # Temayı uygula (Varsayılan olarak Açık Tema ve Libadwaita StyleManager ile zorlanmış temiz düzen)
        self.apply_theme_css(False)
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)

        # Arayüz metinlerini güncelle
        self.update_ui_texts()
        
        # Arka Plan İşçi İpliğini (Thread) başlat.
        self.stats_active = True
        self.stats_thread = threading.Thread(target=self.bg_stats_worker, daemon=True)
        self.stats_thread.start()

        # Ana arayüz verilerini ekrana basmak için 1 saniyelik hafif timer
        GLib.timeout_add_seconds(1, self.update_ui_with_latest_stats)

    def apply_theme_css(self, is_dark):
        css_provider = Gtk.CssProvider()
        if is_dark:
            css_data = """
            .sidebar {
                background-color: #111823;
                border-right: 1px solid rgba(0, 242, 254, 0.2);
                padding: 10px;
            }
            .sidebar-btn {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 10px;
                margin: 2px 0;
                color: #e2e8f0;
                font-weight: 500;
            }
            .sidebar-btn:hover {
                background-color: rgba(0, 242, 254, 0.15);
                color: #00f2fe;
            }
            .sidebar-btn.active {
                background-color: rgba(0, 242, 254, 0.25);
                color: #00f2fe;
                font-weight: bold;
                border-left: 3px solid #00f2fe;
            }
            .hw-card {
                background-color: rgba(22, 28, 36, 0.85);
                border: 1px solid rgba(0, 242, 254, 0.25);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
            }
            .hw-card:hover {
                border-color: rgba(0, 242, 254, 0.6);
                background-color: rgba(26, 32, 44, 0.95);
            }
            .hw-card-title {
                color: rgba(226, 232, 240, 0.55);
            }
            .hw-card-value {
                color: #00f2fe;
            }
            """
        else:
            css_data = """
            .sidebar {
                background-color: #ffffff;
                border-right: 1px solid rgba(0, 128, 138, 0.25);
                padding: 10px;
            }
            .sidebar-btn {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 10px;
                margin: 2px 0;
                color: #1f2937;
                font-weight: 500;
            }
            .sidebar-btn:hover {
                background-color: rgba(0, 128, 138, 0.1);
                color: #047857;
            }
            .sidebar-btn.active {
                background-color: rgba(0, 128, 138, 0.15);
                color: #047857;
                font-weight: bold;
                border-left: 3px solid #047857;
            }
            .hw-card {
                background-color: #ffffff;
                border: 1px solid rgba(0, 128, 138, 0.3);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06);
            }
            .hw-card:hover {
                border-color: rgba(0, 128, 138, 0.8);
                background-color: #f9fafb;
            }
            .hw-card-title {
                color: rgba(31, 41, 55, 0.7);
            }
            .hw-card-value {
                color: #047857;
            }
            """
            
        common_css = """
        .hw-card, .sidebar, .sidebar-btn, preferencesgroup, preferencespage, listview, listbox, button, switch, scale {
            transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .suggested-action, button.suggested-action {
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
            color: #050505;
            border-radius: 8px;
            font-weight: bold;
            border: none;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
        }
        button.suggested-action:hover {
            background: linear-gradient(135deg, #00f2fe 30%, #00e0ed 100%);
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.6);
        }
        switch:checked {
            background-color: #00f2fe;
            border-color: #00f2fe;
        }
        scale highlight {
            background-color: #00f2fe;
        }
        scale slider {
            background-color: #00f2fe;
            border: 2px solid #e2e8f0;
            border-radius: 50%;
        }
        progressbar progress {
            background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
            border-radius: 4px;
        }
        .hw-card {
            margin: 4px;
            min-width: 210px;
            min-height: 80px;
            border-radius: 12px;
            padding: 12px;
        }
        .hw-card-title {
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .hw-card-value {
            font-size: 13px;
            font-weight: 800;
            margin-top: 4px;
        }
        """
        full_css = css_data + common_css
        css_provider.load_from_data(full_css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def create_hw_card(self, title, icon):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("hw-card")
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon_label = Gtk.Label(label=icon)
        icon_label.set_valign(Gtk.Align.CENTER)
        title_label = Gtk.Label(label=title)
        title_label.add_css_class("hw-card-title")
        title_label.set_halign(Gtk.Align.START)
        
        title_box.append(icon_label)
        title_box.append(title_label)
        card.append(title_box)
        
        val_label = Gtk.Label(label="...")
        val_label.add_css_class("hw-card-value")
        val_label.set_halign(Gtk.Align.START)
        val_label.set_wrap(True)
        val_label.set_max_width_chars(32)
        card.append(val_label)
        
        return card, val_label, title_label

    def create_main_content(self):
        root_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        # 1. Sol Sidebar
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.sidebar_box.add_css_class("sidebar")
        self.sidebar_box.set_size_request(60, -1)
        
        sidebar_header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar_header.set_margin_top(12)
        sidebar_header.set_margin_bottom(12)
        
        # Hamburger Menü Butonu (☰) - Sol tarafa hizalandı (START)
        hamburger_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hamburger_box.set_halign(Gtk.Align.START)
        hamburger_box.set_margin_start(10)
        self.btn_hamburger = Gtk.Button()
        self.btn_hamburger.set_icon_name("open-menu-symbolic")
        self.btn_hamburger.add_css_class("flat")
        self.btn_hamburger.connect("clicked", self.on_hamburger_clicked)
        hamburger_box.append(self.btn_hamburger)
        sidebar_header.append(hamburger_box)
        
        self.sidebar_box.append(sidebar_header)
        
        # Dikey Buton Grubu
        self.sidebar_btn_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.sidebar_btn_container.set_margin_start(4)
        self.sidebar_btn_container.set_margin_end(4)
        self.sidebar_box.append(self.sidebar_btn_container)
        
        root_layout.append(self.sidebar_box)
        
        # 2. Sağ İçerik Alanı
        right_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_container.set_hexpand(True)
        
        self.header_bar = Adw.HeaderBar()
        right_container.append(self.header_bar)
        
        self.view_stack = Gtk.Stack()
        self.view_stack.set_vexpand(True)
        self.view_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.view_stack.set_transition_duration(250)
        self.view_stack.connect("notify::visible-child", self.on_stack_child_changed)
        
        right_container.append(self.view_stack)
        root_layout.append(right_container)
        
        self.construct_preferences_pages()
        mindarc_extra.build_extra_pages(self)
        self.setup_sidebar_navigation()
        
        return root_layout

    def setup_sidebar_navigation(self):
        child = self.sidebar_btn_container.get_first_child()
        while child:
            self.sidebar_btn_container.remove(child)
            child = self.sidebar_btn_container.get_first_child()
            
        items = [
            ("about", "ℹ️", _("System Info")),
            ("hardware", "💻", _("Internal Hardware")),
            ("peripherals", "🖱️", _("Peripherals")),
            ("usb_installer", "💾", _("MindOS USB Installer [EXPERIMENTAL]")),
            ("appearance", "⚙️", _("General Settings")),
            ("performance", "⚡", _("Performance and Tweak")),
        ] + mindarc_extra.extra_sidebar_items(self)
        
        self.sidebar_items = []
        for page_name, icon, text in items:
            btn = Gtk.Button()
            btn.add_css_class("sidebar-btn")
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            
            icon_lbl = Gtk.Label(label=icon)
            icon_lbl.set_valign(Gtk.Align.CENTER)
            
            txt_lbl = Gtk.Label(label=text)
            txt_lbl.set_valign(Gtk.Align.CENTER)
            txt_lbl.set_visible(self.sidebar_expanded)
            
            box.append(icon_lbl)
            box.append(txt_lbl)
            btn.set_child(box)
            
            if not self.sidebar_expanded:
                btn.set_tooltip_text(text)
                
            btn.connect("clicked", self.on_sidebar_btn_clicked, page_name)
            
            self.sidebar_btn_container.append(btn)
            self.sidebar_items.append((btn, txt_lbl, text, page_name))

    def on_sidebar_btn_clicked(self, button, page_name):
        self.view_stack.set_visible_child_name(page_name)

    def on_stack_child_changed(self, stack, gparam):
        child = stack.get_visible_child()
        if child:
            name = stack.get_visible_child_name()
            self.update_active_sidebar_button(name)
            
            # USB Installer seçildiğinde Beta Uyarısını tetikle (Yeni!)
            if name == "usb_installer":
                self.show_usb_beta_warning_dialog()

    def show_usb_beta_warning_dialog(self):
        """
        Sekme açıldığında kullanıcıya bu özelliğin deneysel olduğunu belirten uyarı popupu.
        """
        if self.usb_warning_shown:
            return
            
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Beta Warning"),
            body=_("This is an experimental beta feature. Your USB drive could be damaged, and all existing data will be permanently erased. The MindOS team is not responsible for any damage or data loss that may occur. Please proceed with caution.")
        )
        dialog.add_response("ok", "Tamam / OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        
        def on_response(dialog, response_id):
            self.usb_warning_shown = True
            dialog.destroy()
            
        dialog.connect("response", on_response)
        dialog.present()

    def update_active_sidebar_button(self, page_name):
        for btn, label, text, name in self.sidebar_items:
            if name == page_name:
                btn.add_css_class("active")
            else:
                btn.remove_css_class("active")

    def on_hamburger_clicked(self, button):
        self.sidebar_expanded = not self.sidebar_expanded
        self.target_sidebar_width = 200 if self.sidebar_expanded else 60
        
        if not self.sidebar_expanded:
            for btn, label, text, name in self.sidebar_items:
                label.set_visible(False)

        if self.sidebar_tick_id:
            self.sidebar_box.remove_tick_callback(self.sidebar_tick_id)
            
        self.sidebar_tick_id = self.sidebar_box.add_tick_callback(self.on_sidebar_tick_step)

    def on_sidebar_tick_step(self, widget, frame_clock):
        step = 16
        if self.current_sidebar_width < self.target_sidebar_width:
            self.current_sidebar_width = min(self.current_sidebar_width + step, self.target_sidebar_width)
        else:
            self.current_sidebar_width = max(self.current_sidebar_width - step, self.target_sidebar_width)
            
        self.sidebar_box.set_size_request(self.current_sidebar_width, -1)
        
        if self.current_sidebar_width == self.target_sidebar_width:
            if self.sidebar_expanded:
                for btn, label, text, name in self.sidebar_items:
                    label.set_visible(True)
            else:
                for btn, label, text, name in self.sidebar_items:
                    label.set_visible(False)
                    btn.set_tooltip_text(text)
            self.sidebar_tick_id = 0
            return False
            
        return True

    def construct_preferences_pages(self):
        """
        Sağ taraftaki ViewStack içine eklenecek olan tüm kontrol paneli sayfalarını oluşturur.
        """
        # --- 1. SEKMELER: SİSTEM HAKKINDA (System Info) ---
        self.page_about = Adw.PreferencesPage()
        self.page_about.set_title(_("System Info"))
        
        self.group_about = Adw.PreferencesGroup()
        self.group_about.set_title(_("Welcome to Mind-Arc Control Center"))
        self.group_about.set_description(_("System overview details"))
        
        # OS Row
        self.row_os = Adw.ActionRow()
        self.row_os.set_title(_("OS Name"))
        self.row_os.add_prefix(Gtk.Label.new("💻"))
        self.label_os_val = Gtk.Label(label=get_os_name())
        self.row_os.add_suffix(self.label_os_val)
        self.group_about.add(self.row_os)
        
        # Kernel Row
        self.row_kernel = Adw.ActionRow()
        self.row_kernel.set_title(_("Kernel Version"))
        self.row_kernel.add_prefix(Gtk.Label.new("⚙️"))
        self.label_kernel_val = Gtk.Label(label=os.uname().release)
        self.row_kernel.add_suffix(self.label_kernel_val)
        self.group_about.add(self.row_kernel)
        
        # Masaüstü Ortamı Row
        self.row_desktop_env = Adw.ActionRow()
        self.row_desktop_env.set_title(_("Desktop Environment"))
        self.row_desktop_env.add_prefix(Gtk.Label.new("🪟"))
        self.label_desktop_env_val = Gtk.Label(label=os.environ.get("XDG_CURRENT_DESKTOP", "GNOME").strip())
        self.row_desktop_env.add_suffix(self.label_desktop_env_val)
        self.group_about.add(self.row_desktop_env)

        # Hostname Row
        self.row_hostname = Adw.ActionRow()
        self.row_hostname.set_title(_("Hostname"))
        self.row_hostname.add_prefix(Gtk.Label.new("📛"))
        self.label_hostname_val = Gtk.Label(label=platform.node())
        self.row_hostname.add_suffix(self.label_hostname_val)
        self.group_about.add(self.row_hostname)
        
        # Architecture Row
        self.row_arch = Adw.ActionRow()
        self.row_arch.set_title(_("System Architecture"))
        self.row_arch.add_prefix(Gtk.Label.new("🧬"))
        self.label_arch_val = Gtk.Label(label=platform.machine())
        self.row_arch.add_suffix(self.label_arch_val)
        self.group_about.add(self.row_arch)
        
        # Display Server Row
        self.row_display_server = Adw.ActionRow()
        self.row_display_server.set_title(_("Display Server"))
        self.row_display_server.add_prefix(Gtk.Label.new("🖥️"))
        self.label_display_server_val = Gtk.Label(label=os.environ.get("XDG_SESSION_TYPE", "X11").upper())
        self.row_display_server.add_suffix(self.label_display_server_val)
        self.group_about.add(self.row_display_server)
        
        # Disk Storage Row
        self.row_disk = Adw.ActionRow()
        self.row_disk.set_title(_("Disk Storage"))
        self.row_disk.add_prefix(Gtk.Label.new("💽"))
        self.label_disk_val = Gtk.Label(label=get_disk_usage())
        self.row_disk.add_suffix(self.label_disk_val)
        self.group_about.add(self.row_disk)

        # Uptime Row
        self.row_uptime = Adw.ActionRow()
        self.row_uptime.set_title(_("Uptime"))
        self.row_uptime.add_prefix(Gtk.Label.new("⏱️"))
        self.label_uptime_val = Gtk.Label(label="")
        self.row_uptime.add_suffix(self.label_uptime_val)
        self.group_about.add(self.row_uptime)
        
        self.page_about.add(self.group_about)
        self.view_stack.add_named(self.page_about, "about")

        # --- 2. SEKMELER: DAHİLİ DONANIM ---
        self.page_hardware = Adw.PreferencesPage()
        self.page_hardware.set_title(_("Internal Hardware"))
        
        self.group_hw_specs = Adw.PreferencesGroup()
        self.group_hw_specs.set_title(_("System Specifications"))
        
        grid_hw = Gtk.Grid()
        grid_hw.set_column_spacing(10)
        grid_hw.set_row_spacing(10)
        grid_hw.set_halign(Gtk.Align.CENTER)
        grid_hw.set_margin_top(10)
        grid_hw.set_margin_bottom(10)
        
        box_cpu_cores, self.lbl_cpu_cores_val, self.lbl_cpu_cores_title = self.create_hw_card(_("CPU Cores"), "🧬")
        box_cpu_speed, self.lbl_cpu_speed_val, self.lbl_cpu_speed_title = self.create_hw_card(_("CPU Clock Speed"), "⏱️")
        box_ram_speed, self.lbl_ram_speed_val, self.lbl_ram_speed_title = self.create_hw_card(_("RAM Speed"), "⚡")
        box_gpu_driver, self.lbl_gpu_driver_val, self.lbl_gpu_driver_title = self.create_hw_card(_("GPU Driver"), "🎮")
        
        box_cpu_model, self.lbl_cpu_model_val, self.lbl_cpu_model_title = self.create_hw_card(_("CPU Model"), "💻")
        box_gpu_model, self.lbl_gpu_model_val, self.lbl_gpu_model_title = self.create_hw_card(_("GPU Model"), "👾")
        
        grid_hw.attach(box_cpu_model, 0, 0, 2, 1)
        grid_hw.attach(box_gpu_model, 0, 1, 2, 1)
        grid_hw.attach(box_cpu_cores, 0, 2, 1, 1)
        grid_hw.attach(box_cpu_speed, 1, 2, 1, 1)
        grid_hw.attach(box_ram_speed, 0, 3, 1, 1)
        grid_hw.attach(box_gpu_driver, 1, 3, 1, 1)
        
        self.group_hw_specs.add(grid_hw)
        self.page_hardware.add(self.group_hw_specs)
        
        self.group_hw_live = Adw.PreferencesGroup()
        self.group_hw_live.set_title(_("Live Metrics"))
        self.group_hw_live.set_description(_("Monitor CPU, RAM and GPU metrics"))
        
        self.row_cpu = Adw.ActionRow()
        self.row_cpu.set_title(_("CPU Status"))
        self.row_cpu.add_prefix(Gtk.Label.new("💻"))
        self.label_cpu_val = Gtk.Label(label="0% | 0°C")
        self.cpu_progress = Gtk.ProgressBar()
        self.cpu_progress.set_size_request(150, -1)
        self.cpu_progress.set_valign(Gtk.Align.CENTER)
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cpu_box.append(self.cpu_progress)
        cpu_box.append(self.label_cpu_val)
        self.row_cpu.add_suffix(cpu_box)
        self.group_hw_live.add(self.row_cpu)
        
        self.row_ram = Adw.ActionRow()
        self.row_ram.set_title(_("RAM Status"))
        self.row_ram.add_prefix(Gtk.Label.new("⚡"))
        self.label_ram_val = Gtk.Label(label="0 / 0 GB")
        self.ram_progress = Gtk.ProgressBar()
        self.ram_progress.set_size_request(150, -1)
        self.ram_progress.set_valign(Gtk.Align.CENTER)
        ram_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ram_box.append(self.ram_progress)
        ram_box.append(self.label_ram_val)
        self.row_ram.add_suffix(ram_box)
        self.group_hw_live.add(self.row_ram)
        
        self.row_gpu_status = Adw.ActionRow()
        self.row_gpu_status.set_title(_("GPU Status"))
        self.row_gpu_status.add_prefix(Gtk.Label.new("🔥"))
        self.label_gpu_status_val = Gtk.Label(label="0% | 0°C")
        self.gpu_progress = Gtk.ProgressBar()
        self.gpu_progress.set_size_request(150, -1)
        self.gpu_progress.set_valign(Gtk.Align.CENTER)
        gpu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        gpu_box.append(self.gpu_progress)
        gpu_box.append(self.label_gpu_status_val)
        self.row_gpu_status.add_suffix(gpu_box)
        self.group_hw_live.add(self.row_gpu_status)

        self.page_hardware.add(self.group_hw_live)

        # Fan Kontrol Paneli
        group_fan_row = Adw.PreferencesGroup()
        self.row_fan_btn = Adw.ActionRow()
        self.row_fan_btn.set_title(_("Hardware Control [EXPERIMENTAL]"))
        self.row_fan_btn.set_subtitle(_("Hardware fan and safety configurations"))
        self.row_fan_btn.add_prefix(Gtk.Label.new("⚙️"))
        
        self.btn_hardware_control = Gtk.Button(label=_("(TEMPORARILY DISABLED)"))
        self.btn_hardware_control.add_css_class("suggested-action")
        self.btn_hardware_control.set_valign(Gtk.Align.CENTER)
        self.btn_hardware_control.set_sensitive(False)
        self.row_fan_btn.add_suffix(self.btn_hardware_control)
        group_fan_row.add(self.row_fan_btn)
        self.page_hardware.add(group_fan_row)

        self.view_stack.add_named(self.page_hardware, "hardware")

        # --- 3. SEKMELER: HARİCİ DONANIMLAR (Peripherals) ---
        self.page_peripherals = Adw.PreferencesPage()
        self.page_peripherals.set_title(_("Peripherals"))
        
        self.group_mice = Adw.PreferencesGroup()
        self.group_mice.set_title(_("Mice"))
        self.group_mice.set_description(_("Mice and Keyboard speed settings"))
        self.row_mice_list = Adw.ActionRow()
        self.row_mice_list.set_title(_("Connected Devices"))
        self.row_mice_list.add_prefix(Gtk.Label.new("🖱️"))
        self.mice_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.row_mice_list.add_suffix(self.mice_list_box)
        self.group_mice.add(self.row_mice_list)
        
        self.row_mouse_speed = Adw.ActionRow()
        self.row_mouse_speed.set_title(_("Mouse Speed"))
        self.row_mouse_speed.add_prefix(Gtk.Label.new("⚡"))
        self.mouse_speed_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1.0, 1.0, 0.1)
        self.mouse_speed_slider.set_size_request(200, -1)
        self.mouse_speed_slider.set_valign(Gtk.Align.CENTER)
        self.mouse_speed_slider.set_value(self.get_mouse_speed_gsettings())
        self.mouse_speed_slider.connect("value-changed", self.on_mouse_speed_changed)
        self.row_mouse_speed.add_suffix(self.mouse_speed_slider)
        self.group_mice.add(self.row_mouse_speed)
        self.page_peripherals.add(self.group_mice)
        
        self.group_keyboards = Adw.PreferencesGroup()
        self.group_keyboards.set_title(_("Keyboards"))
        self.row_kbd_list = Adw.ActionRow()
        self.row_kbd_list.set_title(_("Connected Devices"))
        self.row_kbd_list.add_prefix(Gtk.Label.new("⌨️"))
        self.kbd_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.row_kbd_list.add_suffix(self.kbd_list_box)
        self.group_keyboards.add(self.row_kbd_list)
        self.page_peripherals.add(self.group_keyboards)
        
        self.group_headsets = Adw.PreferencesGroup()
        self.group_headsets.set_title(_("Audio and Headsets"))
        self.row_headset_list = Adw.ActionRow()
        self.row_headset_list.set_title(_("Connected Devices"))
        self.row_headset_list.add_prefix(Gtk.Label.new("🎧"))
        self.headset_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.row_headset_list.add_suffix(self.headset_list_box)
        self.group_headsets.add(self.row_headset_list)
        self.page_peripherals.add(self.group_headsets)
        
        self.group_bluetooth = Adw.PreferencesGroup()
        self.group_bluetooth.set_title(_("Bluetooth and Receivers"))
        self.row_bt_list = Adw.ActionRow()
        self.row_bt_list.set_title(_("Connected Devices"))
        self.row_bt_list.add_prefix(Gtk.Label.new("🛜"))
        self.bt_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.row_bt_list.add_suffix(self.bt_list_box)
        self.group_bluetooth.add(self.row_bt_list)
        self.page_peripherals.add(self.group_bluetooth)

        self.view_stack.add_named(self.page_peripherals, "peripherals")

        # --- YENİ BÖLÜM: MindOS USB Installer [EXPERIMENTAL] ---
        self.page_usb_installer = Adw.PreferencesPage()
        self.page_usb_installer.set_title(_("MindOS USB Installer [EXPERIMENTAL]"))
        
        group_usb = Adw.PreferencesGroup()
        group_usb.set_title(_("MindOS USB Installer [EXPERIMENTAL]"))
        group_usb.set_description(_("Installs a complete, permanent MindOS on a USB drive or external disk (not a live system)"))
        
        # 1. USB Seçim Kutusu
        self.row_usb_select = Adw.ComboRow()
        self.row_usb_select.set_title(_("Target USB Drive"))
        self.row_usb_select.add_prefix(Gtk.Label.new("💾"))
        self.usb_combo_model = Gtk.StringList.new([_("No USB drives detected.")])
        self.row_usb_select.set_model(self.usb_combo_model)
        group_usb.add(self.row_usb_select)
        
        # 2. ISO Seçme Kutusu (Yeni!) - Dosya Seçme Native Dialog Tetikleyicili
        self.row_iso_select = Adw.ActionRow()
        self.row_iso_select.set_title(_("Source ISO File"))
        self.row_iso_select.add_prefix(Gtk.Label.new("💿"))
        
        iso_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.entry_iso_path = Gtk.Entry()
        self.entry_iso_path.set_placeholder_text("Select ISO file...")
        self.entry_iso_path.set_width_chars(25)
        self.entry_iso_path.set_valign(Gtk.Align.CENTER)
        
        self.btn_browse_iso = Gtk.Button()
        self.btn_browse_iso.set_icon_name("document-open-symbolic")
        self.btn_browse_iso.set_valign(Gtk.Align.CENTER)
        self.btn_browse_iso.connect("clicked", self.on_browse_iso_clicked)
        
        iso_box.append(self.entry_iso_path)
        iso_box.append(self.btn_browse_iso)
        
        self.row_iso_select.add_suffix(iso_box)
        group_usb.add(self.row_iso_select)
        
        # 3. Kullanıcı Adı Girişi
        self.row_new_username = Adw.ActionRow()
        self.row_new_username.set_title(_("New Username"))
        self.row_new_username.add_prefix(Gtk.Label.new("👤"))
        self.entry_username = Gtk.Entry()
        self.entry_username.set_placeholder_text("e.g. mindos")
        self.entry_username.set_valign(Gtk.Align.CENTER)
        self.row_new_username.add_suffix(self.entry_username)
        group_usb.add(self.row_new_username)
        
        # 4. Sudo Şifre Girişi
        self.row_new_password = Adw.ActionRow()
        self.row_new_password.set_title(_("Sudo Password"))
        self.row_new_password.add_prefix(Gtk.Label.new("🔑"))
        self.entry_password = Gtk.Entry()
        self.entry_password.set_visibility(False)
        self.entry_password.set_valign(Gtk.Align.CENTER)
        self.row_new_password.add_suffix(self.entry_password)
        group_usb.add(self.row_new_password)
        
        # 5. Sistem Dili Seçimi
        self.row_system_lang = Adw.ComboRow()
        self.row_system_lang.set_title(_("Target System Language"))
        self.row_system_lang.add_prefix(Gtk.Label.new("🌐"))
        self.system_lang_model = Gtk.StringList.new(["Türkçe (tr_TR)", "English (en_US)"])
        self.row_system_lang.set_model(self.system_lang_model)
        group_usb.add(self.row_system_lang)
        
        # 6. Klavye Düzeni
        self.row_kbd_layout = Adw.ComboRow()
        self.row_kbd_layout.set_title(_("Keyboard Layout"))
        self.row_kbd_layout.add_prefix(Gtk.Label.new("⌨️"))
        self.kbd_layout_model = Gtk.StringList.new(["Türkçe Q (tr)", "English US (us)"])
        self.row_kbd_layout.set_model(self.kbd_layout_model)
        group_usb.add(self.row_kbd_layout)
        
        # 7. Kurulumu Başlat Butonu
        self.row_btn_install = Adw.ActionRow()
        self.btn_start_install = Gtk.Button(label=_("Start Installation"))
        self.btn_start_install.add_css_class("suggested-action")
        self.btn_start_install.set_valign(Gtk.Align.CENTER)
        self.btn_start_install.connect("clicked", self.on_start_install_clicked)
        self.row_btn_install.add_suffix(self.btn_start_install)
        group_usb.add(self.row_btn_install)
        
        self.page_usb_installer.add(group_usb)
        self.view_stack.add_named(self.page_usb_installer, "usb_installer")

        # --- 4. SEKMELER: GÖRÜNÜM VE GENEL AYARLAR ---
        self.page_appearance = Adw.PreferencesPage()
        self.page_appearance.set_title(_("Appearance and General Settings"))
        
        self.group_appear = Adw.PreferencesGroup()
        self.group_appear.set_title(_("General Settings"))
        self.group_appear.set_description(_("Adjust display and network settings"))
        
        self.row_dark_mode = Adw.ActionRow()
        self.row_dark_mode.set_title(_("Dark Mode"))
        self.row_dark_mode.add_prefix(Gtk.Label.new("🌙"))
        self.switch_dark_mode = Gtk.Switch()
        self.switch_dark_mode.set_valign(Gtk.Align.CENTER)
        self.switch_dark_mode.set_active(False)
        self.switch_dark_mode.connect("notify::active", self.on_dark_mode_toggled)
        self.row_dark_mode.add_suffix(self.switch_dark_mode)
        self.group_appear.add(self.row_dark_mode)
        
        self.row_lang = Adw.ComboRow()
        self.row_lang.set_title(_("Language / Dil"))
        self.row_lang.add_prefix(Gtk.Label.new("🌐"))
        self.lang_model = Gtk.StringList.new(["Türkçe", "English"])
        self.row_lang.set_model(self.lang_model)
        if self.current_lang_code == 'tr':
            self.row_lang.set_selected(0)
        else:
            self.row_lang.set_selected(1)
        self.row_lang.connect("notify::selected", self.on_language_changed)
        self.group_appear.add(self.row_lang)
        
        self.row_volume = Adw.ActionRow()
        self.row_volume.set_title(_("System Volume"))
        self.row_volume.add_prefix(Gtk.Label.new("🔊"))
        self.volume_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.volume_slider.set_size_request(200, -1)
        self.volume_slider.set_valign(Gtk.Align.CENTER)
        self.volume_slider.set_value(get_system_volume())
        self.volume_slider.connect("value-changed", self.on_volume_changed)
        self.row_volume.add_suffix(self.volume_slider)
        self.group_appear.add(self.row_volume)
        
        self.row_brightness = Adw.ActionRow()
        self.row_brightness.set_title(_("Screen Brightness"))
        self.row_brightness.add_prefix(Gtk.Label.new("☀️"))
        self.brightness_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.brightness_slider.set_size_request(200, -1)
        self.brightness_slider.set_valign(Gtk.Align.CENTER)
        self.brightness_slider.set_value(get_screen_brightness())
        self.brightness_slider.connect("value-changed", self.on_brightness_changed)
        self.row_brightness.add_suffix(self.brightness_slider)
        self.group_appear.add(self.row_brightness)
        
        self.row_screen_timeout = Adw.ComboRow()
        self.row_screen_timeout.set_title(_("Screen Timeout"))
        self.row_screen_timeout.add_prefix(Gtk.Label.new("💤"))
        self.timeout_model = Gtk.StringList.new([_("1 Minute"), _("5 Minutes"), _("15 Minutes"), _("Never")])
        self.row_screen_timeout.set_model(self.timeout_model)
        self.row_screen_timeout.set_selected(self.get_screen_timeout_index())
        self.row_screen_timeout.connect("notify::selected", self.on_screen_timeout_changed)
        self.group_appear.add(self.row_screen_timeout)
        
        self.row_notifications = Adw.ActionRow()
        self.row_notifications.set_title(_("System Notifications"))
        self.row_notifications.add_prefix(Gtk.Label.new("🔔"))
        self.switch_notifications = Gtk.Switch()
        self.switch_notifications.set_valign(Gtk.Align.CENTER)
        self.switch_notifications.set_active(True)
        self.switch_notifications.connect("notify::active", self.on_notifications_toggled)
        self.row_notifications.add_suffix(self.switch_notifications)
        self.group_appear.add(self.row_notifications)
        
        self.row_dnd = Adw.ActionRow()
        self.row_dnd.set_title(_("Do Not Disturb"))
        self.row_dnd.add_prefix(Gtk.Label.new("🔕"))
        self.switch_dnd = Gtk.Switch()
        self.switch_dnd.set_valign(Gtk.Align.CENTER)
        self.switch_dnd.set_active(not get_gsettings_bool("org.gnome.desktop.notifications", "show-banners", True))
        self.switch_dnd.connect("notify::active", self.on_dnd_toggled)
        self.row_dnd.add_suffix(self.switch_dnd)
        self.group_appear.add(self.row_dnd)
        
        self.row_privacy_mic = Adw.ActionRow()
        self.row_privacy_mic.set_title(_("Microphone Access"))
        self.row_privacy_mic.add_prefix(Gtk.Label.new("🎙️"))
        self.switch_privacy_mic = Gtk.Switch()
        self.switch_privacy_mic.set_valign(Gtk.Align.CENTER)
        self.switch_privacy_mic.set_active(get_mic_hard_status())
        self.switch_privacy_mic.connect("notify::active", self.on_privacy_mic_toggled)
        self.row_privacy_mic.add_suffix(self.switch_privacy_mic)
        self.group_appear.add(self.row_privacy_mic)
        
        self.row_privacy_cam = Adw.ActionRow()
        self.row_privacy_cam.set_title(_("Camera Access"))
        self.row_privacy_cam.add_prefix(Gtk.Label.new("📷"))
        self.switch_privacy_cam = Gtk.Switch()
        self.switch_privacy_cam.set_valign(Gtk.Align.CENTER)
        self.switch_privacy_cam.set_active(get_camera_hard_status())
        self.switch_privacy_cam.connect("notify::active", self.on_privacy_cam_toggled)
        self.row_privacy_cam.add_suffix(self.switch_privacy_cam)
        self.group_appear.add(self.row_privacy_cam)
        
        self.page_appearance.add(self.group_appear)
        
        self.group_network = Adw.PreferencesGroup()
        self.group_network.set_title(_("Network Connections"))
        
        self.row_wifi = Adw.ActionRow()
        self.row_wifi.set_title(_("Wi-Fi"))
        self.row_wifi.add_prefix(Gtk.Label.new("📡"))
        self.switch_wifi = Gtk.Switch()
        self.switch_wifi.set_valign(Gtk.Align.CENTER)
        self.switch_wifi.set_active(self.get_wifi_status())
        self.switch_wifi.connect("notify::active", self.on_wifi_toggled)
        self.row_wifi.add_suffix(self.switch_wifi)
        self.row_bluetooth = Adw.ActionRow()
        self.row_bluetooth.set_title(_("Bluetooth"))
        self.row_bluetooth.add_prefix(Gtk.Label.new("🛜"))
        self.switch_bluetooth = Gtk.Switch()
        self.switch_bluetooth.set_valign(Gtk.Align.CENTER)
        self.switch_bluetooth.set_active(self.get_bluetooth_status())
        self.switch_bluetooth.connect("notify::active", self.on_bluetooth_toggled)
        self.row_bluetooth.add_suffix(self.switch_bluetooth)
        self.group_network.add(self.row_bluetooth)
        self.page_appearance.add(self.group_network)
        
        self.view_stack.add_named(self.page_appearance, "appearance")

        # --- 5. SEKMELER: PERFORMANS & TWEAK (11 Tweak) ---
        self.page_performance = Adw.PreferencesPage()
        self.page_performance.set_title(_("Performance and Tweak"))
        
        self.group_perf = Adw.PreferencesGroup()
        self.group_perf.set_title(_("Performance and Tweak"))
        self.group_perf.set_description(_("Optimize system performance"))
        
        self.tweak_rows = []
        
        def create_tweak_row(title_key, subtitle_key, icon, button_key, callback, impact_key):
            row = Adw.ActionRow()
            row.add_prefix(Gtk.Label.new(icon))
            btn = Gtk.Button()
            btn.add_css_class("suggested-action")
            btn.set_valign(Gtk.Align.CENTER)
            btn.connect("clicked", callback)
            row.add_suffix(btn)
            
            self.tweak_rows.append({
                "type": "button",
                "row": row,
                "control": btn,
                "title_key": title_key,
                "subtitle_key": subtitle_key,
                "button_key": button_key,
                "impact_key": impact_key
            })
            return row

        def create_tweak_switch_row(title_key, subtitle_key, icon, active_status, callback, impact_key):
            row = Adw.ActionRow()
            row.add_prefix(Gtk.Label.new(icon))
            sw = Gtk.Switch()
            sw.set_valign(Gtk.Align.CENTER)
            sw.set_active(active_status)
            sw.connect("notify::active", callback)
            row.add_suffix(sw)
            
            self.tweak_rows.append({
                "type": "switch",
                "row": row,
                "control": sw,
                "title_key": title_key,
                "subtitle_key": subtitle_key,
                "button_key": None,
                "impact_key": impact_key
            })
            return row

        self.group_perf.add(create_tweak_row(
            "Clear System Cache", "Clear System Cache", "🧹", "Clear System Cache",
            self.on_clear_cache_clicked, "Medium"
        ))
        self.group_perf.add(create_tweak_row(
            "RAM Optimization", "Compress system RAM to free up memory", "📦", "Apply",
            self.on_ram_opt_clicked, "Medium"
        ))
        self.group_perf.add(create_tweak_switch_row(
            "Performance Mode", "Set CPU governor to performance mode", "🔥",
            self.get_cpu_governor_status(), self.on_perf_mode_toggled, "High"
        ))
        self.group_perf.add(create_tweak_row(
            "ZRAM Optimization", "Optimize ZRAM swappiness for responsiveness", "⚡", "Apply",
            self.on_zram_clicked, "Medium"
        ))
        self.group_perf.add(create_tweak_row(
            "System Log Vacuum", "Clean system journal logs older than 1 day", "📝", "Apply",
            self.on_log_vacuum_clicked, "Low"
        ))
        
        self.page_performance.add(self.group_perf)
        self.view_stack.add_named(self.page_performance, "performance")

    def create_fan_control_content(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        self.fan_header_bar = Adw.HeaderBar()
        main_box.append(self.fan_header_bar)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        main_box.append(scrolled)
        
        pref_page = Adw.PreferencesPage()
        scrolled.set_child(pref_page)
        
        self.group_fan = Adw.PreferencesGroup()
        self.group_fan.set_title(_("GPU Fan Control"))
        self.group_fan.set_description(_("Hardware fan and safety configurations"))
        pref_page.add(self.group_fan)
        
        self.row_fan_device = Adw.ActionRow()
        self.row_fan_device.set_title(_("Controlled Device"))
        self.row_fan_device.add_prefix(Gtk.Label.new("🎮"))
        
        self.lbl_fan_device_val = Gtk.Label(label="Unknown GPU")
        self.row_fan_device.add_suffix(self.lbl_fan_device_val)
        self.group_fan.add(self.row_fan_device)
        
        self.row_warning_info = Adw.ActionRow()
        self.row_warning_info.set_title(_("Warning"))
        self.row_warning_info.set_subtitle(_("Hardware settings require root privileges."))
        self.row_warning_info.add_prefix(Gtk.Label.new("⚠️"))
        self.group_fan.add(self.row_warning_info)
        
        self.row_pwm_enable = Adw.ActionRow()
        self.row_pwm_enable.set_title(_("Fan Speed (PWM)") + " Manual Control")
        self.row_pwm_enable.add_prefix(Gtk.Label.new("⚙️"))
        self.switch_pwm = Gtk.Switch()
        self.switch_pwm.set_valign(Gtk.Align.CENTER)
        self.row_pwm_enable.add_suffix(self.switch_pwm)
        self.group_fan.add(self.row_pwm_enable)
        
        self.row_fan_speed = Adw.ActionRow()
        self.row_fan_speed.set_title(_("Fan Speed (PWM)"))
        self.row_fan_speed.add_prefix(Gtk.Label.new("🌀"))
        
        self.fan_speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 77, 255, 5)  # en az %30: fan asla durmasın
        self.fan_speed_scale.set_size_request(250, -1)
        self.fan_speed_scale.set_valign(Gtk.Align.CENTER)
        
        pwm_path, enable_path = get_gpu_pwm_paths()
        if enable_path and os.path.exists(enable_path):
            try:
                with open(enable_path, "r") as f:
                    self.switch_pwm.set_active(f.read().strip() == "1")
            except Exception:
                pass
                
        self.fan_speed_scale.set_value(self.read_gpu_pwm())
        self.row_fan_speed.add_suffix(self.fan_speed_scale)
        self.group_fan.add(self.row_fan_speed)
        
        self.row_apply_fan = Adw.ActionRow()
        btn_apply = Gtk.Button(label=_("Apply"))
        btn_apply.add_css_class("suggested-action")
        btn_apply.set_valign(Gtk.Align.CENTER)
        btn_apply.connect("clicked", self.on_apply_fan_clicked)
        self.row_apply_fan.add_suffix(btn_apply)
        self.group_fan.add(self.row_apply_fan)
        
        return main_box

    # --- File Chooser Native for ISO Selection ---

    def on_browse_iso_clicked(self, button):
        """
        GTK4 Uyumlu FileChooserNative ile kaynak ISO dosyası seçim penceresini açar.
        """
        dialog = Gtk.FileChooserNative.new(
            _("Select Source ISO File"),
            self,
            Gtk.FileChooserAction.OPEN,
            _("Select"),
            _("Cancel")
        )
        
        filter_iso = Gtk.FileFilter.new()
        filter_iso.set_name(_("ISO Images (*.iso)"))
        filter_iso.add_pattern("*.iso")
        dialog.add_filter(filter_iso)
        
        def on_response(dialog, response_id):
            if response_id == Gtk.ResponseType.ACCEPT:
                file_path = dialog.get_file().get_path()
                self.entry_iso_path.set_text(file_path)
            dialog.destroy()
            
        dialog.connect("response", on_response)
        dialog.show()

    # --- Asenkron Arka Plan Bilgi Okuma İşçi İpliği (Thread Worker) ---

    def bg_stats_worker(self):
        """Donanım bilgilerini arka planda toplar. Her ölçüm ayrı ayrı denenir; biri hata verir ya da
        zaman aşımına uğrarsa yalnızca o alan önceki değerinde kalır, sayfa boş kalmaz."""
        def measure(stats, key, fn):
            try:
                stats[key] = fn()
            except Exception as e:
                print(f"mind-arc: {key} okunamadı: {e}", file=sys.stderr)

        def cpu_speed():
            freq = psutil.cpu_freq()
            return f"{freq.current / 1000.0:.2f} GHz" if freq else "—"

        def uptime():
            sec = get_uptime_seconds()
            return f"{int(sec // 3600)}h {int(sec % 3600 // 60)}m {int(sec % 60)}s"

        slow_every, tick = 5, 0  # aygıt/GPU/USB taraması her 5 saniyede bir
        while self.stats_active:
            stats = dict(self.latest_stats)
            measure(stats, "uptime_str", uptime)
            measure(stats, "cpu_usage", lambda: psutil.cpu_percent(interval=None))
            measure(stats, "cpu_temp", get_cpu_temp)
            measure(stats, "cpu_speed", cpu_speed)
            ram = psutil.virtual_memory()
            stats.update(ram_percent=ram.percent, ram_used_gb=ram.used / 1024 ** 3, ram_total_gb=ram.total / 1024 ** 3)
            measure(stats, "volume", get_system_volume)
            measure(stats, "brightness", get_screen_brightness)
            if tick % slow_every == 0:
                measure(stats, "cpu_model", get_cpu_model)
                measure(stats, "cpu_logical", lambda: psutil.cpu_count(logical=True))
                measure(stats, "cpu_physical", lambda: psutil.cpu_count(logical=False) or psutil.cpu_count())
                measure(stats, "ram_speed", get_ram_speed)
                measure(stats, "gpu_driver", get_gpu_driver)
                measure(stats, "devices", get_categorized_devices)
                measure(stats, "usb_drives", get_usb_drives)
            try:
                stats["gpu_model"], stats["gpu_usage"], stats["gpu_temp"] = get_gpu_info()
            except Exception as e:
                print(f"mind-arc: GPU okunamadı: {e}", file=sys.stderr)
            self.latest_stats = stats
            tick += 1
            time.sleep(1)

    def update_ui_with_latest_stats(self):
        stats = self.latest_stats
        
        self.label_uptime_val.set_text(stats["uptime_str"])
        self.cpu_progress.set_fraction(stats["cpu_usage"] / 100.0)
        temp = stats['cpu_temp']
        self.label_cpu_val.set_text(f"{stats['cpu_usage']:.1f}% | " + (f"{temp:.1f}°C" if temp is not None else "—"))
        self.ram_progress.set_fraction(stats["ram_percent"] / 100.0)
        self.label_ram_val.set_text(f"{stats['ram_used_gb']:.1f} / {stats['ram_total_gb']:.1f} GB ({stats['ram_percent']:.1f}%)")
        self.gpu_progress.set_fraction(stats["gpu_usage"] / 100.0)
        self.label_gpu_status_val.set_text(f"{stats['gpu_usage']}% | {stats['gpu_temp']:.1f}°C")
        self.lbl_fan_device_val.set_text(stats["gpu_model"])
        
        self.is_updating_sliders = True
        try:
            self.volume_slider.set_value(stats["volume"])
            self.brightness_slider.set_value(stats["brightness"])
        except Exception:
            pass
        self.is_updating_sliders = False
        
        self.lbl_cpu_cores_val.set_text(f"{stats['cpu_physical']} / {stats['cpu_logical']}")
        self.lbl_cpu_speed_val.set_text(stats["cpu_speed"])
        self.lbl_ram_speed_val.set_text(stats["ram_speed"])
        self.lbl_gpu_driver_val.set_text(stats["gpu_driver"])
        self.lbl_cpu_model_val.set_text(stats["cpu_model"])
        self.lbl_gpu_model_val.set_text(stats["gpu_model"])
        
        self.update_connected_devices_from_stats(stats["devices"])
        
        current_usbs = [item[0] for item in stats["usb_drives"]]
        if not hasattr(self, 'last_usb_list') or self.last_usb_list != current_usbs:
            self.last_usb_list = current_usbs
            self.rebuild_usb_combo_model(stats["usb_drives"])
        
        return True

    def rebuild_usb_combo_model(self, usb_drives):
        self.usb_drive_data = usb_drives
        items = [d[1] for d in usb_drives]
        if not items:
            items = [_("No USB drives detected.")]
            self.btn_start_install.set_sensitive(False)
        else:
            self.btn_start_install.set_sensitive(True)
            
        n_items = self.usb_combo_model.get_n_items()
        self.usb_combo_model.splice(0, n_items, items)

    def update_connected_devices_from_stats(self, devs):
        def clear_box(box):
            child = box.get_first_child()
            while child:
                box.remove(child)
                child = box.get_first_child()
                
        clear_box(self.mice_list_box)
        clear_box(self.kbd_list_box)
        clear_box(self.headset_list_box)
        clear_box(self.bt_list_box)
        
        # Fareler
        if not devs['mouse']:
            self.mice_list_box.append(Gtk.Label(label=_("No mice detected.")))
        else:
            for m in devs['mouse']:
                self.mice_list_box.append(Gtk.Label(label=m))
                
        # Klavyeler
        if not devs['keyboard']:
            self.kbd_list_box.append(Gtk.Label(label=_("No keyboards detected.")))
        else:
            for k in devs['keyboard']:
                self.kbd_list_box.append(Gtk.Label(label=k))
                
        # Kulaklık & Ses
        if not devs['headset']:
            self.headset_list_box.append(Gtk.Label(label=_("No headsets detected.")))
        else:
            for h in devs['headset']:
                self.headset_list_box.append(Gtk.Label(label=h))
                
        # Bluetooth Alıcılar
        if not devs['bluetooth']:
            self.bt_list_box.append(Gtk.Label(label=_("No bluetooth devices detected.")))
        else:
            for b in devs['bluetooth']:
                self.bt_list_box.append(Gtk.Label(label=b))

    # --- USB Kurucu Buton Klik Tetiği ---

    def on_start_install_clicked(self, button):
        """
        Kurulumu başlatmadan önce zorunlu alanları doğrular ve onay diyalogu fırlatır.
        """
        username = self.entry_username.get_text().strip()
        password = self.entry_password.get_text().strip()
        iso_path = self.entry_iso_path.get_text().strip()
        
        if not username or not password or not iso_path:
            self.show_message_dialog(_("Error"), _("Fields cannot be empty."))
            return
        if len(password) < 6:
            self.show_message_dialog(_("Error"), _("Password must be at least 6 characters."))
            return
            
        if not os.path.exists(iso_path) or not iso_path.lower().endswith(".iso"):
            self.show_message_dialog(_("Error"), _("Please select a valid ISO file."))
            return
            
        selected_idx = self.row_usb_select.get_selected()
        if selected_idx < 0 or selected_idx >= len(self.usb_drive_data):
            self.show_message_dialog(_("Error"), _("No USB drives detected."))
            return
            
        dev_path, dev_label = self.usb_drive_data[selected_idx]
        
        lang_idx = self.row_system_lang.get_selected()
        lang_val = "tr" if lang_idx == 0 else "en"
        
        kbd_idx = self.row_kbd_layout.get_selected()
        kbd_val = "tr" if kbd_idx == 0 else "us"
        
        # Kullanıcıdan disk silme onayı al
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Confirm Disk Wipe"),
            body=f"{_('WARNING: All data on the selected USB drive will be permanently erased. Are you sure you want to proceed?')}\n\nHedef: {dev_label}\nKaynak ISO: {iso_path}"
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("accept", _("I Accept"))
        dialog.set_response_appearance("accept", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response_id):
            if response_id == "accept":
                self.show_install_progress_dialog()
                # Kurulum işçi ipliğini başlat
                install_thread = threading.Thread(
                    target=self.run_usb_installation,
                    args=(dev_path, iso_path, username, password, lang_val, kbd_val),
                    daemon=True
                )
                install_thread.start()
            dialog.destroy()
            
        dialog.connect("response", on_response)
        dialog.present()

    def show_install_progress_dialog(self):
        """
        Kurulum ilerlemesini ve adımlarını canlı gösteren modern progress penceresi.
        """
        self.install_dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Installing MindOS..."),
            body=_("Please wait while the operating system is installed on your USB drive.")
        )
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        self.install_progress_bar = Gtk.ProgressBar()
        self.install_progress_bar.set_fraction(0.0)
        self.install_status_label = Gtk.Label(label=_("Preparing disk (Partitioning)..."))
        self.install_status_label.set_halign(Gtk.Align.CENTER)
        
        box.append(self.install_progress_bar)
        box.append(self.install_status_label)
        
        self.install_dialog.set_extra_child(box)
        self.install_dialog.add_response("close", _("Close"))
        self.install_dialog.set_response_enabled("close", False)
        
        def on_dialog_response(dialog, response_id):
            dialog.destroy()
            
        self.install_dialog.connect("response", on_dialog_response)
        self.install_dialog.present()

    def run_usb_installation(self, dev_path, iso_path, username, password, lang, kbd):
        """
        USB'ye/harici diske tam MindOS kurulumunu /opt/mind-arc/usb-writer ile yapar (canlı sistem değil).
        Tüm root işlemleri tek bir pkexec çağrısında yapılır; girdiler betikte doğrulanır,
        şifre komut satırına değil standart girdiye yazılır.
        """
        steps = {
            "partition": _("Preparing disk (Partitioning)..."),
            "format": _("Formatting partition as ext4..."),
            "copy": _("Transferring system files..."),
            "configure": _("Configuring user and locale settings..."),
            "bootloader": _("Installing bootloader (BIOS + UEFI, Secure Boot)..."),
            "initramfs": _("Preparing the system for first boot..."),
            "sync": _("Writing changes to the drive (this may take a while)..."),
            "done": _("Installation completed successfully!"),
        }
        errors = {
            "invalid_username": _("Username may only contain lowercase letters, digits, '-' and '_'."),
            "system_disk": _("The selected drive holds the running system and cannot be used."),
            "not_removable": _("The selected drive is not a removable USB drive."),
            "partition": _("Disk partitioning failed."),
            "format": _("Disk formatting failed."),
            "mount_iso": _("Failed to mount source ISO file."),
            "mount_target": _("Mounting target partition failed."),
            "too_small": _("The drive is too small. At least 12 GB is required."),
            "weak_password": _("Password must be at least 6 characters."),
            "user": _("Creating the user account failed."),
            "copy": _("Copying system files failed. The drive may be faulty or full."),
            "bootloader": _("Installing the bootloader failed."),
            "initramfs": _("Preparing the system for first boot failed."),
            "invalid_iso": _("The selected ISO is not a valid MindOS image."),
        }

        def update_progress(fraction, status_text):
            GLib.idle_add(self.install_progress_bar.set_fraction, fraction)
            GLib.idle_add(self.install_status_label.set_text, status_text)

        update_progress(0.02, _("Preparing disk (Partitioning)..."))
        try:
            proc = subprocess.Popen(
                ["pkexec", "/opt/mind-arc/usb-writer", dev_path, iso_path, username, lang, kbd],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            proc.stdin.write(password + "\n")
            proc.stdin.close()
            for line in proc.stdout:
                parts = line.split()
                if len(parts) == 3 and parts[0] == "PROGRESS":
                    update_progress(float(parts[1]), steps.get(parts[2], parts[2]))
            err = proc.stderr.read()
            if proc.wait() != 0:
                code = next((l.split()[1] for l in err.splitlines() if l.startswith("ERROR ") and len(l.split()) > 1), "")
                raise Exception(errors.get(code, code or _("Authorization failed or was cancelled.")))
            GLib.idle_add(self.install_dialog.set_heading, _("Installation Completed"))
            GLib.idle_add(self.install_dialog.set_body, _("MindOS was installed on the drive as a full system. You can boot any computer from it; it keeps your files and updates like a normal installation."))
        except Exception as e:
            update_progress(0.0, f"{_('Error:')} {str(e)}")
            GLib.idle_add(self.install_dialog.set_heading, _("Installation Failed"))
        GLib.idle_add(self.install_dialog.set_response_enabled, "close", True)

    # --- Genel Ayarlar Callback Aksiyonları ---

    def on_volume_changed(self, scale):
        if self.is_updating_sliders:
            return
        val = scale.get_value()
        set_system_volume(val)

    def on_brightness_changed(self, scale):
        if self.is_updating_sliders:
            return
        val = scale.get_value()
        set_screen_brightness(val)

    def get_screen_timeout_index(self):
        """Ekran zaman aşımı listesinde sistemdeki geçerli değerin sırası (1/5/15 dk, hiçbir zaman)"""
        try:
            out = subprocess.run(["gsettings", "get", "org.gnome.desktop.session", "idle-delay"],
                                 capture_output=True, text=True).stdout.split()
            return {60: 0, 300: 1, 900: 2, 0: 3}.get(int(out[-1]), 1)
        except Exception:
            return 1

    def on_screen_timeout_changed(self, combo_row, gparam):
        idx = combo_row.get_selected()
        sec = 0
        if idx == 0:
            sec = 60
        elif idx == 1:
            sec = 300
        elif idx == 2:
            sec = 900
            
        try:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.session", "idle-delay", str(sec)], stderr=subprocess.DEVNULL)
            subprocess.run(["xset", "dpms", str(sec), str(sec), str(sec)], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def on_notifications_toggled(self, sw, gparam):
        active = sw.get_active()
        val = "true" if active else "false"
        try:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.notifications", "show-banners", str(val)], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def on_dnd_toggled(self, sw, gparam):
        active = sw.get_active()
        set_gsettings_bool("org.gnome.desktop.notifications", "show-banners", not active)

    def on_privacy_mic_toggled(self, sw, gparam):
        active = sw.get_active()
        set_gsettings_bool("org.gnome.desktop.privacy", "disable-microphone", not active)
        
        if not active:
            subprocess.run("pactl list sources short 2>/dev/null | cut -f2 | xargs -I {} pactl set-source-mute {} 1 2>/dev/null", shell=True)
            subprocess.run("amixer set Capture nocap 2>/dev/null", shell=True)
            subprocess.run("amixer set Capture 0% 2>/dev/null", shell=True)
        else:
            subprocess.run("pactl list sources short 2>/dev/null | cut -f2 | xargs -I {} pactl set-source-mute {} 0 2>/dev/null", shell=True)
            subprocess.run("amixer set Capture cap 2>/dev/null", shell=True)
            subprocess.run("amixer set Capture 100% 2>/dev/null", shell=True)

    def on_privacy_cam_toggled(self, sw, gparam):
        active = sw.get_active()
        set_gsettings_bool("org.gnome.desktop.privacy", "disable-camera", not active)
        
        if not active:
            subprocess.run("pkexec sh -c 'chmod 000 /dev/video* 2>/dev/null; modprobe -r uvcvideo 2>/dev/null'", shell=True)
        else:
            subprocess.run("pkexec sh -c 'chmod 660 /dev/video* 2>/dev/null; modprobe uvcvideo 2>/dev/null'", shell=True)

    # --- Tweak Aksiyonları Metodları ---

    def on_clear_cache_clicked(self, button):
        cmd = "pkexec sh -c 'sync && echo 3 > /proc/sys/vm/drop_caches'"
        try:
            res = subprocess.run(cmd, shell=True)
            if res.returncode == 0:
                self.show_message_dialog(_("Info"), _("Cache cleared successfully!"))
            else:
                self.show_message_dialog(_("Error"), _("Failed to clear cache. Root authorization required."))
        except Exception as e:
            self.show_message_dialog(_("Error"), f"{_('An error occurred:')} {str(e)}")

    def on_ram_opt_clicked(self, button):
        cmd = "pkexec sh -c 'sync && echo 1 > /proc/sys/vm/compact_memory'"
        try:
            res = subprocess.run(cmd, shell=True)
            if res.returncode == 0:
                self.show_message_dialog(_("Info"), _("Optimization applied successfully!"))
            else:
                self.show_message_dialog(_("Error"), _("Failed to optimize. Root authorization required."))
        except Exception as e:
            self.show_message_dialog(_("Error"), f"{_('An error occurred:')} {str(e)}")

    def on_zram_clicked(self, button):
        # MindOS zram ayarları (/etc/sysctl.d/90-mindos-memory.conf): zram hızlı olduğu için yüksek swappiness
        cmd = "pkexec sysctl -w vm.swappiness=180 vm.page-cluster=0 vm.watermark_boost_factor=0"
        self.run_tweak_cmd(cmd)

    def on_log_vacuum_clicked(self, button):
        cmd = "pkexec journalctl --vacuum-time=1d"
        self.run_tweak_cmd(cmd)

    def run_tweak_cmd(self, cmd):
        try:
            res = subprocess.run(cmd, shell=True)
            if res.returncode == 0:
                self.show_message_dialog(_("Info"), _("Optimization applied successfully!"))
            else:
                self.show_message_dialog(_("Error"), _("Failed to optimize. Root authorization required."))
        except Exception as e:
            self.show_message_dialog(_("Error"), f"{_('An error occurred:')} {str(e)}")

    def get_mouse_speed_gsettings(self):
        try:
            settings = Gio.Settings.new("org.gnome.desktop.peripherals.mouse")
            return settings.get_double("speed")
        except Exception:
            try:
                res = subprocess.check_output("gsettings get org.gnome.desktop.peripherals.mouse speed 2>/dev/null", shell=True, text=True)
                return float(res.strip())
            except Exception:
                return 0.0

    def on_mouse_speed_changed(self, scale):
        """GNOME fare ve touchpad hızı (-1 yavaş … 1 hızlı); ikisi birlikte ayarlanır"""
        val = round(scale.get_value(), 2)
        for schema in ("org.gnome.desktop.peripherals.mouse", "org.gnome.desktop.peripherals.touchpad"):
            try:
                Gio.Settings.new(schema).set_double("speed", val)
            except Exception:
                pass

    def get_dark_mode_gsettings(self):
        try:
            settings = Gio.Settings.new("org.gnome.desktop.interface")
            return settings.get_string("color-scheme") == "prefer-dark"
        except Exception:
            try:
                res = subprocess.check_output("gsettings get org.gnome.desktop.interface color-scheme 2>/dev/null", shell=True, text=True)
                return "prefer-dark" in res
            except Exception:
                return False

    def on_dark_mode_toggled(self, switch, gparam):
        active = switch.get_active()
        scheme = "prefer-dark" if active else "prefer-light"
        
        self.apply_theme_css(active)
        
        style_manager = Adw.StyleManager.get_default()
        if active:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            
        try:
            settings = Gio.Settings.new("org.gnome.desktop.interface")
            settings.set_string("color-scheme", scheme)
        except Exception:
            try:
                subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", scheme], stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def get_wifi_status(self):
        try:
            res = subprocess.check_output("nmcli radio wifi 2>/dev/null", shell=True, text=True).strip()
            return res == "enabled"
        except Exception:
            return False

    def on_wifi_toggled(self, switch, gparam):
        status = "on" if switch.get_active() else "off"
        try:
            subprocess.run(["nmcli", "radio", "wifi", status], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def get_bluetooth_status(self):
        try:
            res = subprocess.check_output("rfkill list bluetooth 2>/dev/null", shell=True, text=True)
            if "Soft blocked: yes" in res:
                return False
            return True
        except Exception:
            return False

    def on_bluetooth_toggled(self, switch, gparam):
        action = "unblock" if switch.get_active() else "block"
        try:
            subprocess.run(["rfkill", action, "bluetooth"], stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def get_cpu_governor_status(self):
        try:
            gov_files = glob.glob("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
            if gov_files:
                with open(gov_files[0], "r") as f:
                    return f.read().strip() == "performance"
        except Exception:
            pass
        return False

    def on_perf_mode_toggled(self, switch, gparam):
        active = switch.get_active()
        if active:
            gov = "performance"
        else:
            # Kapatınca sürücünün normal moduna dön: acpi-cpufreq'te schedutil, pstate sürücülerinde powersave
            try:
                with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors") as f:
                    avail = f.read().split()
            except OSError:
                avail = []
            gov = "schedutil" if "schedutil" in avail else "powersave"
        cmd = f"pkexec sh -c 'for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do [ -f $g ] && echo {gov} > $g; done'"
        try:
            res = subprocess.run(cmd, shell=True)
            if res.returncode == 0:
                self.show_message_dialog(_("Info"), _("Performance mode changed!"))
            else:
                switch.set_active(not active)
        except Exception:
            pass

    def on_apply_fan_clicked(self, button):
        pwm_path, pwm_enable_path = get_gpu_pwm_paths()
        if not pwm_path or not pwm_enable_path:
            self.show_message_dialog(_("Error"), _("No compatible AMD GPU fan controls found."))
            return
            
        enable_val = "1" if self.switch_pwm.get_active() else "0"
        pwm_val = max(77, min(255, int(self.fan_speed_scale.get_value())))
        
        cmd = f"pkexec sh -c 'echo {enable_val} > {pwm_enable_path} && echo {pwm_val} > {pwm_path}'"
        try:
            res = subprocess.run(cmd, shell=True)
            if res.returncode == 0:
                self.show_message_dialog(_("Info"), _("Fan settings applied successfully."))
            else:
                msg = _("Failed to apply settings. Root authorization required.")
                msg += "\n\n(AMD GPU fan hız kontrolü için kernel parametresi olarak 'amdgpu.ppfeaturemask=0xffffffff' girilmiş olmalıdır.)"
                self.show_message_dialog(_("Error"), msg)
        except Exception as e:
            self.show_message_dialog(_("Error"), f"{_('An error occurred:')} {str(e)}")

    def read_gpu_pwm(self):
        pwm_path, dummy_enable_path = get_gpu_pwm_paths()
        if pwm_path and os.path.exists(pwm_path):
            try:
                with open(pwm_path, "r") as f:
                    return int(f.read().strip())
            except Exception:
                pass
        return 128

    def set_language_translation(self, lang_code):
        global current_translation
        current_translation = gettext.translation('mind-arc', LOCALE_DIR, languages=[lang_code], fallback=True)
        current_translation.install()

    def show_message_dialog(self, title, msg):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=title,
            body=msg
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()

    def on_language_changed(self, combo_row, gparam):
        selected = combo_row.get_selected()
        if selected == 0:
            self.current_lang_code = 'tr'
        else:
            self.current_lang_code = 'en'
            
        self.set_language_translation(self.current_lang_code)
        self.update_ui_texts()

    def update_ui_texts(self):
        self.set_title(_("Mind-Arc Control Center"))
        self.main_page.set_title(_("Mind-Arc Control Center"))
        self.fan_page.set_title(_("Fan Settings"))
        
        if hasattr(self, 'group_about'):
            self.group_about.set_title(_("Welcome to Mind-Arc Control Center"))
            self.group_about.set_description(_("System overview details"))
        
        self.page_about.set_title(_("System Info"))
        self.row_os.set_title(_("OS Name"))
        self.row_kernel.set_title(_("Kernel Version"))
        self.row_desktop_env.set_title(_("Desktop Environment"))
        self.row_hostname.set_title(_("Hostname"))
        self.row_arch.set_title(_("System Architecture"))
        self.row_display_server.set_title(_("Display Server"))
        self.row_disk.set_title(_("Disk Storage"))
        self.row_uptime.set_title(_("Uptime"))
        
        self.page_hardware.set_title(_("Internal Hardware"))
        self.row_cpu.set_title(_("CPU Status"))
        self.row_ram.set_title(_("RAM Status"))
        self.row_gpu_status.set_title(_("GPU Status"))
        self.row_fan_btn.set_title(_("Hardware Control [EXPERIMENTAL]"))
        self.row_fan_btn.set_subtitle(_("Hardware fan and safety configurations"))
        self.btn_hardware_control.set_label(_("(TEMPORARILY DISABLED)"))
        
        # System specifications group title & card titles translation (Yeni!)
        if hasattr(self, 'group_hw_specs'):
            self.group_hw_specs.set_title(_("System Specifications"))
        if hasattr(self, 'group_hw_live'):
            self.group_hw_live.set_title(_("Live Metrics"))
            self.group_hw_live.set_description(_("Monitor CPU, RAM and GPU metrics"))
            
        if hasattr(self, 'lbl_cpu_cores_title'):
            self.lbl_cpu_cores_title.set_label(_("CPU Cores"))
        if hasattr(self, 'lbl_cpu_speed_title'):
            self.lbl_cpu_speed_title.set_label(_("CPU Clock Speed"))
        if hasattr(self, 'lbl_ram_speed_title'):
            self.lbl_ram_speed_title.set_label(_("RAM Speed"))
        if hasattr(self, 'lbl_gpu_driver_title'):
            self.lbl_gpu_driver_title.set_label(_("GPU Driver"))
        if hasattr(self, 'lbl_cpu_model_title'):
            self.lbl_cpu_model_title.set_label(_("CPU Model"))
        if hasattr(self, 'lbl_gpu_model_title'):
            self.lbl_gpu_model_title.set_label(_("GPU Model"))
        
        self.page_peripherals.set_title(_("Peripherals"))
        self.group_mice.set_title(_("Mice"))
        self.group_mice.set_description(_("Mice and Keyboard speed settings"))
        self.row_mice_list.set_title(_("Connected Devices"))
        self.row_mouse_speed.set_title(_("Mouse Speed"))
        self.group_keyboards.set_title(_("Keyboards"))
        self.row_kbd_list.set_title(_("Connected Devices"))
        self.group_headsets.set_title(_("Audio and Headsets"))
        self.row_headset_list.set_title(_("Connected Devices"))
        self.group_bluetooth.set_title(_("Bluetooth and Receivers"))
        self.row_bt_list.set_title(_("Connected Devices"))
        
        # USB Installer Metinleri
        self.page_usb_installer.set_title(_("MindOS USB Installer [EXPERIMENTAL]"))
        self.row_usb_select.set_title(_("Target USB Drive"))
        self.row_iso_select.set_title(_("Source ISO File"))
        self.row_new_username.set_title(_("New Username"))
        self.row_new_password.set_title(_("Sudo Password"))
        self.row_system_lang.set_title(_("Target System Language"))
        self.row_kbd_layout.set_title(_("Keyboard Layout"))
        self.btn_start_install.set_label(_("Start Installation"))
        
        self.page_appearance.set_title(_("Appearance and General Settings"))
        
        # Appearance groups translation (Yeni!)
        if hasattr(self, 'group_appear'):
            self.group_appear.set_title(_("General Settings"))
            self.group_appear.set_description(_("Adjust display and network settings"))
        if hasattr(self, 'group_network'):
            self.group_network.set_title(_("Network Connections"))
            
        self.row_dark_mode.set_title(_("Dark Mode"))
        self.row_lang.set_title(_("Language / Dil"))
        self.row_volume.set_title(_("System Volume"))
        self.row_brightness.set_title(_("Screen Brightness"))
        self.row_screen_timeout.set_title(_("Screen Timeout"))
        self.row_notifications.set_title(_("System Notifications"))
        self.row_wifi.set_title(_("Wi-Fi"))
        self.row_bluetooth.set_title(_("Bluetooth"))
        self.row_dnd.set_title(_("Do Not Disturb"))
        self.row_privacy_mic.set_title(_("Microphone Access"))
        self.row_privacy_cam.set_title(_("Camera Access"))
        
        # Modeli yenilemek seçimi sıfırlar; seçim korunur ve ekran zaman aşımı ayarı yeniden yazılmaz
        # (eskiden Mind Arc her açılışta ekran kapanma süresini 1 dakikaya indiriyordu)
        if hasattr(self, 'row_screen_timeout'):
            sel = self.row_screen_timeout.get_selected()
            self.row_screen_timeout.handler_block_by_func(self.on_screen_timeout_changed)
            self.timeout_model = Gtk.StringList.new([_("1 Minute"), _("5 Minutes"), _("15 Minutes"), _("Never")])
            self.row_screen_timeout.set_model(self.timeout_model)
            self.row_screen_timeout.set_selected(sel)
            self.row_screen_timeout.handler_unblock_by_func(self.on_screen_timeout_changed)
            
        if hasattr(self, 'row_system_lang'):
            sel = self.row_system_lang.get_selected()
            self.system_lang_model = Gtk.StringList.new(["Türkçe (tr_TR)", "English (en_US)"])
            self.row_system_lang.set_model(self.system_lang_model)
            self.row_system_lang.set_selected(sel)
            
        if hasattr(self, 'row_kbd_layout'):
            sel = self.row_kbd_layout.get_selected()
            self.kbd_layout_model = Gtk.StringList.new(["Türkçe Q (tr)", "English US (us)"])
            self.row_kbd_layout.set_model(self.kbd_layout_model)
            self.row_kbd_layout.set_selected(sel)
            
        self.page_performance.set_title(_("Performance and Tweak"))
        
        # Performance group translation (Yeni!)
        if hasattr(self, 'group_perf'):
            self.group_perf.set_title(_("Performance and Tweak"))
            self.group_perf.set_description(_("Optimize system performance"))
            
        # Tweak rows translation dynamically (Yeni!)
        if hasattr(self, 'tweak_rows'):
            for tweak in self.tweak_rows:
                title = _(tweak["title_key"])
                subtitle = _(tweak["subtitle_key"])
                impact = _(tweak["impact_key"])
                impact_text = f"{_('Performans Etkisi:')} {_(impact)}"
                
                tweak["row"].set_title(title)
                tweak["row"].set_subtitle(subtitle)
                tweak["row"].set_tooltip_text(impact_text)
                tweak["control"].set_tooltip_text(impact_text)
                
                if tweak["type"] == "button":
                    tweak["control"].set_label(_(tweak["button_key"]))
        
        self.row_warning_info.set_title(_("Warning"))
        self.row_warning_info.set_subtitle(_("Hardware settings require root privileges."))
        self.row_pwm_enable.set_title(_("Fan Speed (PWM)") + " Manual Control")
        self.row_fan_speed.set_title(_("Fan Speed (PWM)"))
        self.row_apply_fan.set_title(_("Apply"))
        
        if hasattr(self, 'row_fan_device'):
            self.row_fan_device.set_title(_("Controlled Device"))
        if hasattr(self, 'group_fan'):
            self.group_fan.set_title(_("GPU Fan Control"))
            
        translated_texts = {
            "about": _("System Info"),
            "hardware": _("Internal Hardware"),
            "peripherals": _("Peripherals"),
            "usb_installer": _("MindOS USB Installer [EXPERIMENTAL]"),
            "appearance": _("General Settings"),
            "performance": _("Performance and Tweak")
        }
        for name, icon, text in mindarc_extra.extra_sidebar_items(self):
            translated_texts[name] = text
        mindarc_extra.update_extra_texts(self)
        for btn, label, text, name in self.sidebar_items:
            new_text = translated_texts.get(name, text)
            label.set_label(new_text)
            if not self.sidebar_expanded:
                btn.set_tooltip_text(new_text)

    def close(self):
        self.stats_active = False
        super().close()


class MindArcApplication(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(
            application_id="org.mindos.mind_arc",
            # HANDLES_OPEN: .deb / .mind dosyasına çift tıklanınca (Mind Arc açıksa da) aynı pencereye gelir
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            **kwargs
        )
        
    def do_startup(self):
        Adw.Application.do_startup(self)

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = MindArcWindow(application=self)
        if getattr(self, "start_page", None) and win.view_stack.get_child_by_name(self.start_page):
            win.view_stack.set_visible_child_name(self.start_page)
        if getattr(self, "search_query", None) and hasattr(win, "extra_packages"):
            win.extra_packages.entry.set_text(self.search_query)
            win.extra_packages.entry.grab_focus()
        win.present()

    def do_open(self, files, n_files, hint):
        """Dosya yöneticisinde .deb / .mind dosyasına çift tıklandı"""
        self.start_page = "packages"
        self.do_activate()
        win = self.get_active_window()
        paths = [f.get_path() for f in files if f.get_path()]
        if paths and hasattr(win, "extra_packages"):
            win.extra_packages.install_local(paths[0])


def main():
    # mind-arc --page <about|hardware|peripherals|usb_installer|appearance|performance|packages|maintenance>
    # mind-arc --search <kelime>   Paket Merkezi'ni bu aramayla açar
    argv = list(sys.argv)
    start_page = None
    search_query = None
    if "--search" in argv:
        i = argv.index("--search")
        search_query = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
        start_page = "packages"
    if "--page" in argv:
        i = argv.index("--page")
        start_page = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    app = MindArcApplication()
    app.start_page = start_page
    app.search_query = search_query
    return app.run(argv)

if __name__ == "__main__":
    sys.exit(main())
