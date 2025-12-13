"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.92"
GIT_HASH = "5da0855"
GIT_BRANCH = "small-fixing"
BUILD_DATE = "2025-12-25T23:28:23.614170Z"

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
