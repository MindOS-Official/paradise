#!/usr/bin/env bash
# chroot içinde çalışır: kaldırılacak paketleri listeler (sadece kurulu olanlar)
export LANG=C
inst() { dpkg-query -Wf '${db:Status-Abbrev} ${Package}\n' "$@" 2>/dev/null | awk '$1=="ii"{print $2}'; }
{
  # Dil görevleri (TR + EN hariç) ve kurulu olmayan masaüstlerinin task'ları
  inst 'task-*' | grep -vxE 'task-(turkish|turkish-desktop|english|gnome-desktop|desktop|laptop)'
  inst 'live-task-localisation*'
  # Uygulama çevirileri (TR hariç) ve yardım dosyaları
  inst 'firefox-esr-l10n-*' 'thunderbird-l10n-*' 'libreoffice-l10n-*' | grep -vE -- '-tr$'
  inst 'libreoffice-help-*' 'gimp-help-*' gnome-user-docs 'live-*-doc'
  # Sözlükler (EN/TR hariç)
  inst 'hunspell-*' 'hyphen-*' 'mythes-*' 'aspell-*' 'myspell-*' 'w*' 'i[a-z]*' | grep -E '^(hunspell|hyphen|mythes|aspell|myspell)-|^w[a-z]+$|^i(american|british|polish|spanish|french|german|italian|swiss|catalan|danish|dutch|norwegian|portuguese|swedish|ukrainian|russian|czech|bulgarian|hungarian|lithuanian|ngerman|ogerman|wolof)' \
     | grep -vE '^(hunspell|hyphen|mythes|aspell)-(en|en-us|tr)$|^(hunspell-tools|aspell)$|^(wget|whiptail|wireplumber|wamerican|wtmpdb|which|wpasupplicant|wireless-tools|wireless-regdb|wbritish)$|^i(american)$'
  # Giriş yöntemleri (CJK) ve ağır yerel veri
  inst 'ibus*' 'fcitx*' 'mozc*' 'anthy*' 'libpinyin*' 'libchewing*' 'libhangul*' 'libm17n*' 'm17n-*' 'gir1.2-ibus*' 'pocketsphinx*' locales-all
  # Ekstra fontlar (temel Noto + CJK regular + emoji kalıyor)
  inst fonts-noto-extra fonts-noto-cjk-extra fonts-noto-ui-extra fonts-unifont
  # Sunucu / egzotik donanım firmware'leri
  inst firmware-netronome firmware-marvell-prestera firmware-cavium firmware-qlogic firmware-myricom firmware-bnx2x firmware-bnx2 firmware-netxen firmware-ivtv firmware-siano
  # RAM yiyen arka plan servisleri / gereksiz uygulamalar
  inst snapd gnome-software 'gnome-software-plugin-*' packagekit packagekit-tools 'gnome-packagekit*' \
       evolution evolution-ews 'evolution-plugin*' orca brltty speech-dispatcher 'speech-dispatcher-*' xbrlapi \
       gnome-games gnome-2048 aisleriot gnome-chess five-or-more hitori iagno lightsoff quadrapassel swell-foop tali \
       gnome-mahjongg gnome-mines gnome-sudoku gnome-klotski gnome-nibbles gnome-robots gnome-taquin gnome-tetravex four-in-a-row \
       malcontent malcontent-gui geoclue-2-demo
  # Derleyici araç zinciri ve eski kernel
  inst build-essential dkms 'gcc-14' 'g++-14' 'linux-headers-*' 'linux-kbuild-*' linux-image-amd64 'linux-image-6.12*'
} | sort -u
