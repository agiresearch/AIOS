import os
import sys

import shutil

def delete_directories(root_dir, target_dirs):
    """
    Recursively deletes directories with names in target_dirs starting from root_dir.
    """
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            if dirname in target_dirs:
                full_path = os.path.join(dirpath, dirname)
                print(f"Deleting {full_path}...")
                shutil.rmtree(full_path, ignore_errors=True)

if __name__ == "__main__":
    root_directory = './'
    targets = {'.ipynb_checkpoints', '__pycache__', "logs", ".pytest_cache", "context_restoration"}
    delete_directories(root_directory, targets)
