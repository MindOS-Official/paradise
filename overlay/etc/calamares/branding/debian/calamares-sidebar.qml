/* MindOS Paradise - Calamares kenar çubuğu
 * Üstte MindOS banner'ı (lotus + "MindOS"), altında kurulum adımları.
 * Renkler branding.desc içindeki style: bölümünden gelir. */
import io.calamares.ui 1.0
import io.calamares.core 1.0

import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: sideBar
    color: Branding.styleString(Branding.SidebarBackground)
    anchors.fill: parent

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        Image {
            id: banner
            source: "mindos-banner.png"
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.topMargin: 22
            Layout.bottomMargin: 18
            Layout.preferredWidth: Math.min(sideBar.width - 28, 180)
            Layout.preferredHeight: Layout.preferredWidth * sourceSize.height / Math.max(sourceSize.width, 1)
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
        }

        Repeater {
            model: ViewManager
            Rectangle {
                Layout.leftMargin: 10
                Layout.rightMargin: 10
                Layout.fillWidth: true
                height: 34
                radius: 8
                color: index == ViewManager.currentStepIndex
                       ? Branding.styleString(Branding.SidebarBackgroundCurrent) : "transparent"

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 14
                    color: Branding.styleString(index == ViewManager.currentStepIndex
                                                ? Branding.SidebarTextCurrent : Branding.SidebarText)
                    font.pointSize: 11
                    font.bold: index == ViewManager.currentStepIndex
                    text: display
                }
            }
        }

        Item {
            Layout.fillHeight: true
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 12
            color: Branding.styleString(Branding.SidebarText)
            opacity: 0.6
            font.pointSize: 8
            text: "MindOS Paradise"
        }
    }
}
