"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.67"
GIT_HASH = "db6225f"
GIT_BRANCH = "v2-installer-architecture"
BUILD_DATE = "2025-12-11T01:42:42.822369Z"

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
