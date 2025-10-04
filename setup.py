"""
Setup configuration for Deep Organizer package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().strip().split('\n')

setup(
    name="deep-organizer",
    version="1.0.0",
    author="Deep Organizer",
    author_email="",
    description="AI-powered file organization tool that intelligently organizes files based on content analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/deep-organizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
    },
    entry_points={
        "console_scripts": [
            "deep-organizer=deep_organizer.cli:main",
            "deep_organizer=deep_organizer.cli:main",
        ],
    },
    keywords=[
        "ai",
        "file-organization", 
        "automation",
        "cli",
        "productivity",
        "file-management",
        "langchain",
        "openai",
        "gpt"
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/deep-organizer/issues",
        "Source": "https://github.com/yourusername/deep-organizer",
        "Documentation": "https://github.com/yourusername/deep-organizer#readme",
    },
    include_package_data=True,
    zip_safe=False,
)