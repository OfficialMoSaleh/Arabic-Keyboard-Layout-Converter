"""
تطبيق تحويل لوحة المفاتيح الشامل لنظام ويندوز
يعمل في كل البرامج (Word, Telegram, Notepad, Excel, Browsers, WhatsApp, etc.)
مع شريط عائم على الشاشة واختصارات عالمية فورية
يعمل بهدوء في الخلفية دون الظهور في شريط المهام (Taskbar)
"""

import ctypes
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk, messagebox

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None

from clipboard_helper import get_clipboard, set_clipboard, sequence_number, has_text
from converter import convert

# ---------------------------------------------------------------------------
# Win32 bindings (private instances with explicit, 64-bit-safe prototypes)
# ---------------------------------------------------------------------------
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT_PTR = ctypes.c_ssize_t

user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int
user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
user32.PeekMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_size_t]
user32.keybd_event.restype = None
user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
user32.MapVirtualKeyW.restype = wintypes.UINT
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL

if ctypes.sizeof(ctypes.c_void_p) == 8:
    _get_long = user32.GetWindowLongPtrW
    _set_long = user32.SetWindowLongPtrW
else:  # 32-bit Python
    _get_long = user32.GetWindowLongW
    _set_long = user32.SetWindowLongW
_get_long.argtypes = [wintypes.HWND, ctypes.c_int]
_get_long.restype = ctypes.c_ssize_t
_set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
_set_long.restype = ctypes.c_ssize_t

kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateEventW.restype = wintypes.HANDLE
kernel32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.OpenEventW.restype = wintypes.HANDLE
kernel32.SetEvent.argtypes = [wintypes.HANDLE]
kernel32.SetEvent.restype = wintypes.BOOL
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.WaitForSingleObject.restype = wintypes.DWORD
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x0001, 0x0002, 0x0004, 0x0008, 0x4000
WM_HOTKEY, WM_USER = 0x0312, 0x0400
PM_NOREMOVE = 0

VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN = 0x10, 0x11, 0x12, 0x5B, 0x5C
VK_A, VK_C, VK_V, VK_X, VK_Z = 0x41, 0x43, 0x56, 0x58, 0x5A
VK_END, VK_RIGHT = 0x23, 0x27
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
GA_ROOT = 2
SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_NOACTIVATE, SWP_FRAMECHANGED = 0x0001, 0x0002, 0x0004, 0x0010, 0x0020
ERROR_ALREADY_EXISTS = 183

# Default multi-hotkey list registered simultaneously
HOTKEY_CONFIGS = [
    (101, "Ctrl + Shift + Z", MOD_CONTROL | MOD_SHIFT, 0x5A),
    (102, "Ctrl + Alt + Z",   MOD_CONTROL | MOD_ALT,   0x5A),
    (103, "Ctrl + Shift + X", MOD_CONTROL | MOD_SHIFT, 0x58),
    (104, "Ctrl + Alt + X",   MOD_CONTROL | MOD_ALT,   0x58),
]

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ArabicKeyConverter")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
DEFAULT_SETTINGS = {
    "floating": True,
    "widget_pos": None,
    "beep": True,
    "auto_select": True
}


def load_settings():
    data = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    return data


def save_settings(data):
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Keyboard simulation
# ---------------------------------------------------------------------------
def _key(vk, up=False):
    flags = KEYEVENTF_KEYUP if up else 0
    if vk in (VK_LWIN, VK_RWIN, VK_END, VK_RIGHT):
        flags |= KEYEVENTF_EXTENDEDKEY
    user32.keybd_event(vk, user32.MapVirtualKeyW(vk, 0), flags, 0)


def send_ctrl_combo(vk):
    _key(VK_CONTROL)
    _key(vk)
    _key(vk, up=True)
    _key(VK_CONTROL, up=True)


