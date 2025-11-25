import flet as ft
import os
import threading
from typing import List, Dict
from utils.styles import ColorPalette, TextStyles
from utils.ocr_helper import OCRHelper

class OCRView(ft.Container):
    def __init__(self, page: ft.Page, file_picker: ft.FilePicker):
        super().__init__(expand=True)
        self.page = page
        self.ocr_helper = OCRHelper()
        self.files_data: List[Dict] = [] # List of {path, original_name, new_name, status, text_preview}
        
        # UI Components
        self.file_picker = file_picker
        # self.page.overlay.append(self.file_picker) # Managed by main.py
        
        self.drop_zone = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=64, color=ColorPalette.PRIMARY),
                    ft.Text("Drop screenshots here or click to select", style=TextStyles.SUBHEADER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ColorPalette.with_opacity(ColorPalette.PRIMARY, 0.05),
            border=ft.border.all(2, ColorPalette.PRIMARY),
            border_radius=15,
            padding=40,
            on_click=lambda _: self.file_picker.pick_files(allow_multiple=True, file_type=ft.FilePickerFileType.IMAGE),
            alignment=ft.alignment.center,
            ink=True,
        )

        self.files_list = ft.ListView(expand=True, spacing=10)
        
        self.lang_dropdown = ft.Dropdown(
            label="OCR Language",
            options=[
                ft.dropdown.Option("eng+fra", "English + French"),
                ft.dropdown.Option("eng", "English"),
                ft.dropdown.Option("fra", "French"),
            ],
            value="eng+fra",
            on_change=self.on_config_change
        )
        
        self.word_count_slider = ft.Slider(
            min=1, max=5, divisions=4, label="{value} keywords", value=3,
            on_change=self.on_config_change
        )

        self.apply_btn = ft.ElevatedButton(
            "Rename All",
            icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.PRIMARY, 
                color=ColorPalette.BACKGROUND,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            on_click=self.rename_all,
            disabled=True
        )

        self.padding = 20
        self.content = ft.Column(
            [
                ft.Text("OCR Screenshot Organizer", style=TextStyles.HEADER),
                ft.Container(height=10),
                self.drop_zone,
                ft.Container(height=20),
                ft.Row([
                    self.lang_dropdown,
                    ft.Column([ft.Text("Keywords:"), self.word_count_slider]),
                    ft.Container(expand=True),
                    self.apply_btn
                ]),
                ft.Divider(),
                self.files_list
            ],
            expand=True
        )

    def on_config_change(self, e):
        self.ocr_helper.lang = self.lang_dropdown.value
        # Re-generate names if we have text
        for data in self.files_data:
            if data.get('text_preview'):
                data['new_name'] = self.ocr_helper.generate_filename(
                    data['text_preview'], 
                    os.path.splitext(data['original_name'])[1],
                    int(self.word_count_slider.value)
                )
        self.update_list()

    def on_files_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                self.files_data.append({
                    'path': f.path,
                    'original_name': f.name,
                    'new_name': 'Analyzing...',
                    'status': 'pending',
                    'text_preview': ''
                })
            self.update_list()
            self.start_ocr_process()

    def start_ocr_process(self):
        threading.Thread(target=self.process_files).start()

    def process_files(self):
        for data in self.files_data:
            if data['status'] == 'pending':
                data['status'] = 'processing'
                self.update_list_safe()
                
                text = self.ocr_helper.extract_text(data['path'])
                data['text_preview'] = text[:50] + "..." if text else "No text found"
                
                data['new_name'] = self.ocr_helper.generate_filename(
                    text, 
                    os.path.splitext(data['original_name'])[1],
                    int(self.word_count_slider.value)
                )
                
                data['status'] = 'done'
                self.update_list_safe()
        
        # Enable rename button if we have processed files
        self.apply_btn.disabled = False
        self.update_list_safe()

    def update_list_safe(self):
        self.update_list()

    def update_list(self):
        self.files_list.controls.clear()
        for i, data in enumerate(self.files_data):
            self.files_list.controls.append(self.create_file_item(i, data))
        self.apply_btn.disabled = not any(d['status'] == 'done' for d in self.files_data)
        self.update()

    def create_file_item(self, index, data):
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.IMAGE, size=40, color=ColorPalette.SECONDARY),
                    ft.Column([
                        ft.Text(data['original_name'], style=TextStyles.BODY, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Detected: {data['text_preview']}", style=TextStyles.CAPTION),
                    ], expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD, color=ColorPalette.TEXT_SECONDARY),
                    ft.TextField(
                        value=data['new_name'], 
                        expand=True, 
                        on_change=lambda e, idx=index: self.update_name(idx, e.control.value),
                        text_style=TextStyles.MONO,
                        border_color=ColorPalette.BORDER,
                        focused_border_color=ColorPalette.PRIMARY,
                    ),
                    self.get_status_icon(data['status'])
                ]),
                padding=15,
                bgcolor=ColorPalette.SURFACE,
                border_radius=10,
            ),
            color=ColorPalette.SURFACE,
            elevation=2,
        )

    def get_status_icon(self, status):
        if status == 'pending': return ft.Icon(ft.Icons.HOURGLASS_EMPTY, color=ColorPalette.TEXT_SECONDARY)
        if status == 'processing': return ft.ProgressRing(width=20, height=20, color=ColorPalette.PRIMARY)
        if status == 'done': return ft.Icon(ft.Icons.CHECK_CIRCLE, color=ColorPalette.PRIMARY)
        if status == 'renamed': return ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE, color=ColorPalette.SECONDARY)
        return ft.Icon(ft.Icons.ERROR, color=ColorPalette.ERROR)

    def update_name(self, index, value):
        self.files_data[index]['new_name'] = value

    def rename_all(self, e):
        count = 0
        for data in self.files_data:
            if data['status'] == 'done':
                try:
                    dir_path = os.path.dirname(data['path'])
                    new_path = os.path.join(dir_path, data['new_name'])
                    os.rename(data['path'], new_path)
                    data['path'] = new_path
                    data['original_name'] = data['new_name']
                    data['status'] = 'renamed'
                    count += 1
                except Exception as ex:
                    print(f"Rename error: {ex}")
        
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Renamed {count} files"))
        self.page.snack_bar.open = True
        self.update_list()
