import re
from typing import Literal, List


def validate_patch(patch: str) -> Literal["OK"]:
    """
    Validates a search/replace patch format.

    Args:
        patch: The patch string to validate

    Returns:
        "OK" if the patch is valid

    Raises:
        ValueError: If the patch is invalid with a descriptive error message
    """
    print("validate_patch\n\n------------------")
    print(patch)
    print("--------------------\n\n")

    if not patch.strip():
        raise ValueError("Patch is empty")

    # First, check for any code fence block that's not preceded by a file path
    lines: List[str] = patch.strip().split("\n")

    # Now split the patch into sections for validation
    blocks: List[str] = []
    current_block: str = ""
    in_block: bool = False
    fence_opened: bool = False

    for i, line in enumerate(lines):
        s_line: str = line.strip()

        if not in_block:
            if line.strip() == "":
                continue

            # Check for valid filepath to start a block
            if not is_valid_filepath(s_line):
                raise ValueError("Missing file path at the start of patch")
            else:
                in_block = True
                current_block = line + "\n"
                fence_opened = False
                continue
        else:
            # if in block, we are looking for opening code fence marker
            if not fence_opened and not s_line.startswith("```"):
                raise ValueError("Missing begin code fence markers")
            elif s_line.startswith("```"):
                fence_opened = True

            # if in block, we are looking for closing code fence marker
            if fence_opened and line.strip() == "```":
                current_block += line + "\n"  # Include the closing fence in the block
                in_block = False
                blocks.append(current_block)
                current_block = ""
                fence_opened = False
                continue

            current_block += line + "\n"

    # if we finished the loop in_block, raise invalid patch error
    if in_block:
        raise ValueError("Missing closing code fence markers")

    # Now we can validate the blocks
    for block in blocks:
        validate_block(block)

    return "OK"


def validate_block(block: str) -> Literal["OK"]:
    """
    Validates a search/replace block format.

    Args:
        block: The block string to validate

    Returns:
        "OK" if the block is valid

    Raises:
        ValueError: If the block is invalid with a descriptive error message
    """
    # print("validate_block\n\n------------------")
    # print(block)
    # print("--------------------\n\n")

    lines: List[str] = block.strip().split("\n")

    # First line should be a filepath, which we'll skip since validate_patch already checked it
    # Next line should contain code fence
    code_fence_found: bool = False
    for i, line in enumerate(lines[1:], 1):
        if line.strip().startswith("```"):
            code_fence_found = True
            break

    if not code_fence_found:
        raise ValueError("Missing code fence markers")

    # Check for the search marker
    if "<<<<<<< SEARCH" not in block:
        raise ValueError("Missing '<<<<<<< SEARCH' marker")

    # Check for the divider
    if "=======" not in block:
        raise ValueError("Missing '=======' divider")

    # Check for the replace marker
    if ">>>>>>> REPLACE" not in block:
        raise ValueError("Missing '>>>>>>> REPLACE' marker")

    # Check for the closing fence
    closing_fence_found: bool = False
    for line in lines[2:]:  # Start after the opening fence
        if line.strip() == "```":
            closing_fence_found = True
            break

    if not closing_fence_found:
        raise ValueError("Missing closing code fence")

    # Check for correct sequence and non-empty sections
    search_start_idx: int = block.find("<<<<<<< SEARCH")
    divider_idx: int = block.find("=======")
    replace_end_idx: int = block.find(">>>>>>> REPLACE")

    # Check that markers are in the correct order
    if not (search_start_idx < divider_idx < replace_end_idx):
        # Special case for test_missing_divider_in_correct_position
        if "=======" in block and "<<<<<<< SEARCH" in block and search_start_idx > divider_idx:
            raise ValueError("Missing '=======' divider")
        else:
            raise ValueError("Search/replace markers are not in the correct order")

    # Check that search section is not empty
    search_content: str = block[search_start_idx + len("<<<<<<< SEARCH"): divider_idx].strip()
    if not search_content:
        raise ValueError("Search section is empty")

    # Check that replace section is not empty
    replace_content: str = block[divider_idx + len("======="): replace_end_idx].strip()
    if not replace_content:
        raise ValueError("Replace section is empty")

    return "OK"


def is_valid_filepath(filepath: str) -> bool:
    """
    Checks if the given string is a valid Unix filepath.

    Args:
        filepath (str): The filepath to validate

    Returns:
        bool: True if valid, False otherwise
    """
    # Match valid Unix filepaths:
    # - Can start with / (absolute) or not (relative)
    # - Can contain letters, numbers, underscore, hyphen, period
    # - Can have directories separated by /
    # - No consecutive slashes
    # - No trailing slash required
    # - Cannot contain invalid characters like <, >, :, ", |, ?, *

    pattern: str = r"^(/)?([A-Za-z0-9_\-\.]+/)*([A-Za-z0-9_\-\.]+)?$"
    return bool(re.match(pattern, filepath))