def wait_modifiers_released(timeout=1.0):
    deadline = time.time() + timeout
    watched = (VK_CONTROL, VK_SHIFT, VK_MENU, VK_LWIN, VK_RWIN)
    while time.time() < deadline:
        if not any(user32.GetAsyncKeyState(vk) & 0x8000 for vk in watched):
            return True
        time.sleep(0.01)
    for vk in (VK_SHIFT, VK_MENU, VK_LWIN, VK_RWIN):
        if user32.GetAsyncKeyState(vk) & 0x8000:
            _key(vk, up=True)
    return False


# ---------------------------------------------------------------------------
# Global hotkey listener (manages multiple hotkeys simultaneously)
# ---------------------------------------------------------------------------
class MultiHotkeyListener(threading.Thread):
    def __init__(self, on_hotkey, on_status):
        super().__init__(daemon=True)
        self.on_hotkey = on_hotkey
        self.on_status = on_status
        self.thread_id = 0
        self.registered_ids = set()
        self.ready = threading.Event()

    def run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, WM_USER, WM_USER, PM_NOREMOVE)
        
        active_names = []
        for hid, name, mods, vk in HOTKEY_CONFIGS:
            if user32.RegisterHotKey(None, hid, mods | MOD_NOREPEAT, vk):
                self.registered_ids.add(hid)
                active_names.append(name)
        
        self.on_status(active_names)
        self.ready.set()

        while True:
            res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break
            if msg.message == WM_HOTKEY and msg.wParam in self.registered_ids:
                threading.Thread(target=self._safe_call, daemon=True).start()

        for hid in list(self.registered_ids):
            user32.UnregisterHotKey(None, hid)

    def _safe_call(self):
        try:
            self.on_hotkey()
        except Exception as exc:
            print(f"hotkey handler error: {exc}")

    def stop(self):
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)  # WM_QUIT


