/* MindOS Paradise - kurulum slayt gösterisi
 * Metinler kurulum dilinde gösterilir (Türkçe veya İngilizce). */
import QtQuick 2.15
import calamares.slideshow 1.0

Presentation {
    id: presentation

    function tr(turkish, english) {
        return Qt.locale().name.substring(0, 2) === "tr" ? turkish : english
    }

    Timer {
        interval: 9000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    component MindSlide: Slide {
        property string image
        property string heading
        property string body

        Image {
            id: shot
            source: image
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 10
            width: Math.min(parent.width * 0.92, 640)
            height: width * 400 / 720
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
        }
        Text {
            id: titleText
            anchors.top: shot.bottom
            anchors.topMargin: 6
            anchors.horizontalCenter: parent.horizontalCenter
            width: shot.width
            horizontalAlignment: Text.AlignHCenter
            text: heading
            color: "#073642"
            font.pointSize: 16
            font.bold: true
            wrapMode: Text.WordWrap
        }
        Text {
            anchors.top: titleText.bottom
            anchors.topMargin: 6
            anchors.horizontalCenter: parent.horizontalCenter
            width: shot.width
            horizontalAlignment: Text.AlignHCenter
            text: body
            color: "#586e75"
            font.pointSize: 11
            wrapMode: Text.WordWrap
        }
    }

    MindSlide {
        image: "slide-welcome.png"
        heading: presentation.tr("MindOS Paradise'a Hoş Geldin", "Welcome to MindOS Paradise")
        body: presentation.tr("Kurulum birkaç dakika içinde kendiliğinden tamamlanacak. Bu sırada MindOS'u biraz tanıyalım.",
                              "Installation will finish on its own in a few minutes. Meanwhile, let's get to know MindOS.")
    }
    MindSlide {
        image: "slide-mindpkg.png"
        heading: presentation.tr("mindpkg ile tek komut", "One command with mindpkg")
        body: presentation.tr("Chrome, VS Code, VLC... İstediğin uygulamayı <b>sudo mindpkg install &lt;ad&gt;</b> ile kur. mindpkg en doğru depoyu kendisi seçer: üretici deposu, Debian ya da MindOS.",
                              "Chrome, VS Code, VLC... Install any app with <b>sudo mindpkg install &lt;name&gt;</b>. mindpkg picks the right source by itself: vendor, Debian or MindOS.")
    }
    MindSlide {
        image: "slide-packages.png"
        heading: presentation.tr("Paket Merkezi", "Package Center")
        body: presentation.tr("Terminal kullanmadan ara, popüler uygulamaları tek tıkla kur ve kaldır: Mind-Arc Kontrol Merkezi → Paket Merkezi.",
                              "Search and install popular apps with one click, no terminal needed: Mind-Arc Control Center → Package Center.")
    }
    MindSlide {
        image: "slide-arcmenu.png"
        heading: presentation.tr("MindOS Menüsü", "MindOS Menu")
        body: presentation.tr("Super tuşuna bas ya da sol üstteki lotusa tıkla. Uygulamaların, dosyaların ve ayarların tek bir menüde.",
                              "Press the Super key or click the lotus in the top-left corner. Your apps, files and settings in one menu.")
    }
    MindSlide {
        image: "slide-maintenance.png"
        heading: presentation.tr("Sistem Bakımı", "System Maintenance")
        body: presentation.tr("RAM ve zram durumunu izle, sistemi güncelle, gereksiz paketleri ve önbellekleri tek tıkla temizle.",
                              "Watch RAM and zram usage, update the system and clean unused packages and caches with one click.")
    }
    MindSlide {
        image: "slide-helper.png"
        heading: presentation.tr("Mind Helper", "Mind Helper")
        body: presentation.tr("Linux hakkında merak ettiğin her şeyi sor. mindpkg rehberi ve eğitimler seni bekliyor.",
                              "Ask anything about Linux. The mindpkg guide and tutorials are waiting for you.")
    }
    MindSlide {
        image: "slide-speed.png"
        heading: presentation.tr("Hafif ve hızlı", "Light and fast")
        body: presentation.tr("MindOS'a özel derlenmiş Linux 7.2 çekirdeği, sıkıştırılmış zram belleği ve sadeleştirilmiş sistem: daha az RAM, daha hızlı açılış.",
                              "A Linux 7.2 kernel built for MindOS, compressed zram memory and a slimmed-down system: less RAM, faster boot.")
    }
}
