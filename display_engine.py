#!/usr/bin/env python3
"""
Display Project Engine for Hyprland & DankMaterialShell.
Manages Display Projection modes: primary_only, duplicate, extend, secondary_only.
"""

import sys
import os
import json
import subprocess

OUTPUTS_LUA_PATH = os.path.expanduser("~/.config/hypr/dms/outputs.lua")

def get_monitors():
    try:
        raw = subprocess.check_output(["hyprctl", "monitors", "all", "-j"], timeout=2).decode()
        monitors = json.loads(raw)
        return monitors
    except Exception as e:
        sys.stderr.write(f"Error querying monitors: {e}\n")
        return []

def get_active_monitors():
    try:
        raw = subprocess.check_output(["hyprctl", "monitors", "-j"], timeout=2).decode()
        return json.loads(raw)
    except Exception:
        return []

def hypr_eval(code):
    try:
        res = subprocess.run(["hyprctl", "eval", code], capture_output=True, text=True, timeout=2)
        return res.returncode == 0
    except Exception as e:
        sys.stderr.write(f"hypr_eval error: {e}\n")
        return False

def hypr_dispatch(cmd):
    try:
        res = subprocess.run(["hyprctl", "dispatch"] + cmd.split(), capture_output=True, text=True, timeout=2)
        return res.returncode == 0
    except Exception as e:
        sys.stderr.write(f"hypr_dispatch error: {e}\n")
        return False

def hypr_keyword(key, val):
    try:
        res = subprocess.run(["hyprctl", "keyword", key, str(val)], capture_output=True, text=True, timeout=2)
        return res.returncode == 0
    except Exception as e:
        sys.stderr.write(f"hypr_keyword error: {e}\n")
        return False

def detect_current_state():
    all_mons = get_monitors()
    if not all_mons:
        return {
            "currentMode": "extend",
            "monitors": [],
            "primary": "",
            "secondary": "",
            "error": "No monitors detected"
        }

    # Sort monitors: HDMI-A-1 or eDP-1 or id 0 first
    def mon_sort_key(m):
        name = m.get("name", "").lower()
        if "edp" in name:
            return 0
        if "hdmi" in name:
            return 1
        return 10 + m.get("id", 0)

    sorted_mons = sorted(all_mons, key=mon_sort_key)
    mon1 = sorted_mons[0]
    mon2 = sorted_mons[1] if len(sorted_mons) > 1 else None

    # Detect mode
    # Check if mirror
    if mon2 and (mon2.get("mirrorOf", "none") not in ("none", "") or mon1.get("mirrorOf", "none") not in ("none", "")):
        current_mode = "duplicate"
    elif mon2 and (mon2.get("disabled", False) or not mon2.get("dpmsStatus", True) or mon2.get("x", 0) >= 9000):
        current_mode = "primary_only"
    elif mon2 and (mon1.get("disabled", False) or not mon1.get("dpmsStatus", True) or mon1.get("x", 0) >= 9000):
        current_mode = "secondary_only"
    else:
        current_mode = "extend"

    def format_mon(m):
        if not m:
            return None
        return {
            "name": m.get("name", ""),
            "model": m.get("model", m.get("name", "")),
            "description": m.get("description", ""),
            "width": m.get("width", 1920),
            "height": m.get("height", 1080),
            "refresh": round(m.get("refreshRate", 60.0), 2),
            "x": m.get("x", 0),
            "y": m.get("y", 0),
            "disabled": m.get("disabled", False),
            "dpms": m.get("dpmsStatus", True),
            "mirrorOf": m.get("mirrorOf", "none")
        }

    return {
        "currentMode": current_mode,
        "monitors": [format_mon(m) for m in sorted_mons],
        "primary": format_mon(mon1),
        "secondary": format_mon(mon2) if mon2 else None
    }

