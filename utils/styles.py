import flet as ft

class ColorPalette:
    # Modern Dark Theme (Graphite/Teal inspired)
    BACKGROUND = "#1A1B26"  # Deep Blue-Grey
    SURFACE = "#24283B"     # Slightly lighter Blue-Grey
    PRIMARY = "#4FD6BE"     # Teal/Mint Accent
    SECONDARY = "#BB9AF7"   # Soft Purple Accent
    ERROR = "#F7768E"       # Soft Red
    
    # Text
    TEXT_PRIMARY = "#C0CAF5" # Off-white/Blue-ish
    TEXT_SECONDARY = "#565F89" # Muted Blue-Grey
    
    # UI Elements
    BORDER = "#414868"
    CONTAINER_BG = "#292E42"

    @staticmethod
    def with_opacity(color: str, opacity: float) -> str:
        """Apply opacity to a hex color code. Returns #AARRGGBB."""
        if color.startswith("#"):
            c = color.lstrip("#")
            if len(c) == 6:
                alpha = int(opacity * 255)
                return f"#{alpha:02x}{c}"
        return color

class TextStyles:
    HEADER = ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=ColorPalette.TEXT_PRIMARY, font_family="Inter")
    SUBHEADER = ft.TextStyle(size=18, weight=ft.FontWeight.W_500, color=ColorPalette.PRIMARY, font_family="Inter")
    BODY = ft.TextStyle(size=14, color=ColorPalette.TEXT_PRIMARY, font_family="Inter")
    CAPTION = ft.TextStyle(size=12, color=ColorPalette.TEXT_SECONDARY, font_family="Inter")
    MONO = ft.TextStyle(size=13, color=ColorPalette.SECONDARY, font_family="JetBrains Mono")
