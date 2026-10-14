# Güvenlik

## İmzalama anahtarları

MindOS iki anahtar kullanır. Özel kısımları yalnızca MindOS geliştiricisinde durur ve bu repoda
**hiçbir zaman** yer almaz (`.gitignore` ve `scripts/export-from-build.sh` içindeki tarama bunu
engeller).

| Anahtar | Ne imzalar | Herkese açık kısım |
|---|---|---|
| MindOS Secure Boot anahtarı (MOK) | Kernel ve kernel modülleri | `secureboot/MOK.crt`, `secureboot/MindOS-SecureBoot.der` (ISO'da ve kurulu sistemde `/usr/share/mindos/secureboot/`) |
| mindpkg sürüm anahtarı (Ed25519) | mindpkg güncellemeleri ve sistem bileşenleri (`.deb`) | `secureboot/mindpkg-release.pub`, ayrıca `src/mindpkg/mindpkg` içinde `RELEASE_PUBKEY` |

MOK sertifikasının SHA-256 parmak izi:
`41:A2:FC:9F:1F:87:E0:DC:BC:6F:6F:96:B8:1C:62:49:1B:51:81:30:BE:55:0B:E6:44:A4:35:8C:26:D4:8C:96`

mindpkg, imzası bu anahtarla doğrulanmayan bir mindpkg sürümünü ya da sistem bileşenini kurmaz;
paket deposu ele geçirilse bile sahte güncelleme dağıtılamaz.

## Kendi derlemeniz (fork)

Kendi MindOS türevinizi dağıtacaksanız kendi MOK anahtarınızı ve kendi Ed25519 anahtarınızı üretin,
`RELEASE_PUBKEY`'i değiştirin. Resmi MindOS anahtarıyla imzalanmamış derlemeler resmi güncelleme
kanalını kullanamaz.

## Güvenlik açığı bildirmek

Lütfen açığı herkese açık bir issue yerine GitHub'ın **Security → Report a vulnerability**
(özel bildirim) bölümünden bildirin.
