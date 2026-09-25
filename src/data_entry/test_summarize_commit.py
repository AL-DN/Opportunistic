# Author: Alden Sahi
# Date: 08/15/2026
# Program Name: test_summarize_commit
# Program Description:
#   1. Makes test folder
#   2. Creates a test file
#   3. Writes a test function 
#   3. Calls the summarize_commit command
#   4. Validate Output

from pathlib import Path
import subprocess

class DebugSummarizeCommit:
    def __init__(self):
        self.repo_root = Path(__file__).resolve().parent
        self.test_folder_path: Path 

    def create_test_folder(self)->None:
        """Creates test folder in root directory."""

        test_folder = self.repo_root / "debug_summarize_commit"
        test_folder.mkdir(exist_ok=True)
        self.test_folder_path = test_folder

    def create_test_file(self)-> int:
        """Creates Test File in Test Folder with a Temp Function"""
        
        with open(self.test_folder_path / "test_file.py", "w", encoding="utf-8") as f:
            f.write(
                """def test_function(): print("This is a test function")"""
            )
            
        if not (self.test_folder_path / "test_file.py").exists():
            raise FileNotFoundError("Test file was not created successfully.")
        else:
            print("Test file created successfully.")
            return 1        
    
    def call_summarize_commit(self)->None:
        """Calls the summarize commit function annd validates the output."""
        subprocess.run(
            ["python", "summarize_commit.py",]
        )
        
        
        

debug = DebugSummarizeCommit()
res = debug.create_test_folder()
success = debug.create_test_file()
        