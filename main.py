import flet as ft
from views.renamer_view import RenamerView
from views.sorter_view import SorterView
from views.duplicates_view import DuplicatesView
from views.ocr_view import OCRView
from views.exif_view import ExifView
from utils.styles import ColorPalette
from views.color_palette_view import ColorPaletteView

def main(page: ft.Page):
    page.title = "File Toolbox"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = ColorPalette.BACKGROUND
    
    # Fonts
    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap",
        "JetBrains Mono": "https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap"
    }
    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme=ft.ColorScheme(
            primary=ColorPalette.PRIMARY,
            secondary=ColorPalette.SECONDARY,
            background=ColorPalette.BACKGROUND,
            surface=ColorPalette.SURFACE,
            error=ColorPalette.ERROR,
        )
    )

    # Content container reference
    content_container = ft.Ref[ft.Container]()
    current_view_index = 0
    
    # Create file picker at page level (will be used by RenamerView)
    renamer_file_picker = ft.FilePicker()
    page.overlay.append(renamer_file_picker)

    # Create file picker for OCR View
    ocr_file_picker = ft.FilePicker()
    page.overlay.append(ocr_file_picker)

    # Create file picker for Color Palette View
    palette_file_picker = ft.FilePicker()
    page.overlay.append(palette_file_picker)

    def get_view(index):
        """Get or recreate view for the given index"""
        if index == 0:
            return RenamerView(page, renamer_file_picker)
        elif index == 1:
            return SorterView()
        elif index == 2:
            return DuplicatesView()
        elif index == 3:
            view = OCRView(page, ocr_file_picker)
            ocr_file_picker.on_result = view.on_files_selected
            return view
        elif index == 4:
            return ExifView()
        elif index == 5:
            return ColorPaletteView(page, palette_file_picker)

    def on_nav_change(e):
        nonlocal current_view_index
        current_view_index = e.control.selected_index
        # Update only the content, not the whole page
        content_container.current.content = get_view(current_view_index)
        content_container.current.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, 
                selected_icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE_ROUNDED, 
                label="Renamer"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.FOLDER_OPEN, 
                selected_icon=ft.Icons.FOLDER_OPEN_ROUNDED, 
                label="Sorter"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.COPY_ALL, 
                selected_icon=ft.Icons.COPY_ALL_ROUNDED, 
                label="Duplicates"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.TEXT_SNIPPET, 
                selected_icon=ft.Icons.TEXT_SNIPPET_ROUNDED, 
                label="OCR"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CAMERA_ALT, 
                selected_icon=ft.Icons.CAMERA_ALT_ROUNDED, 
                label="EXIF"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PALETTE, 
                selected_icon=ft.Icons.PALETTE_ROUNDED, 
                label="Palette"
            ),
        ],
        on_change=on_nav_change,
        bgcolor=ColorPalette.SURFACE,
        indicator_color=ColorPalette.PRIMARY,
        indicator_shape=ft.RoundedRectangleBorder(radius=10),
    )

    # Initial Render
    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1, color=ColorPalette.BORDER),
                ft.Container(
                    ref=content_container,
                    content=get_view(0),
                    expand=True,
                    padding=20, # Add global padding for content
                ),
            ],
            expand=True,
            spacing=0,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
