# Briefcase Setup Guide for Deep Organizer

## Installation

Requires Python 3.10 or newer.

```bash
pip install briefcase
```

## Configuration

Create `pyproject.toml` configuration (adding to existing file):

```toml
[tool.briefcase]
project_name = "Deep Organizer"
bundle = "com.deeporganizer"
version = "1.0.0"
url = "https://github.com/MarkCodering/deep-organizer"
license = "MIT"
author = "Deep Organizer Team"
author_email = "contact@deeporganizer.com"

[tool.briefcase.app.deep-organizer]
formal_name = "Deep Organizer"
description = "AI-powered file organization tool"
icon = "packaging/mac/deep_organizer"  # Will look for .icns/.png
sources = ["deep_organizer"]
requires = [
    "langgraph",
    "langchain[anthropic]",
    "langchain[openai]",
    "python-dotenv",
    "PyQt6>=6.7"
]

[tool.briefcase.app.deep-organizer.macOS]
requires = [
    "std-nslog~=1.0.0"
]
universal_build = false  # Target Apple Silicon only to avoid universal merge issues
```

## Build Commands

```bash
# If you previously built with PySide6, remove cached artefacts
rm -rf build/deep-organizer dist/deep-organizer ~/.briefcase/support/*

# Create the app scaffold
briefcase create

# Build the app
briefcase build

# Refresh the bundle and reinstall dependencies
briefcase update -r

# Run the app (for testing)
briefcase run
# Package for distribution (creates .app bundle)
briefcase package

# Package and code sign (for App Store or distribution)
briefcase package --adhoc-sign
```

## Advantages over PyInstaller

- **Smaller bundle size** (typically 30-50% smaller)
- **Faster startup** (lazy loading)
- **Native look & feel** (proper macOS integration)
- **Better updates** (can use delta updates)
- **Cross-platform** (same config for all platforms)
