"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.75"
GIT_HASH = "4cb62f8"
GIT_BRANCH = "server-integration"
BUILD_DATE = "2025-12-11T12:24:42.344738Z"

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
