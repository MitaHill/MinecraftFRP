"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.32"
GIT_HASH = "35e3160"
GIT_BRANCH = "v2-installer-architecture"
BUILD_DATE = "2025-12-10T05:47:57.515858Z"

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
