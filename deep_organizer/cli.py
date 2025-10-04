"""
Command line interface for Deep Organizer.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import os

from .core import FileOrganizer
from . import __version__


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="deep-organizer",
        description="AI-powered file organization tool that intelligently organizes files based on content analysis.",
        epilog="Example: deep-organizer --directory ~/Downloads --dry-run"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"deep-organizer {__version__}"
    )
    
    parser.add_argument(
        "-d", "--directory",
        type=str,
        default=".",
        help="Directory to organize (default: current directory)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="openai:gpt-4-mini",
        help="AI model to use for organization (default: openai:gpt-4-mini)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually moving files"
    )
    
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=1000,
        help="Maximum characters to read from each file (default: 1000)"
    )
    
    parser.add_argument(
        "--exclude-files",
        nargs="*",
        help="Additional files to exclude from organization"
    )
    
    parser.add_argument(
        "--exclude-folders",
        nargs="*",
        help="Additional folders to exclude from organization"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check if required environment variables are set"
    )
    
    return parser


def check_environment() -> bool:
    """
    Check if required environment variables are set.
    
    Returns:
        True if environment is properly configured, False otherwise
    """
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for AI model access"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} - {description}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  • {var}")
        print("\n💡 Create a .env file in your working directory with:")
        print("   OPENAI_API_KEY=your_openai_api_key_here")
        return False
    
    print("✅ Environment variables are properly configured!")
    return True


def validate_directory(directory: str) -> Optional[Path]:
    """
    Validate that the directory exists and is accessible.
    
    Args:
        directory: Directory path to validate
        
    Returns:
        Path object if valid, None otherwise
    """
    try:
        path = Path(directory).resolve()
        if not path.exists():
            print(f"❌ Error: Directory does not exist: {path}")
            return None
        if not path.is_dir():
            print(f"❌ Error: Path is not a directory: {path}")
            return None
        if not os.access(path, os.R_OK | os.W_OK):
            print(f"❌ Error: Insufficient permissions for directory: {path}")
            return None
        return path
    except Exception as e:
        print(f"❌ Error validating directory: {e}")
        return None


def print_banner():
    """Print the application banner."""
    print("""
🤖📁 Deep Organizer v{version}
AI-powered file organization tool
    """.format(version=__version__).strip())


def print_summary(result: dict, dry_run: bool = False):
    """
    Print a summary of the organization results.
    
    Args:
        result: Result dictionary from FileOrganizer.organize()
        dry_run: Whether this was a dry run
    """
    print("\n" + "="*60)
    if dry_run:
        print("🔍 DRY RUN COMPLETED")
    else:
        print("✅ ORGANIZATION COMPLETED")
    print("="*60)
    
    if result["success"]:
        print("📊 Summary:")
        print(f"   Status: {'Analyzed (no changes made)' if dry_run else 'Successfully organized'}")
        
        # Extract useful information from the agent result
        if "result" in result and "messages" in result["result"]:
            messages = result["result"]["messages"]
            if messages:
                last_message = messages[-1]
                if "content" in last_message:
                    print("\n🤖 AI Agent Report:")
                    print("   " + last_message["content"])
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error occurred')}")


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Print banner unless we're just checking environment
    if not args.check_env:
        print_banner()
    
    # Handle environment check
    if args.check_env:
        return 0 if check_environment() else 1
    
    # Check environment variables
    if not check_environment():
        print("\n💡 Use --check-env to verify your environment setup.")
        return 1
    
    # Validate directory
    work_dir = validate_directory(args.directory)
    if work_dir is None:
        return 1
    
    if args.verbose:
        print(f"📂 Working directory: {work_dir}")
        print(f"🤖 AI Model: {args.model}")
        print(f"📏 Max file read size: {args.max_file_size} characters")
        if args.dry_run:
            print("🔍 Dry run mode: No files will be moved")
    
    try:
        # Prepare exclusion sets
        excluded_files = set()
        excluded_folders = set()
        
        if args.exclude_files:
            excluded_files.update(args.exclude_files)
            if args.verbose:
                print(f"🚫 Additional excluded files: {', '.join(args.exclude_files)}")
        
        if args.exclude_folders:
            excluded_folders.update(args.exclude_folders)
            if args.verbose:
                print(f"🚫 Additional excluded folders: {', '.join(args.exclude_folders)}")
        
        # Create organizer instance
        organizer = FileOrganizer(
            work_dir=str(work_dir),
            model=args.model,
            excluded_files=excluded_files if excluded_files else None,
            excluded_folders=excluded_folders if excluded_folders else None,
            max_file_read_size=args.max_file_size
        )
        
        # Get file list for preview
        file_list = organizer.get_file_list()
        if args.verbose:
            print(f"📋 Found {len(file_list)} items to analyze:")
            for item in file_list[:10]:  # Show first 10
                print(f"   • {item}")
            if len(file_list) > 10:
                print(f"   ... and {len(file_list) - 10} more")
        
        print(f"\n🚀 Starting {'analysis' if args.dry_run else 'organization'}...")
        
        # Run organization
        result = organizer.organize(dry_run=args.dry_run)
        
        # Print results
        print_summary(result, dry_run=args.dry_run)
        
        return 0 if result["success"] else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Organization interrupted by user.")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())