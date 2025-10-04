# Deep Organizer 🤖📁

> An intelligent AI agent that automatically organizes files in your directories using advanced language models and content analysis.

## Overview

Deep Organizer is a Python-based AI agent that uses LangGraph and OpenAI's GPT models to intelligently analyze and organize files in a directory. The agent reads file contents, understands their purpose, creates appropriately named folders, and moves files into logical groupings automatically.

## Features

- 🧠 **AI-Powered Analysis**: Uses GPT models to understand file content and context
- 📂 **Smart Folder Creation**: Automatically creates descriptive folders with proper naming
- 🔒 **Safety First**: Protects important system files and folders from being moved
- 📄 **Content-Based Organization**: Analyzes file contents, not just extensions
- ⚡ **Automated Workflow**: Single command execution with comprehensive reporting
- 🛡️ **Error Handling**: Robust error handling and validation

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for GPT model access)

### Option 1: Install from PyPI (Recommended)

```bash
pip install deep-organizer
```

### Option 2: Install from Source

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd deep-organizer
   ```

2. **Install the package**:
   ```bash
   pip install -e .
   ```

   Or for development with extra dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Environment Setup

Create a `.env` file in your working directory or set environment variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

Or export the variable in your shell:
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

## Usage

### Command Line Interface

After installation, you can use `deep-organizer` from anywhere in your terminal.

#### Basic Usage

```bash
# Organize files in the current directory
deep-organizer

# Organize files in a specific directory
deep-organizer --directory ~/Downloads

# Preview what would be organized (dry run)
deep-organizer --dry-run
```

#### Advanced Options

```bash
# Use verbose output to see detailed progress
deep-organizer --verbose

# Use a different AI model
deep-organizer --model "openai:gpt-4"

# Exclude additional files or folders
deep-organizer --exclude-files "secret.txt" "private.doc" \
                --exclude-folders "temp" "cache"

# Adjust file reading limit
deep-organizer --max-file-size 2000

# Check environment setup
deep-organizer --check-env
```

#### Complete Example

```bash
# Organize Downloads folder with verbose output and dry-run first
deep-organizer --directory ~/Downloads --dry-run --verbose

# If satisfied with the preview, run for real
deep-organizer --directory ~/Downloads --verbose
```

### What the Tool Does

The AI agent will:
1. Scan all files in the specified directory
2. Read and analyze file contents (up to specified character limit)
3. Create appropriate folders based on content analysis
4. Move files into their designated folders
5. Provide a comprehensive summary of actions taken

### Protected Files and Folders

The following items are automatically protected from being moved or analyzed:

**Protected Files**:
- `.env` - Environment variables
- `main.py` - The organizer script itself
- `.gitignore` - Git ignore file
- `requirements.txt` - Python dependencies

**Protected Folders**:
- `venv/` - Virtual environment
- `__pycache__/` - Python cache
- `.git/` - Git repository data

## How It Works

### Core Components

1. **File Discovery** (`get_file_list()`)
   - Scans the current directory
   - Filters out protected files and folders
   - Returns a clean list for processing

2. **Content Analysis** (`read_file()`)
   - Safely reads text files with encoding handling
   - Limits read size to prevent memory issues
   - Handles binary files gracefully

3. **Folder Management** (`create_folder()`)
   - Creates folders with validation
   - Prevents path traversal attacks
   - Ensures proper naming conventions

4. **File Movement** (`move_file()`)
   - Safely moves files between directories
   - Validates source and destination paths
   - Prevents moving of protected files

5. **AI Agent Integration**
   - Uses LangGraph's React agent framework
   - Leverages OpenAI's GPT-4-mini for intelligent decisions
   - Provides structured prompts for consistent behavior

### Agent Behavior

The AI agent follows this workflow:

1. **Analysis Phase**: Reads and analyzes file contents to understand their purpose
2. **Planning Phase**: Determines logical folder structure based on content themes
3. **Creation Phase**: Creates folders with descriptive, capitalized names
4. **Organization Phase**: Moves files into appropriate folders
5. **Reporting Phase**: Provides a summary of actions taken

## Configuration

### Model Configuration

By default, the agent uses `openai:gpt-4-mini`. You can modify this in `main.py`:

```python
agent = create_react_agent(
    model="openai:gpt-4",  # or "anthropic:claude-3-sonnet" etc.
    tools=[get_cur_dir, get_file_list, create_folder, move_file, read_file],
    # ...
)
```

### Safety Limits

Adjust these constants in `main.py` as needed:

```python
MAX_FILE_READ_SIZE = 1000  # Characters to read per file
EXCLUDED_FILES = {".env", "main.py", ".gitignore", "requirements.txt"}
EXCLUDED_FOLDERS = {"venv", "__pycache__", ".git"}
```

## Examples

### Before Organization
```
/messy-directory/
├── report.pdf
├── vacation_photo.jpg
├── budget.xlsx
├── recipe.txt
├── presentation.pptx
├── song.mp3
└── code_snippet.py
```

### After Organization
```
/messy-directory/
├── Documents/
│   ├── report.pdf
│   ├── budget.xlsx
│   └── presentation.pptx
├── Images/
│   └── vacation_photo.jpg
├── Audio/
│   └── song.mp3
├── Recipes/
│   └── recipe.txt
└── Code/
    └── code_snippet.py
```

## Troubleshooting

### Common Issues

1. **"Error running agent: API key not found"**
   - Ensure your `.env` file contains a valid `OPENAI_API_KEY`
   - Verify the API key has sufficient credits

2. **"Permission denied" errors**
   - Ensure you have write permissions in the target directory
   - Check if files are not currently in use by other applications

3. **"Binary file cannot be read" messages**
   - This is normal behavior for binary files (images, executables, etc.)
   - The agent will still organize them based on file extensions

### Debug Mode

For debugging, you can add print statements or modify the recursion limit:

```python
result = agent.invoke(
    {"messages": [...]},
    {"recursion_limit": 2000}  # Increase for complex directories
)
```

## Contributing

Contributions are welcome! Here are some ways you can help:

- 🐛 Report bugs or issues
- 💡 Suggest new features or improvements
- 📚 Improve documentation
- 🔧 Submit pull requests

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test them
4. Submit a pull request

## Dependencies

- **langgraph**: Framework for building language model agents
- **langchain[anthropic]**: LangChain with Anthropic support
- **python-dotenv**: Environment variable management

## Security Considerations

- The agent only operates on the current working directory
- Protected files and system folders are excluded by design
- File reading is limited to prevent memory exhaustion
- Path traversal attacks are prevented through validation
- API keys are kept secure in environment variables

## Performance

- **File Reading**: Limited to 1000 characters per file for efficiency
- **API Calls**: Optimized to minimize token usage
- **Memory Usage**: Minimal memory footprint through streaming
- **Processing Speed**: Depends on file count and API response times

## Roadmap

- [ ] Support for custom organization rules
- [ ] GUI interface for non-technical users
- [ ] Integration with cloud storage services
- [ ] Batch processing for multiple directories
- [ ] Custom AI model support
- [ ] Undo functionality

## License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2024 Deep Organizer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Search existing issues on GitHub
3. Create a new issue with detailed information
4. Include your Python version, OS, and error messages

---

**Made with ❤️ and AI** | *Organizing chaos, one directory at a time*
