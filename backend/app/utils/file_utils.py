import os
import zipfile
import shutil
import logging
from typing import List

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".py", ".zip"}


def validate_file_extension(filename: str) -> bool:
    """Validates that the uploaded file is either a Python (.py) file or a ZIP (.zip) archive."""
    if not filename or "." not in filename:
        return False
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS


def safe_extract_zip(zip_path: str, extract_to: str) -> List[str]:
    """Extracts a ZIP archive safely, strictly preventing path traversal attacks (Zip Slip).

    Returns a list of absolute paths to extracted files.
    """
    extracted_files: List[str] = []
    real_extract_to = os.path.realpath(os.path.abspath(extract_to))
    os.makedirs(real_extract_to, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            # Resolve target path
            target_path = os.path.realpath(os.path.abspath(os.path.join(real_extract_to, member.filename)))

            # Prevent directory traversal
            if not target_path.startswith(real_extract_to + os.sep) and target_path != real_extract_to:
                logger.error(f"Malicious zip entry detected: {member.filename}")
                raise ValueError(f"Path traversal detected in zip archive: {member.filename}")

            # Do not extract dangerous or symlink attributes
            if member.is_dir():
                os.makedirs(target_path, exist_ok=True)
                continue

            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with archive.open(member) as source, open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)

            extracted_files.append(target_path)

    return extracted_files


def get_python_files(directory: str) -> List[str]:
    """Recursively retrieves all Python (.py) source files in the given directory,

    ignoring common virtual environment, cache, and version control directories.
    """
    python_files: List[str] = []
    ignored_dirs = {
        "__pycache__", ".git", ".venv", "venv", "env",
        ".env", "node_modules", ".pytest_cache", ".mypy_cache"
    }

    if os.path.isfile(directory) and directory.lower().endswith(".py"):
        return [os.path.abspath(directory)]

    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to avoid traversing ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]

        for file in files:
            if file.lower().endswith(".py"):
                full_path = os.path.abspath(os.path.join(root, file))
                python_files.append(full_path)

    return python_files


def get_code_snippet(file_path: str, line_num: int, context: int = 3) -> str:
    """Reads surrounding lines of code around the given line number for context.

    Returns formatted lines with line numbers and a marker for the target line.
    """
    if not os.path.exists(file_path):
        return ""

    content = ""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if not content:
        return ""

    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return ""

    start = max(1, line_num - context)
    end = min(total_lines, line_num + context)

    snippet_lines = []
    for idx in range(start, end + 1):
        line_content = lines[idx - 1]
        marker = " > " if idx == line_num else "   "
        snippet_lines.append(f"{marker}{idx:4d} | {line_content}")

    return "\n".join(snippet_lines)


def cleanup_directory(path: str) -> None:
    """Safely removes a temporary directory or file."""
    if not path or not os.path.exists(path):
        return

    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Failed to cleanup path {path}: {e}")
