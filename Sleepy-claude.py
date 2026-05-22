#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║    ⌨  RAPID-FIRE MACRO PRO  –  CROSS-PLATFORM EDITION    ║
║       Linux / Windows / macOS – Single Codebase           ║
╚══════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import threading
import time
import json
import os
import re
import ctypes
import subprocess
import platform
import sys
from pathlib import Path

# ── Platform Detection ──────────────────────────────────────────────────────
SYSTEM = platform.system()  # "Linux", "Windows", "Darwin" (macOS)
IS_LINUX = SYSTEM == "Linux"
IS_WINDOWS = SYSTEM == "Windows"
IS_MACOS = SYSTEM == "Darwin"

# ── Optional drag-and-drop support ──────────────────────────────────────────
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_OK = True
except ImportError:
    DND_OK = False

# ── Cross-Platform Mouse Support ────────────────────────────────────────────
try:
    from pynput import mouse as pynput_mouse, keyboard as pynput_keyboard
    PYNPUT_OK = True
except ImportError:
    PYNPUT_OK = False

# ── Platform-Specific Keyboard Input ────────────────────────────────────────
KB_OK = False
KB_LIB_NAME = None

if IS_WINDOWS:
    # Windows: Try keyboard library or fall back to pyautogui
    try:
        import keyboard as kb_lib
        KB_OK = True
        KB_LIB_NAME = "keyboard"
    except ImportError:
        try:
            import pyautogui
            KB_OK = True
            KB_LIB_NAME = "pyautogui"
        except ImportError:
            pass
elif IS_LINUX:
    # Linux: keyboard library + optional X11 direct injection
    try:
        import keyboard as kb_lib
        KB_OK = True
        KB_LIB_NAME = "keyboard"
    except ImportError:
        if PYNPUT_OK:
            pynput_kb = pynput_keyboard
            KB_OK = True
            KB_LIB_NAME = "pynput"
elif IS_MACOS:
    # macOS: pynput or keyboard library
    try:
        from pynput import keyboard as pynput_kb
        KB_OK = True
        KB_LIB_NAME = "pynput"
    except ImportError:
        try:
            import keyboard as kb_lib
            KB_OK = True
            KB_LIB_NAME = "keyboard"
        except ImportError:
            pass

# ── Linux-Specific: Direct X11 Hardware Injection ──────────────────────────
X11_OK = False
DISPLAY_CONN = None

if IS_LINUX:
    try:
        X11 = ctypes.CDLL("libX11.so.6")
        Xtest = ctypes.CDLL("libXtst.so.6")
        X11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        X11.XOpenDisplay.restype = ctypes.c_void_p
        X11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        X11.XStringToKeysym.restype = ctypes.c_ulong
        X11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        X11.XKeysymToKeycode.restype = ctypes.c_ubyte
        Xtest.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                             ctypes.c_int, ctypes.c_ulong]
        Xtest.XTestFakeKeyEvent.restype = ctypes.c_int
        DISPLAY_CONN = X11.XOpenDisplay(None)
        if not DISPLAY_CONN:
            raise RuntimeError("Could not open X11 Display context")
        X11_OK = True
    except Exception as e:
        print(f"[X11 Direct Engine] Initialization error: {e}")
        X11_OK = False
        DISPLAY_CONN = None
else:
    X11_OK = False

# ── Cross-Platform File Paths ──────────────────────────────────────────────
def get_config_dir():
    """Get platform-appropriate config directory"""
    if IS_WINDOWS:
        config_dir = Path.home() / "AppData" / "Local" / "RapidFireMacroPro"
    elif IS_MACOS:
        config_dir = Path.home() / "Library" / "Application Support" / "RapidFireMacroPro"
    else:  # Linux
        config_dir = Path.home() / ".config" / "rapid-fire-macro-pro"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

CONFIG_DIR = get_config_dir()
PROFILES_FILE = CONFIG_DIR / "macro_profiles.json"
MOUSE_CONFIG_FILE = CONFIG_DIR / "mouse_config.json"

# ═══════════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  –  Light Pink Theme with Black Text
# ═══════════════════════════════════════════════════════════════════════════════
C = {
    "bg":       "#fdf6f9",    # very light pink background
    "surface":  "#f9e8f0",    # light pink surface
    "panel":    "#f5d9e8",    # medium-light pink panel
    "card":     "#fce7f3",    # light pink card
    "key_bg":   "#f5d9e8",    # light pink key background
    "key_fg":   "#000000",    # black text
    "key_bdr":  "#f0c4dd",    # medium pink border
    "hover":    "#f9e8f0",
    "sel_bg":   "#f0a8d4",    # medium pink selected
    "sel_bdr":  "#e88ec0",    # darker pink border
    "sel_fg":   "#000000",    # black text
    "accent":   "#e88ec0",    # medium pink accent
    "fire":     "#e88ec0",    # medium pink fire state
    "green":    "#22c55e",    # green for active
    "green_hi": "#16a34a",    # dark green for hover
    "muted":    "#999999",    # gray muted text
    "text":     "#000000",    # black text
    "text_hi":  "#000000",    # black text
    "tab_act":  "#fce7f3",    # light pink active tab
    "tab_in":   "#f9e8f0",    # medium light pink inactive tab
    "tab_bdr":  "#e88ec0",    # pink tab border
    "danger":   "#ef4444",
}

LAYOUT = [
    [("Esc","esc",1.0), ("","",0.5),
     ("F1","f1",1), ("F2","f2",1), ("F3","f3",1), ("F4","f4",1), ("","",0.3),
     ("F5","f5",1), ("F6","f6",1), ("F7","f7",1), ("F8","f8",1), ("","",0.3),
     ("F9","f9",1), ("F10","f10",1), ("F11","f11",1), ("F12","f12",1)],
    [("`","`",1), ("1","1",1), ("2","2",1), ("3","3",1), ("4","4",1),
     ("5","5",1), ("6","6",1), ("7","7",1), ("8","8",1), ("9","9",1),
     ("0","0",1), ("-","-",1), ("=","=",1), ("⌫ Back","backspace",2.0)],
    [("Tab","tab",1.5),
     ("Q","q",1), ("W","w",1), ("E","e",1), ("R","r",1), ("T","t",1),
     ("Y","y",1), ("U","u",1), ("I","i",1), ("O","o",1), ("P","p",1),
     ("[","[",1), ("]","]",1), ("\\","\\",1.5)],
    [("Caps","caps_lock",1.75),
     ("A","a",1), ("S","s",1), ("D","d",1), ("F","f",1), ("G","g",1),
     ("H","h",1), ("J","j",1), ("K","k",1), ("L","l",1), (";",";",1), ("'","'",1),
     ("↵ Enter","enter",2.25)],
    [("⇧ Shift","shift",2.25),
     ("Z","z",1), ("X","x",1), ("C","c",1), ("V","v",1), ("B","b",1),
     ("N","n",1), ("M","m",1), (",",",",1), (".", ".",1), ("/","/",1),
     ("⇧ Shift","shift_r",2.75)],
    [("Ctrl","ctrl_l",1.5), ("❖ Win","cmd",1.25), ("Alt","alt_l",1.25),
     ("Space","space",6.25),
     ("Alt","alt_r",1.25), ("Fn","fn",1.0), ("▤","menu",1.0), ("Ctrl","ctrl_r",1.5)],
]

KNAME: dict = {
    "esc":"Escape","f1":"F1","f2":"F2","f3":"F3","f4":"F4","f5":"F5","f6":"F6",
    "f7":"F7","f8":"F8","f9":"F9","f10":"F10","f11":"F11","f12":"F12",
    "backspace":"BackSpace","tab":"Tab","caps_lock":"Caps_Lock",
    "enter":"Return","shift":"Shift_L","shift_r":"Shift_R",
    "ctrl_l":"Control_L","ctrl_r":"Control_R",
    "alt_l":"Alt_L","alt_r":"Alt_R",
    "cmd":"Super_L","space":"space","menu":"Menu",
    "[":"bracketleft","]":"bracketright","\\":"backslash","`":"grave",
    "-":"minus","=":"equal",";":"semicolon","'":"apostrophe",
    ",":"comma",".":"period","/":"slash",
}

def kid_to_kname(kid: str) -> str:
    return KNAME.get(kid, kid)

def clean_label(raw: str) -> str:
    return (raw.replace("⌫ ","").replace("↵ ","")
               .replace("⇧ ","").replace("❖ ","")
               .replace("▤","Menu").strip())

def load_profiles() -> dict:
    try:
        with open(PROFILES_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data if data else {"Default": {}}
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[Profiles] Load error: {e}")
    return {"Default": {}}

def save_profiles(profiles: dict):
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2)
    except Exception as e:
        print(f"[Profiles] Could not save: {e}")

