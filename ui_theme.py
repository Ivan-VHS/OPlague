"""Single-palette DAK theme for the OPlague read-only workbench."""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Iterator

THEME_ENV = "OPLAGUE_UI_THEME"
PALETTES: dict[str, dict[str, str]] = {
    "dak": {
        "bg": "#050505", "surface": "#101010", "elevated": "#181818",
        "fg": "#FFFFFF", "secondary": "#E5E5E5", "muted": "#A6A6A6",
        "heading": "#FFFFFF", "blue": "#FFD700", "blue_hover": "#FFE45C", "on_blue": "#080808",
        "red": "#C43A45", "red_hover": "#D64C57", "on_red": "#FFFFFF",
        "border": "#3A3A3A", "focus": "#FFE45C", "selection": "#3A3100",
        "selection_fg": "#FFFFFF", "disabled": "#A6A6A6", "log": "#050505",
        "log_text": "#FFFFFF", "mode": "dak",
        "success": "#2EAD68", "warning": "#FFD700", "error": "#FF6B72", "info": "#6CA8FF",
        "brand": "#FFD700", "brand_hover": "#FFE45C", "on_brand": "#080808",
        "brand_secondary": "#FFD700", "on_brand_secondary": "#080808",
        "page": "#050505", "surface_alt": "#181818", "text": "#FFFFFF",
        "accent": "#FFD700", "accent_hover": "#FFE45C", "danger": "#C43A45",
        "editor": "#101010", "editor_text": "#FFFFFF",
    },
}

