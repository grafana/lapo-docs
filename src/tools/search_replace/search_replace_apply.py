import re
import os
import tempfile
import subprocess
from typing import List, Tuple, Optional
from rich import print


def split_search_replace_into_file_blocks(patch_content: str) -> List[Tuple[str, str]]:
    """Split a patch into file-specific blocks.

    Parameters:
        patch_content (str): The entire patch content as a string, containing one or more
            file blocks. Each file block starts with a filename line which serves as the
            delimiter between blocks. Each block contains search/replace sections with
            '<<<<<<< SEARCH', '=======', and '>>>>>>> REPLACE' markers.

            Example with multiple blocks:
            docusaurus/docs/path/to/file1.md
            ```markdown
            <<<<<<< SEARCH
            old content for file1
            =======
            new content for file1
            >>>>>>> REPLACE
            ```

            docusaurus/docs/path/to/file2.md
            ```markdown
            <<<<<<< SEARCH
            old content for file2
            =======
            new content for file2
            >>>>>>> REPLACE
            ```

    Returns:
        list: A list of tuples (filename, block_content), where filename is the extracted
            file path and block_content is the full content for that file's patch including
            all search/replace sections for that file.
    """
    # Match any line that looks like a filepath with forward slashes
    file_pattern = r"^(\S+/\S+)$"

    # Find all filepath matches
    filepath_matches = list(re.finditer(file_pattern, patch_content, re.MULTILINE))

    if not filepath_matches:
        return []

    file_blocks = []
    # Group blocks by filename
    filename_to_blocks = {}

    for i, match in enumerate(filepath_matches):
        filename = match.group(1)
        start_pos = match.start()

        # Get the end position (either the start of the next filename or the end of the content)
        if i < len(filepath_matches) - 1:
            end_pos = filepath_matches[i + 1].start()
        else:
            end_pos = len(patch_content)

        # Extract the block content
        block_content = patch_content[start_pos:end_pos].strip()

        # Add the block to the list for this filename
        if filename not in filename_to_blocks:
            filename_to_blocks[filename] = []

        filename_to_blocks[filename].append(block_content)

    # For each filename, combine all blocks for that file
    for filename, blocks in filename_to_blocks.items():
        combined_content = "\n\n".join(blocks)
        file_blocks.append((filename, combined_content))

    return file_blocks


def split_block_into_search_replace_pairs(block_content: str) -> List[Tuple[str, str]]:
    """Extract search/replace pairs from a block.

    Parameters:
        block_content (str): Content of a single file block containing one or more
            search/replace sections with '<<<<<<< SEARCH', '=======', and '>>>>>>> REPLACE' markers.
            Each section may be preceded by a filename line.

    Returns:
        list: A list of tuples (search_part, replace_part), where search_part is the
            text to find and replace_part is the text to replace it with.
    """
    # First, remove the filename lines if they exist within the block content
    # This is necessary as the block may contain multiple sections each with the filename
    file_pattern = r"^(\S+/\S+)$"
    block_content = re.sub(file_pattern, "", block_content, flags=re.MULTILINE)

    # Find all search/replace sections directly
    search_pattern = r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
    matches = re.findall(search_pattern, block_content, re.DOTALL)

    pairs = []
    for search_part, replace_part in matches:
        # Remove markdown code block markers if present
        search_part = re.sub(r"```\w*\n|\n```", "", search_part).strip()
        replace_part = re.sub(r"```\w*\n|\n```", "", replace_part).strip()

        pairs.append((search_part, replace_part))

    return pairs


def apply_search_replace_pairs_to_content(content: str, search_replace_pairs: List[Tuple[str, str]]) -> str:
    """Apply search/replace pairs to content.

    Parameters:
        content (str): The original file content as a string that will be modified
            by applying search/replace operations.
        search_replace_pairs (list): A list of tuples (search_part, replace_part), where
            each tuple represents a text replacement operation. Each search_part string
            will be replaced with its corresponding replace_part string.

    Returns:
        str: The modified content after all search/replace operations have been applied.
    """
    for search_part, replace_part in search_replace_pairs:
        content = content.replace(search_part, replace_part)
    return content


