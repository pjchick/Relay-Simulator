"""
Version information for the simulation engine.
"""

import subprocess
import os
from pathlib import Path

__version__ = "0.1.0"
__author__ = "pjchick"
__description__ = "Multi-threaded relay logic simulation engine"


def get_git_commit_info():
    """
    Get Git commit information (commit hash and date).
    
    Returns:
        dict: {
            'commit': str - short commit hash (7 chars) or 'unknown',
            'commit_full': str - full commit hash or 'unknown',
            'date': str - commit date or 'unknown',
            'branch': str - current branch or 'unknown',
            'dirty': bool - True if there are uncommitted changes
        }
    """
    result = {
        'commit': 'unknown',
        'commit_full': 'unknown',
        'date': 'unknown',
        'branch': 'unknown',
        'dirty': False
    }
    
    try:
        # Try to find the git repository root
        current_file = Path(__file__).resolve()
        repo_root = current_file.parent.parent.parent  # Go up to project root
        
        # Get commit hash (short)
        try:
            commit = subprocess.check_output(
                ['git', 'rev-parse', '--short=7', 'HEAD'],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            result['commit'] = commit
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Get full commit hash
        try:
            commit_full = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            result['commit_full'] = commit_full
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Get commit date
        try:
            date = subprocess.check_output(
                ['git', 'log', '-1', '--format=%ci'],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            result['date'] = date
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Get current branch
        try:
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            result['branch'] = branch
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Check if working directory is dirty
        try:
            status = subprocess.check_output(
                ['git', 'status', '--porcelain'],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            result['dirty'] = bool(status)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
    except Exception:
        # If anything fails, return defaults
        pass
    
    return result


def get_version_string():
    """
    Get complete version string with Git information.
    
    Returns:
        str: Version string like "0.1.0 (commit: a1b2c3d)"
    """
    git_info = get_git_commit_info()
    
    version_str = __version__
    
    if git_info['commit'] != 'unknown':
        version_str += f" (build: {git_info['commit']}"
        if git_info['dirty']:
            version_str += "-dirty"
        version_str += ")"
    
    return version_str


def get_build_info():
    """
    Get detailed build information.
    
    Returns:
        dict: Complete version and build information
    """
    git_info = get_git_commit_info()
    
    return {
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'git_commit': git_info['commit'],
        'git_commit_full': git_info['commit_full'],
        'git_date': git_info['date'],
        'git_branch': git_info['branch'],
        'git_dirty': git_info['dirty'],
        'version_string': get_version_string()
    }
