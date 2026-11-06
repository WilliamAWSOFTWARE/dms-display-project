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
        text: "Selector rápido de visualización multimonitor centrado al estilo Windows para Hyprland en DankMaterialShell."
        font.pixelSize: Theme.fontSizeSmall
        color: Theme.surfaceVariantText
        wrapMode: Text.WordWrap
    }

    StyledText {
        width: parent.width
        text: "• Atajo predeterminado: SUPER + P\n• Navegación: Flechas o pulsar SUPER + P para ciclar\n• Aplicar: Pulsa Enter, Espacio o haz clic en cualquier tarjeta\n• Cancelar: Pulsa Escape o haz clic fuera del panel"
        font.pixelSize: Theme.fontSizeSmall
        color: Theme.surfaceText
        wrapMode: Text.WordWrap
    }
}
