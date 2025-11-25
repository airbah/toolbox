import flet as ft
from utils.styles import ColorPalette, TextStyles

def ExifView():
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.CAMERA_ALT, size=64, color=ColorPalette.SECONDARY),
                ft.Text("EXIF Cleaner", style=TextStyles.HEADER),
                ft.Text("Coming Soon", style=TextStyles.SUBHEADER),
                ft.Text("This module is under construction.", style=TextStyles.BODY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True
    )
