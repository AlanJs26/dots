"""Validation utilities."""

from urllib.parse import urlparse
import re


def is_url_valid(url: str) -> bool:
    """Check if a string is a valid URL (has scheme and netloc).

    Args:
        url: URL string to validate

    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False

def is_git_url_valid(url: str) -> bool:
    return bool(re.search(r"git@\w+\.\w+:\w+\/[\w-]+\.git", url))
    
