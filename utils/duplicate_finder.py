import os
import hashlib
import send2trash
from typing import List, Dict, Generator, Optional
from dataclasses import dataclass

@dataclass
class DuplicateFile:
    path: str
    size: int
    modified: float

@dataclass
class DuplicateGroup:
    hash_value: str
    files: List[DuplicateFile]
    
    @property
    def size(self) -> int:
        return self.files[0].size if self.files else 0
        
    @property
    def count(self) -> int:
        return len(self.files)

class DuplicateFinder:
    def __init__(self):
        self._stop_requested = False

    def stop(self):
        """Request to stop the scanning process."""
        self._stop_requested = True

    def scan_directory(self, paths: List[str], recursive: bool = True, min_size: int = 0) -> Generator[str, None, List[DuplicateGroup]]:
        """
        Scans directories for duplicates.
        Yields status messages.
        Returns a list of DuplicateGroup.
        """
        self._stop_requested = False
        files_by_size: Dict[int, List[str]] = {}
        
        # Phase 1: Group by size
        yield "Phase 1/3: Scanning files..."
        for root_path in paths:
            if self._stop_requested: break
            
            if recursive:
                for root, _, files in os.walk(root_path):
                    if self._stop_requested: break
                    for file in files:
                        if file.startswith('.'): continue # Skip hidden files
                        file_path = os.path.join(root, file)
                        try:
                            size = os.path.getsize(file_path)
                            if size >= min_size:
                                if size not in files_by_size:
                                    files_by_size[size] = []
                                files_by_size[size].append(file_path)
                        except OSError:
                            continue
            else:
                # Non-recursive
                try:
                    for item in os.listdir(root_path):
                        if self._stop_requested: break
                        file_path = os.path.join(root_path, item)
                        if os.path.isfile(file_path) and not item.startswith('.'):
                            try:
                                size = os.path.getsize(file_path)
                                if size >= min_size:
                                    if size not in files_by_size:
                                        files_by_size[size] = []
                                    files_by_size[size].append(file_path)
                            except OSError:
                                continue
                except OSError:
                    pass

        # Filter out unique sizes
        potential_duplicates = {s: f for s, f in files_by_size.items() if len(f) > 1}
        total_groups = len(potential_duplicates)
        
        # Phase 2: Partial Hash (First 4k)
        yield f"Phase 2/3: Pre-hashing {total_groups} groups..."
        files_by_partial_hash: Dict[str, List[str]] = {}
        
        for size, file_list in potential_duplicates.items():
            if self._stop_requested: break
            
            for file_path in file_list:
                try:
                    p_hash = self._get_file_hash(file_path, first_chunk_only=True)
                    # Combine size and partial hash to avoid collisions
                    key = f"{size}_{p_hash}"
                    if key not in files_by_partial_hash:
                        files_by_partial_hash[key] = []
                    files_by_partial_hash[key].append(file_path)
                except OSError:
                    continue

        # Filter again
        potential_duplicates_2 = {k: f for k, f in files_by_partial_hash.items() if len(f) > 1}
        total_groups_2 = len(potential_duplicates_2)

        # Phase 3: Full Hash
        yield f"Phase 3/3: Full hashing {total_groups_2} groups..."
        final_duplicates: Dict[str, DuplicateGroup] = {}
        
        processed_count = 0
        for key, file_list in potential_duplicates_2.items():
            if self._stop_requested: break
            processed_count += 1
            if processed_count % 10 == 0:
                yield f"Phase 3/3: Verifying group {processed_count}/{total_groups_2}..."

            # Group by full hash within this partial match group
            temp_groups: Dict[str, List[DuplicateFile]] = {}
            
            for file_path in file_list:
                try:
                    full_hash = self._get_file_hash(file_path, first_chunk_only=False)
                    if full_hash not in temp_groups:
                        temp_groups[full_hash] = []
                    
                    stats = os.stat(file_path)
                    temp_groups[full_hash].append(DuplicateFile(
                        path=file_path,
                        size=stats.st_size,
                        modified=stats.st_mtime
                    ))
                except OSError:
                    continue
            
            # Add confirmed duplicates to result
            for h, files in temp_groups.items():
                if len(files) > 1:
                    final_duplicates[h] = DuplicateGroup(hash_value=h, files=files)

        yield "Scan complete."
        return list(final_duplicates.values())

    def _get_file_hash(self, file_path: str, first_chunk_only: bool = False) -> str:
        """Calculates MD5 hash of a file."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            if first_chunk_only:
                chunk = f.read(4096)
                hasher.update(chunk)
            else:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        return hasher.hexdigest()

    def delete_file(self, file_path: str) -> bool:
        """Sends a file to the trash."""
        try:
            send2trash.send2trash(file_path)
            return True
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
            return False