# ── X11 key tap helper (used by AHK engine) ──────────────────────────────────
AHK_SPECIAL_KEYS = {
    "enter":"Return","return":"Return","space":"space","tab":"Tab",
    "backspace":"BackSpace","delete":"Delete","escape":"Escape","esc":"Escape",
    "up":"Up","down":"Down","left":"Left","right":"Right",
    "home":"Home","end":"End","pgup":"Prior","pgdn":"Next",
    "f1":"F1","f2":"F2","f3":"F3","f4":"F4","f5":"F5","f6":"F6",
    "f7":"F7","f8":"F8","f9":"F9","f10":"F10","f11":"F11","f12":"F12",
}
AHK_MOD_MAP  = {"^":"ctrl","!":"alt","+":"shift","#":"super"}
KB_MOD_XNAME = {"ctrl":"Control_L","alt":"Alt_L","shift":"Shift_L","super":"Super_L"}

def tap_key(key_name: str, modifiers: list = None):
    """Cross-platform key press function"""
    if modifiers is None:
        modifiers = []
    
    try:
        if IS_LINUX and X11_OK and DISPLAY_CONN:
            # Linux: X11 direct injection (fastest & most reliable)
            _tap_key_x11(key_name, modifiers)
        elif PYNPUT_OK:
            # macOS, Windows, Linux fallback: pynput
            _tap_key_pynput(key_name, modifiers)
        elif KB_LIB_NAME == "keyboard":
            # Windows, Linux: keyboard library fallback
            _tap_key_keyboard(key_name, modifiers)
        elif KB_LIB_NAME == "pyautogui":
            # Windows: pyautogui fallback
            _tap_key_pyautogui(key_name, modifiers)
    except Exception as e:
        print(f"[KeyInput] Error tapping key '{key_name}': {e}")

def _tap_key_x11(keysym_name: str, modifiers: list):
    """X11 direct hardware injection (Linux only)"""
    mod_codes = []
    for mod in modifiers:
        sym  = X11.XStringToKeysym(KB_MOD_XNAME.get(mod, mod).encode())
        code = X11.XKeysymToKeycode(DISPLAY_CONN, sym)
        if code:
            Xtest.XTestFakeKeyEvent(DISPLAY_CONN, code, 1, 0)
            mod_codes.append(code)
    sym  = X11.XStringToKeysym(keysym_name.encode())
    code = X11.XKeysymToKeycode(DISPLAY_CONN, sym)
    if code:
        Xtest.XTestFakeKeyEvent(DISPLAY_CONN, code, 1, 0)
        Xtest.XTestFakeKeyEvent(DISPLAY_CONN, code, 0, 0)
    for code in reversed(mod_codes):
        Xtest.XTestFakeKeyEvent(DISPLAY_CONN, code, 0, 0)
    X11.XFlush(DISPLAY_CONN)

def _tap_key_pynput(key_name: str, modifiers: list):
    """pynput-based key press (macOS, Windows, Linux)"""
    from pynput.keyboard import Controller, Key
    controller = Controller()
    
    # Map key names to pynput Key enum
    key_map = {
        "space": Key.space, "enter": Key.enter, "return": Key.enter,
        "tab": Key.tab, "backspace": Key.backspace, "delete": Key.delete,
        "escape": Key.esc, "esc": Key.esc, "home": Key.home, "end": Key.end,
        "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
        "pageup": Key.page_up, "pagedown": Key.page_down, "page_up": Key.page_up, "page_down": Key.page_down,
        "caps_lock": Key.caps_lock, "shift": Key.shift, "shift_l": Key.shift_l, "shift_r": Key.shift_r,
        "ctrl": Key.ctrl, "ctrl_l": Key.ctrl_l, "ctrl_r": Key.ctrl_r,
        "alt": Key.alt, "alt_l": Key.alt_l, "alt_r": Key.alt_r,
        "cmd": Key.cmd, "cmd_l": Key.cmd_l, "cmd_r": Key.cmd_r,
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4, "f5": Key.f5,
        "f6": Key.f6, "f7": Key.f7, "f8": Key.f8, "f9": Key.f9, "f10": Key.f10,
        "f11": Key.f11, "f12": Key.f12,
    }
    
    # Press modifiers
    mod_keys = []
    for mod in modifiers:
        mod_key = key_map.get(mod, None)
        if mod_key:
            controller.press(mod_key)
            mod_keys.append(mod_key)
    
    # Press main key
    key_obj = key_map.get(key_name.lower(), key_name.lower() if len(key_name) == 1 else None)
    if key_obj:
        controller.press(key_obj)
        controller.release(key_obj)
    
    # Release modifiers
    for mod_key in reversed(mod_keys):
        controller.release(mod_key)

def _tap_key_keyboard(key_name: str, modifiers: list):
    """keyboard library-based key press"""
    import keyboard as kb
    
    key_map = {
        "space": "space", "enter": "enter", "return": "enter",
        "tab": "tab", "backspace": "backspace", "delete": "delete",
        "escape": "esc", "esc": "esc", "home": "home", "end": "end",
        "up": "up", "down": "down", "left": "left", "right": "right",
        "pageup": "page_up", "pagedown": "page_down",
        "caps_lock": "caps_lock", "shift": "shift", "shift_l": "shift_l", "shift_r": "shift_r",
        "ctrl": "ctrl_l", "ctrl_l": "ctrl_l", "ctrl_r": "ctrl_r",
        "alt": "alt_l", "alt_l": "alt_l", "alt_r": "alt_r",
    }
    
    key_name_mapped = key_map.get(key_name.lower(), key_name.lower())
    
    if modifiers:
        combo = "+".join([mod.strip() for mod in modifiers] + [key_name_mapped])
        kb.press_and_release(combo)
    else:
        kb.press_and_release(key_name_mapped)

def _tap_key_pyautogui(key_name: str, modifiers: list):
    """pyautogui-based key press (Windows primarily)"""
    import pyautogui
    
    key_map = {
        "space": "space", "enter": "enter", "return": "enter",
        "tab": "tab", "backspace": "backspace", "delete": "delete",
        "escape": "esc", "esc": "esc", "home": "home", "end": "end",
        "up": "up", "down": "down", "left": "left", "right": "right",
        "pageup": "pageup", "pagedown": "pagedown",
    }
    
    key_name_mapped = key_map.get(key_name.lower(), key_name.lower())
    
    if modifiers:
        for mod in modifiers:
            pyautogui.keyDown(mod)
        pyautogui.press(key_name_mapped)
        for mod in reversed(modifiers):
            pyautogui.keyUp(mod)
    else:
        pyautogui.press(key_name_mapped)

# Legacy alias for compatibility
def x11_tap_key(keysym_name: str, modifiers: list = None):
    """Legacy function - calls tap_key for compatibility"""
    if modifiers is None:
        modifiers = []
    tap_key(keysym_name, modifiers)

# ═══════════════════════════════════════════════════════════════════════════════
#  MACRO ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class MacroEngine:
    def __init__(self):
        self._hooks:   dict = {}
        self._held:    dict = {}
        self._firing:  dict = {}
        self._delays:  dict = {}
        self._cbs:     dict = {}
        self._counts:  dict = {}

    def register(self, kid, delay_var, on_start=None, on_stop=None, on_tick=None):
        self.unregister(kid)
        self._delays[kid] = delay_var
        self._held[kid]   = False
        self._firing[kid] = False
        self._counts[kid] = 0
        self._cbs[kid]    = (on_start, on_stop, on_tick)
        if not KB_OK: return
        kname = kid.lower() if len(kid) == 1 else kid_to_kname(kid)
        remap = {
            "Caps_Lock":"caps lock","Shift_L":"left shift","Shift_R":"right shift",
            "Control_L":"left ctrl","Control_R":"right ctrl",
            "Alt_L":"left alt","Alt_R":"right alt",
            "Return":"enter","Escape":"esc",
        }
        kname = remap.get(kname, kname)
        def _press(e):
            if not self._held.get(kid, False):
                self._held[kid] = True
                self._start_fire(kid)
        def _release(e):
            self._held[kid] = False
        try:
            h1 = kb_lib.on_press_key(kname,   _press,   suppress=True)
            h2 = kb_lib.on_release_key(kname, _release, suppress=True)
            self._hooks[kid] = [h1, h2]
        except Exception as ex:
            print(f"[Engine] Hook failed for '{kname}': {ex}")

    def unregister(self, kid):
        self._held[kid]   = False
        self._firing[kid] = False
        if kid in self._hooks and KB_OK:
            for h in self._hooks.pop(kid):
                try: kb_lib.unhook(h)
                except: pass
        for store in (self._delays, self._cbs, self._counts):
            store.pop(kid, None)

    def unregister_all(self):
        for kid in list(self._hooks.keys()):
            self.unregister(kid)
        self._held.clear()
        self._firing.clear()

    def _start_fire(self, kid):
        if self._firing.get(kid): return
        self._firing[kid] = True
        self._counts[kid] = 0
        threading.Thread(target=self._fire_loop, args=(kid,), daemon=True).start()
        cb = self._cbs.get(kid, (None, None, None))
        if cb[0]: cb[0](kid)

    def _fire_loop(self, kid):
        p_name  = kid_to_kname(kid)
        on_stop = self._cbs.get(kid, (None, None, None))[1]
        on_tick = self._cbs.get(kid, (None, None, None))[2]
        
        while self._firing.get(kid) and self._held.get(kid):
            t0 = time.perf_counter()
            try:
                tap_key(p_name)
                self._counts[kid] = self._counts.get(kid, 0) + 1
                if on_tick: on_tick(kid, self._counts[kid])
            except Exception as ex:
                print(f"[Engine] Core Send Error '{p_name}': {ex}")
            target   = self._delays[kid].get() / 1000.0
            deadline = t0 + target
            coarse   = target - 0.0004
            if coarse > 0: time.sleep(coarse)
            while time.perf_counter() < deadline: pass
        self._firing[kid] = False
        if on_stop: on_stop(kid)

