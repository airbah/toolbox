import sys
import os
import shutil
from unittest.mock import MagicMock

# Mock send2trash before importing duplicate_finder
sys.modules['send2trash'] = MagicMock()

import unittest
from utils.duplicate_finder import DuplicateFinder

class TestDuplicateFinder(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_duplicates_temp"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create file 1
        with open(os.path.join(self.test_dir, "file1.txt"), "w") as f:
            f.write("content A")
            
        # Create file 2 (duplicate of 1)
        with open(os.path.join(self.test_dir, "file2.txt"), "w") as f:
            f.write("content A")
            
        # Create file 3 (different)
        with open(os.path.join(self.test_dir, "file3.txt"), "w") as f:
            f.write("content B")
            
        # Create file 4 (same size as 3 but different content - hash collision test potential)
        with open(os.path.join(self.test_dir, "file4.txt"), "w") as f:
            f.write("content C")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan(self):
        finder = DuplicateFinder()
        # Consume generator
        gen = finder.scan_directory([self.test_dir])
        results = []
        try:
            while True:
                next(gen)
        except StopIteration as e:
            results = e.value
            
        self.assertEqual(len(results), 1)
        group = results[0]
        self.assertEqual(len(group.files), 2)
        paths = sorted([f.path for f in group.files])
        self.assertTrue(paths[0].endswith("file1.txt"))
        self.assertTrue(paths[1].endswith("file2.txt"))

if __name__ == "__main__":
    unittest.main()
