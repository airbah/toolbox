import flet as ft
import os
import json
import threading
import time
from send2trash import send2trash
from utils.styles import ColorPalette, TextStyles
from utils.video_recorder import VideoRecorder, RegionSelector


class VideoRecorderView(ft.Container):
    # Config file for saved regions
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".toolbox_recorder.json")
    
    def __init__(self, page: ft.Page, file_picker: ft.FilePicker):
        super().__init__(expand=True)
        self.page = page
        self.file_picker = file_picker
        self.recorder = VideoRecorder()
        self.region_selector = RegionSelector()
        self.timer_thread = None
        self.selected_region = None
        
        # Status variables
        self.is_recording = False
        self.is_paused = False
        
        # Saved regions
        self.saved_regions = self._load_regions()
        
        # UI Components
        self._build_ui()
        
        # Load existing videos from Videos folder
        self._load_existing_videos()
    
    def _load_regions(self) -> list:
        """Load saved regions from config file."""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('regions', [])
        except Exception as e:
            print(f"Error loading regions: {e}")
        return []
    
    def _save_regions(self):
        """Save regions to config file."""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({'regions': self.saved_regions}, f, indent=2)
        except Exception as e:
            print(f"Error saving regions: {e}")
    
    def _load_existing_videos(self):
        """Load existing screen capture videos from Videos folder."""
        videos_folder = os.path.join(os.path.expanduser("~"), "Videos")
        if not os.path.exists(videos_folder):
            return
        
        try:
            # Find all screen_capture_*.mp4 files
            video_files = []
            for filename in os.listdir(videos_folder):
                if filename.startswith("screen_capture_") and filename.endswith(".mp4"):
                    filepath = os.path.join(videos_folder, filename)
                    if os.path.isfile(filepath):
                        # Get modification time for sorting
                        mtime = os.path.getmtime(filepath)
                        video_files.append((filepath, mtime))
            
            # Sort by modification time (newest first)
            video_files.sort(key=lambda x: x[1], reverse=True)
            
            # Add to history (limit to 20 most recent)
            for filepath, _ in video_files[:20]:
                self._add_to_history_silent(filepath)
                
        except Exception as e:
            print(f"Error loading existing videos: {e}")
    
    def _add_to_history_silent(self, path: str):
        """Add a video to history without updating UI (for initial load)."""
        if not os.path.exists(path):
            return
            
        file_size = os.path.getsize(path) / (1024 * 1024)  # MB
        filename = os.path.basename(path)
        
        # Create card reference to use in delete callback
        card_ref = ft.Ref[ft.Card]()
        
        item = ft.Card(
            ref=card_ref,
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.VIDEO_FILE, size=40, color=ColorPalette.SECONDARY),
                    ft.Column([
                        ft.Text(filename, style=TextStyles.BODY, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{file_size:.2f} MB • {path}", style=TextStyles.CAPTION),
                    ], expand=True),
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        icon_color=ColorPalette.PRIMARY,
                        tooltip="Ouvrir le dossier",
                        on_click=lambda _, p=path: self._open_folder(p),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PLAY_ARROW,
                        icon_color=ColorPalette.PRIMARY,
                        tooltip="Lire la vidéo",
                        on_click=lambda _, p=path: self._play_video(p),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ColorPalette.ERROR,
                        tooltip="Supprimer",
                        on_click=lambda _, p=path, r=card_ref: self._delete_recording(p, r),
                    ),
                ]),
                padding=15,
                bgcolor=ColorPalette.SURFACE,
                border_radius=10,
            ),
            color=ColorPalette.SURFACE,
            elevation=2,
        )
        
        self.history_list.controls.append(item)
        
    def _build_ui(self):
        """Build the user interface."""
        
        # Region display
        self.region_text = ft.Text(
            "Aucune zone sélectionnée",
            style=TextStyles.BODY,
            color=ColorPalette.TEXT_SECONDARY
        )
        
        self.region_preview = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CROP_FREE, size=48, color=ColorPalette.TEXT_SECONDARY),
                self.region_text,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ColorPalette.CONTAINER_BG,
            border=ft.border.all(2, ColorPalette.BORDER),
            border_radius=15,
            padding=30,
            alignment=ft.alignment.center,
            expand=True,
        )
        
        # Select region button
        self.select_btn = ft.ElevatedButton(
            "Nouvelle zone",
            icon=ft.Icons.CROP,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.PRIMARY,
                color=ColorPalette.BACKGROUND,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=15
            ),
            on_click=self.on_select_region,
        )
        
        # Saved regions dropdown
        self.regions_dropdown = ft.Dropdown(
            label="Zones sauvegardées",
            options=self._get_region_options(),
            on_change=self.on_region_selected_from_list,
            width=280,
            border_color=ColorPalette.BORDER,
            focused_border_color=ColorPalette.PRIMARY,
        )
        
        # Delete saved region button
        self.delete_region_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=ColorPalette.ERROR,
            tooltip="Supprimer cette zone",
            on_click=self.on_delete_saved_region,
            visible=False,
        )
        
        # Recording controls
        self.record_btn = ft.ElevatedButton(
            "Démarrer l'enregistrement",
            icon=ft.Icons.FIBER_MANUAL_RECORD,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.ERROR,
                color="#FFFFFF",
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            on_click=self.on_record_toggle,
            disabled=True,
        )
        
        self.pause_btn = ft.ElevatedButton(
            "Pause",
            icon=ft.Icons.PAUSE,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.SECONDARY,
                color=ColorPalette.BACKGROUND,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            on_click=self.on_pause_toggle,
            visible=False,
        )
        
        self.stop_btn = ft.ElevatedButton(
            "Arrêter et sauvegarder",
            icon=ft.Icons.STOP,
            style=ft.ButtonStyle(
                bgcolor=ColorPalette.SURFACE,
                color=ColorPalette.TEXT_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            on_click=self.on_stop_recording,
            visible=False,
        )
        
        # Timer display
        self.timer_text = ft.Text(
            "00:00:00",
            size=48,
            weight=ft.FontWeight.BOLD,
            color=ColorPalette.TEXT_PRIMARY,
            font_family="JetBrains Mono",
        )
        
        self.frame_count_text = ft.Text(
            "0 frames",
            style=TextStyles.CAPTION,
        )
        
        self.timer_container = ft.Container(
            content=ft.Column([
                self.timer_text,
                self.frame_count_text,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            visible=False,
            padding=20,
        )
        
        # Recording indicator
        self.recording_indicator = ft.Container(
            content=ft.Row([
                ft.Container(
                    width=12,
                    height=12,
                    bgcolor=ColorPalette.ERROR,
                    border_radius=6,
                ),
                ft.Text("ENREGISTREMENT EN COURS", color=ColorPalette.ERROR, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            visible=False,
        )
        
        # Audio recording indicator
        self.audio_indicator = ft.Row([
            ft.Icon(ft.Icons.MIC, size=16, color=ColorPalette.PRIMARY),
            ft.Text("Audio: actif", style=TextStyles.CAPTION, color=ColorPalette.PRIMARY),
        ], spacing=5, visible=False)
        
        # FPS selector
        self.fps_dropdown = ft.Dropdown(
            label="FPS",
            options=[
                ft.dropdown.Option("15", "15 FPS"),
                ft.dropdown.Option("24", "24 FPS"),
                ft.dropdown.Option("30", "30 FPS (Recommandé)"),
                ft.dropdown.Option("60", "60 FPS"),
            ],
            value="30",
            on_change=self.on_fps_change,
            width=200,
        )
        
        # Audio toggle
        audio_available = self.recorder.is_audio_available()
        self.audio_switch = ft.Switch(
            label="Enregistrer le son",
            value=audio_available,  # Enable by default if available
            disabled=not audio_available,
            on_change=self.on_audio_toggle,
        )
        
        # Set recorder audio flag
        self.recorder.record_audio = audio_available
        
        # Audio status indicator
        if audio_available:
            device_info = self.recorder.audio_recorder.get_device_info()
            self.audio_status = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.MIC, size=16, color=ColorPalette.PRIMARY),
                    ft.Text("Audio disponible", style=TextStyles.CAPTION, color=ColorPalette.PRIMARY),
                ], spacing=5),
                ft.Text(f"Périphérique: {device_info}", style=TextStyles.CAPTION, color=ColorPalette.TEXT_SECONDARY),
            ], spacing=2)
        else:
            self.audio_status = ft.Row([
                ft.Icon(ft.Icons.MIC_OFF, size=16, color=ColorPalette.TEXT_SECONDARY),
                ft.Text("Audio non disponible (installer pyaudiowpatch)", style=TextStyles.CAPTION, color=ColorPalette.TEXT_SECONDARY),
            ], spacing=5)
        
        # Output path
        self.output_path_field = ft.TextField(
            label="Chemin de sortie",
            value=self.recorder.get_default_output_path(),
            expand=True,
            border_color=ColorPalette.BORDER,
            focused_border_color=ColorPalette.PRIMARY,
            text_style=TextStyles.MONO,
        )
        
        self.browse_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            icon_color=ColorPalette.PRIMARY,
            on_click=self.on_browse_output,
        )
        
        # History list
        self.history_list = ft.ListView(expand=True, spacing=10)
        
        # Main layout
        self.padding = 20
        self.content = ft.Column([
            # Header
            ft.Text("Screen Video Recorder", style=TextStyles.HEADER),
            ft.Text("Capturez une zone de votre écran en vidéo MP4", style=TextStyles.CAPTION),
            ft.Container(height=20),
            
            # Main content row
            ft.Row([
                # Left panel - Controls
                ft.Container(
                    content=ft.Column([
                        ft.Text("Zone de capture", style=TextStyles.SUBHEADER),
                        ft.Container(height=5),
                        ft.Row([self.regions_dropdown, self.delete_region_btn]),
                        ft.Container(height=5),
                        self.select_btn,
                        ft.Container(height=10),
                        self.region_preview,
                        ft.Container(height=20),
                        
                        # Settings
                        ft.Text("Paramètres", style=TextStyles.SUBHEADER),
                        ft.Container(height=10),
                        self.fps_dropdown,
                        ft.Container(height=10),
                        self.audio_switch,
                        self.audio_status,
                        ft.Container(height=10),
                        ft.Row([self.output_path_field, self.browse_btn]),
                    ], spacing=5),
                    width=350,
                    padding=20,
                    bgcolor=ColorPalette.SURFACE,
                    border_radius=15,
                ),
                
                ft.Container(width=20),
                
                # Right panel - Recording
                ft.Container(
                    content=ft.Column([
                        self.recording_indicator,
                        self.audio_indicator,
                        ft.Container(height=20),
                        self.timer_container,
                        ft.Container(height=20),
                        ft.Row([
                            self.record_btn,
                            self.pause_btn,
                            self.stop_btn,
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                    expand=True,
                    padding=30,
                    bgcolor=ColorPalette.SURFACE,
                    border_radius=15,
                ),
            ], expand=True),
            
            ft.Container(height=20),
            
            # History section
            ft.Text("Historique des captures", style=TextStyles.SUBHEADER),
            ft.Container(
                content=self.history_list,
                expand=True,
                bgcolor=ColorPalette.CONTAINER_BG,
                border_radius=10,
                padding=10,
            ),
        ], expand=True)
        
    def on_select_region(self, e):
        """Open region selector overlay."""
        # Minimize the window before selecting
        self.page.window.minimized = True
        self.page.update()
        
        # Small delay to let the window minimize
        time.sleep(0.5)
        
        # Run region selection in a thread to not block UI
        def select():
            self.region_selector.select_region(self._on_region_selected)
        
        threading.Thread(target=select, daemon=True).start()
    
    def _on_region_selected(self, region):
        """Callback when region is selected."""
        # Restore window
        self.page.window.minimized = False
        self.page.update()
        
        if region:
            self.selected_region = region
            x, y, w, h = region
            self.region_text.value = f"Zone: {w}x{h} pixels @ ({x}, {y})"
            self.region_preview.border = ft.border.all(2, ColorPalette.PRIMARY)
            self.region_preview.content = ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=48, color=ColorPalette.PRIMARY),
                self.region_text,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.record_btn.disabled = False
            self.recorder.set_region(x, y, w, h)
            
            # Save region to history
            self._add_region_to_history(region)
        else:
            self.region_text.value = "Sélection annulée"
            self.region_preview.border = ft.border.all(2, ColorPalette.BORDER)
        
        self.page.update()
    
    def _get_region_options(self) -> list:
        """Get dropdown options for saved regions."""
        options = []
        for i, region in enumerate(self.saved_regions):
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            name = region.get('name', f"Zone {i+1}")
            options.append(ft.dropdown.Option(
                key=str(i),
                text=f"{name} ({w}x{h} @ {x},{y})"
            ))
        return options
    
    def _add_region_to_history(self, region):
        """Add a new region to the saved regions."""
        x, y, w, h = region
        
        # Check if this region already exists (similar position/size)
        for saved in self.saved_regions:
            if (abs(saved['x'] - x) < 10 and abs(saved['y'] - y) < 10 and 
                abs(saved['w'] - w) < 10 and abs(saved['h'] - h) < 10):
                # Region already exists, move it to front
                self.saved_regions.remove(saved)
                self.saved_regions.insert(0, saved)
                self._save_regions()
                self._update_regions_dropdown()
                return
        
        # Add new region
        new_region = {
            'name': f"Zone {len(self.saved_regions) + 1}",
            'x': x, 'y': y, 'w': w, 'h': h
        }
        self.saved_regions.insert(0, new_region)
        
        # Keep only last 10 regions
        if len(self.saved_regions) > 10:
            self.saved_regions = self.saved_regions[:10]
        
        self._save_regions()
        self._update_regions_dropdown()
    
    def _update_regions_dropdown(self):
        """Update the regions dropdown with current saved regions."""
        self.regions_dropdown.options = self._get_region_options()
        if self.saved_regions:
            self.regions_dropdown.value = "0"  # Select the most recent
        self.page.update()
    
    def on_region_selected_from_list(self, e):
        """Handle selection of a saved region from dropdown."""
        if e.control.value is None:
            return
        
        index = int(e.control.value)
        if 0 <= index < len(self.saved_regions):
            region = self.saved_regions[index]
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            
            self.selected_region = (x, y, w, h)
            self.region_text.value = f"Zone: {w}x{h} pixels @ ({x}, {y})"
            self.region_preview.border = ft.border.all(2, ColorPalette.PRIMARY)
            self.region_preview.content = ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=48, color=ColorPalette.PRIMARY),
                self.region_text,
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.record_btn.disabled = False
            self.recorder.set_region(x, y, w, h)
            self.delete_region_btn.visible = True
            self.page.update()
    
    def on_delete_saved_region(self, e):
        """Delete the currently selected saved region."""
        if self.regions_dropdown.value is None:
            return
        
        index = int(self.regions_dropdown.value)
        if 0 <= index < len(self.saved_regions):
            del self.saved_regions[index]
            self._save_regions()
            self._update_regions_dropdown()
            
            # Reset selection
            self.regions_dropdown.value = None
            self.delete_region_btn.visible = False
            self.page.update()
    
    def on_record_toggle(self, e):
        """Start or stop recording."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start the recording."""
        self.recorder.set_output_path(self.output_path_field.value)
        self.recorder.fps = int(self.fps_dropdown.value)
        
        # Minimize window during recording
        self.page.window.minimized = True
        self.page.update()
        
        # Small delay before starting
        time.sleep(0.3)
        
        if self.recorder.start_recording():
            self.is_recording = True
            self.is_paused = False
            
            # Update UI
            self.record_btn.text = "Enregistrement..."
            self.record_btn.disabled = True
            self.pause_btn.visible = True
            self.stop_btn.visible = True
            self.select_btn.disabled = True
            self.fps_dropdown.disabled = True
            self.audio_switch.disabled = True
            self.timer_container.visible = True
            self.recording_indicator.visible = True
            
            # Show audio indicator if recording audio
            if self.recorder.record_audio and self.recorder.audio_recorder.audio_started:
                self.audio_indicator.visible = True
                self.audio_indicator.controls[1].value = f"Audio: actif ({self.recorder.audio_recorder.get_device_info()})"
            else:
                self.audio_indicator.visible = False
            
            # Restore window
            self.page.window.minimized = False
            self.page.update()
            
            # Start timer update thread
            self.timer_thread = threading.Thread(target=self._update_timer, daemon=True)
            self.timer_thread.start()
    
    def _stop_recording(self):
        """Stop the recording and save."""
        self.is_recording = False
        output_path = self.recorder.stop_recording()
        
        # Update UI
        self.record_btn.text = "Démarrer l'enregistrement"
        self.record_btn.disabled = False
        self.pause_btn.visible = False
        self.stop_btn.visible = False
        self.select_btn.disabled = False
        self.fps_dropdown.disabled = False
        self.audio_switch.disabled = not self.recorder.is_audio_available()
        self.timer_container.visible = False
        self.recording_indicator.visible = False
        self.audio_indicator.visible = False
        self.timer_text.value = "00:00:00"
        self.frame_count_text.value = "0 frames"
        
        if output_path and os.path.exists(output_path):
            # Add to history
            self._add_to_history(output_path)
            
            # Show success message
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Vidéo sauvegardée: {output_path}"),
                bgcolor=ColorPalette.PRIMARY,
            )
            self.page.snack_bar.open = True
        
        self.page.update()
    
    def on_stop_recording(self, e):
        """Stop button clicked."""
        self._stop_recording()
    
    def on_pause_toggle(self, e):
        """Toggle pause state."""
        if self.is_paused:
            self.recorder.resume_recording()
            self.is_paused = False
            self.pause_btn.text = "Pause"
            self.pause_btn.icon = ft.Icons.PAUSE
            self.recording_indicator.content.controls[1].value = "ENREGISTREMENT EN COURS"
        else:
            self.recorder.pause_recording()
            self.is_paused = True
            self.pause_btn.text = "Reprendre"
            self.pause_btn.icon = ft.Icons.PLAY_ARROW
            self.recording_indicator.content.controls[1].value = "EN PAUSE"
        
        self.page.update()
    
    def on_fps_change(self, e):
        """FPS dropdown changed."""
        self.recorder.fps = int(self.fps_dropdown.value)
    
    def on_audio_toggle(self, e):
        """Audio switch toggled."""
        self.recorder.record_audio = self.audio_switch.value
    
    def on_browse_output(self, e):
        """Open file picker for output path."""
        self.file_picker.save_file(
            dialog_title="Choisir l'emplacement de sauvegarde",
            file_name="screen_capture.mp4",
            file_type=ft.FilePickerFileType.VIDEO,
            allowed_extensions=["mp4"],
        )
    
    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """File picker result handler."""
        if e.path:
            self.output_path_field.value = e.path
            self.page.update()
    
    def _update_timer(self):
        """Update the timer display in a loop."""
        while self.is_recording:
            elapsed = self.recorder.get_elapsed_time()
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            self.timer_text.value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.frame_count_text.value = f"{self.recorder.get_frame_count()} frames"
            
            try:
                self.page.update()
            except:
                pass
            
            time.sleep(0.1)
    
    def _create_history_item(self, path: str):
        """Create a history item card for a recorded video."""
        file_size = os.path.getsize(path) / (1024 * 1024)  # MB
        filename = os.path.basename(path)
        
        # Create card reference to use in delete callback
        card_ref = ft.Ref[ft.Card]()
        
        item = ft.Card(
            ref=card_ref,
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.VIDEO_FILE, size=40, color=ColorPalette.SECONDARY),
                    ft.Column([
                        ft.Text(filename, style=TextStyles.BODY, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{file_size:.2f} MB • {path}", style=TextStyles.CAPTION),
                    ], expand=True),
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        icon_color=ColorPalette.PRIMARY,
                        tooltip="Ouvrir le dossier",
                        on_click=lambda _, p=path: self._open_folder(p),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PLAY_ARROW,
                        icon_color=ColorPalette.PRIMARY,
                        tooltip="Lire la vidéo",
                        on_click=lambda _, p=path: self._play_video(p),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ColorPalette.ERROR,
                        tooltip="Supprimer",
                        on_click=lambda _, p=path, r=card_ref: self._delete_recording(p, r),
                    ),
                ]),
                padding=15,
                bgcolor=ColorPalette.SURFACE,
                border_radius=10,
            ),
            color=ColorPalette.SURFACE,
            elevation=2,
        )
        
        return item
    
    def _add_to_history(self, path: str):
        """Add a recorded video to the history list."""
        item = self._create_history_item(path)
        self.history_list.controls.insert(0, item)
        self.page.update()
    
    def _delete_recording(self, path: str, card_ref: ft.Ref[ft.Card]):
        """Delete a recording file and remove from history."""
        try:
            if os.path.exists(path):
                send2trash(path)
            
            # Remove from history list
            if card_ref.current in self.history_list.controls:
                self.history_list.controls.remove(card_ref.current)
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Vidéo supprimée: {os.path.basename(path)}"),
                bgcolor=ColorPalette.SECONDARY,
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erreur: {str(ex)}"),
                bgcolor=ColorPalette.ERROR,
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _open_folder(self, path: str):
        """Open the folder containing the video."""
        folder = os.path.dirname(path)
        os.startfile(folder)
    
    def _play_video(self, path: str):
        """Play the video with the default player."""
        os.startfile(path)

