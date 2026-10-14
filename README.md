# MindOS Paradise

MindOS Paradise, Debian 13 (trixie) ve GNOME 48 üzerine kurulu, Türkçe öncelikli bir masaüstü
dağıtımıdır. Kendi paket yöneticisi **mindpkg**, kontrol merkezi **Mind Arc**, asistanı
**Mind Helper**, özel derlenmiş ve Secure Boot için imzalanmış Linux 7.2 kernel'i ile gelir.
Sürekli güncellenen (rolling) bir dağıtımdır: yeni sürümler `mindpkg upgrade` ya da Mind Arc →
**Sistem Güncellemesi** ile gelir.

> **English:** MindOS Paradise is a Turkish-first desktop distribution based on Debian 13 and
> GNOME 48, with its own package manager (mindpkg), control center (Mind Arc), assistant
> (Mind Helper) and a custom, Secure Boot–signed Linux 7.2 kernel. It is a rolling release;
> updates arrive through `mindpkg upgrade` or Mind Arc → System Update. All MindOS code in this
> repository is licensed under GPL-3.0-or-later.

- İndir: [Releases](https://github.com/MindOS-Official/paradise/releases)
- Paket deposu: [MindOS-Official/packages](https://github.com/MindOS-Official/packages)
- Web sitesi: <https://mindos-official.github.io/mindos_/>

## Neler var

| Bileşen | Klasör | Açıklama |
|---|---|---|
| mindpkg | `src/mindpkg/` | Paket yöneticisi: `.mind` paketleri, üretici depoları (Chrome, Steam…), imzalı kendini güncelleme, sistem bileşenleri, yeniden başlatarak güncelleme (`upgrade --offline`) |
| Mind Arc | `src/mind-arc/` | Kontrol merkezi: sistem bilgisi, donanım, Sistem Güncellemesi, Paket Merkezi, bakım, USB'ye tam kurulum (`usb-writer`) |
| Mind Helper | `src/mindhelper/` | Asistan ve ipuçları, oturum açılış bildirimleri |
| MindOS Tweaks | `src/shell-extension/` | Panel menülerini panele bitişik açan küçük GNOME Shell eklentisi |
| Sistem dosyaları | `overlay/` | Debian'a eklenen/değiştirilen dosyalar (liste: `overlay.list`): Calamares kurulum ayarları, Plymouth açılış teması, GNOME varsayılanları, güvenlik ve bellek ayarları, Firefox politikaları, systemd servisleri |
| ISO önyükleme | `iso/` | GRUB (UEFI) ve isolinux (BIOS) menüleri |
| Kernel | `kernel/` | Linux 7.2.10 ayarı ve derleme betiği (yama yok, kaynak: kernel.org) |
| Secure Boot | `secureboot/` | İmzalama betikleri ve **herkese açık** sertifikalar (özel anahtarlar burada değildir) |
| Markalama | `branding/` | Logo kaynakları; duvar kağıdı, avatar, açılış ve GRUB görsellerini üreten betikler |
| Derleme | `scripts/build/` | İmaj ve ISO derleme betikleri |
| Testler | `tests/vm/` | QEMU ile kurulum ve güncelleme testleri |
| Paket listesi | `packages/filesystem.manifest` | ISO'daki tüm Debian paketleri ve sürümleri |

Derleme adımları için [BUILDING.md](BUILDING.md), üçüncü taraf bileşenler için
[THIRD_PARTY.md](THIRD_PARTY.md), imzalama ve güvenlik için [SECURITY.md](SECURITY.md).

## Lisans

Bu repodaki MindOS kodu **GNU GPL 3.0 veya sonrası** ile lisanslanmıştır ([LICENSE](LICENSE)).
Üçüncü taraf bileşenler kendi lisanslarıyla gelir ([THIRD_PARTY.md](THIRD_PARTY.md)).
