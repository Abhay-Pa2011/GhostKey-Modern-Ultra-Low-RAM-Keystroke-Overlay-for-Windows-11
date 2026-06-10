import sys
import os
import subprocess
import threading
import time
import ctypes

if sys.platform == "win32":
    try:
        hwnd_console = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd_console != 0:
            ctypes.windll.user32.ShowWindow(hwnd_console, 0)
    except Exception:
        pass

try:
    import pynput
except ImportError:
    try:
        creationflags = 0x08000000 if sys.platform == "win32" else 0
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pynput"],
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        import pynput
    except Exception as e:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput"])
            import pynput
        except Exception:
            sys.exit(1)

import tkinter as tk
from tkinter import ttk, font, colorchooser
from pynput import keyboard

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class KeyboardVisualizerApp:
    def __init__(self):
        self.font_family = "Segoe UI"
        self.font_weight = "bold"
        self.font_size = 28
        self.text_color = "#FFFFFF"
        self.bg_style = "Float Text"
        self.bg_color = "#121212"
        self.bg_opacity = 0.85
        self.fade_delay = 2.0
        self.mode = "All Keystrokes"
        self.position_preset = "Bottom Center"
        self.is_locked = True
        self.drag_mode = False
        
        self.typed_stream = []
        self.last_key_time = time.time()
        self.fade_timer_id = None
        self.active_modifiers = {
            'ctrl': False,
            'shift': False,
            'alt': False,
            'win': False
        }
        
        self.drag_x = 0
        self.drag_y = 0
        self.custom_x = None
        self.custom_y = None

        self.create_overlay_window()
        self.create_settings_window()
        self.start_keyboard_listener()

    def create_overlay_window(self):
        self.overlay = tk.Tk()
        self.overlay.title("Keystroke Overlay")
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        
        self.chroma_key = "#010203" 
        self.overlay.configure(bg=self.chroma_key)
        self.overlay.attributes("-transparentcolor", self.chroma_key)
        
        self.overlay_label = tk.Label(
            self.overlay,
            text="Type something...",
            font=(self.font_family, self.font_size, self.font_weight),
            fg=self.text_color,
            bg=self.chroma_key,
            padx=20,
            pady=10,
            justify="center"
        )
        self.overlay_label.pack(expand=True, fill="both")
        
        self.overlay_label.bind("<Button-1>", self.start_drag)
        self.overlay_label.bind("<B1-Motion>", self.drag_motion)
        
        self.apply_overlay_styles()
        self.reposition_overlay()

    def start_drag(self, event):
        if not self.is_locked:
            self.drag_x = event.x
            self.drag_y = event.y

    def drag_motion(self, event):
        if not self.is_locked:
            x = self.overlay.winfo_x() + (event.x - self.drag_x)
            y = self.overlay.winfo_y() + (event.y - self.drag_y)
            self.overlay.geometry(f"+{x}+{y}")
            self.custom_x = x
            self.custom_y = y

    def create_settings_window(self):
        self.settings = tk.Toplevel()
        self.settings.title("Keyboard Visualizer Controls")
        self.settings.geometry("940x580")
        self.settings.resizable(False, False)
        self.settings.configure(bg="#0B0F19")

        try:
            hwnd = ctypes.windll.user32.GetParent(self.settings.winfo_id())
            rendering_policy = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))
        except Exception:
            pass

        self.settings.protocol("WM_DELETE_WINDOW", self.on_exit)

        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure(".", background="#0B0F19", foreground="#E2E8F0", fieldbackground="#161B30")
        style.configure("TFrame", background="#0B0F19")
        style.configure("TLabel", background="#0B0F19", foreground="#E2E8F0", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI Semibold", 12, "bold"), foreground="#00F5D4", background="#161B30")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#94A3B8")
        style.configure("Card.TFrame", background="#161B30", relief="flat")
        
        style.configure("TCombobox", 
                        fieldbackground="#1E293B", 
                        background="#1E293B", 
                        foreground="#FFFFFF", 
                        arrowcolor="#00F5D4",
                        bordercolor="#334155")
        style.map("TCombobox", fieldbackground=[('readonly', '#1E293B')], selectbackground=[('readonly', '#1E293B')])
        
        style.configure("TCheckbutton", background="#161B30", foreground="#E2E8F0", focuscolor="")
        style.map("TCheckbutton", background=[('active', '#161B30')], foreground=[('active', '#00F5D4')])
        
        style.configure("Horizontal.TScale", background="#161B30", troughcolor="#1E293B", sliderthickness=15)

        main_container = tk.Frame(self.settings, bg="#0B0F19", padx=20, pady=15)
        main_container.pack(fill="both", expand=True)

        top_bar = tk.Frame(main_container, bg="#0B0F19")
        top_bar.pack(side="top", fill="x", pady=(0, 10))

        title_lbl = tk.Label(top_bar, text="KEYBOARD VISUALIZER", font=("Segoe UI Semibold", 16, "bold"), fg="#00F5D4", bg="#0B0F19")
        title_lbl.pack(anchor="w")
        
        subtitle_lbl = tk.Label(top_bar, text="Ultra-Low RAM Windows 11 Keystroke Engine", font=("Segoe UI", 9), fg="#94A3B8", bg="#0B0F19")
        subtitle_lbl.pack(anchor="w")

        bottom_bar = tk.Frame(main_container, bg="#0B0F19")
        bottom_bar.pack(side="bottom", fill="x", pady=(10, 0))
        
        creator_lbl = tk.Label(bottom_bar, text="Contributor: Abhay Pawar", font=("Segoe UI Semibold", 9), fg="#64748B", bg="#0B0F19")
        creator_lbl.pack(anchor="center")

        cols_frame = tk.Frame(main_container, bg="#0B0F19")
        cols_frame.pack(fill="both", expand=True)

        left_col = tk.Frame(cols_frame, bg="#0B0F19")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_col = tk.Frame(cols_frame, bg="#0B0F19")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        card1 = ttk.Frame(left_col, style="Card.TFrame", padding=15)
        card1.pack(fill="x", pady=5)
        
        ttk.Label(card1, text="Typography Settings", style="Header.TLabel").pack(anchor="w", pady=(0, 10))
        
        font_frame = ttk.Frame(card1, style="Card.TFrame")
        font_frame.pack(fill="x", pady=4)
        ttk.Label(font_frame, text="Font Family:", background="#161B30").pack(side="left")
        
        all_system_fonts = sorted(list(font.families()))
        curated_choices = [
            "Segoe UI", "Segoe UI Semibold", "Segoe UI Black", "Arial", "Arial Black", 
            "Consolas", "Courier New", "Georgia", "Impact", "Trebuchet MS", 
            "Verdana", "Century Gothic", "Ink Free", "Lucida Console", "MS Gothic",
            "Forte", "Times New Roman"
        ]
        available_fonts = [f for f in curated_choices if f in all_system_fonts]
        if not available_fonts:
            available_fonts = [f for f in all_system_fonts if not f.startswith("@")][:20]

        self.font_cb = ttk.Combobox(font_frame, values=available_fonts, state="readonly", width=18)
        self.font_cb.set(self.font_family)
        self.font_cb.pack(side="right")
        self.font_cb.bind("<<ComboboxSelected>>", self.on_config_change)

        weight_frame = ttk.Frame(card1, style="Card.TFrame")
        weight_frame.pack(fill="x", pady=4)
        ttk.Label(weight_frame, text="Font Style:", background="#161B30").pack(side="left")
        self.weight_cb = ttk.Combobox(weight_frame, values=["normal", "bold", "italic", "bold italic"], state="readonly", width=18)
        self.weight_cb.set(self.font_weight)
        self.weight_cb.pack(side="right")
        self.weight_cb.bind("<<ComboboxSelected>>", self.on_weight_change)

        size_frame = ttk.Frame(card1, style="Card.TFrame")
        size_frame.pack(fill="x", pady=4)
        ttk.Label(size_frame, text="Font Size:", background="#161B30").pack(side="left")
        self.size_val_lbl = ttk.Label(size_frame, text=f"{self.font_size}px", style="Sub.TLabel", background="#161B30")
        self.size_val_lbl.pack(side="right")
        self.size_slider = ttk.Scale(size_frame, from_=16, to=72, value=self.font_size, orient="horizontal", style="Horizontal.TScale", command=self.on_font_size_slide)
        self.size_slider.pack(side="right", padx=10, fill="x", expand=True)

        color_frame = ttk.Frame(card1, style="Card.TFrame")
        color_frame.pack(fill="x", pady=4)
        ttk.Label(color_frame, text="Text Color:", background="#161B30").pack(side="left")
        self.color_preview = tk.Frame(color_frame, width=24, height=24, bg=self.text_color, highlightbackground="#00F5D4", highlightthickness=1)
        self.color_preview.pack(side="right", padx=5)
        self.color_btn = tk.Button(color_frame, text="Pick Color", bg="#7B2CBF", fg="#FFFFFF", activebackground="#9D4EDD", activeforeground="#FFFFFF", bd=0, padx=10, pady=2, relief="flat", cursor="hand2")
        self.color_btn.config(command=self.pick_text_color)
        self.color_btn.pack(side="right")

        card2 = ttk.Frame(left_col, style="Card.TFrame", padding=15)
        card2.pack(fill="x", pady=5)
        
        ttk.Label(card2, text="Window Transparency & BG", style="Header.TLabel").pack(anchor="w", pady=(0, 10))

        mode_frame = ttk.Frame(card2, style="Card.TFrame")
        mode_frame.pack(fill="x", pady=4)
        ttk.Label(mode_frame, text="Render Mode:", background="#161B30").pack(side="left")
        self.bg_mode_cb = ttk.Combobox(mode_frame, values=["Float Text (Fully Invisible Window)", "Modern Pill Card (Translucent Backplate)"], state="readonly", width=25)
        self.bg_mode_cb.set("Float Text (Fully Invisible Window)" if self.bg_style == "Float Text" else "Modern Pill Card (Translucent Backplate)")
        self.bg_mode_cb.pack(side="right")
        self.bg_mode_cb.bind("<<ComboboxSelected>>", self.on_bg_mode_change)

        self.opacity_frame = ttk.Frame(card2, style="Card.TFrame")
        self.opacity_val_lbl = ttk.Label(self.opacity_frame, text=f"{int(self.bg_opacity*100)}%", style="Sub.TLabel", background="#161B30")
        self.opacity_slider = ttk.Scale(self.opacity_frame, from_=10, to=100, value=self.bg_opacity*100, orient="horizontal", style="Horizontal.TScale", command=self.on_opacity_slide)
        
        self.bg_color_frame = ttk.Frame(card2, style="Card.TFrame")
        self.bg_color_preview = tk.Frame(self.bg_color_frame, width=24, height=24, bg=self.bg_color, highlightbackground="#00F5D4", highlightthickness=1)
        self.bg_color_btn = tk.Button(self.bg_color_frame, text="Pill Color", bg="#7B2CBF", fg="#FFFFFF", activebackground="#9D4EDD", activeforeground="#FFFFFF", bd=0, padx=10, pady=2, relief="flat", cursor="hand2", command=self.pick_bg_color)
        
        self.update_visuals_panel()

        card3 = ttk.Frame(right_col, style="Card.TFrame", padding=15)
        card3.pack(fill="x", pady=5)
        
        ttk.Label(card3, text="Keystroke Settings", style="Header.TLabel").pack(anchor="w", pady=(0, 10))

        cap_frame = ttk.Frame(card3, style="Card.TFrame")
        cap_frame.pack(fill="x", pady=4)
        ttk.Label(cap_frame, text="Display Mode:", background="#161B30").pack(side="left")
        self.cap_mode_cb = ttk.Combobox(cap_frame, values=["All Keystrokes", "Shortcuts Only (Ctrl/Alt/Win)"], state="readonly", width=18)
        self.cap_mode_cb.set("All Keystrokes" if self.mode == "All Keystrokes" else "Shortcuts Only (Ctrl/Alt/Win)")
        self.cap_mode_cb.pack(side="right")
        self.cap_mode_cb.bind("<<ComboboxSelected>>", self.on_config_change)

        fade_frame = ttk.Frame(card3, style="Card.TFrame")
        fade_frame.pack(fill="x", pady=4)
        ttk.Label(fade_frame, text="Visibility Duration:", background="#161B30").pack(side="left")
        self.fade_val_lbl = ttk.Label(fade_frame, text=f"{self.fade_delay}s", style="Sub.TLabel", background="#161B30")
        self.fade_val_lbl.pack(side="right")
        self.fade_slider = ttk.Scale(fade_frame, from_=0.5, to=5.0, value=self.fade_delay, orient="horizontal", style="Horizontal.TScale", command=self.on_fade_slide)
        self.fade_slider.pack(side="right", padx=10, fill="x", expand=True)

        card4 = ttk.Frame(right_col, style="Card.TFrame", padding=15)
        card4.pack(fill="x", pady=5)
        
        ttk.Label(card4, text="Overlay Layout & Controls", style="Header.TLabel").pack(anchor="w", pady=(0, 10))

        pos_frame = ttk.Frame(card4, style="Card.TFrame")
        pos_frame.pack(fill="x", pady=4)
        ttk.Label(pos_frame, text="Screen Position:", background="#161B30").pack(side="left")
        self.pos_cb = ttk.Combobox(pos_frame, values=["Top Left", "Top Center", "Top Right", "Bottom Left", "Bottom Center", "Bottom Right", "Custom (Draggable)"], state="readonly", width=18)
        self.pos_cb.set(self.position_preset)
        self.pos_cb.pack(side="right")
        self.pos_cb.bind("<<ComboboxSelected>>", self.on_position_change)

        self.lock_var = tk.BooleanVar(value=self.is_locked)
        self.lock_cb = ttk.Checkbutton(card4, text="Lock Overlay Position (Enable Click-Through)", variable=self.lock_var, command=self.toggle_lock)
        self.lock_cb.pack(anchor="w", pady=5)

        self.drag_btn = tk.Button(card4, text="🔓 Move / Position Overlay", bg="#00F5D4", fg="#0B0F19", activebackground="#00D8BB", activeforeground="#0B0F19", bd=0, padx=10, pady=6, relief="flat", cursor="hand2", font=("Segoe UI Semibold", 9))
        self.drag_btn.config(command=self.toggle_drag_mode)
        self.drag_btn.pack(fill="x", pady=5)

        info_frame = tk.Frame(right_col, bg="#161B30", bd=1, highlightbackground="#00F5D4", highlightthickness=1)
        info_frame.pack(fill="x", pady=(10, 0), ipady=6, ipadx=6)
        info_label = tk.Label(info_frame, text="✓ Drag Mode unlocks typing view for exact positioning.\n✓ Console auto-hidden on launch successfully.\n✓ Pre-configured with Forte & modern Serif font presets.", font=("Segoe UI", 8), fg="#00F5D4", bg="#161B30", justify="left")
        info_label.pack(anchor="w", padx=10)

    def update_visuals_panel(self):
        if self.bg_style == "Pill Box":
            self.opacity_frame.pack(fill="x", pady=3)
            ttk.Label(self.opacity_frame, text="Backplate Opacity:", background="#161B30").pack(side="left")
            self.opacity_val_lbl.pack(side="right")
            self.opacity_slider.pack(side="right", padx=10, fill="x", expand=True)

            self.bg_color_frame.pack(fill="x", pady=3)
            ttk.Label(self.bg_color_frame, text="Backplate Color:", background="#161B30").pack(side="left")
            self.bg_color_preview.pack(side="right", padx=5)
            self.bg_color_btn.pack(side="right")
        else:
            self.opacity_frame.pack_forget()
            self.bg_color_frame.pack_forget()

    def on_font_size_slide(self, val):
        self.font_size = int(float(val))
        self.size_val_lbl.config(text=f"{self.font_size}px")
        self.on_config_change()

    def on_opacity_slide(self, val):
        self.bg_opacity = float(val) / 100.0
        self.opacity_val_lbl.config(text=f"{int(val)}%")
        self.on_config_change()

    def on_fade_slide(self, val):
        self.fade_delay = round(float(val), 1)
        self.fade_val_lbl.config(text=f"{self.fade_delay}s")

    def pick_text_color(self):
        color = colorchooser.askcolor(initialcolor=self.text_color, title="Select Font Color")
        if color[1]:
            self.text_color = color[1]
            self.color_preview.config(bg=self.text_color)
            self.on_config_change()

    def pick_bg_color(self):
        color = colorchooser.askcolor(initialcolor=self.bg_color, title="Select Backplate Color")
        if color[1]:
            self.bg_color = color[1]
            self.bg_color_preview.config(bg=self.bg_color)
            self.on_config_change()

    def on_bg_mode_change(self, event=None):
        mode_str = self.bg_mode_cb.get()
        if "Float" in mode_str:
            self.bg_style = "Float Text"
        else:
            self.bg_style = "Pill Box"
        self.update_visuals_panel()
        self.on_config_change()

    def on_position_change(self, event=None):
        self.position_preset = self.pos_cb.get()
        if self.position_preset == "Custom (Draggable)":
            self.lock_var.set(False)
            self.toggle_lock()
        else:
            self.reposition_overlay()

    def on_weight_change(self, event=None):
        self.font_weight = self.weight_cb.get()
        self.on_config_change()

    def toggle_lock(self):
        self.is_locked = self.lock_var.get()
        self.apply_click_through()
        self.apply_overlay_styles()

    def toggle_drag_mode(self):
        self.drag_mode = not self.drag_mode
        if self.drag_mode:
            self.is_locked = False
            self.lock_var.set(False)
            self.drag_btn.config(text="🔒 Save Position & Lock", bg="#7B2CBF", fg="#FFFFFF", activebackground="#9D4EDD")
            self.position_preset = "Custom (Draggable)"
            self.pos_cb.set(self.position_preset)
            if self.fade_timer_id:
                self.overlay.after_cancel(self.fade_timer_id)
                self.fade_timer_id = None
            self.overlay.deiconify()
            self.overlay_label.config(text="✥ Drag Me To Reposition ✥")
            self.apply_overlay_styles()
            self.reposition_overlay()
            self.apply_click_through()
        else:
            self.is_locked = True
            self.lock_var.set(True)
            self.drag_btn.config(text="🔓 Move / Position Overlay", bg="#00F5D4", fg="#0B0F19", activebackground="#00D8BB")
            self.overlay_label.config(text="Position Saved!")
            self.apply_overlay_styles()
            self.reposition_overlay()
            self.apply_click_through()
            self.fade_timer_id = self.overlay.after(1500, self.start_fade_out)

    def on_config_change(self, event=None):
        self.font_family = self.font_cb.get()
        cap_val = self.cap_mode_cb.get()
        self.mode = "All Keystrokes" if "All" in cap_val else "Shortcuts Only"
        self.apply_overlay_styles()
        self.reposition_overlay()

    def apply_overlay_styles(self):
        if self.bg_style == "Float Text":
            self.overlay.configure(bg=self.chroma_key)
            self.overlay_label.config(
                font=(self.font_family, self.font_size, self.font_weight),
                fg=self.text_color,
                bg=self.chroma_key,
                bd=0,
                padx=20,
                pady=10
            )
            self.overlay.attributes("-alpha", 1.0)
            self.overlay.attributes("-transparentcolor", self.chroma_key)
        else:
            self.overlay.configure(bg=self.bg_color)
            self.overlay_label.config(
                font=(self.font_family, self.font_size, self.font_weight),
                fg=self.text_color,
                bg=self.bg_color,
                bd=0,
                padx=25,
                pady=15
            )
            self.overlay.attributes("-transparentcolor", "")
            self.overlay.attributes("-alpha", self.bg_opacity)

        if not self.is_locked:
            self.overlay_label.config(highlightbackground="#00F5D4", highlightthickness=2)
        else:
            self.overlay_label.config(highlightthickness=0)

    def apply_click_through(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.overlay.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            if self.is_locked:
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x00080000 | 0x00000020)
            else:
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style & ~0x00000020)
        except Exception as e:
            print(f"Failed to apply Windows transparency filters: {e}")

    def reposition_overlay(self):
        self.overlay.update_idletasks()
        win_w = self.overlay.winfo_width()
        win_h = self.overlay.winfo_height()

        scr_w = self.overlay.winfo_screenwidth()
        scr_h = self.overlay.winfo_screenheight()

        margin = 50
        bottom_margin = 120

        if self.position_preset == "Top Left":
            x, y = margin, margin
        elif self.position_preset == "Top Center":
            x, y = (scr_w - win_w) // 2, margin
        elif self.position_preset == "Top Right":
            x, y = scr_w - win_w - margin, margin
        elif self.position_preset == "Bottom Left":
            x, y = margin, scr_h - win_h - bottom_margin
        elif self.position_preset == "Bottom Center":
            x, y = (scr_w - win_w) // 2, scr_h - win_h - bottom_margin
        elif self.position_preset == "Bottom Right":
            x, y = scr_w - win_w - margin, scr_h - win_h - bottom_margin
        elif self.position_preset == "Custom (Draggable)":
            if self.custom_x is not None and self.custom_y is not None:
                x, y = self.custom_x, self.custom_y
            else:
                x, y = (scr_w - win_w) // 2, scr_h - win_h - bottom_margin
        
        self.overlay.geometry(f"+{x}+{y}")

    def start_keyboard_listener(self):
        self.listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.listener.daemon = True
        self.listener.start()

    def on_key_press(self, key):
        key_str = ""
        is_mod = False
        
        if key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            self.active_modifiers['ctrl'] = True
            is_mod = True
        elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr]:
            self.active_modifiers['alt'] = True
            is_mod = True
        elif key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
            self.active_modifiers['shift'] = True
            is_mod = True
        elif key in [keyboard.Key.cmd, keyboard.Key.cmd_r]:
            self.active_modifiers['win'] = True
            is_mod = True

        if is_mod:
            return

        has_shortcuts = (self.active_modifiers['ctrl'] or 
                         self.active_modifiers['alt'] or 
                         self.active_modifiers['win'])

        try:
            special_keys = {
                keyboard.Key.space: " ",
                keyboard.Key.enter: "Enter ⏎",
                keyboard.Key.tab: "Tab ⇥",
                keyboard.Key.esc: "Esc ⎋",
                keyboard.Key.backspace: "Backspace ⌫",
                keyboard.Key.up: "↑",
                keyboard.Key.down: "↓",
                keyboard.Key.left: "←",
                keyboard.Key.right: "→",
                keyboard.Key.delete: "Del ⌦",
                keyboard.Key.caps_lock: "Caps Lock ⇪",
                keyboard.Key.print_screen: "PrtScn",
                keyboard.Key.scroll_lock: "ScrollLock",
                keyboard.Key.pause: "Pause",
                keyboard.Key.insert: "Insert",
                keyboard.Key.home: "Home ⌂",
                keyboard.Key.end: "End",
                keyboard.Key.page_up: "PgUp",
                keyboard.Key.page_down: "PgDn",
                keyboard.Key.num_lock: "NumLock",
            }

            if key in special_keys:
                key_str = special_keys[key]
            elif hasattr(key, 'char') and key.char is not None:
                val = ord(key.char)
                if 1 <= val <= 26:
                    key_str = chr(val + 64)
                else:
                    key_str = key.char
            elif hasattr(key, 'vk') and key.vk is not None:
                vk = key.vk
                if 65 <= vk <= 90:
                    key_str = chr(vk)
                elif 48 <= vk <= 57:
                    key_str = chr(vk)
                elif 96 <= vk <= 105:
                    key_str = chr(vk - 96 + 48)
                else:
                    key_str = str(key).replace("Key.", "").capitalize()
            else:
                key_str = str(key).replace("Key.", "").capitalize()
        except Exception:
            key_str = str(key)

        if key_str == "Backspace ⌫" and not has_shortcuts:
            if self.typed_stream:
                self.typed_stream.pop()
            self.queue_ui_update(self.get_stream_text(), is_shortcut=False)
            return

        if has_shortcuts:
            shortcut_parts = []
            if self.active_modifiers['ctrl']: shortcut_parts.append("Ctrl")
            if self.active_modifiers['alt']: shortcut_parts.append("Alt")
            if self.active_modifiers['shift']: shortcut_parts.append("Shift")
            if self.active_modifiers['win']: shortcut_parts.append("Win")
            
            if key_str == " ":
                formatted_key = "Space"
            else:
                formatted_key = key_str.upper() if len(key_str) == 1 else key_str
                
            if formatted_key not in shortcut_parts:
                shortcut_parts.append(formatted_key)
                
            display_text = " + ".join(shortcut_parts)
            self.typed_stream = []
            self.queue_ui_update(display_text, is_shortcut=True)
        else:
            if self.mode == "Shortcuts Only":
                return

            if time.time() - self.last_key_time > 1.8:
                self.typed_stream = []

            if key_str == "Enter ⏎":
                self.typed_stream = []
            elif len(key_str) == 1:
                self.typed_stream.append(key_str)
            else:
                self.typed_stream.append(f" [{key_str}] ")

            if len(self.get_stream_text()) > 28:
                self.typed_stream = self.typed_stream[max(1, len(self.typed_stream)-15):]

            self.last_key_time = time.time()
            self.queue_ui_update(self.get_stream_text(), is_shortcut=False)

    def on_key_release(self, key):
        if key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            self.active_modifiers['ctrl'] = False
        elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr]:
            self.active_modifiers['alt'] = False
        elif key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
            self.active_modifiers['shift'] = False
        elif key in [keyboard.Key.cmd, keyboard.Key.cmd_r]:
            self.active_modifiers['win'] = False

    def get_stream_text(self):
        return "".join(self.typed_stream)

    def queue_ui_update(self, text, is_shortcut=False):
        self.overlay.after(0, self.update_overlay_ui, text, is_shortcut)

    def update_overlay_ui(self, text, is_shortcut):
        if self.fade_timer_id:
            self.overlay.after_cancel(self.fade_timer_id)
            self.fade_timer_id = None

        if not text.strip() and not self.drag_mode:
            self.overlay.withdraw()
            return

        self.overlay.deiconify()
        
        if self.drag_mode:
            display_text = f"✥ Drag Me To Reposition ✥\nPreview: {text if text.strip() else 'Type to Preview'}"
        else:
            display_text = text

        self.overlay_label.config(text=display_text)
        
        self.apply_overlay_styles()
        self.reposition_overlay()
        self.apply_click_through()

        if not self.drag_mode:
            ms_delay = int(self.fade_delay * 1000)
            self.fade_timer_id = self.overlay.after(ms_delay, self.start_fade_out)

    def start_fade_out(self):
        self.fade_step()

    def fade_step(self):
        current_alpha = self.overlay.attributes("-alpha")
        target_step = 0.08
        
        if current_alpha > target_step:
            self.overlay.attributes("-alpha", current_alpha - target_step)
            self.fade_timer_id = self.overlay.after(15, self.fade_step)
        else:
            self.overlay.attributes("-alpha", 0.0)
            self.overlay.withdraw()

    def run(self):
        self.overlay.mainloop()

    def on_exit(self):
        try:
            self.listener.stop()
        except Exception:
            pass
        self.settings.destroy()
        self.overlay.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = KeyboardVisualizerApp()
    app.run()