"""
Emoji Maker View
UI for converting images to emojis and managing custom emoji collection.
"""

import flet as ft
from pathlib import Path
from PIL import Image
from utils.styles import ColorPalette
from utils.emoji_maker import EmojiMaker, EMOJI_SIZES, DEFAULT_EMOJI_FOLDER


class EmojiMakerView(ft.Container):
    def __init__(self, page: ft.Page, file_picker: ft.FilePicker):
        super().__init__()
        self.page = page
        self.file_picker = file_picker
        self.expand = True
        
        # Configure file picker
        self.file_picker.on_result = self.on_file_selected
        
        # Initialize emoji maker
        self.emoji_maker = EmojiMaker()
        
        # State
        self.selected_file_path = None
        self.current_emoji = None
        self.selected_size = 128
        self.remove_background = False
        
        # UI Components
        self._build_components()
        self.content = self._build_ui()
        
        # Load existing emojis (without update since not on page yet)
        self._load_emoji_library_initial()
    
    def _build_components(self):
        """Initialize all UI components."""
        
        # Source image preview
        self.source_image = ft.Image(
            src="",
            visible=False,
            height=200,
            width=200,
            fit=ft.ImageFit.CONTAIN,
            border_radius=12,
        )
        
        # Result emoji preview
        self.result_image = ft.Image(
            src="",
            visible=False,
            height=150,
            width=150,
            fit=ft.ImageFit.CONTAIN,
            border_radius=12,
        )
        
        # Size dropdown
        self.size_dropdown = ft.Dropdown(
            label="Emoji Size",
            value="Standard (128x128)",
            options=[ft.dropdown.Option(key) for key in EMOJI_SIZES.keys()],
            on_change=self.on_size_change,
            width=200,
            border_color=ColorPalette.BORDER,
            focused_border_color=ColorPalette.PRIMARY,
        )
        
        # Remove background checkbox
        self.bg_checkbox = ft.Checkbox(
            label="Remove white background",
            value=False,
            on_change=self.on_bg_toggle,
            check_color=ColorPalette.SURFACE,
            fill_color={
                ft.ControlState.SELECTED: ColorPalette.PRIMARY,
            }
        )
        
        # Custom name input
        self.name_input = ft.TextField(
            label="Custom name (optional)",
            hint_text="Leave empty for auto-naming",
            width=250,
            border_color=ColorPalette.BORDER,
            focused_border_color=ColorPalette.PRIMARY,
            cursor_color=ColorPalette.PRIMARY,
        )
        
        # Action buttons
        self.convert_btn = ft.ElevatedButton(
            "Convert to Emoji",
            icon=ft.Icons.AUTO_FIX_HIGH,
            on_click=self.convert_image,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.PRIMARY,
                color=ColorPalette.SURFACE,
                padding=ft.padding.symmetric(horizontal=25, vertical=15),
            )
        )
        
        self.copy_btn = ft.ElevatedButton(
            "Copy to Clipboard",
            icon=ft.Icons.CONTENT_COPY,
            on_click=self.copy_to_clipboard,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.SECONDARY,
                color=ColorPalette.SURFACE,
                padding=ft.padding.symmetric(horizontal=25, vertical=15),
            )
        )
        
        # Emoji library grid
        self.emoji_grid = ft.GridView(
            runs_count=6,
            max_extent=100,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            expand=True,
        )
        
        # Status text
        self.status_text = ft.Text(
            "",
            size=12,
            color=ColorPalette.TEXT_SECONDARY,
        )
    
    def _build_ui(self):
        """Build the main UI layout."""
        
        # Header
        header = ft.Column([
            ft.Text(
                "Emoji Maker",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=ColorPalette.TEXT_PRIMARY,
            ),
            ft.Text(
                "Convert your images to emoji format. Copy to clipboard and use Win+V to access your custom emojis!",
                size=14,
                color=ColorPalette.TEXT_SECONDARY,
            ),
        ], spacing=5)
        
        # Source image section
        source_section = ft.Container(
            content=ft.Column([
                ft.Text("Source Image", size=16, weight=ft.FontWeight.W_500, color=ColorPalette.PRIMARY),
                ft.Container(
                    content=ft.Column([
                        self.source_image,
                        ft.ElevatedButton(
                            "Select Image",
                            icon=ft.Icons.IMAGE_SEARCH,
                            on_click=lambda _: self.file_picker.pick_files(
                                allow_multiple=False,
                                allowed_extensions=["jpg", "jpeg", "png", "webp", "gif", "bmp"]
                            ),
                            style=ft.ButtonStyle(padding=20),
                        ),
                    ], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    ),
                    padding=20,
                    bgcolor=ColorPalette.CONTAINER_BG,
                    border_radius=12,
                    width=250,
                    height=300,
                    alignment=ft.alignment.center,
                ),
            ], spacing=10),
        )
        
        # Options section
        options_section = ft.Container(
            content=ft.Column([
                ft.Text("Options", size=16, weight=ft.FontWeight.W_500, color=ColorPalette.PRIMARY),
                ft.Container(
                    content=ft.Column([
                        self.size_dropdown,
                        self.bg_checkbox,
                        self.name_input,
                        ft.Container(height=10),
                        self.convert_btn,
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=20,
                    bgcolor=ColorPalette.CONTAINER_BG,
                    border_radius=12,
                    width=280,
                ),
            ], spacing=10),
        )
        
        # Result section
        result_section = ft.Container(
            content=ft.Column([
                ft.Text("Result", size=16, weight=ft.FontWeight.W_500, color=ColorPalette.PRIMARY),
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=self.result_image,
                            bgcolor="#2a2a3a",
                            border_radius=12,
                            padding=20,
                            width=180,
                            height=180,
                            alignment=ft.alignment.center,
                        ),
                        self.copy_btn,
                        self.status_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    ),
                    padding=20,
                    bgcolor=ColorPalette.CONTAINER_BG,
                    border_radius=12,
                    width=250,
                ),
            ], spacing=10),
        )
        
        # Top row: conversion workflow
        conversion_row = ft.Row(
            controls=[
                source_section,
                ft.Icon(ft.Icons.ARROW_FORWARD, size=40, color=ColorPalette.PRIMARY),
                options_section,
                ft.Icon(ft.Icons.ARROW_FORWARD, size=40, color=ColorPalette.PRIMARY),
                result_section,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=20,
        )
        
        # Library section
        library_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Your Emoji Library",
                        size=18,
                        weight=ft.FontWeight.W_500,
                        color=ColorPalette.PRIMARY,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        icon_color=ColorPalette.TEXT_SECONDARY,
                        tooltip="Refresh library",
                        on_click=lambda _: self._refresh_emoji_library(),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        icon_color=ColorPalette.TEXT_SECONDARY,
                        tooltip="Open emoji folder",
                        on_click=self.open_emoji_folder,
                    ),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Text(
                    f"Saved in: {DEFAULT_EMOJI_FOLDER}",
                    size=11,
                    color=ColorPalette.TEXT_SECONDARY,
                ),
                ft.Container(
                    content=self.emoji_grid,
                    bgcolor=ColorPalette.CONTAINER_BG,
                    border_radius=12,
                    padding=15,
                    expand=True,
                ),
            ], spacing=10, expand=True),
            expand=True,
            padding=ft.padding.only(top=20),
        )
        
        # Tip section
        tip_section = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.TIPS_AND_UPDATES, color=ColorPalette.SECONDARY, size=20),
                ft.Text(
                    "💡 Tip: Enable Windows Clipboard History (Win+V) to access all your copied emojis!",
                    size=13,
                    color=ColorPalette.SECONDARY,
                ),
            ], spacing=10),
            bgcolor=ColorPalette.with_opacity(ColorPalette.SECONDARY, 0.1),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            margin=ft.margin.only(top=15),
        )
        
        return ft.Column([
            header,
            ft.Divider(height=20, color=ColorPalette.BORDER),
            conversion_row,
            tip_section,
            library_section,
        ], expand=True, spacing=10)
    
    def on_file_selected(self, e: ft.FilePickerResultEvent):
        """Handle file selection."""
        if e.files and len(e.files) > 0:
            self.selected_file_path = e.files[0].path
            
            # Show source image preview
            self.source_image.src = self.selected_file_path
            self.source_image.visible = True
            self.source_image.update()
            
            # Enable convert button
            self.convert_btn.disabled = False
            self.convert_btn.update()
            
            # Reset result
            self.result_image.visible = False
            self.copy_btn.disabled = True
            self.current_emoji = None
            self.result_image.update()
            self.copy_btn.update()
    
    def on_size_change(self, e):
        """Handle size dropdown change."""
        self.selected_size = EMOJI_SIZES[e.control.value]
    
    def on_bg_toggle(self, e):
        """Handle background removal toggle."""
        self.remove_background = e.control.value
    
    def convert_image(self, e):
        """Convert the selected image to emoji format."""
        if not self.selected_file_path:
            return
        
        try:
            # Get custom name if provided
            custom_name = self.name_input.value.strip() if self.name_input.value else None
            
            # Convert image
            self.current_emoji = self.emoji_maker.convert_to_emoji(
                image_path=self.selected_file_path,
                size=self.selected_size,
                remove_background=self.remove_background,
                output_name=custom_name,
                save_to_folder=True
            )
            
            # Update result preview
            # Save temporary file for preview
            temp_path = Path.home() / ".temp_emoji_preview.png"
            self.current_emoji.save(temp_path, "PNG")
            
            self.result_image.src = str(temp_path)
            self.result_image.visible = True
            self.result_image.update()
            
            # Enable copy button
            self.copy_btn.disabled = False
            self.copy_btn.update()
            
            # Update status
            self.status_text.value = f"✓ Emoji created ({self.selected_size}x{self.selected_size})"
            self.status_text.color = ColorPalette.PRIMARY
            self.status_text.update()
            
            # Refresh library
            self._refresh_emoji_library()
            
            # Show success message
            self.page.open(
                ft.SnackBar(
                    content=ft.Text(f"Emoji created and saved!"),
                    action="OK",
                    bgcolor=ColorPalette.PRIMARY,
                )
            )
            
        except Exception as ex:
            self.page.open(
                ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"),
                    bgcolor=ColorPalette.ERROR,
                )
            )
    
    def copy_to_clipboard(self, e):
        """Copy current emoji to clipboard."""
        if not self.current_emoji:
            return
        
        try:
            # Copy with PNG format for transparency support
            success = self.emoji_maker.copy_png_to_clipboard(self.current_emoji)
            
            if success:
                self.status_text.value = "✓ Copied! Use Ctrl+V to paste"
                self.status_text.color = ColorPalette.PRIMARY
                self.status_text.update()
                
                self.page.open(
                    ft.SnackBar(
                        content=ft.Text("Emoji copied! Use Win+V to see clipboard history"),
                        action="OK",
                    )
                )
            else:
                raise Exception("Failed to copy")
                
        except Exception as ex:
            self.page.open(
                ft.SnackBar(
                    content=ft.Text(f"Error copying: {str(ex)}"),
                    bgcolor=ColorPalette.ERROR,
                )
            )
    
    def _load_emoji_library_initial(self):
        """Load emoji library initially (without calling update)."""
        self.emoji_grid.controls.clear()
        
        emojis = self.emoji_maker.get_saved_emojis()
        
        if not emojis:
            # Show empty state
            self.emoji_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.EMOJI_EMOTIONS_OUTLINED, size=48, color=ColorPalette.TEXT_SECONDARY),
                        ft.Text("No emojis yet", color=ColorPalette.TEXT_SECONDARY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                )
            )
        else:
            for emoji_path in emojis:
                self._add_emoji_card(emoji_path)
    
    def _refresh_emoji_library(self):
        """Refresh the emoji library grid."""
        self._load_emoji_library_initial()
        self.emoji_grid.update()
    
    def _add_emoji_card(self, emoji_path: Path):
        """Add an emoji card to the grid."""
        
        def copy_emoji(e, path=emoji_path):
            """Copy this emoji to clipboard."""
            try:
                img = self.emoji_maker.load_emoji(path)
                success = self.emoji_maker.copy_png_to_clipboard(img)
                if success:
                    self.page.open(
                        ft.SnackBar(
                            content=ft.Text(f"Copied {path.stem}!"),
                            duration=1500,
                        )
                    )
            except Exception as ex:
                print(f"Error copying emoji: {ex}")
        
        def delete_emoji(e, path=emoji_path):
            """Delete this emoji."""
            if self.emoji_maker.delete_emoji(path):
                self._refresh_emoji_library()
                self.page.open(
                    ft.SnackBar(
                        content=ft.Text(f"Deleted {path.stem}"),
                        duration=1500,
                    )
                )
        
        card = ft.Container(
            content=ft.Stack([
                # Emoji image (clickable to copy)
                ft.Container(
                    content=ft.Image(
                        src=str(emoji_path),
                        width=70,
                        height=70,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    on_click=copy_emoji,
                    tooltip=f"Click to copy: {emoji_path.stem}",
                    ink=True,
                    border_radius=8,
                    padding=10,
                    expand=True,
                ),
                # Delete button (top-right corner)
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=14,
                        icon_color=ColorPalette.TEXT_SECONDARY,
                        tooltip="Delete",
                        on_click=delete_emoji,
                        style=ft.ButtonStyle(
                            padding=2,
                            bgcolor=ft.Colors.with_opacity(0.5, ColorPalette.SURFACE),
                        ),
                    ),
                    alignment=ft.alignment.top_right,
                ),
            ]),
            bgcolor=ColorPalette.SURFACE,
            border_radius=10,
            border=ft.border.all(1, ColorPalette.BORDER),
        )
        
        self.emoji_grid.controls.append(card)
    
    def open_emoji_folder(self, e):
        """Open the emoji folder in file explorer."""
        import subprocess
        try:
            subprocess.run(['explorer', str(self.emoji_maker.emoji_folder)], check=True)
        except Exception as ex:
            self.page.open(
                ft.SnackBar(
                    content=ft.Text(f"Could not open folder: {ex}"),
                    bgcolor=ColorPalette.ERROR,
                )
            )