def apply_mode(mode):
    state = detect_current_state()
    mon1 = state.get("primary")
    mon2 = state.get("secondary")

    if not mon1:
        return {"success": False, "error": "No primary monitor found"}

    m1_name = mon1["name"]
    # Standard preferred modes: check if we know exact modes, or use detected
    m1_w = mon1.get("width", 1920)
    m1_h = mon1.get("height", 1080)
    m1_r = mon1.get("refresh", 60.0)
    m1_mode = f"{m1_w}x{m1_h}@{int(m1_r)}" if m1_r.is_integer() else f"{m1_w}x{m1_h}@{m1_r:.2f}"

    if not mon2:
        # Only single monitor present
        hypr_eval(f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "0x0", scale = 1, mirror = "none" }})')
        hypr_dispatch(f"dpms on {m1_name}")
        return {"success": True, "mode": "primary_only"}

    m2_name = mon2["name"]
    m2_w = mon2.get("width", 2560)
    m2_h = mon2.get("height", 1080)
    m2_r = mon2.get("refresh", 200.0)
    m2_mode = f"{m2_w}x{m2_h}@{int(m2_r)}" if m2_r.is_integer() else f"{m2_w}x{m2_h}@{m2_r:.3f}"

    lua_lines = []

    if mode == "primary_only":
        lua_lines = [
            f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "0x0", scale = 1, mirror = "none" }})',
            f'hl.monitor({{ output = "{m2_name}", mode = "{m2_mode}", position = "10000x0", scale = 1, mirror = "none" }})',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m1_name}" }}))',
            f'hl.dispatch(hl.dsp.dpms({{ action = "off", monitor = "{m2_name}" }}))'
        ]
        # Also keyword monitor fallback
        hypr_keyword("monitor", f"{m1_name},{m1_mode},0x0,1")
        hypr_keyword("monitor", f"{m2_name},{m2_mode},10000x0,1")
        hypr_dispatch(f"dpms on {m1_name}")
        hypr_dispatch(f"dpms off {m2_name}")

    elif mode == "secondary_only":
        lua_lines = [
            f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "10000x0", scale = 1, mirror = "none" }})',
            f'hl.monitor({{ output = "{m2_name}", mode = "{m2_mode}", position = "0x0", scale = 1, mirror = "none" }})',
            f'hl.dispatch(hl.dsp.dpms({{ action = "off", monitor = "{m1_name}" }}))',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m2_name}" }}))'
        ]
        hypr_keyword("monitor", f"{m1_name},{m1_mode},10000x0,1")
        hypr_keyword("monitor", f"{m2_name},{m2_mode},0x0,1")
        hypr_dispatch(f"dpms off {m1_name}")
        hypr_dispatch(f"dpms on {m2_name}")

    elif mode == "duplicate":
        # When duplicating, use compatible common resolution (e.g. 1920x1080@60)
        dup_mode = f"{m1_w}x{m1_h}@60"
        lua_lines = [
            f'hl.monitor({{ output = "{m1_name}", mode = "{dup_mode}", position = "0x0", scale = 1, mirror = "none" }})',
            f'hl.monitor({{ output = "{m2_name}", mode = "{dup_mode}", position = "0x0", scale = 1, mirror = "{m1_name}" }})',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m1_name}" }}))',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m2_name}" }}))'
        ]
        hypr_keyword("monitor", f"{m1_name},{dup_mode},0x0,1")
        hypr_keyword("monitor", f"{m2_name},{dup_mode},0x0,1,mirror,{m1_name}")
        hypr_dispatch(f"dpms on {m1_name}")
        hypr_dispatch(f"dpms on {m2_name}")

    else:  # extend (default)
        mode = "extend"
        lua_lines = [
            f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "0x0", scale = 1, mirror = "none" }})',
            f'hl.monitor({{ output = "{m2_name}", mode = "{m2_mode}", position = "{m1_w}x0", scale = 1, mirror = "none" }})',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m1_name}" }}))',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m2_name}" }}))'
        ]
        hypr_keyword("monitor", f"{m1_name},{m1_mode},0x0,1")
        hypr_keyword("monitor", f"{m2_name},{m2_mode},{m1_w}x0,1")
        hypr_dispatch(f"dpms on {m1_name}")
        hypr_dispatch(f"dpms on {m2_name}")

    # Execute Lua in Hyprland
    lua_code = "\n".join(lua_lines)
    hypr_eval(lua_code)

    # Persist in outputs.lua if writable
    try:
        os.makedirs(os.path.dirname(OUTPUTS_LUA_PATH), exist_ok=True)
        persisted_content = "-- Auto-generated by displayProject plugin\n\n"
        for line in lua_lines:
            if line.startswith("hl.monitor"):
                persisted_content += line + "\n"
        with open(OUTPUTS_LUA_PATH, "w") as f:
            f.write(persisted_content)
    except Exception as e:
        sys.stderr.write(f"Warning: could not write {OUTPUTS_LUA_PATH}: {e}\n")

    return {"success": True, "mode": mode}

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "get":
        state = detect_current_state()
        print(json.dumps(state))
    elif sys.argv[1] == "set" and len(sys.argv) >= 3:
        target_mode = sys.argv[2]
        res = apply_mode(target_mode)
        print(json.dumps(res))
    else:
        print(json.dumps({"error": f"Unknown arguments {sys.argv}"}))

if __name__ == "__main__":
    main()
