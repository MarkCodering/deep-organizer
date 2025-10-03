import shutil
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent

load_dotenv()

# Constants
EXCLUDED_FILES = {".env", "main.py", ".gitignore", "requirements.txt"}
EXCLUDED_FOLDERS = {"venv", "__pycache__", ".git"}
MAX_FILE_READ_SIZE = 1000


def get_cur_dir() -> str:
    """Returns the current directory path as a string."""
    return str(Path(__file__).parent.resolve())


def get_file_list() -> List[str]:
    """
    Returns a filtered list of files and folders in the current directory.
    Excludes protected files and folders defined in constants.
    """
    try:
        current_dir = Path(get_cur_dir())
        all_items = [item.name for item in current_dir.iterdir()]
        
        # Filter out excluded items
        filtered_items = [
            item for item in all_items 
            if item not in EXCLUDED_FILES and item not in EXCLUDED_FOLDERS
        ]
        
        return filtered_items
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


def create_folder(folder_name: str) -> str:
    """
    Creates a new folder in the current directory.
    
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
        
        path = Path(get_cur_dir()) / folder_name
        path.mkdir(parents=True, exist_ok=True)
        return f"Folder '{folder_name}' created successfully at {path}"
    except Exception as e:
        return f"Error creating folder '{folder_name}': {str(e)}"


def move_file(file_name: str, dest_folder: str) -> str:
    """
    Moves a file to the specified folder within the current directory.
    
    Args:
        file_name: Name of the file to move
        dest_folder: Destination folder name
        
    Returns:
        Success or error message
    """
    try:
        # Security check - prevent moving protected files
        if file_name in EXCLUDED_FILES:
            return f"Error: Cannot move protected file '{file_name}'."
        
        current_dir = Path(get_cur_dir())
        src_path = current_dir / file_name
        dest_path = current_dir / dest_folder / file_name
        
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


def read_file(file_name: str) -> str:
    """
    Reads the content of a text file with a character limit.
    
    Args:
        file_name: Name of the file to read
        
    Returns:
        File content (truncated) or error message
    """
    try:
        # Security check
        if file_name in EXCLUDED_FILES:
            return f"Error: Cannot read protected file '{file_name}'."
        
        path = Path(get_cur_dir()) / file_name
        
        if not path.exists():
            return f"Error: File '{file_name}' does not exist."
        
        if not path.is_file():
            return f"Error: '{file_name}' is not a file."
        
        # Try to read as text, handle binary files gracefully
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read(MAX_FILE_READ_SIZE)
                if len(content) == MAX_FILE_READ_SIZE:
                    content += f"\n... (truncated at {MAX_FILE_READ_SIZE} characters)"
                return content
        except UnicodeDecodeError:
            return f"Error: '{file_name}' appears to be a binary file and cannot be read as text."
    except Exception as e:
        return f"Error reading file '{file_name}': {str(e)}"


def main():
    """Main function to initialize and run the file organization agent."""
    # Create the agent
    agent = create_react_agent(
        model="openai:gpt-5-mini",
        tools=[get_cur_dir, get_file_list, create_folder, move_file, read_file],
        prompt=(
            "You are a helpful file organization assistant. Your task is to:\n"
            "1. Analyze files in the current directory by reading their content\n"
            "2. Create folders with descriptive names (starting with capital letters)\n"
            "3. Organize files into appropriate folders based on their content and type\n"
            "4. Provide a summary of the organization performed\n\n"
            "Note: Some files and folders are protected and cannot be moved or read."
        ),
    )
    
    # Run the agent
    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Please organize the files in the current directory. "
                            "Create appropriate folders and move files based on their content and type. "
                            "Protected files and folders will be automatically excluded."
                        )
                    }
                ]
            },
            {"recursion_limit": 1000}
        )
        
        print("\n" + "="*50)
        print("File Organization Complete!")
        print("="*50)
        
    except Exception as e:
        print(f"Error running agent: {str(e)}")


if __name__ == "__main__":
    main()