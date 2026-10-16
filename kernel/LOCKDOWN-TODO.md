# Secure Boot kernel kilitlemesi (lockdown=integrity) — yapılacak

Debian/Ubuntu kernel'leri Secure Boot açıkken kendiliğinden `lockdown=integrity` ile açılır; MindOS
kernel'i açılmaz (`CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE`, Debian'ın EFI kilitleme yaması yok).

Denenen yol (1.0.2'den çıkarıldı): GRUB `${shim_lock}`/`${lockdown}` değişkenine göre kernel satırına
`lockdown=integrity` ekleyen /etc/grub.d/01_mindos-lockdown. Sanal makinede kilitleme açılınca sistem
initramfs'te kaldı: modüller MindOS anahtarıyla imzalı ama bu anahtar kernel'in güvendiği anahtarlıkta
değil; kilitleme "unsigned module loading is restricted" diyerek disk ve dosya sistemi sürücülerini
reddetti.

Doğru çözüm, bir sonraki kernel derlemesinde:
1. MindOS sertifikasını kernel'e gömmek: `CONFIG_SYSTEM_TRUSTED_KEYS="secureboot/MOK.pem"`
   (yalnızca sertifika; özel anahtar asla kaynak ağacına girmez).
2. Modülleri aynı anahtarla imzalamak (sign-kernel-deb.sh zaten yapıyor).
3. Kilitlemeyi Secure Boot açıkken etkinleştirmek (yukarıdaki GRUB betiği ya da Debian'ın
   "efi: Lock down the kernel if booted in secure boot mode" yaması).
4. Secure Boot açık sanal makinede (vmtest/sb.sh, MOK kaydı ile) ve kapalıyken açılışı sınamak;
   DKMS modülleri (NVIDIA, Broadcom) MOK ile imzalı olduğu için onların da yüklendiğini doğrulamak.
