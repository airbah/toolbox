"""
Emoji Maker Utility
Converts images to emoji-sized formats and manages custom emoji collections.
"""

import os
import io
from pathlib import Path
from PIL import Image
import win32clipboard
from ctypes import windll, c_void_p, Structure, c_long, byref, sizeof
from ctypes.wintypes import DWORD

# Standard emoji sizes
EMOJI_SIZES = {
    "Small (32x32)": 32,
    "Medium (64x64)": 64,
    "Standard (128x128)": 128,
    "Large (256x256)": 256,
}

DEFAULT_EMOJI_FOLDER = Path.home() / "Documents" / "CustomEmojis"


class EmojiMaker:
    """Handles image to emoji conversion and clipboard operations."""
    
    def __init__(self, emoji_folder: Path = None):
        self.emoji_folder = emoji_folder or DEFAULT_EMOJI_FOLDER
        self.emoji_folder.mkdir(parents=True, exist_ok=True)
    
    def convert_to_emoji(
        self,
        image_path: str,
        size: int = 128,
        remove_background: bool = False,
        output_name: str = None,
        save_to_folder: bool = True
    ) -> Image.Image:
        """
        Convert an image to emoji format.
        
        Args:
            image_path: Path to the source image
            size: Target size (width and height)
            remove_background: Whether to attempt background removal (basic)
            output_name: Custom name for the saved emoji
            save_to_folder: Whether to save to the emoji folder
            
        Returns:
            PIL Image object of the converted emoji
        """
        # Load image
        img = Image.open(image_path)
        
        # Convert to RGBA for transparency support
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Crop to square (center crop)
        img = self._crop_to_square(img)
        
        # Resize with high-quality resampling
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Optional: basic background removal (makes near-white pixels transparent)
        if remove_background:
            img = self._remove_background(img)
        
        # Save to folder if requested
        if save_to_folder:
            if output_name:
                filename = f"{output_name}.png"
            else:
                original_name = Path(image_path).stem
                filename = f"{original_name}_{size}x{size}.png"
            
            output_path = self.emoji_folder / filename
            img.save(output_path, "PNG")
        
        return img
    
    def _crop_to_square(self, img: Image.Image) -> Image.Image:
        """Crop image to a centered square."""
        width, height = img.size
        
        if width == height:
            return img
        
        # Determine the size of the square
        min_dim = min(width, height)
        
        # Calculate crop coordinates (center crop)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        
        return img.crop((left, top, right, bottom))
    
    def _remove_background(self, img: Image.Image, threshold: int = 240) -> Image.Image:
        """
        Basic background removal - makes near-white pixels transparent.
        For more advanced removal, consider using rembg library.
        """
        data = img.getdata()
        new_data = []
        
        for item in data:
            # If pixel is near-white, make it transparent
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        img.putdata(new_data)
        return img
    
    def copy_to_clipboard(self, img: Image.Image) -> bool:
        """
        Copy a PIL Image to Windows clipboard.
        The image will appear in Win+V clipboard history.
        
        Args:
            img: PIL Image to copy
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to BMP format for Windows clipboard
            output = io.BytesIO()
            
            # Convert RGBA to RGB with white background for clipboard compatibility
            if img.mode == 'RGBA':
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img_to_copy = background
            else:
                img_to_copy = img.convert('RGB')
            
            # Save as BMP
            img_to_copy.save(output, 'BMP')
            data = output.getvalue()[14:]  # Remove BMP file header
            output.close()
            
            # Copy to clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            return True
            
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return False
    
    def copy_png_to_clipboard(self, img: Image.Image) -> bool:
        """
        Copy a PNG image with transparency to Windows clipboard.
        Preserves alpha channel for apps that support it.
        
        Args:
            img: PIL Image to copy
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save as PNG to bytes
            output = io.BytesIO()
            img.save(output, 'PNG')
            png_data = output.getvalue()
            output.close()
            
            # Register PNG format
            CF_PNG = windll.user32.RegisterClipboardFormatW("PNG")
            
            # Copy to clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            
            # Set PNG data
            win32clipboard.SetClipboardData(CF_PNG, png_data)
            
            # Also set DIB for compatibility
            output2 = io.BytesIO()
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                background.save(output2, 'BMP')
            else:
                img.convert('RGB').save(output2, 'BMP')
            
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, output2.getvalue()[14:])
            output2.close()
            
            win32clipboard.CloseClipboard()
            return True
            
        except Exception as e:
            print(f"Error copying PNG to clipboard: {e}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return False
    
    def get_saved_emojis(self) -> list:
        """
        Get list of all saved custom emojis.
        
        Returns:
            List of emoji file paths
        """
        if not self.emoji_folder.exists():
            return []
        
        emoji_extensions = {'.png', '.gif', '.webp'}
        emojis = []
        
        for file in self.emoji_folder.iterdir():
            if file.suffix.lower() in emoji_extensions:
                emojis.append(file)
        
        return sorted(emojis, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def delete_emoji(self, emoji_path: Path) -> bool:
        """Delete a saved emoji."""
        try:
            if emoji_path.exists():
                emoji_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting emoji: {e}")
            return False
    
    def load_emoji(self, emoji_path: Path) -> Image.Image:
        """Load an emoji image from the saved folder."""
        return Image.open(emoji_path)





