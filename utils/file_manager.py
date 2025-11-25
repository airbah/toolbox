import os
import pathlib
import shutil

def get_file_details(filepath):
    """Returns a dictionary with file details."""
    path = pathlib.Path(filepath)
    return {
        "name": path.name,
        "stem": path.stem,
        "suffix": path.suffix,
        "parent": str(path.parent),
        "size": path.stat().st_size,
        "path": str(path)
    }

def rename_file(old_path, new_name):
    """Renames a file. Returns the new path if successful, raises error otherwise."""
    path = pathlib.Path(old_path)
    new_path = path.parent / new_name
    
    if new_path.exists():
        raise FileExistsError(f"File '{new_name}' already exists.")
    
    path.rename(new_path)
    return str(new_path)

def get_unique_filename(directory, filename):
    """Generates a unique filename if the file already exists."""
    path = pathlib.Path(directory) / filename
    if not path.exists():
        return filename
    
    stem = path.stem
    suffix = path.suffix
    counter = 1
    
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = path.parent / new_filename
        if not new_path.exists():
            return new_filename
        counter += 1
