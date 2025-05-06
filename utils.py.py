import re
import os

def clean_filename(name):
    """
    Clean a string to make it suitable for use as a filename or folder name.
    Remove invalid characters and trim whitespace.
    """
    # Remove characters that are invalid in filenames
    cleaned = re.sub(r'[\\/*?:"<>|]', '', name)
    # Replace multiple spaces with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Trim whitespace
    cleaned = cleaned.strip()
    return cleaned

def create_directory_if_not_exists(directory_path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return directory_path
