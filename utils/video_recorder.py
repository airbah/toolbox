import mss
import cv2
import numpy as np
import threading
import time
import os
import wave
import subprocess
import tempfile
from typing import Tuple, Optional, Callable
from datetime import datetime


class AudioRecorder:
    """Helper class for system audio recording using WASAPI loopback."""
    
    def __init__(self):
        self.recording = False
        self.paused = False
        self.audio_frames = []
        self.record_thread: Optional[threading.Thread] = None
        self.sample_rate = 44100
        self.channels = 2
        self._pyaudio = None
        self._stream = None
        self._available = None
        self._loopback_device = None
        self.last_error: Optional[str] = None
        self.audio_started = False
        
    def is_available(self) -> bool:
        """Check if audio recording is available."""
        if self._available is not None:
            return self._available
        try:
            import pyaudiowpatch as pyaudio
            p = pyaudio.PyAudio()
            # Try to find a loopback device
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            
            if not default_speakers.get("isLoopbackDevice", False):
                # Find the loopback device for the default speakers
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        self._available = True
                        self._loopback_device = loopback
                        p.terminate()
                        return True
            else:
                self._available = True
                self._loopback_device = default_speakers
                p.terminate()
                return True
            
            p.terminate()
            self._available = False
            return False
        except Exception as e:
            print(f"Audio not available: {e}")
            self.last_error = str(e)
            self._available = False
            return False
    
    def get_device_info(self) -> str:
        """Get info about the audio device being used."""
        if self._loopback_device:
            return f"{self._loopback_device.get('name', 'Unknown')} @ {int(self._loopback_device.get('defaultSampleRate', 0))}Hz"
        return "No device"
    
    def start_recording(self) -> bool:
        """Start recording system audio."""
        if not self.is_available():
            self.last_error = "Audio not available"
            return False
            
        try:
            import pyaudiowpatch as pyaudio
            
            self._pyaudio = pyaudio.PyAudio()
            wasapi_info = self._pyaudio.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = self._pyaudio.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            
            # Find loopback device
            loopback_device = None
            if not default_speakers.get("isLoopbackDevice", False):
                for loopback in self._pyaudio.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        loopback_device = loopback
                        break
            else:
                loopback_device = default_speakers
            
            if not loopback_device:
                self.last_error = "No loopback device found"
                return False
            
            self._loopback_device = loopback_device
            self.sample_rate = int(loopback_device["defaultSampleRate"])
            self.channels = int(loopback_device["maxInputChannels"])
            
            # Use a larger buffer for more reliable capture
            frames_per_buffer = int(self.sample_rate * 0.02)  # 20ms buffer
            
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                frames_per_buffer=frames_per_buffer,
                input=True,
                input_device_index=loopback_device["index"],
            )
            
            self.recording = True
            self.paused = False
            self.audio_frames = []
            self.audio_started = True
            self.last_error = None
            
            print(f"Audio recording started: {self.get_device_info()}, channels={self.channels}")
            
            self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
            self.record_thread.start()
            return True
            
        except Exception as e:
            self.last_error = str(e)
            print(f"Failed to start audio recording: {e}")
            return False
    
    def _record_loop(self):
        """Main audio recording loop."""
        frames_per_buffer = int(self.sample_rate * 0.02)  # Match the buffer size
        while self.recording:
            if not self.paused and self._stream:
                try:
                    data = self._stream.read(frames_per_buffer, exception_on_overflow=False)
                    if data:
                        self.audio_frames.append(data)
                except Exception as e:
                    print(f"Audio read error: {e}")
            else:
                time.sleep(0.01)
    
    def pause_recording(self):
        """Pause the recording."""
        self.paused = True
        
    def resume_recording(self):
        """Resume the recording."""
        self.paused = False
    
    def stop_recording(self) -> bytes:
        """Stop recording and return audio data."""
        self.recording = False
        
        if self.record_thread:
            self.record_thread.join(timeout=2)
        
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
            
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
        
        audio_data = b''.join(self.audio_frames)
        self.audio_frames = []
        return audio_data
    
    def save_to_wav(self, audio_data: bytes, filepath: str):
        """Save audio data to a WAV file."""
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)


