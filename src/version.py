"""
Application version information.
This file is auto-generated during build process.
"""

VERSION = "0.5.32"
GIT_HASH = "4e19b5a"
GIT_BRANCH = "refactor-build-modularization"
BUILD_DATE = "2025-12-09T18:56:08.247419Z"

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
