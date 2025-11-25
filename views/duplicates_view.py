import flet as ft
import threading
import time
from typing import List, Optional
from utils.styles import ColorPalette, TextStyles
from utils.duplicate_finder import DuplicateFinder, DuplicateGroup

class DuplicatesView(ft.Container):
    def __init__(self):
        super().__init__(expand=True)
        self.finder = DuplicateFinder()
        self.scan_thread: Optional[threading.Thread] = None
        self.duplicate_groups: List[DuplicateGroup] = []
        
        # UI Components - State 1: Config
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_selected)
        self.selected_folder_text = ft.Text("No folder selected", style=TextStyles.BODY, color=ColorPalette.TEXT_SECONDARY)
        self.recursive_switch = ft.Switch(label="Scan subfolders", value=True, active_color=ColorPalette.PRIMARY)
        self.min_size_slider = ft.Slider(min=0, max=10, divisions=10, label="{value} MB", value=0)
        self.scan_btn = ft.ElevatedButton(
            "Start Scan", 
            icon=ft.Icons.SEARCH, 
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.PRIMARY, 
                color=ColorPalette.BACKGROUND,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            on_click=self.start_scan,
            disabled=True
        )

        # UI Components - State 2: Scanning
        self.progress_bar = ft.ProgressBar(width=400, color=ColorPalette.PRIMARY, bgcolor=ColorPalette.SURFACE)
        self.status_text = ft.Text("Ready", style=TextStyles.BODY)
        self.cancel_btn = ft.OutlinedButton("Cancel", on_click=self.cancel_scan, style=ft.ButtonStyle(color=ColorPalette.ERROR))

        # UI Components - State 3: Results
        self.results_list = ft.ListView(expand=True, spacing=10, padding=20)
        self.results_summary = ft.Text("", style=TextStyles.SUBHEADER)
        self.delete_btn = ft.ElevatedButton(
            "Delete Selected", 
            icon=ft.Icons.DELETE, 
            style=ft.ButtonStyle(bgcolor=ColorPalette.ERROR, color=ColorPalette.TEXT_PRIMARY),
            on_click=self.delete_selected,
            disabled=True
        )

        # Layout Containers
        self.config_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Duplicate Finder", style=TextStyles.HEADER),
                    ft.Divider(color=ColorPalette.BORDER),
                    ft.Row([
                        ft.ElevatedButton(
                            "Select Folder", 
                            icon=ft.Icons.FOLDER_OPEN, 
                            on_click=lambda _: self.folder_picker.get_directory_path(),
                            style=ft.ButtonStyle(
                                bgcolor=ColorPalette.SECONDARY, 
                                color=ColorPalette.BACKGROUND,
                                shape=ft.RoundedRectangleBorder(radius=10)
                            )
                        ),
                        ft.Container(
                            content=self.selected_folder_text,
                            padding=10,
                            border=ft.border.all(1, ColorPalette.BORDER),
                            border_radius=10,
                            expand=True
                        )
                    ]),
                    ft.Container(height=10),
                    self.recursive_switch,
                    ft.Text("Minimum File Size (MB):", style=TextStyles.BODY),
                    self.min_size_slider,
                    ft.Container(height=20),
                    self.scan_btn
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=30,
            bgcolor=ColorPalette.CONTAINER_BG,
            border_radius=15,
            border=ft.border.all(1, ColorPalette.BORDER),
            visible=True,
            alignment=ft.alignment.center
        )

        self.scanning_container = ft.Column(
            [
                ft.Text("Scanning...", style=TextStyles.HEADER),
                ft.Container(height=20),
                self.progress_bar,
                ft.Container(height=10),
                self.status_text,
                ft.Container(height=20),
                self.cancel_btn
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False
        )

        self.results_container = ft.Column(
            [
                ft.Row([
                    self.results_summary,
                    ft.Container(expand=True),
                    ft.PopupMenuButton(
                        icon=ft.Icons.SELECT_ALL,
                        items=[
                            ft.PopupMenuItem(text="Select All", on_click=lambda _: self.select_all(True)),
                            ft.PopupMenuItem(text="Deselect All", on_click=lambda _: self.select_all(False)),
                            ft.PopupMenuItem(text="Select All Except Newest", on_click=lambda _: self.select_smart("newest")),
                            ft.PopupMenuItem(text="Select All Except Oldest", on_click=lambda _: self.select_smart("oldest")),
                        ]
                    ),
                    self.delete_btn
                ]),
                ft.Divider(),
                self.results_list
            ],
            expand=True,
            visible=False
        )

        self.content = ft.Stack([
            self.folder_picker,
            self.config_container,
            self.scanning_container,
            self.results_container
        ])

    def on_folder_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.selected_folder_text.value = e.path
            self.scan_btn.disabled = False
            self.update()

    def start_scan(self, e):
        self.config_container.visible = False
        self.scanning_container.visible = True
        self.results_container.visible = False
        self.update()
        
        path = self.selected_folder_text.value
        recursive = self.recursive_switch.value
        min_size = int(self.min_size_slider.value * 1024 * 1024)
        
        self.scan_thread = threading.Thread(
            target=self.run_scan,
            args=([path], recursive, min_size)
        )
        self.scan_thread.start()

    def run_scan(self, paths, recursive, min_size):
        try:
            for status in self.finder.scan_directory(paths, recursive, min_size):
                self.status_text.value = status
                self.update()
            
            # Scan complete
            self.duplicate_groups = self.finder.scan_directory(paths, recursive, min_size) # Re-run to get result? No, generator yields status then returns? 
            # Wait, generator in python returns value via StopIteration but that's hard to get in for loop.
            # I should modify scan_directory to yield status and then yield result or store result.
            # Let's check duplicate_finder.py again. 
            # It returns list at the end. But generator return value is tricky.
            # I will modify duplicate_finder.py to yield results as the last item or change how I call it.
            # Actually, let's fix duplicate_finder.py to yield a special object or just store it.
            # Or better: yield status strings, and the last yield is the result list?
            # No, type hint says Generator[str, None, List[DuplicateGroup]].
            # To get the return value of a generator:
            # gen = finder.scan_directory(...)
            # for status in gen: ...
            # result = gen.value (only works if caught StopIteration)
            
            # Let's adjust this method to just consume the generator properly.
            gen = self.finder.scan_directory(paths, recursive, min_size)
            try:
                while True:
                    status = next(gen)
                    self.status_text.value = status
                    self.update()
            except StopIteration as e:
                self.duplicate_groups = e.value
                
            self.show_results()
            
        except Exception as e:
            self.status_text.value = f"Error: {str(e)}"
            self.update()

    def cancel_scan(self, e):
        self.finder.stop()
        self.config_container.visible = True
        self.scanning_container.visible = False
        self.update()

    def show_results(self):
        self.scanning_container.visible = False
        self.results_container.visible = True
        
        self.results_list.controls.clear()
        
        total_dupes = sum(len(g.files) - 1 for g in self.duplicate_groups)
        total_size = sum(g.size * (len(g.files) - 1) for g in self.duplicate_groups)
        self.results_summary.value = f"Found {len(self.duplicate_groups)} groups ({total_dupes} duplicates). Potential savings: {total_size / 1024 / 1024:.2f} MB"
        
        for group in self.duplicate_groups:
            self.results_list.controls.append(self.create_group_card(group))
        
        self.update()

    def create_group_card(self, group: DuplicateGroup):
        files_column = ft.Column()
        for file in group.files:
            files_column.controls.append(
                ft.Row([
                    ft.Checkbox(
                        label=f"{file.path} ({file.size/1024:.1f} KB)", 
                        value=False,
                        data=file,
                        on_change=self.on_selection_change,
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW,
                        tooltip="Open File",
                        on_click=lambda _, f=file.path: self.open_file(f)
                    )
                ])
            )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.COPY_ALL, color=ColorPalette.SECONDARY),
                        ft.Text(f"Group Hash: {group.hash_value[:8]}...", style=TextStyles.BODY, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Size: {group.size/1024:.1f} KB", style=TextStyles.MONO)
                    ], spacing=10),
                    ft.Divider(color=ColorPalette.BORDER),
                    files_column
                ]),
                padding=15,
                bgcolor=ColorPalette.SURFACE,
                border_radius=10,
            ),
            color=ColorPalette.SURFACE,
            elevation=2,
        )

    def open_file(self, path: str):
        try:
            self.page.launch_url(f"file://{path}")
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Could not open file: {e}"))
            self.page.snack_bar.open = True
            self.page.update()

    def on_selection_change(self, e):
        # Enable delete button if any checked
        any_checked = False
        for card in self.results_list.controls:
            # Access the column of files
            files_col = card.content.content.controls[1]
            for row in files_col.controls:
                # Checkbox is the first item in the Row
                checkbox = row.controls[0]
                if checkbox.value:
                    any_checked = True
                    break
            if any_checked: break
            
        self.delete_btn.disabled = not any_checked
        self.update()

    def select_all(self, select: bool):
        for card in self.results_list.controls:
            files_col = card.content.content.controls[1]
            for row in files_col.controls:
                checkbox = row.controls[0]
                checkbox.value = select
        self.on_selection_change(None)

    def select_smart(self, criteria: str):
        for i, card in enumerate(self.results_list.controls):
            group = self.duplicate_groups[i]
            files_col = card.content.content.controls[1]
            
            # Sort files in group based on criteria
            if criteria == "newest":
                # Keep newest unchecked, check others
                sorted_files = sorted(group.files, key=lambda x: x.modified, reverse=True)
                keep_file = sorted_files[0]
            elif criteria == "oldest":
                # Keep oldest unchecked, check others
                sorted_files = sorted(group.files, key=lambda x: x.modified)
                keep_file = sorted_files[0]
            
            for row in files_col.controls:
                checkbox = row.controls[0]
                file = checkbox.data
                checkbox.value = (file != keep_file)
                
        self.on_selection_change(None)

    def delete_selected(self, e):
        files_to_delete = []
        for card in self.results_list.controls:
            files_col = card.content.content.controls[1]
            for row in files_col.controls:
                checkbox = row.controls[0]
                if checkbox.value:
                    files_to_delete.append(checkbox.data.path)
        
        count = 0
        for path in files_to_delete:
            if self.finder.delete_file(path):
                count += 1
        
        # Show snackbar
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Moved {count} files to trash"))
        self.page.snack_bar.open = True
        
        # Reset view
        self.config_container.visible = True
        self.results_container.visible = False
        self.duplicate_groups = []
        self.update()
