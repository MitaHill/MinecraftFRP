"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.6.6"
GIT_HASH = "e644ba9"
GIT_BRANCH = "main"
BUILD_DATE = "2025-12-18T14:48:00.149101Z"

def get_version_info():
    """Get formatted version information."""
    return {
        "version": VERSION,
        "git_hash": GIT_HASH,
        "git_branch": GIT_BRANCH,
        "build_date": BUILD_DATE
    }

def get_version_string():
    """Get version string for display."""
    return f"MinecraftFRP v{VERSION} ({GIT_HASH})"
