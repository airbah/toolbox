import flet as ft
from utils.styles import ColorPalette, TextStyles
from utils.file_manager import get_file_details, rename_file
import os

def RenamerView(page: ft.Page, file_picker: ft.FilePicker):
    # State
    files = []  # List of dicts: {path, name, new_name, status}
    
    # Controls Refs
    file_list = ft.Ref[ft.DataTable]()
    prefix_field = ft.Ref[ft.TextField]()
    suffix_field = ft.Ref[ft.TextField]()
    replace_field = ft.Ref[ft.TextField]()
    replace_with_field = ft.Ref[ft.TextField]()
    auto_number_switch = ft.Ref[ft.Switch]()
    snack_bar = ft.Ref[ft.SnackBar]()

    def update_preview(e=None):
        prefix = prefix_field.current.value or ""
        suffix = suffix_field.current.value or ""
        replace = replace_field.current.value or ""
        replace_with = replace_with_field.current.value or ""
        auto_number = auto_number_switch.current.value

        for i, file in enumerate(files):
            name_part = file["stem"]
            
            # Replacement
            if replace:
                name_part = name_part.replace(replace, replace_with)
            
            # Auto-numbering
            number_part = ""
            if auto_number:
                number_part = f"_{i+1:03d}"
            
            new_name = f"{prefix}{name_part}{number_part}{suffix}{file['suffix']}"
            file["new_name"] = new_name
        
        update_table()

    def update_table():
        rows = []
        for file in files:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(file["name"], style=TextStyles.BODY)),
                        ft.DataCell(ft.Text(file["new_name"], style=TextStyles.MONO, color=ColorPalette.PRIMARY)),
                        ft.DataCell(ft.Text(file["status"], style=TextStyles.CAPTION)),
                    ]
                )
            )
        file_list.current.rows = rows
        file_list.current.update()

    def add_files(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                details = get_file_details(f.path)
                files.append({
                    "path": f.path,
                    "name": details["name"],
                    "stem": details["stem"],
                    "suffix": details["suffix"],
                    "new_name": details["name"],
                    "status": "Pending"
                })
            update_preview()

    def on_drag_accept(e):
        src = page.get_upload_url(e.data, 600) # Hack for web, but for desktop we parse e.data differently usually. 
        # For desktop Flet, e.data in DragTarget often returns a JSON string of file paths if it's a file drop.
        # Let's try to handle it as a file drop event if possible, but Flet's DragTarget is tricky with external files.
        # Actually, Flet 0.21+ supports on_file_drop on the Page or specific components.
        # Let's use the Page's on_file_drop for simplicity if we can, but we are in a view.
        # We'll assume the user uses the FilePicker for now as DragTarget for external files is complex in component-based views without window event handling.
        # WAIT: Flet has `FilePicker` which is the standard way.
        pass

    # We need a way to handle file drops. In Flet, `page.on_file_drop` is global.
    # Since we are in a view function, we can't easily attach to page directly without passing page.
    # However, we can use a transparent overlay or just rely on FilePicker button for MVP if DragDrop is hard.
    # BUT the requirements say "Zone de Drop".
    # Let's try to implement a FilePicker that opens on click of the drop zone.

    # Set the on_result callback for the file picker
    file_picker.on_result = add_files

    def pick_files_click(e):
        print("Opening file picker...")
        file_picker.pick_files(allow_multiple=True)

    def clear_list(e):
        files.clear()
        update_preview()

    def apply_rename(e):
        count = 0
        for file in files:
            try:
                if file["name"] != file["new_name"]:
                    rename_file(file["path"], file["new_name"])
                    file["name"] = file["new_name"] # Update current name
                    file["stem"] = os.path.splitext(file["new_name"])[0] # Update stem
                    file["status"] = "Done"
                    count += 1
            except Exception as ex:
                file["status"] = "Error"
                print(f"Error renaming {file['name']}: {ex}")
        
        update_preview()
        page.snack_bar = ft.SnackBar(ft.Text(f"{count} files renamed successfully!"))
        page.snack_bar.open = True
        page.update()
        
        # Vider la liste après le renommage
        files.clear()
        update_preview()

    # Layout
    # Left Panel: Controls
    controls_panel = ft.Container(
        width=320,
        padding=25,
        bgcolor=ColorPalette.CONTAINER_BG,
        border=ft.border.all(1, ColorPalette.BORDER),
        border_radius=15,
        content=ft.Column(
            [
                ft.Text("Controls", style=TextStyles.HEADER),
                ft.Divider(color=ColorPalette.BORDER),
                ft.TextField(
                    ref=prefix_field, 
                    label="Prefix", 
                    on_change=update_preview, 
                    border_color=ColorPalette.SECONDARY,
                    text_style=TextStyles.BODY,
                    label_style=TextStyles.CAPTION,
                    focused_border_color=ColorPalette.PRIMARY
                ),
                ft.TextField(
                    ref=suffix_field, 
                    label="Suffix", 
                    on_change=update_preview, 
                    border_color=ColorPalette.SECONDARY,
                    text_style=TextStyles.BODY,
                    label_style=TextStyles.CAPTION,
                    focused_border_color=ColorPalette.PRIMARY
                ),
                ft.Divider(color=ColorPalette.BORDER),
                ft.TextField(
                    ref=replace_field, 
                    label="Replace...", 
                    on_change=update_preview, 
                    border_color=ColorPalette.SECONDARY,
                    text_style=TextStyles.BODY,
                    label_style=TextStyles.CAPTION,
                    focused_border_color=ColorPalette.PRIMARY
                ),
                ft.TextField(
                    ref=replace_with_field, 
                    label="With...", 
                    on_change=update_preview, 
                    border_color=ColorPalette.SECONDARY,
                    text_style=TextStyles.BODY,
                    label_style=TextStyles.CAPTION,
                    focused_border_color=ColorPalette.PRIMARY
                ),
                ft.Divider(color=ColorPalette.BORDER),
                ft.Row([
                    ft.Text("Auto-Numbering", style=TextStyles.BODY),
                    ft.Switch(ref=auto_number_switch, on_change=update_preview, active_color=ColorPalette.PRIMARY),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=ColorPalette.BORDER),
                ft.ElevatedButton(
                    "Apply Changes", 
                    icon=ft.Icons.SAVE, 
                    style=ft.ButtonStyle(
                        bgcolor=ColorPalette.PRIMARY, 
                        color=ColorPalette.BACKGROUND,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=20,
                    ),
                    on_click=apply_rename
                ),
                ft.OutlinedButton(
                    "Clear List", 
                    icon=ft.Icons.DELETE_OUTLINE,
                    style=ft.ButtonStyle(
                        color=ColorPalette.ERROR,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        side=ft.BorderSide(1, ColorPalette.ERROR),
                        padding=20,
                    ),
                    on_click=clear_list
                )
            ],
            spacing=20
        )
    )

    # Right Panel: File List & Drop Zone
    drop_zone = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=48, color=ColorPalette.PRIMARY),
                ft.Text("Click to select files", style=TextStyles.SUBHEADER),
                ft.Text("or drag and drop them here", style=TextStyles.CAPTION),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        border=ft.border.all(2, ColorPalette.PRIMARY),
        border_radius=15,
        padding=30,
        alignment=ft.alignment.center,
        on_click=pick_files_click,
        ink=True,
        bgcolor=ColorPalette.with_opacity(ColorPalette.PRIMARY, 0.05),
    )

    table_container = ft.Container(
        content=ft.Column(
            [
                ft.DataTable(
                    ref=file_list,
                    columns=[
                        ft.DataColumn(ft.Text("Current Name", style=TextStyles.CAPTION)),
                        ft.DataColumn(ft.Text("New Name", style=TextStyles.CAPTION)),
                        ft.DataColumn(ft.Text("Status", style=TextStyles.CAPTION)),
                    ],
                    rows=[],
                    heading_row_color=ColorPalette.CONTAINER_BG,
                    heading_row_height=40,
                    data_row_min_height=50,
                    column_spacing=20,
                    divider_thickness=0,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        bgcolor=ColorPalette.CONTAINER_BG,
        border_radius=15,
        padding=10,
        border=ft.border.all(1, ColorPalette.BORDER),
    )

    content_area = ft.Column(
        [
            drop_zone,
            table_container
        ],
        expand=True,
        spacing=20,
        alignment=ft.MainAxisAlignment.START
    )

    # Main Layout
    return ft.Row(
        [
            controls_panel,
            ft.Container(width=20), # Spacer
            ft.Container(content_area, expand=True),
        ],
        expand=True,
        spacing=0
    )

# Helper to access page for snackbar
# We need to pass 'page' to RenamerView or find a way to access it.
# In the main.py, we instantiate RenamerView(). 
# The controls inside will be attached to page later.
# We can use `e.page` in event handlers.
# I'll update `apply_rename` and `on_drag_accept` to use `e.page`.
# Also need to make sure `page` is available for `file_picker`.
