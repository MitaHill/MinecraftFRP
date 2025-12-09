"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.31"
GIT_HASH = "unknown"
GIT_BRANCH = "unknown"
BUILD_DATE = "unknown"

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
