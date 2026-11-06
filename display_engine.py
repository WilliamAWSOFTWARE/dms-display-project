#!/usr/bin/env python3
"""
Display Project Engine for Hyprland & DankMaterialShell.
Accurately preserves native monitor resolutions and refresh rates.
"""

import sys
import os
import json
import subprocess
import re

OUTPUTS_LUA_PATH = os.path.expanduser("~/.config/hypr/dms/outputs.lua")
CACHE_FILE = os.path.expanduser("~/.config/dms/plugins/displayProject/monitors_cache.json")

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        sys.stderr.write(f"Warning: could not save monitors cache: {e}\n")

def get_monitors():
    try:
        raw = subprocess.check_output(["hyprctl", "monitors", "all", "-j"], timeout=2).decode()
        monitors = json.loads(raw)
        return monitors
    except Exception as e:
        sys.stderr.write(f"Error querying monitors: {e}\n")
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
        args = ["hyprctl", "dispatch"] + cmd.split()
        res = subprocess.run(args, capture_output=True, text=True, timeout=2)
        return res.returncode == 0
    except Exception as e:
        sys.stderr.write(f"hypr_dispatch error: {e}\n")
        return False

def update_and_get_native_cache(all_mons):
    cache = load_cache()
    updated = False

    for m in all_mons:
        name = m.get("name")
        if not name:
            continue
        modes = m.get("availableModes", [])
        parsed = []
        for s in modes:
            match = re.match(r"(\d+)x(\d+)@([\d.]+)Hz", s)
            if match:
                w, h, r = int(match.group(1)), int(match.group(2)), float(match.group(3))
                parsed.append((w, h, r, s))

        # Sort by resolution (w*h) desc, then refresh rate desc
        parsed.sort(key=lambda x: (x[0] * x[1], x[2]), reverse=True)
        if parsed:
            best = parsed[0]
            w, h, r = best[0], best[1], best[2]
            if abs(r - 200.01) < 0.1:
                mode_str = f"{w}x{h}@200.007"
            elif r.is_integer():
                mode_str = f"{w}x{h}@{int(r)}.000"
            else:
                mode_str = f"{w}x{h}@{r:.3f}"

            # Only overwrite cache if this is higher or equal to what's cached
            old = cache.get(name)
            if not old or (w * h >= old.get("width", 0) * old.get("height", 0) and r >= old.get("refresh", 0)):
                cache[name] = {
                    "width": w,
                    "height": h,
                    "refresh": r,
                    "mode_str": mode_str,
                    "model": m.get("model", name)
                }
                updated = True

    if updated or not os.path.exists(CACHE_FILE):
        save_cache(cache)

    return cache

def detect_current_state():
    all_mons = get_monitors()
    if not all_mons:
        return {
            "currentMode": "extend",
            "monitors": [],
            "primary": None,
            "secondary": None,
            "error": "No monitors detected"
        }

    cache = update_and_get_native_cache(all_mons)

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

    # Detect active mode
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
        name = m.get("name", "")
        c_entry = cache.get(name, {})
        native_w = c_entry.get("width", m.get("width", 1920))
        native_h = c_entry.get("height", m.get("height", 1080))
        native_r = c_entry.get("refresh", round(m.get("refreshRate", 60.0), 2))
        native_mode = c_entry.get("mode_str", f"{native_w}x{native_h}@{native_r}")

        return {
            "name": name,
            "model": m.get("model", name),
            "description": m.get("description", ""),
            "width": m.get("width", 1920),
            "height": m.get("height", 1080),
            "refresh": round(m.get("refreshRate", 60.0), 2),
            "native_width": native_w,
            "native_height": native_h,
            "native_refresh": native_r,
            "native_mode": native_mode,
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
    all_mons = get_monitors()
    if not all_mons:
        return {"success": False, "error": "No monitors detected"}

    cache = update_and_get_native_cache(all_mons)

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

    m1_name = mon1["name"]
    m1_cache = cache.get(m1_name, {})
    m1_w = m1_cache.get("width", mon1.get("width", 1920))
    m1_h = m1_cache.get("height", mon1.get("height", 1080))
    m1_mode = m1_cache.get("mode_str", f"{m1_w}x{m1_h}@60.000")

    if not mon2:
        # Only single display available
        lua_code = f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "0x0", scale = 1, mirror = "none" }})\n'
        lua_code += f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m1_name}" }}))\n'
        hypr_eval(lua_code)
        return {"success": True, "mode": "primary_only"}

    m2_name = mon2["name"]
    m2_cache = cache.get(m2_name, {})
    m2_w = m2_cache.get("width", mon2.get("width", 2560))
    m2_h = m2_cache.get("height", mon2.get("height", 1080))
    m2_mode = m2_cache.get("mode_str", f"{m2_w}x{m2_h}@200.007")

    lua_lines = []

    if mode == "primary_only":
        # Monitor 1 on native, Monitor 2 parked at 10000x0 and DPMS off
        lua_lines = [
            f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "0x0", scale = 1, mirror = "none" }})',
            f'hl.monitor({{ output = "{m2_name}", mode = "{m2_mode}", position = "10000x0", scale = 1, mirror = "none" }})',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m1_name}" }}))',
            f'hl.dispatch(hl.dsp.dpms({{ action = "off", monitor = "{m2_name}" }}))'
        ]

    elif mode == "secondary_only":
        # Monitor 2 on native at 0x0, Monitor 1 parked at 10000x0 and DPMS off
        lua_lines = [
            f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "10000x0", scale = 1, mirror = "none" }})',
            f'hl.monitor({{ output = "{m2_name}", mode = "{m2_mode}", position = "0x0", scale = 1, mirror = "none" }})',
            f'hl.dispatch(hl.dsp.dpms({{ action = "off", monitor = "{m1_name}" }}))',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m2_name}" }}))'
        ]

    elif mode == "duplicate":
        # Mirror: Secondary mirrors Primary. Use Primary's mode.
        dup_mode = f"{m1_w}x{m1_h}@60.000"
        lua_lines = [
            f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "0x0", scale = 1, mirror = "none" }})',
            f'hl.monitor({{ output = "{m2_name}", mode = "{dup_mode}", position = "0x0", scale = 1, mirror = "{m1_name}" }})',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m1_name}" }}))',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m2_name}" }}))'
        ]

    else:  # extend (default)
        mode = "extend"
        # Both monitors side-by-side with their full native modes and refresh rates!
        # Primary at 0x0, Secondary at m1_width x 0
        lua_lines = [
            f'hl.monitor({{ output = "{m1_name}", mode = "{m1_mode}", position = "0x0", scale = 1, mirror = "none" }})',
            f'hl.monitor({{ output = "{m2_name}", mode = "{m2_mode}", position = "{m1_w}x0", scale = 1, mirror = "none" }})',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m1_name}" }}))',
            f'hl.dispatch(hl.dsp.dpms({{ action = "on", monitor = "{m2_name}" }}))'
        ]

    # Execute Lua in Hyprland
    lua_code = "\n".join(lua_lines)
    hypr_eval(lua_code)

    # Persist in outputs.lua cleanly
    try:
        os.makedirs(os.path.dirname(OUTPUTS_LUA_PATH), exist_ok=True)
        persisted = "-- Auto-generated by DMS / displayProject\n\n"
        for line in lua_lines:
            if line.startswith("hl.monitor"):
                persisted += line + "\n"
        persisted += 'hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })\n'
        with open(OUTPUTS_LUA_PATH, "w") as f:
            f.write(persisted)
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
