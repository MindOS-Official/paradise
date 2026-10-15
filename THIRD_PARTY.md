# Üçüncü taraf bileşenler

MindOS Paradise ISO'su aşağıdaki bileşenleri, kendi lisanslarıyla birlikte dağıtır.

| Bileşen | Lisans | Kaynak |
|---|---|---|
| Debian 13 paketleri (`packages/filesystem.manifest`) | Paket başına; her paketin lisansı imajda `/usr/share/doc/<paket>/copyright` | <https://sources.debian.org>, belirli sürümler: <https://snapshot.debian.org> |
| Linux 7.2.10 (`linux-image-7.2.10-mindos`) | GPL-2.0 | <https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.2.10.tar.xz>, yamasız; ayar ve derleme betiği `kernel/` |
| Blur my Shell v73, aunetx (`third_party/blur-my-shell@aunetx`) | GPL-3.0 | <https://github.com/aunetx/blur-my-shell> |
| Plymouth "spinner" teması görselleri (`overlay/usr/share/plymouth/themes/mindos`) | GPL-2.0-or-later | Debian `plymouth-themes` paketi |
| Calamares kurulum programı | GPL-3.0 | Debian `calamares` paketi; değiştirilmemiştir, yalnızca `overlay/etc/calamares` ile ayarlanır |
| ArcMenu, Dash to Dock, Desktop Icons NG | GPL-2.0 / GPL-3.0 | Debian paketleri |
| shim, GRUB (Secure Boot zinciri) | GPL-3.0 (GRUB), BSD-2 (shim) | Debian'ın imzalı `shim-signed` ve `grub-efi-amd64-signed` paketleri |
| Cantarell yazı tipi (markalama betikleri) | SIL OFL 1.1 | Debian `fonts-cantarell` paketi |
| Broadcom STA "wl" Wi-Fi sürücüsü (`broadcom-sta-dkms`, isteğe bağlı) | Broadcom sınırlı lisansı (kapalı kaynak parça) | Debian `broadcom-sta` paketi; Linux 7.x yaması `patches/broadcom-sta-6.30.223.271-kernel7.patch` |
