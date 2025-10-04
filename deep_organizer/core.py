"""
Core functionality for the Deep Organizer AI agent.
"""

import shutil
from pathlib import Path
from typing import List, Optional
import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()


class FileOrganizer:
    """Main class for organizing files using AI."""
    
    # Constants
    DEFAULT_EXCLUDED_FILES = {".env", "main.py", ".gitignore", "requirements.txt", 
                              "setup.py", "pyproject.toml", "LICENSE", "README.md"}
    DEFAULT_EXCLUDED_FOLDERS = {"venv", "__pycache__", ".git", "node_modules", 
                                "dist", "build", ".pytest_cache", ".tox"}
    DEFAULT_MAX_FILE_READ_SIZE = 1000
    
    def __init__(self, 
                 work_dir: Optional[str] = None,
                 model: str = "openai:gpt-4-mini",
                 excluded_files: Optional[set] = None,
                 excluded_folders: Optional[set] = None,
                 max_file_read_size: int = DEFAULT_MAX_FILE_READ_SIZE):
        """
        Initialize the FileOrganizer.
        
        Args:
            work_dir: Directory to organize (defaults to current directory)
            model: AI model to use for organization decisions
            excluded_files: Set of files to exclude from organization
            excluded_folders: Set of folders to exclude from organization
            max_file_read_size: Maximum characters to read from each file
        """
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        self.model = model
        self.excluded_files = excluded_files or self.DEFAULT_EXCLUDED_FILES
        self.excluded_folders = excluded_folders or self.DEFAULT_EXCLUDED_FOLDERS
        self.max_file_read_size = max_file_read_size
        
        # Validate working directory
        if not self.work_dir.exists() or not self.work_dir.is_dir():
            raise ValueError(f"Work directory does not exist or is not a directory: {self.work_dir}")
    
    def get_cur_dir(self) -> str:
        """Returns the current working directory path as a string."""
        return str(self.work_dir.resolve())
    
    def get_file_list(self) -> List[str]:
        """
        Returns a filtered list of files and folders in the working directory.
        Excludes protected files and folders defined in constants.
        """
        try:
            all_items = [item.name for item in self.work_dir.iterdir()]
            
            # Filter out excluded items
            filtered_items = [
                item for item in all_items 
                if item not in self.excluded_files and item not in self.excluded_folders
            ]
            
            return filtered_items
        except Exception as e:
            return [f"Error listing files: {str(e)}"]
    
    def create_folder(self, folder_name: str) -> str:
        """
        Creates a new folder in the working directory.
        
        Args:
            folder_name: Name of the folder to create
            
        Returns:
            Success or error message
        """
        try:
            # Validate folder name
            if not folder_name or folder_name.strip() == "":
                return "Error: Folder name cannot be empty."
            
            # Prevent path traversal
            if ".." in folder_name or "/" in folder_name or "\\" in folder_name:
                return "Error: Invalid folder name. Avoid path separators."
            
            path = self.work_dir / folder_name
            path.mkdir(parents=True, exist_ok=True)
            return f"Folder '{folder_name}' created successfully at {path}"
        except Exception as e:
            return f"Error creating folder '{folder_name}': {str(e)}"
    
    def move_file(self, file_name: str, dest_folder: str) -> str:
        """
        Moves a file to the specified folder within the working directory.
        
        Args:
            file_name: Name of the file to move
            dest_folder: Destination folder name
            
        Returns:
            Success or error message
        """
        try:
            # Security check - prevent moving protected files
            if file_name in self.excluded_files:
                return f"Error: Cannot move protected file '{file_name}'."
            
            src_path = self.work_dir / file_name
            dest_path = self.work_dir / dest_folder / file_name
            
            # Validate source file exists
            if not src_path.exists():
                return f"Error: Source file '{file_name}' does not exist."
            
            # Validate it's a file, not a directory
            if not src_path.is_file():
                return f"Error: '{file_name}' is not a file."
            
            # Validate destination folder exists
            if not dest_path.parent.exists():
                return f"Error: Destination folder '{dest_folder}' does not exist."
            
            # Use shutil.move for better cross-platform compatibility
            shutil.move(str(src_path), str(dest_path))
            return f"File '{file_name}' moved to '{dest_folder}' successfully."
        except Exception as e:
            return f"Error moving file '{file_name}': {str(e)}"
    
    def read_file(self, file_name: str) -> str:
        """
        Reads the content of a text file with a character limit.
        
        Args:
            file_name: Name of the file to read
            
        Returns:
            File content (truncated) or error message
        """
        try:
            # Security check
            if file_name in self.excluded_files:
                return f"Error: Cannot read protected file '{file_name}'."
            
            path = self.work_dir / file_name
            
            if not path.exists():
                return f"Error: File '{file_name}' does not exist."
            
            if not path.is_file():
                return f"Error: '{file_name}' is not a file."
            
            # Try to read as text, handle binary files gracefully
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read(self.max_file_read_size)
                    if len(content) == self.max_file_read_size:
                        content += f"\n... (truncated at {self.max_file_read_size} characters)"
                    return content
            except UnicodeDecodeError:
                return f"Error: '{file_name}' appears to be a binary file and cannot be read as text."
        except Exception as e:
            return f"Error reading file '{file_name}': {str(e)}"
    
    def organize(self, dry_run: bool = False) -> dict:
        """
        Main function to organize files using the AI agent.
        
        Args:
            dry_run: If True, only show what would be done without actually moving files
            
        Returns:
            Dictionary with organization results
        """
        try:
            # Create the agent with bound methods
            agent = create_react_agent(
                model=self.model,
                tools=[self.get_cur_dir, self.get_file_list, self.create_folder, self.move_file, self.read_file],
                prompt=(
                    "You are a helpful file organization assistant. Your task is to:\n"
                    "1. Analyze files in the current directory by reading their content\n"
                    "2. Create folders with descriptive names (starting with capital letters)\n"
                    "3. Organize files into appropriate folders based on their content and type\n"
                    "4. Provide a summary of the organization performed\n\n"
                    "Note: Some files and folders are protected and cannot be moved or read."
                ),
            )
            
            # Prepare the message
            message_content = (
                "Please organize the files in the current directory. "
                "Create appropriate folders and move files based on their content and type. "
                "Protected files and folders will be automatically excluded."
            )
            
            if dry_run:
                message_content += " This is a dry run - only analyze and report what you would do, don't actually create folders or move files."
            
            # Run the agent
            result = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": message_content
                        }
                    ]
                },
                {"recursion_limit": 1000}
            )
            
            return {
                "success": True,
                "result": result,
                "message": "File organization completed successfully!"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error during organization: {str(e)}"
            }