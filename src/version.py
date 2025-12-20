"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.6.10"
GIT_HASH = "0cf057e"
GIT_BRANCH = "NT"
BUILD_DATE = "2025-12-20T18:03:38.009563Z"

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
