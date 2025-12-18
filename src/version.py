"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.6.3"
GIT_HASH = "a76b985"
GIT_BRANCH = "main"
BUILD_DATE = "2025-12-15T17:58:15.163862Z"

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