def apply_search_replace_to_content(
    source_content: str, search_replace_blocks: str, target_filename: Optional[str] = None
) -> Tuple[str, bool]:
    """Process a patch and apply it to source content.

    Parameters:
        source_content (str): The original file content as a string.
        search_replace_blocks (str): The entire patch content as a string, which may contain
            file headers and one or more search/replace blocks. Each block is marked
            with '<<<<<<< SEARCH', '=======', and '>>>>>>> REPLACE' delimiters.
        target_filename (str, optional): The filename to verify against the patch.
            If provided, only apply patches that match this filename.

    Returns:
        tuple: A tuple containing:
            - str: The modified source content after applying all patches.
            - bool: True if the patch was applied successfully, False if the filename didn't match.
    """
    # If the patch content is empty, return the source content unchanged
    if not search_replace_blocks.strip():
        return source_content, True  # Return True for empty patches to match test expectations

    # Get all file blocks from the patch
    file_blocks = split_search_replace_into_file_blocks(search_replace_blocks)
    if not file_blocks:
        return source_content, False

    # If target_filename is provided, verify it matches the filename in the patch
    if target_filename:
        # Find the file block that matches the target filename
        for filename, block in file_blocks:
            if filename == target_filename:
                # Extract search/replace pairs for this file
                search_replace_pairs = split_block_into_search_replace_pairs(block)

                # Apply the patch
                patched_content = apply_search_replace_pairs_to_content(source_content, search_replace_pairs)
                return patched_content, bool(search_replace_pairs)  # Return True if any pairs were applied

        # No matching filename found
        return source_content, False
    else:
        # When no target_filename is provided, apply all blocks
        # This is potentially dangerous, as it might apply mismatched blocks,
        # but we keep it for backward compatibility
        patched_content = source_content
        applied = False

        for _, block in file_blocks:
            # Extract search/replace pairs for this file
            search_replace_pairs = split_block_into_search_replace_pairs(block)

            # Apply the search/replace pairs
            if search_replace_pairs:
                patched_content = apply_search_replace_pairs_to_content(patched_content, search_replace_pairs)
                applied = True

        return patched_content, applied


def generate_git_patch_from_search_replace(repo_path: str, search_replace_blocks: str) -> str:
    """Generate a git patch by applying search/replace blocks to content.

    Parameters:
        repo_path (str): The path to the git repository.
        search_replace_blocks (str): String containing one or more search/replace blocks with
            '<<<<<<< SEARCH', '=======', and '>>>>>>> REPLACE' markers.

    Returns:
        str: A valid git patch that can be applied with git apply.
    """

    # blocks will have all blocks grouped by filename
    blocks = split_search_replace_into_file_blocks(search_replace_blocks)
    if not blocks:
        return ""

    patches = []

    # blocks could be for multiple files
    # and there might be more than one block per file
    for filename, block_content in blocks:

        original_content = get_file_content(repo_path, filename)
        modified_content, success = apply_search_replace_to_content(original_content, block_content, filename)

        # TODO handle error
        if not success:
            print(f"Failed to apply search/replace to {filename}")
            continue

        # If no changes were applied, skip this file
        if original_content == modified_content:
            print(f"No changes applied to {filename}")
            continue

        # now we'll create a patch for this file
        with tempfile.NamedTemporaryFile("w", delete=False) as temp_file:
            temp_file.write(modified_content)
            temp_file.flush()
            git_patch = generate_git_patch(repo_path, filename, temp_file.name)
            patches.append(git_patch)

    return "\n".join(patches)


def generate_git_patch(repo_path: str, orig_file_path: str, modified_file_path: str) -> str:
    """Generate a git patch by comparing two files.

    Parameters:
        repo_path (str): The path to the git repository.
        orig_file_path (str): The path to the original file.
        modified_file_path (str): The path to the modified file.

    Returns:
        str: A valid git patch that can be applied with git apply.
    """
    try:
        # Get the original filename without the path
        orig_filename = os.path.basename(orig_file_path)

        # Use git diff with paths to original and modified files
        diff_cmd = ["git", "diff", "--no-index", "--no-prefix", "--no-color",
                    orig_file_path, modified_file_path]

        # Run the command in the repo context
        result = subprocess.run(
            diff_cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=repo_path,
        )

        # Only treat exit codes > 1 as errors, exit code 1 means differences found
        if result.returncode > 1:
            print(f"Error in git diff command. Return code: {result.returncode}")
            return ""

        output = cleanup_git_patch(result.stdout)

        # prepend the file name as a/ and b/
        output = f"+++ b/{orig_file_path}\n" + output
        output = f"--- a/{orig_file_path}\n" + output

        return output
    except Exception as e:
        print(f"Error generating git patch: {e}")
        return ""


def cleanup_git_patch(patch_content: str) -> str:
    """Clean up a git patch by removing all file-related lines.

    This function removes lines that start with 'diff --git', 'index', '---', and '+++'

    Parameters:
        patch_content (str): The git patch content to clean up.

    Returns:
        str: The cleaned-up git patch content.
    """

    output = patch_content
    # replace ^diff --git.*?$ with empty
    output = re.sub(r"^diff --git.*?$\n", "", output, flags=re.MULTILINE)

    # replace ^index.*?$ with empty
    output = re.sub(r"^index.*?$\n", "", output, flags=re.MULTILINE)

    # replace --- filename
    output = re.sub(r"^---.*?$\n", "", output, flags=re.MULTILINE)

    # replace +++ filename
    output = re.sub(r"^\+\+\+.*?$\n", "", output, flags=re.MULTILINE)

    return output


def get_file_content(repo_path: str, filename: str) -> str:
    file_path = os.path.join(repo_path, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
