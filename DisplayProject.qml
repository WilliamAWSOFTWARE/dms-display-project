import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.Common
import qs.Services
import qs.DCommon.Widgets
import qs.Modules.Plugins

PluginComponent {
    id: root

    readonly property string scriptPath: {
        const urlStr = Qt.resolvedUrl("./display_engine.py").toString();
        return urlStr.replace(/^file:\/\//, "");
    }

    property var displayState: null
    property string activeMode: displayState && displayState.currentMode ? displayState.currentMode : "extend"
    property int selectedIndex: 2
    property bool isApplying: false

    readonly property var modes: [
        {
            id: "primary_only",
            title: "PC screen only",
            desc: displayState && displayState.primary ? `${displayState.primary.name} · ${displayState.primary.native_width}x${displayState.primary.native_height} @${Math.round(displayState.primary.native_refresh)}Hz` : "Primary display only",
            icon: "laptop"
        },
        {
            id: "duplicate",
            title: "Duplicate",
            desc: "Duplicate desktop on all displays",
            icon: "burst_mode"
        },
        {
            id: "extend",
            title: "Extend",
            desc: displayState && displayState.secondary ? `Extended desktop (${displayState.secondary.native_width}x${displayState.secondary.native_height} @${Math.round(displayState.secondary.native_refresh)}Hz)` : "Extend desktop across all displays",
            icon: "view_column"
        },
        {
            id: "secondary_only",
            title: "Second screen only",
            desc: displayState && displayState.secondary ? `${displayState.secondary.name} · ${displayState.secondary.native_width}x${displayState.secondary.native_height} @${Math.round(displayState.secondary.native_refresh)}Hz` : "Secondary display only",
            icon: "tv"
        }
    ]

    function refreshState() {
        queryBuffer = "";
        queryProcess.running = true;
    }

    function openFlyout() {
        refreshState();
        const focused = CompositorService.getFocusedScreen() ?? (Quickshell.screens[0] ?? null);
        if (focused) overlay.screen = focused;

        // Set selected index to current active mode
        for (let i = 0; i < modes.length; i++) {
            if (modes[i].id === activeMode) {
                selectedIndex = i;
                break;
            }
        }

        overlay.visible = true;
        Qt.callLater(() => overlayFocusScope.forceActiveFocus());
    }

    function closeFlyout() {
        overlay.visible = false;
    }

    function toggleFlyout() {
        if (overlay.visible) closeFlyout();
        else openFlyout();
    }

    function cycleNext() {
        if (!overlay.visible) {
            openFlyout();
            // Start on next mode relative to current
            selectedIndex = (selectedIndex + 1) % modes.length;
        } else {
            selectedIndex = (selectedIndex + 1) % modes.length;
        }
    }

    function applySelected() {
        if (selectedIndex >= 0 && selectedIndex < modes.length) {
            applyMode(modes[selectedIndex].id);
        }
    }

    function applyMode(modeId) {
        if (isApplying) return;
        isApplying = true;
        applyBuffer = "";
        applyProcess.command = ["python3", root.scriptPath, "set", modeId];
        applyProcess.running = true;
        closeFlyout();
    }

    property string queryBuffer: ""
    Process {
        id: queryProcess
        command: ["python3", root.scriptPath, "get"]
        stdout: SplitParser {
            onRead: data => { root.queryBuffer += data; }
        }
        onExited: (code, status) => {
            if (code === 0 && root.queryBuffer.trim().length > 0) {
                try {
                    const parsed = JSON.parse(root.queryBuffer.trim());
                    root.displayState = parsed;
                    if (parsed.currentMode) {
                        root.activeMode = parsed.currentMode;
                    }
                } catch (e) {
                    console.warn("DisplayProject: Failed to parse display state:", e);
                }
            }
            root.queryBuffer = "";
        }
    }

    property string applyBuffer: ""
    Process {
        id: applyProcess
        stdout: SplitParser {
            onRead: data => { root.applyBuffer += data; }
        }
        onExited: (code, status) => {
            root.isApplying = false;
            root.refreshState();
        }
    }

    // IPC Endpoint
    IpcHandler {
        target: "displayProject"

        function toggle(): string {
            root.toggleFlyout();
            return overlay.visible ? "opened" : "closed";
        }

        function open(): string {
            root.openFlyout();
            return "opened";
        }

        function close(): string {
            root.closeFlyout();
            return "closed";
        }

        function cycle(): string {
            root.cycleNext();
            return `cycled:${root.modes[root.selectedIndex].id}`;
        }

        function apply(mode: string): string {
            root.applyMode(mode);
            return `applied:${mode}`;
        }

        function status(): string {
            return JSON.stringify(root.displayState || {});
        }
    }

    // Fullscreen Overlay with Sidebar Flyout
    PanelWindow {
        id: overlay
        visible: false
        color: "transparent"

        WlrLayershell.namespace: "dms:plugins:displayProject"
        WlrLayershell.layer: WlrLayershell.Overlay
        WlrLayershell.exclusiveZone: -1
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive

        anchors {
            top: true
            left: true
            right: true
            bottom: true
        }

        // Semi-transparent backdrop
        Rectangle {
            anchors.fill: parent
            color: Theme.withAlpha(Theme.scrimColor, 0.45)
            opacity: overlay.visible ? 1 : 0
            Behavior on opacity {
                NumberAnimation { duration: Theme.shortDuration }
            }

            MouseArea {
                anchors.fill: parent
                onClicked: root.closeFlyout()
            }
        }

        // Keyboard handler
        FocusScope {
            id: overlayFocusScope
            anchors.fill: parent
            focus: true

            Keys.onPressed: event => {
                if (event.isAutoRepeat) {
                    event.accepted = true;
                    return;
                }

                switch (event.key) {
                case Qt.Key_Up:
                case Qt.Key_Left:
                case Qt.Key_Backtab:
                    root.selectedIndex = (root.selectedIndex - 1 + root.modes.length) % root.modes.length;
                    event.accepted = true;
                    break;
                case Qt.Key_Down:
                case Qt.Key_Right:
                case Qt.Key_Tab:
                    root.selectedIndex = (root.selectedIndex + 1) % root.modes.length;
                    event.accepted = true;
                    break;
                case Qt.Key_Return:
                case Qt.Key_Enter:
                case Qt.Key_Space:
                    root.applySelected();
                    event.accepted = true;
                    break;
                case Qt.Key_1:
                    root.selectedIndex = 0;
                    root.applySelected();
                    event.accepted = true;
                    break;
                case Qt.Key_2:
                    root.selectedIndex = 1;
                    root.applySelected();
                    event.accepted = true;
                    break;
                case Qt.Key_3:
                    root.selectedIndex = 2;
                    root.applySelected();
                    event.accepted = true;
                    break;
                case Qt.Key_4:
                    root.selectedIndex = 3;
                    root.applySelected();
                    event.accepted = true;
                    break;
                case Qt.Key_Escape:
                    root.closeFlyout();
                    event.accepted = true;
                    break;
                }
            }

            // Centered Modal Dialog Panel
            Rectangle {
                id: flyoutPanel
                width: 440
                height: Math.min(parent.height - Theme.spacingXL * 2, contentColumn.implicitHeight + Theme.spacingL * 2)
                anchors.centerIn: parent
                radius: Theme.cornerRadius * 1.5
                color: Theme.surfaceContainerHigh
                border.color: Theme.withAlpha(Theme.outline, 0.25)
                border.width: 1

                scale: overlay.visible ? 1.0 : 0.95
                opacity: overlay.visible ? 1.0 : 0.0
                Behavior on scale { NumberAnimation { duration: Theme.shortDuration; easing.type: Easing.OutCubic } }
                Behavior on opacity { NumberAnimation { duration: Theme.shortDuration } }

                // Drop shadow simulation
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -1
                    radius: flyoutPanel.radius + 1
                    color: "transparent"
                    border.color: Theme.withAlpha(Theme.surfaceVariantText, 0.1)
                    border.width: 1
                    z: -1
                }

                // Prevent clicks inside panel from closing
                MouseArea {
                    anchors.fill: parent
                    onClicked: mouse.accepted = true
                }

                Column {
                    id: contentColumn
                    width: parent.width - Theme.spacingL * 2
                    anchors.centerIn: parent
                    spacing: Theme.spacingM

                    // Header
                    Row {
                        width: parent.width
                        spacing: Theme.spacingM

                        Rectangle {
                            width: 42
                            height: 42
                            radius: Theme.cornerRadius
                            color: Theme.primaryContainer
                            anchors.verticalCenter: parent.verticalCenter

                            DIcon {
                                name: "devices"
                                size: Theme.iconSize
                                color: Theme.primary
                                anchors.centerIn: parent
                            }
                        }

                        Column {
                            width: parent.width - 42 - 36 - Theme.spacingM * 2
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2

                            StyledText {
                                text: "Project"
                                font.pixelSize: Theme.fontSizeLarge
                                font.weight: Font.DemiBold
                                color: Theme.surfaceText
                            }

                            StyledText {
                                text: "SUPER + P or Arrows to choose · Enter to apply"
                                font.pixelSize: Theme.fontSizeSmall - 1
                                color: Theme.surfaceVariantText
                                elide: Text.ElideRight
                                width: parent.width
                            }
                        }

                        DActionButton {
                            iconName: "close"
                            iconSize: Theme.iconSizeSmall
                            iconColor: Theme.surfaceVariantText
                            anchors.verticalCenter: parent.verticalCenter
                            onClicked: root.closeFlyout()
                        }
                    }

                    // Divider
                    Rectangle {
                        width: parent.width
                        height: 1
                        color: Theme.withAlpha(Theme.outline, 0.2)
                    }

                    // 4 Projection Mode Cards
                    Column {
                        width: parent.width
                        spacing: Theme.spacingS

                        Repeater {
                            model: root.modes

                            delegate: Rectangle {
                                id: cardDelegate
                                required property var modelData
                                required property int index

                                readonly property bool isSelected: root.selectedIndex === index
                                readonly property bool isActive: root.activeMode === modelData.id

                                width: parent.width
                                height: 74
                                radius: Theme.cornerRadius
                                color: {
                                    if (isSelected) return Theme.primaryContainer;
                                    if (cardMouse.containsMouse) return Theme.surfaceContainerHighest;
                                    return Theme.surfaceContainer;
                                }

                                border.color: isSelected ? Theme.primary : (isActive ? Theme.withAlpha(Theme.primary, 0.5) : Theme.withAlpha(Theme.outline, 0.15))
                                border.width: isSelected ? 2 : 1

                                Behavior on color { ColorAnimation { duration: Theme.shortDuration } }
                                Behavior on border.color { ColorAnimation { duration: Theme.shortDuration } }

                                Row {
                                    anchors.fill: parent
                                    anchors.leftMargin: Theme.spacingM
                                    anchors.rightMargin: Theme.spacingM
                                    spacing: Theme.spacingM

                                    // Icon Box
                                    Rectangle {
                                        width: 44
                                        height: 44
                                        radius: Theme.cornerRadius
                                        color: cardDelegate.isSelected ? Theme.surfaceContainerHighest : (cardDelegate.isActive ? Theme.withAlpha(Theme.primary, 0.15) : Theme.surfaceContainerHigh)
                                        anchors.verticalCenter: parent.verticalCenter

                                        DIcon {
                                            name: cardDelegate.modelData.icon
                                            size: 24
                                            color: cardDelegate.isSelected ? Theme.primary : (cardDelegate.isActive ? Theme.primary : Theme.surfaceText)
                                            anchors.centerIn: parent
                                        }
                                    }

                                    // Texts
                                    Column {
                                        width: parent.width - 44 - (badgeBox.visible ? badgeBox.width + Theme.spacingS : 0) - Theme.spacingM * 2
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 3

                                        StyledText {
                                            text: cardDelegate.modelData.title
                                            font.pixelSize: Theme.fontSizeMedium
                                            font.weight: cardDelegate.isSelected ? Font.Bold : Font.DemiBold
                                            color: cardDelegate.isSelected ? Theme.primary : Theme.surfaceText
                                            elide: Text.ElideRight
                                            width: parent.width
                                        }

                                        StyledText {
                                            text: cardDelegate.modelData.desc
                                            font.pixelSize: Theme.fontSizeSmall - 1
                                            color: cardDelegate.isSelected ? Theme.surfaceText : Theme.surfaceVariantText
                                            elide: Text.ElideRight
                                            width: parent.width
                                        }
                                    }

                                    // Active State Badge
                                    Rectangle {
                                        id: badgeBox
                                        visible: cardDelegate.isActive
                                        width: 58
                                        height: 24
                                        radius: 12
                                        color: cardDelegate.isSelected ? Theme.primary : Theme.withAlpha(Theme.primary, 0.2)
                                        anchors.verticalCenter: parent.verticalCenter

                                        Row {
                                            anchors.centerIn: parent
                                            spacing: 4

                                            DIcon {
                                                name: "check"
                                                size: 14
                                                color: cardDelegate.isSelected ? Theme.surfaceContainerHighest : Theme.primary
                                                anchors.verticalCenter: parent.verticalCenter
                                            }

                                            StyledText {
                                                text: "Active"
                                                font.pixelSize: Theme.fontSizeSmall - 2
                                                font.weight: Font.DemiBold
                                                color: cardDelegate.isSelected ? Theme.surfaceContainerHighest : Theme.primary
                                                anchors.verticalCenter: parent.verticalCenter
                                            }
                                        }
                                    }
                                }

                                MouseArea {
                                    id: cardMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        root.selectedIndex = cardDelegate.index;
                                        root.applySelected();
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        refreshState();
        console.info("DisplayProject: daemon loaded — use 'dms ipc call displayProject cycle' to open/cycle");
    }
}

