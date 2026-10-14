# System-wide .bashrc file for interactive bash(1) shells.

# To enable the settings / commands in this file for login shells as well,
# this file has to be sourced in /etc/profile.

# If not running interactively, don't do anything
[ -z "${PS1-}" ] && return

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(< /etc/debian_chroot)
fi

# set a fancy prompt (non-color, overwrite the one in /etc/profile)
# but only if not SUDOing and have SUDO_PS1 set; then assume smart user.
if ! [ -n "${SUDO_USER-}" -a -n "${SUDO_PS1-}" ]; then
  PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi

# Commented out, don't overwrite xterm -T "title" -n "icontitle" by default.
# If this is an xterm set the title to user@host:dir
#case "$TERM" in
#xterm*|rxvt*)
#    PROMPT_COMMAND='echo -ne "\033]0;${USER}@${HOSTNAME}: ${PWD}\007"'
#    ;;
#*)
#    ;;
#esac

# enable bash completion in interactive shells
#if ! shopt -oq posix; then
#  if [ -f /usr/share/bash-completion/bash_completion ]; then
#    . /usr/share/bash-completion/bash_completion
#  elif [ -f /etc/bash_completion ]; then
#    . /etc/bash_completion
#  fi
#fi

# if the command-not-found package is installed, use it
if [ -x /usr/lib/command-not-found -o -x /usr/share/command-not-found/command-not-found ]; then
	function command_not_found_handle {
	        # check because c-n-f could've been removed in the meantime
                if [ -x /usr/lib/command-not-found ]; then
		   /usr/lib/command-not-found -- "$1"
                   return $?
                elif [ -x /usr/share/command-not-found/command-not-found ]; then
		   /usr/share/command-not-found/command-not-found -- "$1"
                   return $?
		else
		   printf "%s: command not found\n" "$1" >&2
		   return 127
		fi
	}
fi

# --- MindOS Paradise Özel Kurulum Kısayolları ---

# Google Chrome Kurulumu (Önce indirir, sonra kurar ve kalıntıyı siler)
alias kur-chrome='echo "Google Chrome indiriliyor..." && wget -qO /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && sudo dpkg -i /tmp/chrome.deb && sudo apt-get install -f -y && rm /tmp/chrome.deb && echo "Google Chrome başarıyla kuruldu!"'

# Spotify Kurulumu (Curl ile anahtar çeker, repoyu ekler ve kurar)
alias kur-spotify='echo "Spotify kuruluyor..." && curl -sS https://download.spotify.com/debian/pubkey_7A3A762FAFD4A51F.gpg | sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/spotify.gpg && echo "deb http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list && sudo apt-get update && sudo apt-get install spotify-client -y && echo "Spotify başarıyla kuruldu!"'

# Steam Kurulumu (32-bit mimariyi açar ve kurar)
alias kur-steam='echo "Steam kuruluyor..." && sudo dpkg --add-architecture i386 && sudo apt-get update && sudo apt-get install steam -y && echo "Steam başarıyla kuruldu!"'

# VS Code Kurulumu
alias kur-vscode='echo "Visual Studio Code kuruluyor..." && wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg && sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg && sudo sh -c "echo \"deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main\" > /etc/apt/sources.list.d/vscode.list" && rm -f packages.microsoft.gpg && sudo apt install apt-transport-https -y && sudo apt update && sudo apt install code -y && echo "VS Code başarıyla kuruldu!"'

# Discord Kurulumu
alias kur-discord='echo "Discord indiriliyor..." && wget -qO /tmp/discord.deb "https://discordapp.com/api/download?platform=linux&format=deb" && sudo dpkg -i /tmp/discord.deb && sudo apt-get install -f -y && rm /tmp/discord.deb && echo "Discord başarıyla kuruldu!"'

# Sistemi Tamamen Güncelleme ve Temizleme
alias sistem-temizle='echo "Sistem temizleniyor..." && sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y --purge && sudo apt clean && echo "Sistem pırıl pırıl!"'

# Hızlı Yardım Menüsü
alias mindos-yardim='echo -e "\nMindOS Paradise Özel Komutları:\n kur-chrome\n kur-spotify\n kur-steam\n kur-vscode\n kur-discord\n sistem-temizle\n"'

# Sadece paket listelerini denetler (sudo apt update)
alias guncelle='sudo apt update'

# Her şeyi yükseltir: mindpkg'nin kendisi, .mind paketleri ve sistem paketleri
alias tam-guncelle='sudo mindpkg upgrade'

# Terminal açılınca sistem bilgisini bir kez göster (iç içe kabuklarda ve sudo -i'de değil).
# Dar pencerede logo bilgilerin içine taşmasın diye yalnızca bilgiler gösterilir.
if [ -t 1 ] && [ -z "$MINDOS_FASTFETCH_SHOWN" ] && [ "$TERM" != "dumb" ] && [ "$EUID" -ne 0 ]; then
    export MINDOS_FASTFETCH_SHOWN=1
    if [ "${COLUMNS:-$(tput cols 2>/dev/null || echo 80)}" -ge 100 ]; then
        fastfetch
    else
        fastfetch --logo none
    fi
fi