def contrast_ratio(foreground: str, background: str) -> float:
    """Return WCAG contrast ratio for two #RRGGBB colors."""
    def luminance(value: str) -> float:
        raw = value.lstrip("#")
        if len(raw) != 6:
            raise ValueError(f"Expected #RRGGBB color, got {value!r}")
        channels = [int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        linear = [
            channel / 12.92 if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    first, second = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (first + 0.05) / (second + 0.05)



def palette_contrast_issues(palette: dict[str, str]) -> list[str]:
    """Return WCAG AA violations for the fixed semantic palette."""
    pairs = (
        ("fg", "bg"), ("fg", "surface"), ("muted", "bg"),
        ("heading", "bg"), ("on_blue", "blue"), ("on_red", "red"),
        ("selection_fg", "selection"), ("success", "bg"),
        ("warning", "bg"), ("error", "bg"), ("info", "bg"),
        ("on_brand", "brand"), ("on_brand_secondary", "brand_secondary"),
    )
    issues = []
    for foreground, background in pairs:
        if foreground not in palette or background not in palette:
            issues.append(f"missing token: {foreground}/{background}")
        elif contrast_ratio(palette[foreground], palette[background]) < 4.5:
            issues.append(f"{foreground}/{background} below 4.5:1")
    return issues


def set_dpi_awareness() -> None:
    """Request Per-Monitor V2 DPI awareness before creating the Tk root."""
    if os.name != "nt":
        return
    try:
        setter = getattr(ctypes.windll.user32, "SetProcessDpiAwarenessContext", None)
        if setter is not None:
            setter(ctypes.c_void_p(-4))
        else:
            ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        return


def _settings_path() -> Path:
    if os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "OPlague" / "ui-settings.json"
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "oplague" / "ui-settings.json"


def load_preferred_theme() -> str:
    """Return the fixed Dak palette; legacy preferences are normalized on apply."""
    return "dak"

def _save_preferred_theme(mode: str) -> None:
    """Persist the fixed Dak palette with same-directory atomic replacement."""
    if str(mode or "").casefold() not in {"system", "light", "dark", "amber", "dak"}:
        raise ValueError("Theme must be one of the legacy modes or 'dak'")

    temporary: Path | None = None
    try:
        path = _settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump({"version": 1, "mode": "dak"}, stream, ensure_ascii=False, indent=2)
            stream.write(chr(10))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError:
        return
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

def _system_dark() -> bool:
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return int(value) == 0
        except (OSError, ImportError, ValueError):
            return False
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=1, check=False,
            )
            return result.stdout.strip().casefold() == "dark"
        except (OSError, subprocess.SubprocessError):
            return False
    gtk_theme = os.environ.get("GTK_THEME", "").casefold()
    return gtk_theme.endswith(":dark") or "-dark" in gtk_theme


def palette_for(mode: str = "dak", *, system_dark: bool | None = None) -> dict[str, str]:
    """Return the same Dak palette for current and legacy theme identifiers."""
    requested = str(mode or "dak").casefold()
    if requested not in {"dak", "system", "light", "dark", "amber"}:
        raise ValueError("Theme must be one of 'dak', 'system', 'light', 'dark' or 'amber'")

    result = dict(PALETTES["dak"])
    result.update({
        "page": result["bg"],
        "surface_alt": result["elevated"],
        "text": result["fg"],
        "accent": result["brand"],
        "accent_hover": result["brand_hover"],
        "danger": result["red"],
        "editor": result["surface"],
        "editor_text": result["fg"],
        "log_text": result["log_text"],
    })
    issues = palette_contrast_issues(result)
    if issues:
        raise ValueError("Dak palette fails UI/UX 40026: " + "; ".join(issues))
    return result

def _walk(widget: tk.Misc) -> Iterator[tk.Misc]:
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def apply_ui_theme(root: tk.Misc, mode: str = "dak") -> dict[str, str]:
    """Apply a complete theme atomically to ttk and classic Tk data widgets."""
    colors = palette_for(mode)
    root._oplague_theme_mode = "dak"  # type: ignore[attr-defined]
    style = ttk.Style(root)
    try:
        installed = {family.casefold(): family for family in tkfont.families(root)}
    except tk.TclError:
        installed = {}
    display_font = next(
        (installed[name.casefold()] for name in ("Lobster", "Pacifico") if name.casefold() in installed),
        "Georgia",
    )
    script_font = next(
        (installed[name.casefold()] for name in ("Caveat", "Marck Script", "Bad Script") if name.casefold() in installed),
        "Georgia",
    )
    try:
        if "clam" in style.theme_names() and style.theme_use() != "clam":
            style.theme_use("clam")
    except tk.TclError:
        pass

    try:
        root.configure(background=colors["bg"])
        root.option_add("*Font", ("Segoe UI", 10))
        root.option_add("*Text.background", colors["surface"])
        root.option_add("*Text.foreground", colors["fg"])
        root.option_add("*Text.insertBackground", colors["fg"])
        root.option_add("*Text.selectBackground", colors["selection"])
        root.option_add("*Text.selectForeground", colors["selection_fg"])
    except tk.TclError:
        pass

    style.configure(".", font=("Segoe UI", 10), background=colors["bg"], foreground=colors["fg"])
    style.configure("TFrame", background=colors["bg"])
    style.configure("Panel.TFrame", background=colors["surface"])
    style.configure("Card.TFrame", background=colors["elevated"])
    style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
    style.configure("Title.TLabel", background=colors["bg"], foreground=colors["heading"], font=(display_font, 18))
    style.configure("Section.TLabel", background=colors["bg"], foreground=colors["heading"], font=(script_font, 12), padding=(4, 5))
    style.configure("Muted.TLabel", background=colors["bg"], foreground=colors["muted"])
    for status_name in ("Success", "Warning", "Error", "Info"):
        token = status_name.lower()
        style.configure(
            f"Status.{status_name}.TLabel",
            background=colors["bg"], foreground=colors[token], padding=(6, 3),
        )
    style.configure(
        "TButton", padding=(14, 13), focuscolor=colors["focus"],
        foreground=colors["fg"], background=colors["surface"],
        bordercolor=colors["border"], lightcolor=colors["surface"],
        darkcolor=colors["border"], borderwidth=1, relief="flat", focusthickness=2,
    )
    style.map(
        "TButton",
        foreground=[("disabled", colors["disabled"]), ("pressed", colors["selection_fg"]), ("active", colors["fg"])],
        background=[("disabled", colors["elevated"]), ("pressed", colors["selection"]), ("active", colors["elevated"])],
    )
    style.configure(
        "Primary.TButton", padding=(15, 13), foreground=colors["on_brand"],
        background=colors["brand"], bordercolor=colors["brand"],
        lightcolor=colors["brand"], darkcolor=colors["brand"],
    )
    style.map(
        "Primary.TButton",
        foreground=[("disabled", colors["disabled"]), ("!disabled", colors["on_brand"])],
        background=[("disabled", colors["elevated"]), ("pressed", colors["brand"]), ("active", colors["brand_hover"])],
    )
    style.configure(
        "Danger.TButton", padding=(14, 13), foreground=colors["fg"],
        background=colors["surface"], bordercolor=colors["red"],
        lightcolor=colors["surface"], darkcolor=colors["red"],
    )
    style.map(
        "Danger.TButton",
        foreground=[("disabled", colors["disabled"]), ("!disabled", colors["fg"])],
        background=[("disabled", colors["elevated"]), ("pressed", colors["selection"]), ("active", colors["surface"])],
    )
    style.configure(
        "TEntry", fieldbackground=colors["surface"], foreground=colors["fg"],
        bordercolor=colors["border"], lightcolor=colors["border"],
        darkcolor=colors["border"], padding=(8, 8),
    )
    style.map("TEntry", fieldbackground=[("focus", colors["surface"])], bordercolor=[("focus", colors["focus"])])
    style.configure("TNotebook", background=colors["bg"], borderwidth=0, tabmargins=(0, 3, 0, 0))
    style.configure(
        "TNotebook.Tab", padding=(16, 13), background=colors["elevated"],
        foreground=colors["secondary"], borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", colors["surface"]), ("active", colors["selection"])],
        foreground=[("selected", colors["fg"]), ("active", colors["fg"])],
    )
    style.configure("TLabelframe", background=colors["surface"], bordercolor=colors["border"])
    style.configure("TLabelframe.Label", background=colors["surface"], foreground=colors["heading"], font=(script_font, 11))
    style.configure(
        "Treeview", rowheight=42, background=colors["surface"],
        fieldbackground=colors["surface"], foreground=colors["fg"],
        bordercolor=colors["border"], relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", colors["selection"])],
        foreground=[("selected", colors["selection_fg"])],
    )
    style.configure(
        "Treeview.Heading", padding=(9, 9), background=colors["elevated"],
        foreground=colors["fg"], relief="flat", font=("Segoe UI Semibold", 10),
    )
    style.configure("TSeparator", background=colors["border"])
    style.configure("Horizontal.TProgressbar", background=colors["brand"], troughcolor=colors["elevated"])

    for widget in _walk(root):
        try:
            if isinstance(widget, tk.Text):
                widget.configure(
                    background=colors["editor"], foreground=colors["editor_text"],
                    insertbackground=colors["editor_text"], selectbackground=colors["selection"],
                    selectforeground=colors["selection_fg"], highlightbackground=colors["border"],
                    highlightcolor=colors["focus"], highlightthickness=1, relief="flat", borderwidth=1,
                )
            elif isinstance(widget, tk.Listbox):
                widget.configure(
                    background=colors["surface"], foreground=colors["fg"],
                    selectbackground=colors["selection"], selectforeground=colors["selection_fg"],
                    highlightbackground=colors["border"], highlightcolor=colors["focus"],
                    highlightthickness=1, relief="flat", borderwidth=1,
                )
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    background=colors["editor"], foreground=colors["editor_text"],
                    insertbackground=colors["editor_text"], selectbackground=colors["selection"],
                    selectforeground=colors["selection_fg"], highlightbackground=colors["border"],
                    highlightcolor=colors["focus"], relief="flat",
                )
            elif isinstance(widget, tk.Menu):
                widget.configure(
                    background=colors["surface"], foreground=colors["fg"],
                    activebackground=colors["selection"], activeforeground=colors["selection_fg"],
                    relief="flat", borderwidth=0,
                )
        except tk.TclError:
            continue

    root._oplague_native_backdrop = apply_native_backdrop(root)  # type: ignore[attr-defined]
    _save_preferred_theme("dak")
    return colors



def native_backdrop_policy(platform_name: str | None = None) -> str:
    """Choose Windows 11 Mica when the native desktop supports it."""
    import sys
    return "mica" if (platform_name or sys.platform) == "win32" else "opaque"


def apply_native_backdrop(root: tk.Misc) -> bool:
    """Request DWM Mica for the top-level window; unsupported hosts stay opaque."""
    if native_backdrop_policy() != "mica":
        return False
    try:
        root.update_idletasks()
        handle = root.winfo_id()
        dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
        set_attribute = dwmapi.DwmSetWindowAttribute
        set_attribute.argtypes = (
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint,
        )
        set_attribute.restype = ctypes.c_long
        backdrop_type = ctypes.c_int(2)  # DWMSBT_MAINWINDOW
        result = set_attribute(
            ctypes.c_void_p(handle), 38, ctypes.byref(backdrop_type),
            ctypes.sizeof(backdrop_type),
        )
        return result == 0
    except (AttributeError, OSError, tk.TclError, TypeError, ValueError):
        return False