class VideoRecorder:
    """Helper class for screen region video recording with optional audio."""
    
    def __init__(self):
        self.recording = False
        self.paused = False
        self.region: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
        self.output_path: Optional[str] = None
        self.fps = 30
        self.frames = []
        self.record_thread: Optional[threading.Thread] = None
        self.on_frame_captured: Optional[Callable[[int], None]] = None
        self.on_recording_stopped: Optional[Callable[[str], None]] = None
        self._start_time = 0
        self._frame_count = 0
        
        # Audio recording
        self.record_audio = False
        self.audio_recorder = AudioRecorder()
        
    def is_audio_available(self) -> bool:
        """Check if audio recording is available."""
        return self.audio_recorder.is_available()
        
    def set_region(self, x: int, y: int, width: int, height: int):
        """Set the screen region to capture."""
        # Ensure dimensions are even (required by many video codecs)
        width = width if width % 2 == 0 else width + 1
        height = height if height % 2 == 0 else height + 1
        self.region = (x, y, width, height)
        
    def set_output_path(self, path: str):
        """Set the output file path."""
        self.output_path = path
        
    def get_default_output_path(self) -> str:
        """Generate a default output path with timestamp."""
        videos_folder = os.path.join(os.path.expanduser("~"), "Videos")
        if not os.path.exists(videos_folder):
            videos_folder = os.path.expanduser("~")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(videos_folder, f"screen_capture_{timestamp}.mp4")
    
    def start_recording(self) -> bool:
        """Start recording the selected region."""
        if not self.region:
            return False
            
        if not self.output_path:
            self.output_path = self.get_default_output_path()
            
        self.recording = True
        self.paused = False
        self.frames = []
        self._frame_count = 0
        self._start_time = time.time()
        
        # Start audio recording if enabled
        if self.record_audio and self.audio_recorder.is_available():
            self.audio_recorder.start_recording()
        
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.record_thread.start()
        return True
    
    def pause_recording(self):
        """Pause the recording."""
        self.paused = True
        if self.record_audio:
            self.audio_recorder.pause_recording()
        
    def resume_recording(self):
        """Resume the recording."""
        self.paused = False
        if self.record_audio:
            self.audio_recorder.resume_recording()
    
    def stop_recording(self) -> Optional[str]:
        """Stop recording and save the video."""
        self.recording = False
        
        # Stop audio recording first
        audio_data = None
        if self.record_audio and self.audio_recorder.recording:
            audio_data = self.audio_recorder.stop_recording()
        
        if self.record_thread:
            self.record_thread.join(timeout=2)
            
        if not self.frames:
            return None
            
        return self._save_video(audio_data)
    
    def _record_loop(self):
        """Main recording loop running in a separate thread."""
        with mss.mss() as sct:
            x, y, w, h = self.region
            monitor = {"left": x, "top": y, "width": w, "height": h}
            
            frame_interval = 1.0 / self.fps
            next_frame_time = time.time()
            
            while self.recording:
                current_time = time.time()
                
                if current_time >= next_frame_time and not self.paused:
                    # Capture frame
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    # Convert BGRA to BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    self.frames.append(frame)
                    self._frame_count += 1
                    
                    if self.on_frame_captured:
                        try:
                            self.on_frame_captured(self._frame_count)
                        except:
                            pass
                    
                    next_frame_time = current_time + frame_interval
                else:
                    # Small sleep to prevent CPU spinning
                    time.sleep(0.001)
    
    def _save_video(self, audio_data: Optional[bytes] = None) -> Optional[str]:
        """Save captured frames to MP4 file, optionally with audio."""
        if not self.frames or not self.region:
            return None
            
        x, y, w, h = self.region
        
        # Calculate actual FPS based on recorded frames and time
        actual_duration = time.time() - self._start_time
        actual_fps = len(self.frames) / actual_duration if actual_duration > 0 else self.fps
        
        # If we have audio, we need to use ffmpeg to mux
        if audio_data and self._is_ffmpeg_available():
            return self._save_with_audio(audio_data, actual_fps, w, h)
        else:
            return self._save_video_only(actual_fps, w, h)
    
    def _save_video_only(self, fps: float, width: int, height: int) -> str:
        """Save video without audio."""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
        
        for frame in self.frames:
            writer.write(frame)
            
        writer.release()
        self.frames = []
        
        if self.on_recording_stopped:
            try:
                self.on_recording_stopped(self.output_path)
            except:
                pass
                
        return self.output_path
    
    def _save_with_audio(self, audio_data: bytes, fps: float, width: int, height: int) -> str:
        """Save video with audio using ffmpeg."""
        # Check if audio data is valid
        if not audio_data or len(audio_data) < 1000:
            print(f"Audio data too small or empty: {len(audio_data) if audio_data else 0} bytes")
            return self._save_video_only(fps, width, height)
        
        print(f"Audio data size: {len(audio_data)} bytes")
        
        # Create temp files
        temp_dir = tempfile.gettempdir()
        temp_video = os.path.join(temp_dir, "temp_video.avi")  # Use AVI for raw video
        temp_audio = os.path.join(temp_dir, "temp_audio.wav")
        
        # Save video to temp file (use XVID for better compatibility)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
        for frame in self.frames:
            writer.write(frame)
        writer.release()
        self.frames = []
        
        # Save audio to temp file
        self.audio_recorder.save_to_wav(audio_data, temp_audio)
        
        # Check temp files
        print(f"Temp video size: {os.path.getsize(temp_video)} bytes")
        print(f"Temp audio size: {os.path.getsize(temp_audio)} bytes")
        
        # Mux with ffmpeg - re-encode video to H.264 for compatibility
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', temp_video,
                '-i', temp_audio,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                '-movflags', '+faststart',
                self.output_path
            ]
            
            print(f"Running ffmpeg: {' '.join(cmd)}")
            
            # Run ffmpeg and capture output for debugging
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(cmd, startupinfo=startupinfo,
                                   capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"FFmpeg stderr: {result.stderr}")
                raise Exception(f"FFmpeg failed with code {result.returncode}")
            
            print(f"FFmpeg completed successfully. Output size: {os.path.getsize(self.output_path)} bytes")
            
        except Exception as e:
            print(f"FFmpeg error: {e}")
            # If ffmpeg fails, save video only
            self.frames = []  # Already cleared
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
            # Re-read from temp video... or just copy
            import shutil
            shutil.copy(temp_video, self.output_path.replace('.mp4', '.avi'))
            print(f"Saved video without audio as AVI")
        finally:
            # Clean up temp files
            for f in [temp_video, temp_audio]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except:
                    pass
        
        if self.on_recording_stopped:
            try:
                self.on_recording_stopped(self.output_path)
            except:
                pass
                
        return self.output_path
    
    def _is_ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available in PATH."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run(['ffmpeg', '-version'], check=True, startupinfo=startupinfo,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False
    
    def get_elapsed_time(self) -> float:
        """Get elapsed recording time in seconds."""
        if self._start_time and self.recording:
            return time.time() - self._start_time
        return 0
    
    def get_frame_count(self) -> int:
        """Get number of frames captured."""
        return self._frame_count


