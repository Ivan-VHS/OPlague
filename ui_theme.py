"""Adaptive Anatidae white-blue-red theme for the OPlague Tk workbench."""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk
from typing import Iterator

THEME_ENV = "OPLAGUE_UI_THEME"
PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#F4F6FA", "surface": "#FFFFFF", "elevated": "#F4F6FA",
        "fg": "#0A1E46", "secondary": "#0039A6", "muted": "#0039A6",
        "heading": "#0039A6", "blue": "#0039A6", "blue_hover": "#0A1E46", "on_blue": "#FFFFFF",
        "red": "#B51A10", "red_hover": "#D52B1E", "on_red": "#FFFFFF",
        "border": "#0039A6", "focus": "#D52B1E",
        "selection": "#0039A6", "selection_fg": "#FFFFFF", "disabled": "#0039A6",
        "log": "#0A1E46", "log_text": "#FFFFFF", "mode": "light",
    },
    "dark": {
        "bg": "#0A1E46", "surface": "#0039A6", "elevated": "#0039A6",
        "fg": "#FFFFFF", "secondary": "#FFFFFF", "muted": "#FFFFFF",
        "heading": "#FFFFFF", "blue": "#0039A6", "blue_hover": "#0A1E46", "on_blue": "#FFFFFF",
        "red": "#B51A10", "red_hover": "#D52B1E", "on_red": "#FFFFFF",
        "border": "#FFFFFF", "focus": "#D52B1E",
        "selection": "#0A1E46", "selection_fg": "#FFFFFF", "disabled": "#FFFFFF",
        "log": "#0A1E46", "log_text": "#FFFFFF", "mode": "dark",
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


def _install_semantic_status_tokens() -> None:
    """Add high-contrast status roles without changing the product's blue/red identity."""
    for theme_name, palette in PALETTES.items():
        dark = theme_name in {"dark", "night"}
        palette.update({
            # Status meaning is carried by text/icon; hues stay inside the shared brand canon.
            "success": "#73B7FF" if dark else "#0039A6",
            "warning": "#FF7D78" if dark else "#B51A10",
            "error": "#FF7D78" if dark else "#B51A10",
            "info": "#FFFFFF" if dark else "#0A1E46",
        })


def palette_contrast_issues(palette: dict[str, str]) -> list[str]:
    """Return WCAG AA text-pair violations for a semantic desktop palette."""
    required_pairs = (
        ("fg", "bg"), ("fg", "surface"), ("muted", "bg"),
        ("heading", "bg"), ("on_blue", "blue"), ("on_red", "red"),
        ("selection_fg", "selection"), ("success", "bg"),
        ("warning", "bg"), ("error", "bg"), ("info", "bg"),
    )
    issues = []
    for foreground, background in required_pairs:
        if foreground not in palette or background not in palette:
            issues.append(f"missing token: {foreground}/{background}")
        elif contrast_ratio(palette[foreground], palette[background]) < 4.5:
            issues.append(
                f"{foreground}/{background} contrast is below 4.5:1"
            )
    return issues


_install_semantic_status_tokens()


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
    """Return the saved System/Light/Dark choice, defaulting to System."""
    try:
        payload = json.loads(_settings_path().read_text(encoding="utf-8"))
        mode = payload.get("mode") if isinstance(payload, dict) else None
        return mode if mode in {"system", "light", "dark"} else "system"
    except (OSError, ValueError, TypeError):
        return "system"


def _save_preferred_theme(mode: str) -> None:
    """Persist a supported theme choice with same-directory atomic replacement."""
    if mode not in {"system", "light", "dark"}:
        raise ValueError("Theme must be 'system', 'light' or 'dark'")

    temporary: Path | None = None
    try:
        path = _settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Keep the temporary file beside the destination so os.replace stays
        # on one filesystem and readers see either the old or complete new JSON.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(
                {"version": 1, "mode": mode},
                stream,
                ensure_ascii=False,
                indent=2,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError:
        # Settings persistence must not prevent the read-only workbench from starting.
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


def palette_for(mode: str = "system", *, system_dark: bool | None = None) -> dict[str, str]:
    """Resolve System/Light/Dark and return semantic plus legacy token names."""
    requested = str(mode or "system").casefold()
    override = os.environ.get(THEME_ENV, "").casefold()
    if requested == "system" and override in PALETTES:
        requested = override
    if requested == "system":
        requested = "dark" if (_system_dark() if system_dark is None else system_dark) else "light"
    if requested not in PALETTES:
        raise ValueError("Theme must be 'system', 'light' or 'dark'")

    result = dict(PALETTES[requested])
    issues = palette_contrast_issues(result)
    if issues:
        raise ValueError("Theme palette fails UI/UX 40026 contrast contract: " + "; ".join(issues))
    # Compatibility aliases retained for the existing OPlague theme API.
    result.update({
        "page": result["bg"],
        "surface_alt": result["elevated"],
        "text": result["fg"],
        "accent": result["blue"],
        "accent_hover": result["blue_hover"],
        "danger": result["red"],
        "success": result["blue"],
        "editor": result["surface"],
        "editor_text": result["fg"],
        "log_text": result["log_text"],
    })
    return result


def _walk(widget: tk.Misc) -> Iterator[tk.Misc]:
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def apply_ui_theme(root: tk.Misc, mode: str = "system") -> dict[str, str]:
    """Apply a complete theme atomically to ttk and classic Tk data widgets."""
    colors = palette_for(mode)
    root._oplague_theme_mode = mode  # type: ignore[attr-defined]
    style = ttk.Style(root)
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
    style.configure("Title.TLabel", background=colors["bg"], foreground=colors["heading"], font=("Georgia", 18, "bold"))
    style.configure("Section.TLabel", background=colors["bg"], foreground=colors["heading"], font=("Georgia", 11, "bold"), padding=(4, 5))
    style.configure("Muted.TLabel", background=colors["bg"], foreground=colors["muted"])
    # Semantic status styles are text-first and remain readable in every theme.
    for status_name in ("Success", "Warning", "Error", "Info"):
        token = status_name.lower()
        style.configure(
            f"Status.{status_name}.TLabel",
            background=colors["bg"],
            foreground=colors[token],
            padding=(6, 3),
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
        "Primary.TButton", padding=(15, 13), foreground=colors["on_blue"],
        background=colors["blue"], bordercolor=colors["blue"],
        lightcolor=colors["blue"], darkcolor=colors["blue"],
    )
    style.map(
        "Primary.TButton",
        foreground=[("disabled", colors["disabled"]), ("!disabled", colors["on_blue"])],
        background=[("disabled", colors["elevated"]), ("pressed", colors["blue"]), ("active", colors["blue_hover"])],
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
    style.configure("TLabelframe.Label", background=colors["surface"], foreground=colors["heading"], font=("Georgia", 10, "bold"))
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
    style.configure("Horizontal.TProgressbar", background=colors["blue"], troughcolor=colors["elevated"])

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

    _save_preferred_theme(mode)
    return colors
