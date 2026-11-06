# Display Project (Win+P) for DankMaterialShell (DMS)

[![Hyprland](https://img.shields.io/badge/Hyprland-0.50%2B-blue?logo=wayland&logoColor=white)](https://hyprland.org)
[![DankMaterialShell](https://img.shields.io/badge/DMS-Plugin-purple?logo=material-design&logoColor=white)](https://github.com/AvengeMedia/DankMaterialShell)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1-green.svg)](plugin.json)

A native Material Design 3 display projection modal for **Hyprland** on **DankMaterialShell (DMS)**, bringing the familiar Windows **Win + P** multi-monitor switching experience into Linux.

---

## 🎯 Features

- **Windows Win+P Workflow**:
  - **Press `SUPER + P`**: Opens an elegant centered modal dialog with smooth scale and fade animations.
  - **Press `SUPER + P` again**: Cycles through the 4 projection modes smoothly.
  - **Apply**: Press **Enter**, **Space**, numbers **1-4**, or click any card directly.
  - **No Accidental Changes**: No intrusive auto-apply timer; the selected mode only applies when explicitly confirmed.
  - **Cancel**: Press **Escape** or click anywhere outside to close without applying.
- **4 Standard Modes**:
  1. 💻 **Solo pantalla de PC (PC Screen Only)**: Keeps your primary display active and turns off/sleeps secondary monitors.
  2. 🔁 **Duplicar (Duplicate / Mirror)**: Clones your screen across all displays with matching resolution.
  3. 🖥️ 🖥️ **Extender (Extend)**: Spans your desktop across all connected monitors with their native resolutions and refresh rates.
  4. 📺 **Solo segunda pantalla (Second Screen Only)**: Puts your primary display to sleep and runs exclusively on your secondary monitor.
- **Dynamic Monitor Detection**: Automatically discovers monitor names, resolutions, refresh rates, and active states.
- **Hardware Mode Locking**: Remembers and restores the true native resolution and refresh rate (e.g. 200Hz / ultrawide) of every connected monitor, preventing downscale lock-in after mirroring.
- **Instant Response**: Built as a persistent QML daemon with sub-millisecond IPC responsiveness.

---

## 🚀 Keybind Setup (Hyprland)

In your `hyprland.lua` (or `hyprland.conf`), bind `SUPER + P` to trigger the IPC endpoint:

### Modern Lua (`~/.config/hypr/hyprland.lua`):
```lua
hl.bind(mainMod .. " + P", hl.dsp.exec_cmd("dms ipc call displayProject cycle"))
```

### Classic Config (`~/.config/hypr/hyprland.conf`):
```ini
bind = $mainMod, P, exec, dms ipc call displayProject cycle
```

---

## 📦 Installation & Setup

1. Clone or copy the repository into your DMS plugins directory:
   ```bash
   git clone https://github.com/WilliamAWSOFTWARE/dms-display-project.git ~/.config/dms/plugins/displayProject
   ```

2. Open **DMS Settings** (`SUPER + N`) → **Plugins** and verify **Display Project (Win+P)** is enabled.

3. Restart DMS:
   ```bash
   dms restart
   ```

---

<details>
<summary><b>🇪🇸 Documentación en Español (Haz clic para expandir)</b></summary>

### Selector Rápido de Pantallas (Estilo Win + P) para DMS

Modal centrado nativo en Material Design 3 para **Hyprland** en **DankMaterialShell (DMS)**, recreando la experiencia clásica de conmutación de pantallas **Win + P** de Windows en Linux.

#### Características
- **Flujo idéntico a Win + P**:
  - Pulsa **`SUPER + P`**: Se abre el diálogo centrado en pantalla.
  - Vuelve a pulsar **`SUPER + P`**: Va ciclando entre los 4 modos.
  - **Confirmación manual segura**: Sin temporizadores que cambien la pantalla de repente; se aplica al pulsar **Enter**, **Espacio**, números del **1 al 4** o haciendo clic directo sobre la tarjeta.
  - **Cancelar**: Pulsa **Escape** o haz clic fuera del panel para cerrar sin modificar nada.
- **Los 4 Modos**:
  1. 💻 **Solo pantalla de PC**: Monitor principal activo, monitor secundario suspendido vía DPMS.
  2. 🔁 **Duplicar**: Clona la pantalla en ambos monitores.
  3. 🖥️ 🖥️ **Extender**: Escritorio ampliado con las resoluciones y frecuencias nativas de cada pantalla.
  4. 📺 **Solo segunda pantalla**: Monitor secundario activo, monitor principal suspendido.
- **Protección de Resoluciones**: Bloquea y restaura siempre las frecuencias y resoluciones nativas completas (ej. 2560x1080@200Hz y 1920x1080@60Hz) sin importar los cambios temporales de clonación.

#### Instalación
```bash
git clone https://github.com/WilliamAWSOFTWARE/dms-display-project.git ~/.config/dms/plugins/displayProject
dms restart
```

</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Created with ❤️ for the Linux & Hyprland community by [WilliamAWSOFTWARE](https://github.com/WilliamAWSOFTWARE).
