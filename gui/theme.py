import platform
import copy

_system = platform.system()
if _system == "Darwin":
    FONT_FAMILY = "Helvetica Neue"
elif _system == "Windows":
    FONT_FAMILY = "Segoe UI"
else:
    FONT_FAMILY = "Helvetica"

MONO_FAMILY = "Consolas" if _system == "Windows" else "Menlo"

DARK = {
    "BG_BASE":       "#0D0F14",
    "BG_SURFACE":    "#13161E",
    "BG_ELEVATED":   "#1A1D27",
    "BG_HOVER":      "#21253A",
    "BG_SELECTED":   "#252A3D",

    "ACCENT":        "#7C6DED",
    "ACCENT_HOVER":  "#9B8FF5",
    "ACCENT_DIM":    "#3D3572",

    "GREEN":         "#22C55E",
    "RED":           "#EF4444",
    "AMBER":         "#F59E0B",
    "CYAN":          "#06B6D4",

    "TEXT_PRIMARY":  "#F0F2FF",
    "TEXT_SECONDARY":"#8B8FA8",
    "TEXT_MUTED":    "#4B4F6A",

    "BORDER":        "#1E2133",
    "BORDER_FOCUS":  "#7C6DED",
}

LIGHT = {
    "BG_BASE":       "#F0F2F5",
    "BG_SURFACE":    "#FFFFFF",
    "BG_ELEVATED":   "#F7F8FA",
    "BG_HOVER":      "#E8EAF0",
    "BG_SELECTED":   "#DDE0EA",

    "ACCENT":        "#6C5CE7",
    "ACCENT_HOVER":  "#8577ED",
    "ACCENT_DIM":    "#E0DBFA",

    "GREEN":         "#16A34A",
    "RED":           "#DC2626",
    "AMBER":         "#D97706",
    "CYAN":          "#0891B2",

    "TEXT_PRIMARY":  "#1A1D2E",
    "TEXT_SECONDARY":"#5A5E76",
    "TEXT_MUTED":    "#9A9EB6",

    "BORDER":        "#D4D6DE",
    "BORDER_FOCUS":  "#6C5CE7",
}

ACCENT_PRESETS = {
    "purple":  {"ACCENT": "#7C6DED", "ACCENT_HOVER": "#9B8FF5", "ACCENT_DIM": "#3D3572", "BORDER_FOCUS": "#7C6DED"},
    "blue":    {"ACCENT": "#3B82F6", "ACCENT_HOVER": "#60A5FA", "ACCENT_DIM": "#1E3A5F", "BORDER_FOCUS": "#3B82F6"},
    "green":   {"ACCENT": "#22C55E", "ACCENT_HOVER": "#4ADE80", "ACCENT_DIM": "#14532D", "BORDER_FOCUS": "#22C55E"},
    "red":     {"ACCENT": "#EF4444", "ACCENT_HOVER": "#F87171", "ACCENT_DIM": "#7F1D1D", "BORDER_FOCUS": "#EF4444"},
    "cyan":    {"ACCENT": "#06B6D4", "ACCENT_HOVER": "#22D3EE", "ACCENT_DIM": "#164E63", "BORDER_FOCUS": "#06B6D4"},
    "amber":   {"ACCENT": "#F59E0B", "ACCENT_HOVER": "#FBBF24", "ACCENT_DIM": "#78350F", "BORDER_FOCUS": "#F59E0B"},
}

H1    = (FONT_FAMILY, 22, "bold")
H2    = (FONT_FAMILY, 16, "bold")
H3    = (FONT_FAMILY, 13, "bold")
BODY  = (FONT_FAMILY, 12, "normal")
SMALL = (FONT_FAMILY, 10, "normal")
MONO  = (MONO_FAMILY, 11, "normal")

PAD_XS = 4
PAD_SM = 8
PAD_MD = 16
PAD_LG = 24
PAD_XL = 32
RADIUS = 10
SIDEBAR_W = 220
SIDEBAR_COLLAPSED = 60
TOPBAR_H = 56


class ThemeManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mode = "dark"
            cls._instance._colors = copy.deepcopy(DARK)
            cls._instance._accent_name = "purple"
            cls._instance._listeners = []
        return cls._instance


    @property
    def mode(self) -> str:
        return self._mode

    @property
    def colors(self) -> dict:
        return self._colors

    def c(self, key: str) -> str:
        return self._colors[key]

    def toggle_mode(self):
        self._mode = "light" if self._mode == "dark" else "dark"
        base = copy.deepcopy(LIGHT if self._mode == "light" else DARK)
        accent_data = ACCENT_PRESETS.get(self._accent_name, {})
        if self._mode == "light":
            light_accent = {
                "purple": "#E0DBFA", "blue": "#DBEAFE", "green": "#DCFCE7",
                "red": "#FEE2E2", "cyan": "#CFFAFE", "amber": "#FEF3C7",
            }
            if self._accent_name in light_accent:
                accent_data = dict(accent_data)
                accent_data["ACCENT_DIM"] = light_accent[self._accent_name]
        base.update(accent_data)
        self._colors = base
        self._notify()

    def set_accent(self, name: str):
        if name not in ACCENT_PRESETS:
            return
        self._accent_name = name
        accent_data = dict(ACCENT_PRESETS[name])
        if self._mode == "light":
            light_accent = {
                "purple": "#E0DBFA", "blue": "#DBEAFE", "green": "#DCFCE7",
                "red": "#FEE2E2", "cyan": "#CFFAFE", "amber": "#FEF3C7",
            }
            if name in light_accent:
                accent_data["ACCENT_DIM"] = light_accent[name]
        self._colors.update(accent_data)
        self._notify()

    def add_listener(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        self._listeners = [cb for cb in self._listeners if cb is not callback]

    def _notify(self):
        for cb in self._listeners:
            try:
                cb(self._colors)
            except Exception:
                pass
