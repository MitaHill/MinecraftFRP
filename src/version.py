"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.85"
GIT_HASH = "9c1440b"
GIT_BRANCH = "server-integration"
BUILD_DATE = "2025-12-11T21:20:13.740691Z"

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
