# Deep Organizer 🤖📁

> An intelligent AI agent that automatically organizes files in your directories using advanced language models and content analysis.

## Overview

Deep Organizer is now a native-feeling desktop experience for macOS crafted with PySide6. The modern interface guides you through selecting a workspace, configuring your preferred AI model, and running a dry run or full organization in just a few clicks. Behind the scenes it still uses LangGraph and OpenAI (or Anthropic) models to intelligently analyze and organize files, creating folders and moving documents exactly where they belong.

## Features

- 🍎 **Native macOS polish**: Gradient hero header, glassmorphism cards, and SF Pro typography for a first-class desktop feel
- 🧠 **AI-powered analysis**: Uses OpenAI or Anthropic models to understand file content and context
- 📂 **Smart folder creation**: Automatically creates descriptive folders with proper naming
- 🔑 **In-app API key management**: Store keys locally, toggle visibility, and run sessions without touching the shell
- 📄 **Content-based organization**: Analyzes file contents, not just extensions, to determine intent
- ⚡ **Automated workflow**: Dry-run previews, background worker threads, and real-time activity logs keep you informed
- 🛡️ **Safety-first defaults**: Built-in exclusions guard critical files and folders from accidental moves

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for GPT model access)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd deep-organizer
   ```

2. **Install the package with GUI dependencies**:

   ```bash
   pip install -e .
   ```

   Or for development with extra dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

   Planning to ship a desktop bundle?

   ```bash
   pip install -e ".[packaging]"
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

### Launch the desktop app (macOS)

1. Start the GUI:

   ```bash
   python main.py
   ```

2. Paste an API key into the **API Access** panel (or let the app detect a saved/env key), then choose the directory you want to organize.
3. Adjust the AI model or limits if desired, and click **Start Organizing**. Use the dry run toggle to preview the plan before committing changes.

### Command Line Interface (optional)

The original CLI experience remains available for automation or remote environments:

```bash
# Organize files in the current directory
deep-organizer

# Run a dry run
deep-organizer --dry-run
```

### Build a native macOS app bundle

1. Install the optional packaging tools (already included if you ran `pip install -e ".[packaging]"`).
2. (Optional) Provide a custom icon: drop a `deep_organizer.icns` file into `packaging/mac/`. An editable `deep_organizer.svg` is supplied for convenience.
   > Tip: Convert the SVG to an ICNS by exporting PNG sizes (16–1024 px) and running `iconutil -c icns <iconset>` on macOS.
3. Run the build script from the project root:

   ```bash
   packaging/mac/build_app.sh
   ```

   Set `PYTHON_BIN` if you want to point at a specific interpreter, and append `--with-dmg` to produce a distributable DMG (`hdiutil` required).

The script assembles `dist/Deep Organizer.app`. Sign and notarize it before sharing:

```bash
codesign --deep --force --sign "Developer ID Application: Your Name" "dist/Deep Organizer.app"
xcrun notarytool submit "dist/Deep Organizer.app" --apple-id <apple-id> --team-id <team-id> --password <app-specific-password>
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

The GUI exposes model selection directly in the interface. For scripted usage, instantiate `FileOrganizer` with your desired model:

```python
from deep_organizer import FileOrganizer

organizer = FileOrganizer(model="anthropic:claude-3-sonnet")
organizer.organize(dry_run=True)
```

### Safety Limits

Adjust limits programmatically when creating the `FileOrganizer` instance:

```python
FileOrganizer(max_file_read_size=2000)
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
