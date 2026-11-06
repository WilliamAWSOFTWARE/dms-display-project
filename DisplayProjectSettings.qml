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
        text: "Selector rápido de visualización multimonitor al estilo Windows para Hyprland en DankMaterialShell."
        font.pixelSize: Theme.fontSizeSmall
        color: Theme.surfaceVariantText
        wrapMode: Text.WordWrap
    }

    SliderSetting {
        settingKey: "autoApplyTimeout"
        label: "Tiempo de auto-aplicación al ciclar"
        description: "Milisegundos de espera tras pulsar SUPER + P antes de aplicar automáticamente el modo seleccionado. Pon 0 para exigir pulsar Enter."
        defaultValue: 2200
        minimum: 0
        maximum: 5000
        unit: "ms"
        leftIcon: "timer"
    }
}
