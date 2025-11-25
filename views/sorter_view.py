import flet as ft
from utils.styles import ColorPalette, TextStyles

def SorterView():
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=80, color=ColorPalette.PRIMARY),
                ft.Text("File Sorter", style=TextStyles.HEADER),
                ft.Text("Coming Soon", style=TextStyles.SUBHEADER),
                ft.Text("This module is under construction.", style=TextStyles.BODY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=ColorPalette.CONTAINER_BG,
        border_radius=15,
        border=ft.border.all(1, ColorPalette.BORDER),
    )
