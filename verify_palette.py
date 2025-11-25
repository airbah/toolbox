
import sys
import os

# Add the project root to sys.path
sys.path.append('/Users/abdelhakimirbah/workspace/mesApps/file_toolbox_app')

try:
    print("Attempting to import colorgram...")
    import colorgram
    print("Successfully imported colorgram.")

    print("Attempting to import ColorPaletteView...")
    from views.color_palette_view import ColorPaletteView
    print("Successfully imported ColorPaletteView.")

    print("Attempting to import main...")
    import main
    print("Successfully imported main.")
    
    print("Verification successful!")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
