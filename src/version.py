"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.32"
GIT_HASH = "776b5c5"
GIT_BRANCH = "feature-2025-12-09"
BUILD_DATE = "2025-12-09T18:34:42.170259Z"

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
