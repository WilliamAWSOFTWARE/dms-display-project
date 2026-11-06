import QtQuick
import qs.Common
import qs.DCommon.Widgets
import qs.Modules.Plugins

PluginSettings {
    id: root
    pluginId: "displayProject"

    StyledText {
        width: parent.width
        text: "Display Project (Win + P)"
        font.pixelSize: Theme.fontSizeLarge
        font.weight: Font.Bold
        color: Theme.surfaceText
    }

    StyledText {
        width: parent.width
        text: "Windows-style centered quick multi-monitor projection switcher for Hyprland on DankMaterialShell."
        font.pixelSize: Theme.fontSizeSmall
        color: Theme.surfaceVariantText
        wrapMode: Text.WordWrap
    }

    StyledText {
        width: parent.width
        text: "• Default shortcut: SUPER + P\n• Navigation: Arrow keys or press SUPER + P to cycle\n• Apply: Press Enter, Space or click any card\n• Cancel: Press Escape or click outside the panel"
        font.pixelSize: Theme.fontSizeSmall
        color: Theme.surfaceText
        wrapMode: Text.WordWrap
    }
}