# ---------------------------------------------------------------------------
# Floating always-on-top badge (never steals focus, draggable, dismissible)
# ---------------------------------------------------------------------------
class FloatingWidget:
    BG = "#0f172a"
    BTN = "#1e3a8a"
    BTN_HOVER = "#2563eb"

    def __init__(self, parent, scale, pos, on_convert, on_open, on_hide, on_quit, on_moved):
        self.parent = parent
        self.on_convert = on_convert
        self.on_hide = on_hide
        self.on_moved = on_moved
        self.default_text = "🔄 تحويل الكتابة"
        self._flash_job = None
        self._drag = None

        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.95)
        self.win.configure(bg=self.BG)

        self.w = int(210 * scale)
        self.h = int(38 * scale)
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        if pos and 0 <= pos[0] <= sw - 40 and 0 <= pos[1] <= sh - 40:
            self.x, self.y = pos
        else:
            self.x, self.y = sw - self.w - int(30 * scale), int(80 * scale)
        self.win.geometry(f"{self.w}x{self.h}+{self.x}+{self.y}")

        frame = tk.Frame(self.win, bg=self.BG, highlightbackground="#3b82f6", highlightthickness=1)
        frame.pack(fill="both", expand=True)

        # Close/Hide button '✕'
        self.btn_close = tk.Label(
            frame, text="✕", font=("Segoe UI", 9, "bold"),
            fg="#94a3b8", bg=self.BG, cursor="hand2", padx=6
        )
        self.btn_close.pack(side="left")
        self.btn_close.bind("<Button-1>", lambda e: self.on_hide())
        self.btn_close.bind("<Enter>", lambda e: self.btn_close.config(fg="#f87171"))
        self.btn_close.bind("<Leave>", lambda e: self.btn_close.config(fg="#94a3b8"))

        # Convert button (center)
        self.btn = tk.Label(
            frame, text=self.default_text, font=("Segoe UI", 9, "bold"),
            fg="#f8fafc", bg=self.BTN, cursor="hand2"
        )
        self.btn.pack(side="left", fill="both", expand=True, padx=2, pady=3)

        # Drag grip '⋮⋮' (right)
        self.grip = tk.Label(frame, text="⋮⋮", font=("Segoe UI", 11), fg="#64748b", bg=self.BG, cursor="fleur", padx=4)
        self.grip.pack(side="right")

        # Context menu
        self.menu = tk.Menu(self.win, tearoff=0)
        self.menu.add_command(label="فتح نافذة الإعدادات", command=on_open)
        self.menu.add_command(label="إخفاء الزر العائم (الاختصارات تظل تعمل)", command=on_hide)
        self.menu.add_separator()
        self.menu.add_command(label="إنهاء البرنامج بالكامل", command=on_quit)

        # Draggable logic
        for w in (frame, self.btn, self.grip):
            w.bind("<ButtonPress-1>", self._press)
            w.bind("<B1-Motion>", self._motion)
            w.bind("<ButtonRelease-1>", self._release)
            w.bind("<Button-3>", self._popup)

        self.btn.bind("<Enter>", lambda e: self.btn.config(bg=self.BTN_HOVER))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg=self.BTN))

        self.win.update_idletasks()
        self._apply_no_activate()
        self._keep_on_top()

    def _apply_no_activate(self):
        try:
            hwnd = user32.GetAncestor(self.win.winfo_id(), GA_ROOT) or self.win.winfo_id()
            style = _get_long(hwnd, GWL_EXSTYLE)
            _set_long(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
            user32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED)
        except Exception:
            pass

    def _keep_on_top(self):
        try:
            if self.win.state() != "withdrawn":
                self.win.attributes("-topmost", True)
                self.win.lift()
        except tk.TclError:
            return
        self.win.after(2500, self._keep_on_top)

    def _press(self, e):
        self._drag = (e.x_root, e.y_root, self.x, self.y, False)

    def _motion(self, e):
        if not self._drag:
            return
        sx, sy, ox, oy, moved = self._drag
        dx, dy = e.x_root - sx, e.y_root - sy
        if not moved and abs(dx) + abs(dy) < 5:
            return
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        self.x = max(0, min(sw - self.w, ox + dx))
        self.y = max(0, min(sh - self.h, oy + dy))
        self.win.geometry(f"+{self.x}+{self.y}")
        self._drag = (sx, sy, ox, oy, True)

    def _release(self, e):
        drag, self._drag = self._drag, None
        if not drag:
            return
        if drag[4]:
            self.on_moved((self.x, self.y))
        elif e.widget is self.btn:
            self.on_convert()

    def _popup(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def flash(self, text, ok=True, ms=1500):
        if self._flash_job:
            self.win.after_cancel(self._flash_job)
        self.btn.config(text=text, fg="#86efac" if ok else "#fca5a5")
        self._flash_job = self.win.after(ms, self._reset)

    def _reset(self):
        self._flash_job = None
        self.btn.config(text=self.default_text, fg="#f8fafc")

    def hide(self):
        self.win.withdraw()

    def show(self):
        self.win.deiconify()
        self._apply_no_activate()


# ---------------------------------------------------------------------------
# Main window & Orchestrator
# ---------------------------------------------------------------------------
class AppUI:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.scale = max(1.0, root.winfo_fpixels("1i") / 96.0)

        # Set custom keyboard icon
        ico_path = os.path.join(os.path.dirname(__file__), "app.ico")
        if os.path.exists(ico_path):
            try:
                root.iconbitmap(ico_path)
            except Exception:
                pass

        root.title("مُحوّل لغة الكتابة - ويندوز (عربي ⇋ En)")
        root.geometry(f"{int(540 * self.scale)}x{int(540 * self.scale)}")
        root.minsize(int(460 * self.scale), int(500 * self.scale))
        root.configure(bg="#0f172a")

        # By default, withdraw root so NO icon appears on the Windows Taskbar!
        root.withdraw()

        self.current_mode = "auto"
        self.last_foreground_window = 0
        self.busy = threading.Lock()
        self.ui_queue = queue.Queue()

        self.setup_ui()

        self.floating_widget = FloatingWidget(
            root, self.scale, self.settings.get("widget_pos"),
            on_convert=self.trigger_floating_convert,
            on_open=self.show_main_window,
            on_hide=self.hide_floating_from_menu,
            on_quit=self.quit_app,
            on_moved=self.remember_widget_pos,
        )
        if not self.settings.get("floating", True):
            self.floating_widget.hide()
            self.var_floating.set(False)

        # Multi-hotkey background listener
        self.hotkey_thread = MultiHotkeyListener(self.handle_global_hotkey, self.on_hotkeys_ready)
        self.hotkey_thread.start()

        # Listen for IPC event to reopen window if user launches shortcut again
        self.event_listener_thread = threading.Thread(target=self._listen_for_show_event, daemon=True)
        self.event_listener_thread.start()

        # Clicking 'X' on main window hides it (withdraws it) so taskbar remains clean!
        root.protocol("WM_DELETE_WINDOW", self.hide_to_background)
        root.after(100, self.process_queue)
        root.after(100, self.track_foreground)

    def _listen_for_show_event(self):
        ev = kernel32.CreateEventW(None, False, False, "Local\\ArabicKeyConverter_ShowEvent")
        if not ev:
            return
        while True:
            res = kernel32.WaitForSingleObject(ev, 1000)
            if res == 0:  # WAIT_OBJECT_0
                self.ui_queue.put(("show_window",))

    def is_own_window(self, hwnd):
        if not hwnd:
            return True
        try:
            root_hwnd = user32.GetAncestor(self.root.winfo_id(), GA_ROOT) or self.root.winfo_id()
            float_hwnd = user32.GetAncestor(self.floating_widget.win.winfo_id(), GA_ROOT) or self.floating_widget.win.winfo_id()
            h_root = user32.GetAncestor(hwnd, GA_ROOT) or hwnd
            return h_root in (root_hwnd, float_hwnd, self.root.winfo_id(), self.floating_widget.win.winfo_id())
        except Exception:
            return False

    def track_foreground(self):
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd and not self.is_own_window(hwnd):
                self.last_foreground_window = hwnd
        except Exception:
            pass
        self.root.after(100, self.track_foreground)

    # -- thread -> UI bridge -------------------------------------------------
    def notify(self, text, ok=True):
        self.ui_queue.put(("status", text, ok))

    def on_hotkeys_ready(self, active_names):
        self.ui_queue.put(("hotkeys", active_names))

    def process_queue(self):
        try:
            while True:
                kind, *args = self.ui_queue.get_nowait()
                if kind == "status":
                    text, ok = args
                    self.status_lbl.config(text=text, fg="#22c55e" if ok else "#f87171")
                    self.floating_widget.flash(text, ok)
                    self.root.after(2500, lambda t=text: self.status_lbl.cget("text") == t and self.status_lbl.config(text=""))
                elif kind == "hotkeys":
                    names = args[0]
                    self.lbl_shortcuts.config(text="✓ الاختصارات المفعّلة: " + " | ".join(names))
                elif kind == "show_window":
                    self.show_main_window()
                    if not self.floating_widget.win.winfo_viewable() and self.settings.get("floating", True):
                        self.floating_widget.show()
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    # -- UI ------------------------------------------------------------------
    def setup_ui(self):
        header = tk.Frame(self.root, bg="#1e293b", padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="⌨️ مُحوّل الكتابة في كل برامج الويندوز",
                 font=("Segoe UI", 12, "bold"), fg="#f8fafc", bg="#1e293b").pack(side="left")
        tk.Label(header, text="عربي ⇋ English", font=("Segoe UI", 10), fg="#38bdf8", bg="#1e293b").pack(side="right")

        banner = tk.Frame(self.root, bg="#1e3a8a", padx=12, pady=10)
        banner.pack(fill="x", padx=16, pady=(10, 6))
        self.banner_lbl = tk.Label(
            banner,
            text="✨ يعمل في كل برامج الويندوز (Word, Telegram, WhatsApp, Chrome, Notepad, etc.)\n"
                 "اضغط الاختصار العالمي [ Ctrl + Shift + Z ] أو [ Ctrl + Alt + Z ] للتحويل الفوري!\n"
                 "💡 يمكنك الضغط مباشرة دون الحاجة لتحديد النص مسبقاً!",
            font=("Segoe UI", 9), fg="#e0f2fe", bg="#1e3a8a", justify="center"
        )
        self.banner_lbl.pack()

        # Settings
        settings_frame = tk.Frame(self.root, bg="#0f172a", padx=16)
        settings_frame.pack(fill="x", pady=(4, 2))

        self.var_floating = tk.BooleanVar(value=bool(self.settings.get("floating", True)))
        tk.Checkbutton(
            settings_frame, text="إظهار زر التحويل العائم على الشاشة (دائماً فوق النوافذ)",
            variable=self.var_floating, command=self.toggle_floating_badge,
            font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a", selectcolor="#1e293b",
            activebackground="#0f172a", activeforeground="#38bdf8"
        ).pack(anchor="w")

        self.var_auto_select = tk.BooleanVar(value=bool(self.settings.get("auto_select", True)))
        tk.Checkbutton(
            settings_frame, text="التحويل التلقائي للحقل بالكامل عند عدم تحديد نص",
            variable=self.var_auto_select, command=self.on_auto_select_changed,
            font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a", selectcolor="#1e293b",
            activebackground="#0f172a", activeforeground="#38bdf8"
        ).pack(anchor="w")

        self.var_beep = tk.BooleanVar(value=bool(self.settings.get("beep", True)))
        tk.Checkbutton(
            settings_frame, text="صوت تأكيد لطيف عند إتمام التحويل", variable=self.var_beep,
            command=self.on_beep_changed, font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a",
            selectcolor="#1e293b", activebackground="#0f172a", activeforeground="#38bdf8"
        ).pack(anchor="w")

        self.lbl_shortcuts = tk.Label(
            settings_frame, text="جاري تفعيل الاختصارات العالمية...",
            font=("Segoe UI", 8), fg="#22c55e", bg="#0f172a"
        )
        self.lbl_shortcuts.pack(anchor="w", pady=(2, 0))

        # Direct text test box
        main_frame = tk.Frame(self.root, bg="#0f172a", padx=16, pady=4)
        main_frame.pack(fill="both", expand=True)

        mode_frame = tk.Frame(main_frame, bg="#0f172a")
        mode_frame.pack(fill="x", pady=(2, 6))
        self.btn_auto = tk.Button(mode_frame, text="كشف تلقائي (شامل Caps Lock)", bg="#2563eb", fg="white",
                                  relief="flat", padx=10, pady=3, font=("Segoe UI", 9, "bold"),
                                  command=lambda: self.set_mode("auto"))
        self.btn_auto.pack(side="left", padx=2)
        self.btn_ar = tk.Button(mode_frame, text="تحويل للعربية", bg="#1e293b", fg="#94a3b8", relief="flat",
                                padx=10, pady=3, font=("Segoe UI", 9), command=lambda: self.set_mode("to_arabic"))
        self.btn_ar.pack(side="left", padx=2)
        self.btn_en = tk.Button(mode_frame, text="تحويل للإنجليزية", bg="#1e293b", fg="#94a3b8", relief="flat",
                                padx=10, pady=3, font=("Segoe UI", 9), command=lambda: self.set_mode("to_english"))
        self.btn_en.pack(side="left", padx=2)

        tk.Label(main_frame, text="النص الأصلي (تجربة فورية داخل البرنامج):", font=("Segoe UI", 9),
                 fg="#94a3b8", bg="#0f172a").pack(anchor="w", pady=(2, 2))
        self.txt_in = tk.Text(main_frame, height=3, bg="#1e293b", fg="#f8fafc", insertbackground="#38bdf8",
                              relief="flat", font=("Segoe UI", 10), padx=8, pady=6, undo=True)
        self.txt_in.pack(fill="x", pady=(0, 4))
        self.txt_in.bind("<KeyRelease>", self.on_text_change)
        self.txt_in.bind("<<Paste>>", lambda e: self.root.after(10, self.on_text_change))
        self.txt_in.bind("<<Cut>>", lambda e: self.root.after(10, self.on_text_change))

        tk.Label(main_frame, text="النتيجة المحولة:", font=("Segoe UI", 9),
                 fg="#94a3b8", bg="#0f172a").pack(anchor="w", pady=(2, 2))
        self.txt_out = tk.Text(main_frame, height=3, bg="#1e293b", fg="#38bdf8", relief="flat",
                               font=("Segoe UI", 10), padx=8, pady=6)
        self.txt_out.pack(fill="x", pady=(0, 6))

        actions = tk.Frame(main_frame, bg="#0f172a")
        actions.pack(fill="x")
        self.btn_copy = tk.Button(actions, text="📋 نسخ النتيجة", bg="#2563eb", fg="white", relief="flat",
                                  padx=12, pady=4, font=("Segoe UI", 9, "bold"), command=self.copy_result)
        self.btn_copy.pack(side="left", padx=3)
        tk.Button(actions, text="⇄ تبديل", bg="#1e293b", fg="#f8fafc", relief="flat", padx=10, pady=4,
                  font=("Segoe UI", 9), command=self.swap_texts).pack(side="left", padx=3)
        tk.Button(actions, text="مسح", bg="#1e293b", fg="#94a3b8", relief="flat", padx=10, pady=4,
                  font=("Segoe UI", 9), command=self.clear_all).pack(side="left", padx=3)

        tk.Button(actions, text="إخفاء للشريط العائم ⇲", bg="#334155", fg="#f8fafc", relief="flat",
                  padx=10, pady=4, font=("Segoe UI", 8), command=self.hide_to_background).pack(side="right", padx=3)
        tk.Button(actions, text="🚪 إنهاء نهائي", bg="#7f1d1d", fg="#fecaca", relief="flat",
                  padx=8, pady=4, font=("Segoe UI", 8), command=self.quit_app).pack(side="right", padx=3)

        self.status_lbl = tk.Label(actions, text="", font=("Segoe UI", 9), fg="#22c55e", bg="#0f172a")
        self.status_lbl.pack(side="right", padx=6)

    def on_beep_changed(self):
        self.settings["beep"] = bool(self.var_beep.get())
        save_settings(self.settings)

    def on_auto_select_changed(self):
        self.settings["auto_select"] = bool(self.var_auto_select.get())
        save_settings(self.settings)

    def toggle_floating_badge(self):
        visible = bool(self.var_floating.get())
        self.settings["floating"] = visible
        save_settings(self.settings)
        if visible:
            self.floating_widget.show()
        else:
            self.floating_widget.hide()

    def hide_floating_from_menu(self):
        self.var_floating.set(False)
        self.toggle_floating_badge()

    def remember_widget_pos(self, pos):
        self.settings["widget_pos"] = list(pos)
        save_settings(self.settings)

    def show_main_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_to_background(self):
        self.root.withdraw()
        self.floating_widget.flash("يعمل بهدوء في الخلفية 💡", ok=True, ms=2000)

    def quit_app(self):
        try:
            self.hotkey_thread.stop()
        finally:
            self.root.destroy()
            sys.exit(0)

    def set_mode(self, mode):
        self.current_mode = mode
        buttons = {"auto": self.btn_auto, "to_arabic": self.btn_ar, "to_english": self.btn_en}
        for m, btn in buttons.items():
            if m == mode:
                btn.config(bg="#2563eb", fg="white", font=("Segoe UI", 9, "bold"))
            else:
                btn.config(bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9))
        self.on_text_change()

    def on_text_change(self, _event=None):
        text = self.txt_in.get("1.0", "end-1c")
        self.txt_out.delete("1.0", "end")
        if text:
            self.txt_out.insert("1.0", convert(text, self.current_mode))

    def copy_result(self):
        result = self.txt_out.get("1.0", "end-1c")
        if result and set_clipboard(result):
            self.status_lbl.config(text="✓ تم النسخ!", fg="#22c55e")
            self.root.after(1800, lambda: self.status_lbl.config(text=""))

    def swap_texts(self):
        out_val = self.txt_out.get("1.0", "end-1c")
        self.txt_in.delete("1.0", "end")
        self.txt_in.insert("1.0", out_val)
        self.on_text_change()

    def clear_all(self):
        self.txt_in.delete("1.0", "end")
        self.txt_out.delete("1.0", "end")
        self.status_lbl.config(text="")

    # -- Conversion in other Windows applications ----------------------------
    def trigger_floating_convert(self):
        """Floating widget clicked: restore active target window and convert."""
        target = self.last_foreground_window
        if target:
            user32.SetForegroundWindow(target)
            time.sleep(0.06)
        threading.Thread(target=self.execute_conversion, daemon=True).start()

    def handle_global_hotkey(self):
        self.execute_conversion()

    def execute_conversion(self):
        if not self.busy.acquire(blocking=False):
            return
        try:
            self._convert_selection_in_foreground_app()
        except Exception as exc:
            self.notify("حدث خطأ أثناء التحويل", ok=False)
            print(f"conversion error: {exc}")
        finally:
            self.busy.release()

    def _convert_selection_in_foreground_app(self):
        # 1. Release modifier keys if physically held
        wait_modifiers_released()

        # 2. Re-verify target window is foreground
        target = self.last_foreground_window
        curr = user32.GetForegroundWindow()
        if target and curr and self.is_own_window(curr):
            user32.SetForegroundWindow(target)
            time.sleep(0.05)

        # 3. Save current clipboard to restore later
        original_text = get_clipboard() if has_text() else None
        seq_before = sequence_number()

        # 4. Try copying existing selection first
        auto_selected = False
        send_ctrl_combo(VK_C)
        deadline = time.time() + 0.15
        while sequence_number() == seq_before and time.time() < deadline:
            time.sleep(0.015)

        # 5. If nothing was selected, and auto-select is enabled: select all in active field
        if sequence_number() == seq_before and self.settings.get("auto_select", True):
            send_ctrl_combo(VK_A)
            time.sleep(0.03)
            send_ctrl_combo(VK_C)
            deadline = time.time() + 0.25
            while sequence_number() == seq_before and time.time() < deadline:
                time.sleep(0.02)
            if sequence_number() != seq_before:
                auto_selected = True

        # 6. Check if text was acquired
        if sequence_number() == seq_before:
            self.notify("لا يوجد نص لتحويله", ok=False)
            return

        text = get_clipboard()
        if not text or not text.strip():
            self._restore(original_text)
            self.notify("لا يوجد نص لتحويله", ok=False)
            return

        # 7. Convert text
        converted = convert(text, self.current_mode)
        if converted == text:
            self._restore(original_text)
            if auto_selected:
                _key(VK_RIGHT)
                _key(VK_RIGHT, up=True)
            self.notify("لا يوجد ما يحتاج للتحويل", ok=False)
            return

        # 8. Paste converted text back
        if not set_clipboard(converted):
            self._restore(original_text)
            self.notify("تعذر الوصول للحافظة", ok=False)
            return

        time.sleep(0.04)
        send_ctrl_combo(VK_V)
        time.sleep(0.06)

        # If auto-selected in a field/chat, send Right arrow / End to place cursor at the end
        if auto_selected:
            _key(VK_RIGHT)
            _key(VK_RIGHT, up=True)

        # 9. Restore user's previous clipboard content
        time.sleep(0.35)
        self._restore(original_text)

        # Sound beep
        if self.settings.get("beep", True) and winsound:
            try:
                winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                pass

        self.notify("✓ تم التحويل")

    @staticmethod
    def _restore(original_text):
        if original_text is not None:
            set_clipboard(original_text)


def acquire_single_instance():
    handle = kernel32.CreateMutexW(None, False, "Local\\ArabicKeyConverterApp_v3")
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        # Signal running instance to show its window and floating widget!
        ev = kernel32.OpenEventW(0x0002, False, "Local\\ArabicKeyConverter_ShowEvent")  # EVENT_MODIFY_STATE
        if ev:
            kernel32.SetEvent(ev)
            kernel32.CloseHandle(ev)
        return None
    return handle or True


def enable_dpi_awareness():
    try:
        ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


if __name__ == "__main__":
    enable_dpi_awareness()
    _instance = acquire_single_instance()
    if _instance is None:
        # Already running: signaled the existing instance to pop up, exit cleanly
        sys.exit(0)

    root = tk.Tk()
    app = AppUI(root)
    root.mainloop()