# ═══════════════════════════════════════════════════════════════════════════════
#  AHK ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class AHKEngine:
    def __init__(self):
        self._hooks     = []
        self._wine_proc = None
        self._running   = False

    def load_and_run(self, path: str, status_cb=None, log_cb=None):
        self.stop()
        wine_exe = self._find_wine_ahk()
        if wine_exe:
            if log_cb: log_cb("▶ Running via wine + AutoHotkey.exe")
            self._run_wine(path, wine_exe, status_cb, log_cb)
        else:
            if log_cb: log_cb("▶ wine/AutoHotkey not found — using built-in parser\n")
            self._run_parsed(path, status_cb, log_cb)

    def _find_wine_ahk(self):
        if subprocess.run(["which", "wine"], capture_output=True).returncode != 0:
            return None
        for p in [
            os.path.expanduser("~/.wine/drive_c/Program Files/AutoHotkey/AutoHotkey.exe"),
            os.path.expanduser("~/.wine/drive_c/Program Files (x86)/AutoHotkey/AutoHotkey.exe"),
        ]:
            if os.path.exists(p): return p
        return None

    def _run_wine(self, ahk_path, ahk_exe, status_cb, log_cb):
        self._running = True
        def _go():
            try:
                self._wine_proc = subprocess.Popen(
                    ["wine", ahk_exe, ahk_path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                if status_cb: status_cb(True)
                self._wine_proc.wait()
            except Exception as e:
                if log_cb: log_cb(f"wine error: {e}")
            finally:
                self._running = False
                if status_cb: status_cb(False)
        threading.Thread(target=_go, daemon=True).start()

    def _run_parsed(self, path: str, status_cb, log_cb):
        if not KB_OK:
            if log_cb: log_cb("⚠ keyboard library not available — run with sudo")
            return
        try:
            content = open(path, encoding="utf-8", errors="ignore").read()
        except Exception as e:
            if log_cb: log_cb(f"Cannot read file: {e}"); return
        hotkeys = self._parse_hotkeys(content)
        if not hotkeys:
            if log_cb: log_cb("⚠ No supported hotkeys found in file"); return
        for combo, actions in hotkeys:
            def _make_cb(acts):
                def _cb():
                    threading.Thread(target=self._exec_actions,
                                     args=(acts, log_cb), daemon=True).start()
                return _cb
            try:
                h = kb_lib.add_hotkey(combo, _make_cb(actions), suppress=False)
                self._hooks.append(h)
                if log_cb: log_cb(f"  ✓ {combo}")
            except Exception as ex:
                if log_cb: log_cb(f"  ✗ {combo} — {ex}")
        self._running = True
        if status_cb: status_cb(True)
        if log_cb: log_cb(f"\n{len(hotkeys)} hotkey(s) active.")

    def _parse_hotkeys(self, content: str):
        hotkeys, lines, i = [], content.splitlines(), 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith(';'):
                i += 1; continue
            m = re.match(r'^([+^!#]*)([^:\s][^:]*)::(.*)', line)
            if m:
                mods_str = m.group(1)
                key      = m.group(2).strip()
                action   = m.group(3).strip()
                combo = self._build_combo(mods_str, key)
                if combo:
                    if action == '':
                        block, i = [], i + 1
                        while i < len(lines):
                            bl = lines[i].strip()
                            if bl.lower() == 'return': break
                            if bl and not bl.startswith(';'): block.append(bl)
                            i += 1
                        acts = self._parse_actions(block)
                    else:
                        acts = self._parse_actions([action])
                    if acts:
                        hotkeys.append((combo, acts))
            i += 1
        return hotkeys

    def _build_combo(self, mods_str: str, key: str):
        parts = [AHK_MOD_MAP[ch] for ch in mods_str if ch in AHK_MOD_MAP]
        kl = key.lower()
        if kl in AHK_SPECIAL_KEYS:
            parts.append(AHK_SPECIAL_KEYS[kl].lower())
        elif len(key) == 1:
            parts.append(key.lower())
        else:
            return None
        return '+'.join(parts) if parts else None

    def _parse_actions(self, lines: list):
        actions = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'): continue
            m = re.match(r'^[Ss]end[,\s]+(.+)', line)
            if m: actions.append(('send',   m.group(1).strip())); continue
            m = re.match(r'^[Ss]leep[,\s]+(\d+)', line)
            if m: actions.append(('sleep',  int(m.group(1)))); continue
            m = re.match(r'^[Mm]sg[Bb]ox[,\s]*(.*)', line)
            if m: actions.append(('msgbox', m.group(1).strip()))
        return actions

    def _exec_actions(self, actions, log_cb=None):
        for kind, val in actions:
            if   kind == 'send':   self._exec_send(val)
            elif kind == 'sleep':  time.sleep(val / 1000.0)
            elif kind == 'msgbox':
                if log_cb: log_cb(f"[MsgBox] {val}")

    def _exec_send(self, text: str):
        i = 0
        while i < len(text):
            if text[i] == '{':
                end = text.find('}', i)
                if end != -1:
                    kn   = text[i+1:end].lower()
                    ksym = AHK_SPECIAL_KEYS.get(kn, kn.capitalize())
                    tap_key(ksym)
                    i = end + 1; continue
            ch = text[i]
            if   ch == '\n':                    tap_key("return")
            elif ch == ' ':                     tap_key("space")
            elif ch.isupper():                  tap_key(ch.lower(), ["shift"])
            elif ch.isalpha() or ch.isdigit():  tap_key(ch.lower())
            i += 1

    def stop(self):
        self._running = False
        if self._wine_proc:
            try: self._wine_proc.terminate()
            except: pass
            self._wine_proc = None
        if KB_OK:
            for h in self._hooks:
                try: kb_lib.remove_hotkey(h)
                except: pass
        self._hooks.clear()

# ═══════════════════════════════════════════════════════════════════════════════
#  MOUSE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class MouseEngine:
    POLLING_RATES = [125, 250, 500, 1000, 2000, 4000, 8000]
    KNOWN_MICE = {
        "logitech": ["G102","G203","G305","G403","G502","G Pro","G703","G903"],
        "razer":    ["DeathAdder","Viper","Basilisk","Naga","Mamba","Orochi"],
        "steelseries": ["Rival 3","Rival 5","Rival 600","Aerox","Prime"],
        "corsair":  ["M65","Harpoon","Ironclaw","Katar","Scimitar"],
        "generic":  [],
    }

    def __init__(self, app_ref):
        self._app            = app_ref
        self._mice           = []
        self._selected_id    = None
        self._selected_name  = ""
        self._button_remaps  = {}       # {btn_name: (type, value, label)}
        self._has_ratbag     = self._check_tool("ratbagctl")
        self._has_xinput     = self._check_tool("xinput")
        self._remap_listener = None
        self._listening_btn  = False
        self._listen_cb      = None
        self._mice_cache     = None     # Cache mice list
        self._mice_cache_time = 0       # Timestamp of last detection

    def _check_tool(self, tool):
        # Check common installation paths
        common_paths = [
            f"/usr/local/bin/{tool}",
            f"/usr/bin/{tool}",
            f"/bin/{tool}",
        ]
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return True
        # Fallback to PATH lookup
        return subprocess.run(["which", tool], capture_output=True).returncode == 0

    # ── Detection ─────────────────────────────────────────────────────────────────
    def detect_mice(self):
        """Detect mice with caching to reduce subprocess calls"""
        import time
        current_time = time.time()
        # Return cached result if within 2 seconds
        if self._mice_cache is not None and (current_time - self._mice_cache_time) < 2:
            return self._mice_cache
        
        mice = []
        if self._has_xinput:
            try:
                out = subprocess.run(["xinput", "list", "--short"],
                                     capture_output=True, text=True, timeout=2).stdout
                for line in out.splitlines():
                    if "slave  pointer" not in line.lower(): continue
                    m = re.search(r'(.+?)\s+id=(\d+)', line)
                    if not m: continue
                    name, dev_id = m.group(1).strip(), m.group(2)
                    skip = ["virtual","xtest","keyboard","touchpad","tablet","stylus"]
                    if any(s in name.lower() for s in skip): continue
                    brand  = self._detect_brand(name)
                    model  = self._detect_model(name, brand)
                    n_btns = self._get_button_count(dev_id)
                    mice.append({
                        "name": name, "id": dev_id,
                        "brand": brand, "model": model,
                        "buttons": n_btns,
                    })
            except Exception as e:
                pass  # Silently fail, return cached or empty
        
        self._mice = mice
        self._mice_cache = mice
        self._mice_cache_time = current_time
        return mice

    def _detect_brand(self, name: str) -> str:
        nl = name.lower()
        for brand in self.KNOWN_MICE:
            if brand in nl: return brand.capitalize()
        return "Generic"

    def _detect_model(self, name: str, brand: str) -> str:
        nl = name.lower()
        for model in self.KNOWN_MICE.get(brand.lower(), []):
            if model.lower() in nl: return model
        # Try to extract model from name after brand
        words = name.split()
        return " ".join(words[1:]) if len(words) > 1 else name

    def _get_button_count(self, dev_id: str) -> int:
        try:
            out = subprocess.run(
                ["xinput", "get-button-map", dev_id],
                capture_output=True, text=True).stdout
            return len(out.strip().split())
        except Exception:
            return 3

    # ── Hardware control (libratbag) ──────────────────────────────────────────
    def get_dpi(self) -> int | None:
        if not self._has_ratbag or not self._selected_name: return None
        try:
            out = subprocess.run(
                ["ratbagctl", self._selected_name, "dpi", "get"],
                capture_output=True, text=True, timeout=2).stdout
            m = re.search(r'(\d+)', out)
            return int(m.group(1)) if m else None
        except Exception:
            return None

    def set_dpi(self, dpi: int) -> bool:
        if not self._has_ratbag or not self._selected_name: return False
        try:
            subprocess.run(
                ["ratbagctl", self._selected_name, "dpi", "set", str(dpi)],
                capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    def get_polling_rate(self) -> int | None:
        if not self._has_ratbag or not self._selected_name: return None
        try:
            out = subprocess.run(
                ["ratbagctl", self._selected_name, "rate", "get"],
                capture_output=True, text=True, timeout=2).stdout
            m = re.search(r'(\d+)', out)
            return int(m.group(1)) if m else None
        except Exception:
            return None

    def set_polling_rate(self, rate: int) -> bool:
        if not self._has_ratbag or not self._selected_name: return False
        try:
            subprocess.run(
                ["ratbagctl", self._selected_name, "rate", "set", str(rate)],
                capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    # ── Button listen (single-capture for remapping UI) ───────────────────────
    def start_listen(self, callback):
        if not PYNPUT_OK: return False
        self._listening_btn = True
        self._listen_cb = callback
        def _on_click(x, y, btn, pressed):
            if self._listening_btn and pressed:
                self._listening_btn = False
                if self._listen_cb:
                    self._listen_cb(str(btn).replace("Button.", ""))
                return False
        try:
            l = pynput_mouse.Listener(on_click=_on_click)
            l.daemon = True
            l.start()
        except Exception:
            return False
        return True

    def stop_listen(self):
        self._listening_btn = False

    # ── Remap persistence ─────────────────────────────────────────────────────
    def save_remaps(self):
        try:
            with open(MOUSE_CONFIG_FILE, "w") as f:
                json.dump(self._button_remaps, f, indent=2)
        except Exception as e:
            print(f"[Mouse] Save error: {e}")

    def load_remaps(self):
        try:
            with open(MOUSE_CONFIG_FILE) as f:
                self._button_remaps = json.load(f)
        except Exception:
            pass

    # ── Apply all remaps (persistent listener) ────────────────────────────────
    def apply_remaps(self):
        if not PYNPUT_OK or not self._button_remaps: return False
        self._stop_remap_listener()
        def _on_click(x, y, btn, pressed):
            if not pressed: return True
            bname = str(btn).replace("Button.", "")
            if bname not in self._button_remaps: return True
            rtype, rval, _ = self._button_remaps[bname]
            def _exec():
                if rtype == "key":
                    x11_tap_key(rval)
                elif rtype == "macro" and self._app:
                    eng = self._app.engine
                    if rval in self._app._delay_vars:
                        if not eng._firing.get(rval):
                            eng._held[rval] = True
                            eng._start_fire(rval)
                            time.sleep(0.05)
                            eng._held[rval] = False
                elif rtype == "ahk" and self._app:
                    self._app.ahk_engine.load_and_run(rval)
            threading.Thread(target=_exec, daemon=True).start()
            return False  # suppress original click
        try:
            self._remap_listener = pynput_mouse.Listener(on_click=_on_click)
            self._remap_listener.daemon = True
            self._remap_listener.start()
            return True
        except Exception:
            return False

    def _stop_remap_listener(self):
        if self._remap_listener:
            try: self._remap_listener.stop()
            except: pass
            self._remap_listener = None

    def stop(self):
        self.stop_listen()
        self._stop_remap_listener()

# ═══════════════════════════════════════════════════════════════════════════════
#  APPLICATION GUI
# ═══════════════════════════════════════════════════════════════════════════════
class RapidFireApp:
    UNIT  = 45
    GAP   = 3
    KEY_H = 38

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Rapid-Fire Macro Pro")
        self.root.configure(bg=C["bg"])
        self.root.resizable(False, False)

        self.engine      = MacroEngine()
        self.ahk_engine  = AHKEngine()
        self.mouse_engine = MouseEngine(self)
        self.profiles    = load_profiles()
        self.active_prof = list(self.profiles)[0]
        self._btn_reg:    dict = {}
        self._delay_vars: dict = {}
        self._cards:      dict = {}
        
        # ── Animation & Resource Optimization ──────────────────────────────
        self._animation_state = {}  # Track animation states
        self._update_pending = False  # Debounce UI updates
        self._pulse_cycle = 0  # Animation frame counter

        self._build_header()
        self._build_nav()

        self._macro_page = tk.Frame(self.root, bg=C["bg"])
        self._ahk_page   = tk.Frame(self.root, bg=C["bg"])
        self._mouse_page = tk.Frame(self.root, bg=C["bg"])

        self._build_macro_content(self._macro_page)
        self._build_ahk_content(self._ahk_page)
        self._build_mouse_content(self._mouse_page)

        self.mouse_engine.load_remaps()
        self._load_profile(self.active_prof, initial=True)
        self._show_page("macro")

    # ── Header ───────────────────────────────────────────────────────────────
    def _build_header(self):
        hf = tk.Frame(self.root, bg=C["surface"])
        hf.pack(fill="x", padx=0, pady=0)
        left = tk.Frame(hf, bg=C["surface"])
        left.pack(side="left", padx=16, pady=12)
        tk.Label(left, text="⌨", font=("Segoe UI Emoji", 22),
                 bg=C["surface"], fg=C["accent"]).pack(side="left")
        title_text = "RAPID-FIRE MACRO PRO"
        if IS_WINDOWS:
            title_text += " [Windows]"
        elif IS_MACOS:
            title_text += " [macOS]"
        elif IS_LINUX:
            title_text += " [Linux]"
        tk.Label(left, text="  " + title_text,
                 font=("Segoe UI", 13, "bold"),
                 bg=C["surface"], fg=C["text"]).pack(side="left")
        right = tk.Frame(hf, bg=C["surface"])
        right.pack(side="right", padx=16, pady=12)
        
        # Platform-specific status
        if IS_LINUX:
            if X11_OK:
                dot, msg, col = ("●", "X11 Direct ✓", C["green"])
            elif KB_OK:
                dot, msg, col = ("●", f"{KB_LIB_NAME.title()} ✓", C["green"])
            else:
                dot, msg, col = ("✕", "No input", C["danger"])
        elif IS_WINDOWS:
            if KB_OK:
                dot, msg, col = ("●", f"Windows {KB_LIB_NAME.title()} ✓", C["green"])
            else:
                dot, msg, col = ("✕", "No input", C["danger"])
        elif IS_MACOS:
            if KB_OK:
                dot, msg, col = ("●", f"macOS {KB_LIB_NAME.title()} ✓", C["green"])
            else:
                dot, msg, col = ("✕", "No input", C["danger"])
        else:
            dot, msg, col = ("?", "Unknown", C["muted"])
        
        tk.Label(right, text=f"{dot} {msg}",
                 font=("Segoe UI", 8), bg=C["surface"], fg=col).pack()

    # ── Top page navigation ───────────────────────────────────────────────────
    def _build_nav(self):
        nf = tk.Frame(self.root, bg=C["bg"])
        nf.pack(fill="x", padx=0, pady=0)
        self._nav_btns = {}
        for name, label in [("macro", "⌨  MACROS"), ("ahk", "📜  AUTOHOTKEY"), ("mouse", "🖱  MOUSE")]:
            btn = tk.Button(
                nf, text=label,
                font=("Segoe UI", 10, "bold"),
                bg=C["tab_in"], fg=C["text"],
                relief="flat", bd=0, cursor="hand2",
                padx=18, pady=10,
                command=lambda n=name: self._show_page(n),
                activebackground=C["sel_bg"], activeforeground=C["text"]
            )
            btn.pack(side="left", padx=6, pady=8)
            self._nav_btns[name] = btn

    def _show_page(self, name: str):
        """Switch pages with smooth animation"""
        # Fade out all pages
        self._macro_page.pack_forget()
        self._ahk_page.pack_forget()
        self._mouse_page.pack_forget()
        
        # Show target page with slight delay for smooth transition
        def _show():
            if name == "macro":
                self._macro_page.pack(fill="both", expand=True)
            elif name == "ahk":
                self._ahk_page.pack(fill="both", expand=True)
            elif name == "mouse":
                self._mouse_page.pack(fill="both", expand=True)
            
            # Animate button colors
            for n, btn in self._nav_btns.items():
                active = (n == name)
                btn.config(bg=C["sel_bg"] if active else C["tab_in"],
                           fg=C["sel_fg"] if active else C["text"])
        
        # Smooth transition with 50ms delay
        self.root.after(50, _show)

    # ═════════════════════════════════════════════════════════════════════════
    #  MACRO PAGE
    # ═════════════════════════════════════════════════════════════════════════
    def _build_macro_content(self, parent):
        self._build_profile_bar(parent)
        self._build_keyboard(parent)
        tk.Frame(parent, bg=C["key_bdr"], height=1).pack(fill="x", padx=14, pady=(8, 0))
        self._build_cards_area(parent)

    def _build_profile_bar(self, parent):
        outer = tk.Frame(parent, bg=C["surface"], highlightthickness=0)
        outer.pack(fill="x", padx=12, pady=(8, 0))
        self._tab_bar = tk.Frame(outer, bg=C["surface"])
        self._tab_bar.pack(fill="x", padx=4, pady=8)
        self._refresh_tabs()

    def _refresh_tabs(self):
        for w in self._tab_bar.winfo_children(): w.destroy()
        tk.Label(self._tab_bar, text="PROFILES:",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["surface"], fg=C["text"]).pack(side="left", padx=(0, 12))
        for name in self.profiles: self._make_tab(name)
        tk.Button(self._tab_bar, text="+ New",
                  font=("Segoe UI", 9), bg=C["sel_bg"], fg=C["text"],
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                  command=self._add_profile).pack(side="left", padx=4)

    def _make_tab(self, name: str):
        active = (name == self.active_prof)
        frm = tk.Frame(self._tab_bar,
                       bg=C["sel_bg"] if active else C["tab_in"],
                       highlightthickness=0)
        frm.pack(side="left", padx=3, pady=0)
        tk.Button(frm, text=f"  {name}  ",
                  font=("Segoe UI", 9, "bold" if active else "normal"),
                  bg=C["sel_bg"] if active else C["tab_in"],
                  fg=C["text"] if active else C["text"],
                  relief="flat", bd=0, cursor="hand2", pady=4,
                  command=lambda n=name: self._switch_profile(n)).pack(side="left")
        if len(self.profiles) > 1:
            tk.Button(frm, text="✕",
                      font=("Segoe UI", 8),
                      bg=C["sel_bg"] if active else C["tab_in"],
                      fg=C["danger"], relief="flat", bd=0, cursor="hand2", pady=4,
                      command=lambda n=name: self._delete_profile(n)
                      ).pack(side="left", padx=(0, 2))

    def _build_keyboard(self, parent):
        outer = tk.Frame(parent, bg=C["surface"],
                         highlightthickness=0)
        outer.pack(padx=12, pady=(8, 0))
        kb_f = tk.Frame(outer, bg=C["surface"], padx=8, pady=8)
        kb_f.pack()
        for row in LAYOUT:
            rf = tk.Frame(kb_f, bg=C["surface"])
            rf.pack(anchor="w", pady=self.GAP // 2)
            for label, kid, w in row:
                px_w = int(self.UNIT * float(w) + self.GAP * max(0, float(w) - 1))
                if kid == "":
                    tk.Frame(rf, bg=C["surface"], width=px_w,
                             height=self.KEY_H).pack(side="left", padx=self.GAP // 2)
                    continue
                btn = tk.Button(rf, text=label,
                                font=("Segoe UI", 8, "bold"),
                                bg=C["key_bg"], fg=C["key_fg"],
                                activebackground=C["sel_bg"],
                                activeforeground=C["sel_fg"],
                                relief="flat", bd=0, cursor="hand2",
                                padx=2, pady=2,
                                command=lambda k=kid, lbl=label: self._on_key_click(k, lbl))
                btn.pack(side="left", padx=self.GAP // 2)
                btn.config(width=int(self.UNIT / 6 * float(w)), height=2)
                self._btn_reg.setdefault(kid, []).append(btn)

    def _build_cards_area(self, parent):
        hdr = tk.Frame(parent, bg=C["bg"])
        hdr.pack(fill="x", padx=16, pady=(8, 2))
        tk.Label(hdr, text="ACTIVE KEYS",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(side="left")
        self._count_lbl = tk.Label(hdr, text="(none)",
                                   font=("Segoe UI", 8),
                                   bg=C["bg"], fg=C["muted"])
        self._count_lbl.pack(side="left", padx=10)
        tk.Button(hdr, text="💾 Save",
                  font=("Segoe UI", 9, "bold"), bg=C["sel_bg"], fg=C["text"],
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=3,
                  command=self._manual_save).pack(side="right")

        cf = tk.Frame(parent, bg=C["bg"])
        cf.pack(fill="x", padx=12, pady=(0, 12))
        self._canvas = tk.Canvas(cf, bg=C["bg"], bd=0,
                                 highlightthickness=0, height=150)
        sb = ttk.Scrollbar(cf, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._cards_host = tk.Frame(self._canvas, bg=C["bg"])
        self._cw = self._canvas.create_window((0, 0), window=self._cards_host, anchor="nw")
        self._cards_host.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._cw, width=e.width))

    def _show_idle_hint(self):
        pass  # Idle hint removed

    # ── Animation Helpers ──────────────────────────────────────────────────
    def _pulse_animation(self, widget, firing: bool):
        """Pulsing color animation for active macro indicators"""
        if not firing:
            widget.config(fg=C["muted"])
            return
        
        # Pulse effect: cycle through colors
        self._pulse_cycle = (self._pulse_cycle + 1) % 6
        if self._pulse_cycle < 3:
            widget.config(fg=C["fire"])
        else:
            widget.config(fg=C["accent"])
        
        if firing:
            self.root.after(200, lambda: self._pulse_animation(widget, firing))

    def _fade_in_widget(self, widget, target_color, steps=5):
        """Smooth fade-in animation for new widgets"""
        def _fade(step=0):
            if step < steps:
                # Interpolate color smoothly
                alpha = step / steps
                widget.config(bg=self._interpolate_color(C["panel"], target_color, alpha))
                self.root.after(30, lambda: _fade(step + 1))
        _fade()

    def _interpolate_color(self, color1: str, color2: str, alpha: float) -> str:
        """Interpolate between two hex colors"""
        c1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        c = tuple(int(c1[i] * (1-alpha) + c2[i] * alpha) for i in range(3))
        return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"

    def _add_card(self, kid: str, label: str):
        delay_var = self._delay_vars[kid]
        card = tk.Frame(self._cards_host, bg=C["card"], highlightthickness=0)
        card.pack(fill="x", padx=8, pady=6)

        # Key badge
        bdg = tk.Frame(card, bg=C["sel_bg"], highlightthickness=0)
        bdg.pack(side="left", padx=(12, 8), pady=10)
        tk.Label(bdg, text=f" {label} ",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["sel_bg"], fg=C["sel_fg"], padx=6, pady=3).pack()

        # Delay slider
        sl_f = tk.Frame(card, bg=C["card"])
        sl_f.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        val_lbl = tk.Label(sl_f, text=f"{delay_var.get():>4} ms",
                           font=("Segoe UI", 9, "bold"),
                           bg=C["card"], fg=C["accent"], width=9)

        def _on_slide(v, vl=val_lbl, dv=delay_var):
            iv = max(1, int(float(v)))
            dv.set(iv)
            vl.config(text=f"{iv:>4} ms")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("K.Horizontal.TScale",
                        background=C["card"], troughcolor=C["panel"], sliderlength=16)
        sl = ttk.Scale(sl_f, from_=1, to=1000, orient="horizontal",
                       variable=delay_var, style="K.Horizontal.TScale", command=_on_slide)
        sl.pack(side="left", fill="x", expand=True)
        val_lbl.pack(side="left", padx=(8, 0))

        # Status indicator
        status_lbl = tk.Label(card, text="● IDLE",
                              font=("Segoe UI", 8, "bold"),
                              bg=C["card"], fg=C["muted"], width=9)
        status_lbl.pack(side="left", padx=8)
        
        # Count
        count_lbl = tk.Label(card, text="0×",
                             font=("Segoe UI", 8), bg=C["card"], fg=C["text"], width=5)
        count_lbl.pack(side="left")

        # Remove button
        tk.Button(card, text="✕", font=("Segoe UI", 9),
                  bg=C["card"], fg=C["danger"], relief="flat", bd=0,
                  cursor="hand2", padx=10, pady=8,
                  command=lambda k=kid: self._remove_key(k)
                  ).pack(side="right", padx=12)
        
        self._cards[kid] = {"frame": card, "status": status_lbl, "count": count_lbl}

    def _remove_card(self, kid: str):
        if kid in self._cards:
            self._cards[kid]["frame"].destroy()
            del self._cards[kid]

    def _refresh_count(self):
        n = len(self._delay_vars)
        self._count_lbl.config(
            text=f"({n} key{'s' if n != 1 else ''} active)" if n else "(none)")

    def _on_key_click(self, kid: str, raw_label: str):
        label = clean_label(raw_label) or kid.upper()
        if kid in self._delay_vars:
            self._remove_key(kid)
        else:
            init = self.profiles.get(self.active_prof, {}).get(kid, 5)
            var  = tk.IntVar(value=init)
            self._delay_vars[kid] = var
            children = self._cards_host.winfo_children()
            if len(children) == 1 and isinstance(children[0], tk.Label):
                children[0].destroy()
            self._add_card(kid, label)
            self._highlight(kid, True)
            self.engine.register(
                kid, var,
                lambda k: self.root.after(0, lambda: self._card_status(k, True)),
                lambda k: self.root.after(0, lambda: self._card_status(k, False)),
                lambda k, c: self.root.after(0, lambda: self._card_count(k, c))
            )
            self._refresh_count()

    def _remove_key(self, kid: str):
        self.engine.unregister(kid)
        self._remove_card(kid)
        self._delay_vars.pop(kid, None)
        self._highlight(kid, False)
        self._refresh_count()

    def _highlight(self, kid: str, on: bool):
        for btn in self._btn_reg.get(kid, []):
            btn.config(bg=C["sel_bg"] if on else C["key_bg"],
                       fg=C["sel_fg"] if on else C["key_fg"])

    def _card_status(self, kid: str, firing: bool):
        c = self._cards.get(kid)
        if c:
            c["status"].config(text="● FIRE" if firing else "○ IDLE")
            self._pulse_animation(c["status"], firing)

    def _card_count(self, kid: str, count: int):
        c = self._cards.get(kid)
        if c: 
            # Debounce updates: only update every 10 calls to reduce CPU usage
            if not hasattr(c, "_count_skip"):
                c["_count_skip"] = 0
            c["_count_skip"] += 1
            if c["_count_skip"] >= 10:
                c["count"].config(text=f"{count:,}×")
                c["_count_skip"] = 0

    def _snapshot_profile(self):
        self.profiles[self.active_prof] = {k: v.get() for k, v in self._delay_vars.items()}

    def _manual_save(self):
        self._snapshot_profile()
        save_profiles(self.profiles)

    def _clear_all_keys(self):
        self.engine.unregister_all()
        for kid in list(self._delay_vars.keys()):
            self._highlight(kid, False)
            self._remove_card(kid)
        self._delay_vars.clear()

    def _load_profile(self, name: str, initial: bool = False):
        if not initial:
            self._snapshot_profile()
            save_profiles(self.profiles)
        self._clear_all_keys()
        self.active_prof = name
        saved = self.profiles.get(name, {})
        if saved:
            for w in self._cards_host.winfo_children(): w.destroy()
            for kid, delay in saved.items():
                label = self._kid_label(kid)
                var   = tk.IntVar(value=delay)
                self._delay_vars[kid] = var
                self._add_card(kid, label)
                self._highlight(kid, True)
                self.engine.register(
                    kid, var,
                    lambda k: self.root.after(0, lambda: self._card_status(k, True)),
                    lambda k: self.root.after(0, lambda: self._card_status(k, False)),
                    lambda k, c: self.root.after(0, lambda: self._card_count(k, c))
                )
        self._refresh_count()
        self._refresh_tabs()

    def _kid_label(self, kid: str) -> str:
        for row in LAYOUT:
            for lbl, k, _ in row:
                if k == kid: return clean_label(lbl) or kid.upper()
        return kid.upper()

    def _switch_profile(self, name: str):
        if name != self.active_prof: self._load_profile(name)

    def _add_profile(self):
        name = simpledialog.askstring("New Profile", "Profile name:", parent=self.root)
        if not name or not name.strip(): return
        name = name.strip()
        if name in self.profiles: return
        self.profiles[name] = {}
        save_profiles(self.profiles)
        self._switch_profile(name)

    def _delete_profile(self, name: str):
        if len(self.profiles) <= 1: return
        if not messagebox.askyesno("Delete", f'Delete profile "{name}"?', parent=self.root): return
        was_active = (name == self.active_prof)
        del self.profiles[name]
        save_profiles(self.profiles)
        if was_active: self._load_profile(list(self.profiles)[0])
        else: self._refresh_tabs()

    # ═════════════════════════════════════════════════════════════════════════
    #  AHK PAGE
    # ═════════════════════════════════════════════════════════════════════════
    def _build_ahk_content(self, parent):
        self._ahk_file_path = None

        # Drop zone
        drop_outer = tk.Frame(parent, bg=C["panel"], highlightthickness=0)
        drop_outer.pack(fill="x", padx=12, pady=(12, 0))
        self._ahk_drop_lbl = tk.Label(
            drop_outer,
            text="📂  Drop AutoHotkey file here  or  click Browse",
            font=("Segoe UI", 10), bg=C["panel"], fg=C["text"],
            pady=20, padx=16
        )
        self._ahk_drop_lbl.pack(fill="x")
        if DND_OK:
            self._ahk_drop_lbl.drop_target_register(DND_FILES)
            self._ahk_drop_lbl.dnd_bind('<<Drop>>', self._ahk_on_drop)

        # Buttons
        btn_f = tk.Frame(parent, bg=C["bg"])
        btn_f.pack(fill="x", padx=12, pady=(8, 0))
        tk.Button(btn_f, text="📂 Browse",
                  font=("Segoe UI", 9, "bold"),
                  bg=C["sel_bg"], fg=C["text"],
                  relief="flat", bd=0, cursor="hand2", padx=14, pady=6,
                  command=self._ahk_browse).pack(side="left", padx=(0, 8))
        self._ahk_run_btn = tk.Button(
            btn_f, text="▶ Run",
            font=("Segoe UI", 9, "bold"),
            bg=C["green"], fg="#ffffff", activebackground=C["green_hi"],
            relief="flat", bd=0, cursor="hand2", padx=14, pady=6,
            state="disabled", command=self._ahk_run)
        self._ahk_run_btn.pack(side="left", padx=(0, 8))
        self._ahk_stop_btn = tk.Button(
            btn_f, text="■ Stop",
            font=("Segoe UI", 9, "bold"),
            bg=C["danger"], fg="#ffffff",
            relief="flat", bd=0, cursor="hand2", padx=14, pady=6,
            state="disabled", command=self._ahk_stop)
        self._ahk_stop_btn.pack(side="left")
        self._ahk_status_lbl = tk.Label(
            btn_f, text="No file loaded",
            font=("Segoe UI", 8), bg=C["bg"], fg=C["muted"])
        self._ahk_status_lbl.pack(side="right", padx=8)

        # Info
        tk.Label(parent,
                 text="Supports: ^!+# modifiers · Send · Sleep · MsgBox  │  wine+AutoHotkey auto-detected",
                 font=("Segoe UI", 8), bg=C["bg"], fg=C["muted"],
                 wraplength=820, justify="left"
                 ).pack(anchor="w", padx=14, pady=(4, 0))

        # Log / preview
        log_f = tk.Frame(parent, bg=C["bg"])
        log_f.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        tk.Label(log_f, text="FILE PREVIEW  /  LOG",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w", pady=(0, 4))
        txt_wrap = tk.Frame(log_f, bg=C["panel"], highlightthickness=0)
        txt_wrap.pack(fill="both", expand=True)
        self._ahk_log = tk.Text(
            txt_wrap, font=("Segoe UI", 9),
            bg=C["panel"], fg=C["text"],
            insertbackground=C["accent"],
            relief="flat", bd=0, wrap="word", height=12, state="disabled")
        sb = ttk.Scrollbar(txt_wrap, command=self._ahk_log.yview)
        self._ahk_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._ahk_log.pack(fill="both", expand=True, padx=8, pady=8)

    def _ahk_log_write(self, text: str):
        def _do():
            self._ahk_log.config(state="normal")
            self._ahk_log.insert("end", text + "\n")
            self._ahk_log.see("end")
            self._ahk_log.config(state="disabled")
        self.root.after(0, _do)

    def _ahk_set_file(self, path: str):
        path = path.strip().strip('{}')
        if not path.lower().endswith('.ahk'):
            self._ahk_log_write(f"⚠ Not an .ahk file: {os.path.basename(path)}")
            return
        self._ahk_file_path = path
        self._ahk_drop_lbl.config(text=f"📄  {os.path.basename(path)}\n    {path}")
        self._ahk_run_btn.config(state="normal")
        self._ahk_status_lbl.config(text="Ready", fg=C["text"])
        try:
            content = open(path, encoding="utf-8", errors="ignore").read()
            self._ahk_log.config(state="normal")
            self._ahk_log.delete("1.0", "end")
            self._ahk_log.insert("end", content)
            self._ahk_log.config(state="disabled")
        except Exception as e:
            self._ahk_log_write(f"Cannot read: {e}")

    def _ahk_on_drop(self, event):
        self._ahk_set_file(event.data)

    def _ahk_browse(self):
        path = filedialog.askopenfilename(
            title="Select AutoHotkey file",
            filetypes=[("AutoHotkey files", "*.ahk"), ("All files", "*.*")])
        if path: self._ahk_set_file(path)

    def _ahk_run(self):
        if not self._ahk_file_path: return
        self._ahk_log.config(state="normal")
        self._ahk_log.delete("1.0", "end")
        self._ahk_log.config(state="disabled")
        self._ahk_log_write(f"Loading: {self._ahk_file_path}\n")
        self._ahk_run_btn.config(state="disabled")
        self._ahk_stop_btn.config(state="normal")
        self.ahk_engine.load_and_run(
            self._ahk_file_path,
            status_cb=lambda r: self.root.after(0, lambda: self._ahk_status_update(r)),
            log_cb=self._ahk_log_write)

    def _ahk_stop(self):
        self.ahk_engine.stop()
        self._ahk_status_update(False)
        self._ahk_log_write("■ Stopped.")

    def _ahk_status_update(self, running: bool):
        if running:
            self._ahk_status_lbl.config(text="● Running", fg=C["green"])
            self._ahk_run_btn.config(state="disabled")
            self._ahk_stop_btn.config(state="normal")
        else:
            self._ahk_status_lbl.config(text="■ Stopped", fg=C["muted"])
            self._ahk_run_btn.config(state="normal")
            self._ahk_stop_btn.config(state="disabled")

    # ═════════════════════════════════════════════════════════════════════════
    #  MOUSE PAGE
    # ═════════════════════════════════════════════════════════════════════════
    def _build_mouse_content(self, parent):
        # Header
        hdr = tk.Frame(parent, bg=C["bg"])
        hdr.pack(fill="x", padx=14, pady=(12, 8))
        tk.Label(hdr, text="🖱  MOUSE SETTINGS",
                 font=("Segoe UI", 12, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w")

        # ── Mouse Selection ────────────────────────────────────────────────
        sel_f = tk.Frame(parent, bg=C["panel"], highlightthickness=0)
        sel_f.pack(fill="x", padx=12, pady=(0, 10))
        
        tk.Label(sel_f, text="SELECT MOUSE",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=10, pady=(8, 4))
        
        btn_f = tk.Frame(sel_f, bg=C["panel"])
        btn_f.pack(fill="x", padx=10, pady=(0, 8))
        tk.Button(btn_f, text="🔄 Refresh",
                  font=("Segoe UI", 8), bg=C["sel_bg"], fg=C["text"],
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                  command=self._refresh_mice_list).pack(side="left", padx=(0, 8))
        
        self._mouse_dropdown = ttk.Combobox(btn_f, state="readonly",
                                            font=("Segoe UI", 9), width=40)
        self._mouse_dropdown.pack(side="left", fill="x", expand=True)
        self._mouse_dropdown.bind("<<ComboboxSelected>>", lambda e: self._on_mouse_selected())

        # ── DPI Control ────────────────────────────────────────────────────
        dpi_f = tk.Frame(parent, bg=C["panel"], highlightthickness=0)
        dpi_f.pack(fill="x", padx=12, pady=(0, 10))
        
        tk.Label(dpi_f, text="DPI SETTINGS",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=10, pady=(8, 4))
        
        dpi_ctrl = tk.Frame(dpi_f, bg=C["panel"])
        dpi_ctrl.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(dpi_ctrl, text="Current DPI:",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["text"]).pack(side="left")
        self._dpi_val_lbl = tk.Label(dpi_ctrl, text="—",
                                     font=("Segoe UI", 9, "bold"),
                                     bg=C["panel"], fg=C["accent"])
        self._dpi_val_lbl.pack(side="left", padx=10)
        
        dpi_input = tk.Frame(dpi_ctrl, bg=C["panel"])
        dpi_input.pack(side="left", padx=(20, 0))
        tk.Label(dpi_input, text="Set to:",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["text"]).pack(side="left")
        self._dpi_entry = tk.Entry(dpi_input, font=("Segoe UI", 9), width=8, state="disabled")
        self._dpi_entry.pack(side="left", padx=6)
        self._dpi_apply_btn = tk.Button(dpi_input, text="Apply",
                  font=("Segoe UI", 8), bg=C["sel_bg"], fg=C["text"],
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=2,
                  state="disabled",
                  command=self._apply_dpi)
        self._dpi_apply_btn.pack(side="left")

        # ── Polling Rate Control ───────────────────────────────────────────
        rate_f = tk.Frame(parent, bg=C["panel"], highlightthickness=0)
        rate_f.pack(fill="x", padx=12, pady=(0, 10))
        
        tk.Label(rate_f, text="POLLING RATE",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=10, pady=(8, 4))
        
        rate_ctrl = tk.Frame(rate_f, bg=C["panel"])
        rate_ctrl.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(rate_ctrl, text="Current:",
                 font=("Segoe UI", 9), bg=C["panel"], fg=C["text"]).pack(side="left")
        self._rate_val_lbl = tk.Label(rate_ctrl, text="—",
                                      font=("Segoe UI", 9, "bold"),
                                      bg=C["panel"], fg=C["accent"])
        self._rate_val_lbl.pack(side="left", padx=10)
        
        rate_input = tk.Frame(rate_ctrl, bg=C["panel"])
        rate_input.pack(side="left", padx=(20, 0))
        self._rate_dropdown = ttk.Combobox(rate_input, values=self.mouse_engine.POLLING_RATES,
                                           state="disabled", font=("Segoe UI", 9), width=12)
        self._rate_dropdown.pack(side="left")
        self._rate_apply_btn = tk.Button(rate_input, text="Apply",
                  font=("Segoe UI", 8), bg=C["sel_bg"], fg=C["text"],
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=2,
                  state="disabled",
                  command=self._apply_polling_rate)
        self._rate_apply_btn.pack(side="left", padx=(6, 0))

        # ── Status Panel ───────────────────────────────────────────────────
        status_text = "ℹ  Mouse detection: xinput ✓"
        if self.mouse_engine._has_ratbag:
            status_text += "  │  DPI/Polling: libratbag ✓"
        else:
            status_text += "  │  DPI/Polling: libratbag ✗ (optional)"
        
        tk.Label(parent, text=status_text,
                 font=("Segoe UI", 8), bg=C["bg"], fg=C["muted"],
                 wraplength=800, justify="left"
                 ).pack(anchor="w", padx=14, pady=(0, 8))
        
        if not self.mouse_engine._has_ratbag:
            install_info = (
                "To enable DPI and polling rate control:\n"
                "  sudo apt install libratbag-bin  or  compile from https://github.com/libratbag/libratbag"
            )
            info_f = tk.Frame(parent, bg=C["card"], highlightthickness=0)
            info_f.pack(fill="x", padx=12, pady=(0, 10))
            tk.Label(info_f, text=install_info,
                    font=("Segoe UI", 8), bg=C["card"], fg=C["text"],
                    justify="left", wraplength=800).pack(anchor="w", padx=10, pady=8)

        # ── Button Remapping ───────────────────────────────────────────────
        btn_remap_f = tk.Frame(parent, bg=C["panel"], highlightthickness=0)
        btn_remap_f.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        tk.Label(btn_remap_f, text="BUTTON REMAPPING",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=10, pady=(8, 4))
        
        info_txt = "Click 'Listen', press a mouse button to assign an action"
        tk.Label(btn_remap_f, text=info_txt,
                 font=("Segoe UI", 8), bg=C["panel"], fg=C["muted"],
                 wraplength=800, justify="left").pack(anchor="w", padx=10, pady=(0, 8))
        
        # Buttons grid
        self._btn_remap_widgets = {}
        self._build_button_remap_grid(btn_remap_f)
        
        # Control buttons
        ctrl_f = tk.Frame(btn_remap_f, bg=C["panel"])
        ctrl_f.pack(fill="x", padx=10, pady=(8, 10))
        tk.Button(ctrl_f, text="💾 Save Remaps",
                  font=("Segoe UI", 9, "bold"), bg=C["sel_bg"], fg=C["text"],
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=3,
                  command=self._save_mouse_remaps).pack(side="left", padx=(0, 6))
        
        # Enable/disable DPI/polling controls based on libratbag availability
        self._update_libratbag_status()

    def _update_libratbag_status(self):
        """Enable/disable DPI and polling rate controls based on libratbag availability"""
        if self.mouse_engine._has_ratbag:
            self._dpi_entry.config(state="normal")
            self._dpi_apply_btn.config(state="normal")
            self._rate_dropdown.config(state="readonly")
            self._rate_apply_btn.config(state="normal")
        else:
            self._dpi_entry.config(state="disabled")
            self._dpi_apply_btn.config(state="disabled")
            self._rate_dropdown.config(state="disabled")
            self._rate_apply_btn.config(state="disabled")

    def _build_button_remap_grid(self, parent):
        """Build the button remapping grid"""
        grid = tk.Frame(parent, bg=C["panel"])
        grid.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        for i in range(1, 13):
            btn_frame = tk.Frame(grid, bg=C["card"], highlightthickness=0)
            btn_frame.pack(fill="x", padx=4, pady=4)
            
            # Button label
            tk.Label(btn_frame, text=f"Button {i}",
                    font=("Segoe UI", 9, "bold"),
                    bg=C["card"], fg=C["text"]).pack(side="left", padx=10, pady=6)
            
            # Current mapping
            current_lbl = tk.Label(btn_frame, text="(unmapped)",
                                  font=("Segoe UI", 8),
                                  bg=C["card"], fg=C["muted"])
            current_lbl.pack(side="left", padx=8)
            
            # Listen button
            listen_btn = tk.Button(btn_frame, text="🎧 Listen",
                                  font=("Segoe UI", 8),
                                  bg=C["sel_bg"], fg=C["text"],
                                  relief="flat", bd=0, cursor="hand2",
                                  padx=8, pady=3,
                                  command=lambda bid=i: self._listen_button(bid))
            listen_btn.pack(side="left", padx=(8, 4))
            
            # Action type dropdown
            action_dd = ttk.Combobox(btn_frame, values=["key", "macro", "ahk"],
                                    state="readonly", font=("Segoe UI", 8), width=8)
            action_dd.pack(side="left", padx=4)
            action_dd.set("key")
            
            # Value input
            val_entry = tk.Entry(btn_frame, font=("Segoe UI", 8), width=16)
            val_entry.pack(side="left", padx=4)
            val_entry.insert(0, "key_or_id")
            
            # Assign button
            assign_btn = tk.Button(btn_frame, text="✓ Assign",
                                  font=("Segoe UI", 8),
                                  bg=C["green"], fg="#ffffff",
                                  relief="flat", bd=0, cursor="hand2",
                                  padx=8, pady=3,
                                  command=lambda bid=i, ad=action_dd, ve=val_entry: 
                                          self._assign_button_remap(bid, ad, ve))
            assign_btn.pack(side="left", padx=4)
            
            # Remove button
            remove_btn = tk.Button(btn_frame, text="✕",
                                  font=("Segoe UI", 8),
                                  bg=C["danger"], fg="#ffffff",
                                  relief="flat", bd=0, cursor="hand2",
                                  padx=8, pady=3,
                                  command=lambda bid=i: self._remove_button_remap(bid))
            remove_btn.pack(side="right", padx=(0, 8))
            
            self._btn_remap_widgets[i] = {
                "current": current_lbl,
                "action_dd": action_dd,
                "val_entry": val_entry,
                "listen_btn": listen_btn
            }

    def _refresh_mice_list(self):
        """Detect and populate mouse list"""
        mice = self.mouse_engine.detect_mice()
        self.mouse_engine._mice = mice
        
        if not mice:
            self._mouse_dropdown["values"] = ["No mice detected"]
            self._mouse_dropdown.set("No mice detected")
            return
        
        mice_labels = [f"{m['name']} ({m['brand']} {m['model']}) - {m['buttons']} buttons" 
                      for m in mice]
        self._mouse_dropdown["values"] = mice_labels
        if mice_labels:
            self._mouse_dropdown.set(mice_labels[0])
            self._on_mouse_selected()

    def _on_mouse_selected(self):
        """Update DPI and polling rate when mouse is selected"""
        idx = self._mouse_dropdown.current()
        if idx >= 0 and idx < len(self.mouse_engine._mice):
            mouse = self.mouse_engine._mice[idx]
            self.mouse_engine._selected_id = mouse["id"]
            self.mouse_engine._selected_name = mouse["name"]
            self._refresh_dpi_display()
            self._refresh_polling_rate_display()

    def _refresh_dpi_display(self):
        """Refresh DPI value display"""
        dpi = self.mouse_engine.get_dpi()
        if dpi:
            self._dpi_val_lbl.config(text=f"{dpi} DPI")
            self._dpi_entry.delete(0, "end")
            self._dpi_entry.insert(0, str(dpi))
        else:
            self._dpi_val_lbl.config(text="(unavailable)")

    def _refresh_polling_rate_display(self):
        """Refresh polling rate display"""
        rate = self.mouse_engine.get_polling_rate()
        if rate:
            self._rate_val_lbl.config(text=f"{rate} Hz")
            self._rate_dropdown.set(str(rate))
        else:
            self._rate_val_lbl.config(text="(unavailable)")

    def _apply_dpi(self):
        """Apply DPI setting"""
        try:
            dpi = int(self._dpi_entry.get())
            if not self.mouse_engine._selected_name:
                messagebox.showerror("Error", "Please select a mouse first", parent=self.root)
                return
            if not self.mouse_engine._has_ratbag:
                messagebox.showerror("Error", 
                    "DPI control requires libratbag.\n\n"
                    "Install with: sudo apt install libratbag-bin\n"
                    "Or compile from: https://github.com/libratbag/libratbag",
                    parent=self.root)
                return
            if self.mouse_engine.set_dpi(dpi):
                self.root.after(500, self._refresh_dpi_display)
                messagebox.showinfo("Success", f"DPI set to {dpi}", parent=self.root)
            else:
                messagebox.showerror("Error", 
                    f"Failed to set DPI for {self.mouse_engine._selected_name}.\n"
                    "Ensure:\n"
                    "- Mouse is supported by libratbag\n"
                    "- ratbagctl is installed\n"
                    "- Try running as sudo",
                    parent=self.root)
        except ValueError:
            messagebox.showerror("Error", "Invalid DPI value. Enter a number.", parent=self.root)

    def _apply_polling_rate(self):
        """Apply polling rate setting"""
        rate_str = self._rate_dropdown.get()
        try:
            if not rate_str:
                messagebox.showerror("Error", "Please select a polling rate", parent=self.root)
                return
            if not self.mouse_engine._selected_name:
                messagebox.showerror("Error", "Please select a mouse first", parent=self.root)
                return
            if not self.mouse_engine._has_ratbag:
                messagebox.showerror("Error", 
                    "Polling rate control requires libratbag.\n\n"
                    "Install with: sudo apt install libratbag-bin\n"
                    "Or compile from: https://github.com/libratbag/libratbag",
                    parent=self.root)
                return
            rate = int(rate_str)
            if self.mouse_engine.set_polling_rate(rate):
                self.root.after(500, self._refresh_polling_rate_display)
                messagebox.showinfo("Success", f"Polling rate set to {rate} Hz", parent=self.root)
            else:
                messagebox.showerror("Error", 
                    f"Failed to set polling rate for {self.mouse_engine._selected_name}.\n"
                    "Ensure:\n"
                    "- Mouse is supported by libratbag\n"
                    "- ratbagctl is installed\n"
                    "- Try running as sudo",
                    parent=self.root)
        except ValueError:
            messagebox.showerror("Error", "Invalid polling rate value", parent=self.root)

    def _listen_button(self, button_id: int):
        """Listen for a mouse button press"""
        widgets = self._btn_remap_widgets.get(button_id)
        if not widgets:
            return
        
        widgets["listen_btn"].config(text="🎧 Listening...", state="disabled")
        self.root.update()
        
        def on_button_press(btn_name):
            widgets["listen_btn"].config(text="🎧 Listen", state="normal")
            widgets["val_entry"].delete(0, "end")
            widgets["val_entry"].insert(0, btn_name)
            self.root.after(0, self.root.update)
        
        if not self.mouse_engine.start_listen(on_button_press):
            messagebox.showerror("Error", "Could not start mouse listener. pynput required.", parent=self.root)
            widgets["listen_btn"].config(text="🎧 Listen", state="normal")

    def _assign_button_remap(self, button_id: int, action_dd, val_entry):
        """Assign an action to a button"""
        action_type = action_dd.get()
        action_value = val_entry.get()
        
        if not action_value or action_value == "key_name_or_macro_id":
            messagebox.showerror("Error", "Please enter a value (key name, macro ID, or AHK path)", parent=self.root)
            return
        
        # Store in button remaps
        btn_name = str(button_id)
        label = f"{action_type.upper()}: {action_value}"
        self.mouse_engine._button_remaps[btn_name] = (action_type, action_value, label)
        
        # Update display
        widgets = self._btn_remap_widgets.get(button_id)
        if widgets:
            widgets["current"].config(text=label, fg=C["green"])
        
        messagebox.showinfo("Success", f"Button {button_id} mapped to {label}", parent=self.root)

    def _remove_button_remap(self, button_id: int):
        """Remove a button remapping"""
        btn_name = str(button_id)
        if btn_name in self.mouse_engine._button_remaps:
            del self.mouse_engine._button_remaps[btn_name]
            widgets = self._btn_remap_widgets.get(button_id)
            if widgets:
                widgets["current"].config(text="(unmapped)", fg=C["muted"])
            messagebox.showinfo("Success", f"Button {button_id} unmapped", parent=self.root)

    def _save_mouse_remaps(self):
        """Save mouse remaps to file"""
        self.mouse_engine.save_remaps()
        messagebox.showinfo("Success", "Mouse remaps saved!", parent=self.root)

    # ── Close ─────────────────────────────────────────────────────────────────
    def on_close(self):
        self._snapshot_profile()
        save_profiles(self.profiles)
        self.engine.unregister_all()
        self.ahk_engine.stop()
        if DISPLAY_CONN and X11_OK:
            try: X11.XCloseDisplay(DISPLAY_CONN)
            except Exception: pass
        self.root.destroy()

# ═══════════════════════════════════════════════════════════════════════════════
def main():
    root = TkinterDnD.Tk() if DND_OK else tk.Tk()
    app  = RapidFireApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(),  root.winfo_screenheight()
    ww, wh = root.winfo_width(),        root.winfo_height()
    root.geometry(f"+{(sw - ww) // 2}+{(sh - wh) // 2}")
    root.mainloop()

if __name__ == "__main__":
    main()