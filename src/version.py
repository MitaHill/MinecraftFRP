"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.32"
GIT_HASH = "6e8ac5d"
GIT_BRANCH = "v2-installer-architecture"
BUILD_DATE = "2025-12-10T06:20:24.869263Z"

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