class RegionSelector:
    """
    A class to handle screen region selection using tkinter overlay.
    This creates a transparent fullscreen window where user can draw a rectangle.
    """
    
    def __init__(self):
        self.region: Optional[Tuple[int, int, int, int]] = None
        self.selecting = False
        
    def select_region(self, callback: Callable[[Tuple[int, int, int, int]], None]):
        """
        Open a fullscreen overlay for region selection.
        Calls callback with (x, y, width, height) when selection is complete.
        """
        import tkinter as tk
        
        self.region = None
        self.start_x = 0
        self.start_y = 0
        
        # Create fullscreen transparent window
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.3)
        root.attributes('-topmost', True)
        root.configure(bg='black')
        root.config(cursor="cross")
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Create canvas for drawing selection rectangle
        canvas = tk.Canvas(root, width=screen_width, height=screen_height, 
                          bg='black', highlightthickness=0)
        canvas.pack()
        
        selection_rect = None
        
        def on_mouse_down(event):
            nonlocal self, selection_rect
            self.start_x = event.x
            self.start_y = event.y
            if selection_rect:
                canvas.delete(selection_rect)
            selection_rect = canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline='#4FD6BE', width=3, fill='#4FD6BE', stipple='gray25'
            )
        
        def on_mouse_drag(event):
            nonlocal selection_rect
            if selection_rect:
                canvas.coords(selection_rect, self.start_x, self.start_y, event.x, event.y)
        
        def on_mouse_up(event):
            nonlocal self
            end_x, end_y = event.x, event.y
            
            # Calculate region (handle selection in any direction)
            x = min(self.start_x, end_x)
            y = min(self.start_y, end_y)
            w = abs(end_x - self.start_x)
            h = abs(end_y - self.start_y)
            
            if w > 10 and h > 10:  # Minimum size
                self.region = (x, y, w, h)
                root.destroy()
                callback(self.region)
            else:
                # Selection too small, allow retry
                pass
        
        def on_escape(event):
            root.destroy()
            callback(None)
        
        def on_right_click(event):
            root.destroy()
            callback(None)
        
        canvas.bind('<Button-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_drag)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        canvas.bind('<Button-3>', on_right_click)
        root.bind('<Escape>', on_escape)
        
        # Instructions label
        label = tk.Label(root, text="Dessinez un rectangle pour sélectionner la zone à capturer\n(Echap ou clic droit pour annuler)",
                        font=('Arial', 16), fg='white', bg='black')
        label.place(relx=0.5, rely=0.1, anchor='center')
        
        root.mainloop()
