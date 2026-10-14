# MindOS Paradise'ı derlemek

MindOS Paradise şu an bir **remaster** olarak derlenir: Debian 13 GNOME canlı imajının kök dosya
sistemi açılır, MindOS paketleri ve dosyaları eklenir, imaj yeniden ISO'ya paketlenir. Sıfırdan,
tamamen otomatik bir derleme (debootstrap/live-build) planlanıyor.

## Gerekenler

Debian ya da Ubuntu tabanlı bir bilgisayar, `sudo`, yaklaşık 40 GB boş alan ve şu paketler:
`squashfs-tools xorriso rsync python3-pil sbsigntool openssl qemu-system-x86 ovmf`.

## Adımlar

1. **Taban imaj.** Debian 13 GNOME canlı ISO'sunu açıp `filesystem.squashfs`'i bir klasöre
   (ör. `paradise-build/rootfs`) çıkarın. ISO'daki tüm paketler ve sürümleri
   `packages/filesystem.manifest` dosyasındadır; eksikleri chroot içinde `apt-get install` ile kurun.
2. **MindOS dosyaları.** `sudo scripts/apply-overlay.sh paradise-build/rootfs`
3. **Kernel.** `kernel.org`'dan `linux-7.2.10.tar.xz`'i `kernel/` klasörüne indirin
   (`kernel/sha256sums.asc` ile doğrulayın) ve `kernel/build-btf.sh` ile derleyin.
   ISO'daki kernel'in birebir ayarı `kernel/config-7.2.10-mindos.shipped` dosyasındadır.
4. **Secure Boot imzası.** `secureboot/sign-kernel-deb.sh` kernel paketini kendi MOK anahtarınızla
   imzalar. Resmi anahtar repoda yoktur; kendi derlemeniz için kendi anahtarınızı üretin
   (bkz. SECURITY.md).
5. **mindos-apps paketi.** `scripts/build/build-mindos-apps.sh <rootfs> <sürüm> <çıktı>` Mind Arc,
   Mind Helper ve MindOS varsayılanlarını tek `.deb`'de toplar; chroot içinde kurun.
6. **ISO.** Sırasıyla `scripts/build/chroot-mount.sh up`, chroot içinde
   `scripts/build/final-clean.sh`, `chroot-mount.sh down` ve
   `scripts/build/build-iso.sh <derleme_klasörü> <çıktı.iso>`.
   ISO önyükleme menüleri `iso/` klasöründedir.
7. **Test.** `tests/vm/` içindeki betikler ISO'yu QEMU'da açar (`live.sh`), Calamares ile
   otomatik kurar (`run_install.sh`) ve Secure Boot'u dener (`sb.sh`).

## Repoyu derleme klasöründen güncellemek

`scripts/export-from-build.sh <paradise-build>` programları, `overlay.list`'teki sistem
dosyalarını, ISO ayarlarını ve betikleri bu repoya kopyalar. Sonunda özel anahtar taraması yapar;
bir anahtar bulursa hata verir ve repo kullanılmamalıdır.
