import flet as ft
import colorgram
from PIL import Image
from utils.styles import ColorPalette

class ColorPaletteView(ft.Container):
    def __init__(self, page: ft.Page, file_picker: ft.FilePicker):
        super().__init__()
        self.page = page
        self.file_picker = file_picker
        self.expand = True
        
        # Configure file picker
        self.file_picker.on_result = self.on_file_selected
        self.file_picker.allowed_extensions = ["jpg", "jpeg", "png", "webp"]
        
        # State
        self.selected_file_path = None
        self.num_colors = 8
        self.extracted_colors = []
        self.pil_image = None # Store PIL image for pixel access
        
        # UI Components
        self.image_control = ft.Image(
            src="",
            visible=False,
            height=600, # Increased height
            fit=ft.ImageFit.CONTAIN,
            border_radius=10,
        )
        
        # Wrap image in GestureDetector for pipette
        self.image_gesture_detector = ft.GestureDetector(
            content=self.image_control,
            on_tap_down=self.pick_color_at_point,
            mouse_cursor=ft.MouseCursor.CLICK,
        )

        # Wrap GestureDetector in InteractiveViewer for Zoom
        self.interactive_viewer = ft.InteractiveViewer(
            content=self.image_gesture_detector,
            min_scale=0.5,
            max_scale=5.0,
            boundary_margin=ft.margin.all(20),
        )
        
        self.colors_grid = ft.GridView(
            expand=True,
            runs_count=4,
            max_extent=150,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        self.slider = ft.Slider(
            min=2,
            max=32,
            divisions=30,
            value=self.num_colors,
            label="{value} colors",
            on_change=self.on_slider_change,
            disabled=True
        )
        
        self.extract_btn = ft.ElevatedButton(
            "Extract Colors",
            icon=ft.Icons.COLORIZE,
            on_click=self.extract_colors,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.PRIMARY,
                color=ColorPalette.SURFACE,
                padding=20,
            )
        )
        
        self.content = self.build_ui()

    def build_ui(self):
        return ft.Column(
            controls=[
                ft.Text("Color Palette Extractor", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Upload an image to extract its dominant colors. Click on the image to pick a specific color. Use scroll/pinch to zoom.", size=14, color=ft.Colors.GREY_400),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Select Image",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=lambda _: self.file_picker.pick_files(allow_multiple=False),
                            style=ft.ButtonStyle(
                                padding=20,
                            )
                        ),
                        self.extract_btn,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                
                ft.Container(height=10),
                
                ft.Row(
                    controls=[
                        ft.Text("Number of colors:", size=14),
                        ft.Container(content=self.slider, expand=True),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                
                ft.Divider(height=20, color=ft.Colors.GREY_800),
                
                # Main content area
                ft.Row(
                    controls=[
                        # Left side: Image
                        ft.Container(
                            content=self.interactive_viewer,
                            expand=2, # Give more space to image
                            alignment=ft.alignment.top_center,
                            bgcolor=ft.Colors.BLACK12,
                            border_radius=10,
                            padding=10,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE, # Clip zoom overflow
                        ),
                        # Right side: Colors
                        ft.Container(
                            content=self.colors_grid,
                            expand=1,
                            padding=10,
                        ),
                    ],
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            expand=True,
            spacing=10,
        )

    def on_file_selected(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            self.selected_file_path = e.files[0].path
            
            # Load PIL Image first to get dimensions
            try:
                self.pil_image = Image.open(self.selected_file_path)
                img_w, img_h = self.pil_image.size
                
                # Calculate dimensions to fit height=600
                target_height = 600
                scale = target_height / img_h
                target_width = img_w * scale
                
                # Update Image control
                self.image_control.src = self.selected_file_path
                self.image_control.height = target_height
                self.image_control.width = target_width
                self.image_control.visible = True
                
                # Reset zoom
                self.interactive_viewer.scale = 1.0
                self.interactive_viewer.update()

            except Exception as ex:
                print(f"Error loading PIL image: {ex}")
                self.pil_image = None
                # Fallback
                self.image_control.src = self.selected_file_path
                self.image_control.visible = True

            self.extract_btn.disabled = False
            self.slider.disabled = False
            
            self.image_control.update()
            self.extract_btn.update()
            self.slider.update()
            
            # Auto extract on new file
            self.extract_colors(None)

    def on_slider_change(self, e):
        self.num_colors = int(e.control.value)
        if self.selected_file_path:
            self.extract_colors(None)

    def rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

    def add_color_card(self, hex_color, rgb):
        # Determine text color based on brightness
        brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
        text_color = ft.Colors.BLACK if brightness > 128 else ft.Colors.WHITE
        
        # Create the card content
        card_content = ft.Column(
            controls=[
                ft.Container(height=10), # Spacer
                ft.Icon(ft.Icons.COPY, color=text_color, size=20, opacity=0.7),
                ft.Text(hex_color, color=text_color, weight=ft.FontWeight.BOLD, size=14),
                ft.Text(f"RGB{rgb}", color=text_color, size=10, opacity=0.8),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        )

        # Create the container for the card
        card_container = ft.Container(
            content=card_content,
            bgcolor=hex_color,
            border_radius=10,
            alignment=ft.alignment.center,
            on_click=lambda _, code=hex_color: self.copy_to_clipboard(code),
            ink=True,
            tooltip="Click to copy HEX code"
        )

        # Wrap in Stack to add delete button
        card_stack = ft.Stack(
            controls=[
                card_container,
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=text_color,
                        icon_size=16,
                        tooltip="Remove color",
                        on_click=lambda e: self.remove_color(card_stack, hex_color),
                        style=ft.ButtonStyle(
                            padding=0,
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK if brightness > 128 else ft.Colors.WHITE), # Subtle background
                        )
                    ),
                    alignment=ft.alignment.top_right,
                    padding=5,
                )
            ]
        )
        
        self.colors_grid.controls.append(card_stack)

    def remove_color(self, card_control, hex_color):
        if card_control in self.colors_grid.controls:
            self.colors_grid.controls.remove(card_control)
            if hex_color in self.extracted_colors:
                self.extracted_colors.remove(hex_color)
            self.colors_grid.update()

    def extract_colors(self, e):
        if not self.selected_file_path:
            return
            
        try:
            colors = colorgram.extract(self.selected_file_path, self.num_colors)
            self.extracted_colors = []
            self.colors_grid.controls.clear()
            
            for color in colors:
                rgb = (color.rgb.r, color.rgb.g, color.rgb.b)
                hex_color = self.rgb_to_hex(rgb)
                self.extracted_colors.append(hex_color)
                self.add_color_card(hex_color, rgb)
            
            self.colors_grid.update()
            
        except Exception as e:
            print(f"Error extracting colors: {e}")
            self.page.open(
                ft.SnackBar(content=ft.Text(f"Error extracting colors: {str(e)}"), bgcolor=ft.Colors.ERROR)
            )

    def pick_color_at_point(self, e: ft.TapEvent):
        if not self.pil_image:
            return

        # Get original image dimensions
        img_w, img_h = self.pil_image.size
        
        # We know the image control is set to height=600 and width=scaled_width
        # So e.local_x and e.local_y should be relative to that.
        
        target_height = 600
        scale = target_height / img_h
        
        click_x = e.local_x
        click_y = e.local_y
        
        # Map to original coordinates
        orig_x = int(click_x / scale)
        orig_y = int(click_y / scale)
        
        # Clamp to bounds
        orig_x = max(0, min(orig_x, img_w - 1))
        orig_y = max(0, min(orig_y, img_h - 1))
        
        try:
            # Get pixel color
            pixel = self.pil_image.getpixel((orig_x, orig_y))
            # pixel is (R, G, B) or (R, G, B, A)
            if len(pixel) >= 3:
                rgb = pixel[:3]
                hex_color = self.rgb_to_hex(rgb)
                
                # Add to grid
                self.add_color_card(hex_color, rgb)
                self.colors_grid.update()
                
                self.page.open(
                    ft.SnackBar(content=ft.Text(f"Picked color: {hex_color}"), duration=1000)
                )
        except Exception as ex:
            print(f"Error picking color: {ex}")

    def copy_to_clipboard(self, color_code):
        self.page.set_clipboard(color_code)
        self.page.open(
            ft.SnackBar(
                content=ft.Text(f"Copied {color_code} to clipboard!"),
                action="OK",
            )
        )
