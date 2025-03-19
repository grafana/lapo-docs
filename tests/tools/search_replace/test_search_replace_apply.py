from src.tools.search_replace.search_replace_apply import (
    split_search_replace_into_file_blocks,
    split_block_into_search_replace_pairs,
    apply_search_replace_pairs_to_content,
    apply_search_replace_to_content,
)


def test_split_patch_into_file_blocks_single_block():
    # Test with a single file block
    single_block = """docusaurus/docs/file1.md
```markdown
<<<<<<< SEARCH
old content
=======
new content
>>>>>>> REPLACE
```"""
    result = split_search_replace_into_file_blocks(single_block)
    assert len(result) == 1
    assert result[0][0] == "docusaurus/docs/file1.md"
    assert "old content" in result[0][1]
    assert "new content" in result[0][1]


def test_split_patch_into_file_blocks_multiple_blocks():
    # Test with multiple file blocks
    multi_block = """docusaurus/docs/file1.md
```markdown
<<<<<<< SEARCH
old content for file1
=======
new content for file1
>>>>>>> REPLACE
```

docusaurus/docs/file2.md
```markdown
<<<<<<< SEARCH
old content for file2
=======
new content for file2
>>>>>>> REPLACE
```"""
    result = split_search_replace_into_file_blocks(multi_block)
    assert len(result) == 2
    assert result[0][0] == "docusaurus/docs/file1.md"
    assert result[1][0] == "docusaurus/docs/file2.md"
    assert "old content for file1" in result[0][1]
    assert "old content for file2" in result[1][1]


def test_split_patch_into_file_blocks_empty_patch():
    # Test with empty patch
    empty_patch = ""
    result = split_search_replace_into_file_blocks(empty_patch)
    assert len(result) == 0


def test_split_block_into_search_replace_pairs_single_pair():
    # Test with a single search/replace pair
    single_pair = """docusaurus/docs/file1.md
```markdown
<<<<<<< SEARCH
old content
=======
new content
>>>>>>> REPLACE
```"""
    pairs = split_block_into_search_replace_pairs(single_pair)
    assert len(pairs) == 1
    assert pairs[0][0] == "old content"
    assert pairs[0][1] == "new content"


def test_split_block_into_search_replace_pairs_multiple_pairs():
    # Test with multiple search/replace pairs
    multi_pair = """docusaurus/docs/file1.md
```markdown
<<<<<<< SEARCH
old content 1
=======
new content 1
>>>>>>> REPLACE

docusaurus/docs/file1.md
<<<<<<< SEARCH
old content 2
=======
new content 2
>>>>>>> REPLACE
```"""
    pairs = split_block_into_search_replace_pairs(multi_pair)
    assert len(pairs) == 2
    assert pairs[0][0] == "old content 1"
    assert pairs[0][1] == "new content 1"
    assert pairs[1][0] == "old content 2"
    assert pairs[1][1] == "new content 2"


def test_split_block_into_search_replace_pairs_no_pairs():
    # Test with no search/replace pairs
    no_pairs = "docusaurus/docs/file1.md\n```markdown\nJust some content\n```"
    pairs = split_block_into_search_replace_pairs(no_pairs)
    assert len(pairs) == 0


def test_split_block_into_search_replace_pairs_with_markdown_code_blocks():
    # Test with markdown code blocks inside search/replace sections
    markdown_code_blocks = """docusaurus/docs/file1.md
```markdown
<<<<<<< SEARCH
```python
def hello():
    print("Hello")
```
=======
```python
def hello_world():
    print("Hello World")
```
>>>>>>> REPLACE
```"""
    pairs = split_block_into_search_replace_pairs(markdown_code_blocks)
    assert len(pairs) == 1
    assert "def hello():" in pairs[0][0]
    assert "def hello_world():" in pairs[0][1]


def test_apply_search_replace_pairs_to_content_simple_replacement():
    # Test simple replacement
    content = "This is old content in a file."
    pairs = [("old content", "new content")]
    result = apply_search_replace_pairs_to_content(content, pairs)
    assert result == "This is new content in a file."


def test_apply_search_replace_pairs_to_content_multiple_replacements():
    # Test multiple replacements
    content = "First old text. Second old text."
    pairs = [("First old", "First new"), ("Second old", "Second new")]
    result = apply_search_replace_pairs_to_content(content, pairs)
    assert result == "First new text. Second new text."


def test_apply_search_replace_pairs_to_content_no_matches():
    # Test no matches
    content = "This content has no matches."
    pairs = [("nonexistent", "replacement")]
    result = apply_search_replace_pairs_to_content(content, pairs)
    assert result == "This content has no matches."


def test_apply_search_replace_pairs_to_content_empty_pairs():
    # Test with empty pairs list
    content = "This content should remain unchanged."
    pairs = []
    result = apply_search_replace_pairs_to_content(content, pairs)
    assert result == "This content should remain unchanged."


def test_apply_search_replace_pairs_to_content_overlapping_replacements():
    # Test with overlapping replacements (first match should be replaced first)
    content = "This is a test string."
    pairs = [("This is a test", "That was a test"), ("test string", "sample text")]
    result = apply_search_replace_pairs_to_content(content, pairs)
    assert result == "That was a sample text."


def test_apply_search_replace_to_content_basic():
    # Test applying a patch to content
    source = "This is the original content with old text."
    patch = """docusaurus/docs/file.md
```markdown
<<<<<<< SEARCH
old text
=======
new text
>>>>>>> REPLACE
```"""
    result, success = apply_search_replace_to_content(source, patch)
    assert result == "This is the original content with new text."
    assert success is True


def test_apply_search_replace_to_content_multiple_sections():
    # Test with multiple search/replace sections
    source = "First section with old text. Second section with outdated content."
    patch = """docusaurus/docs/file.md
```markdown
<<<<<<< SEARCH
old text
=======
new text
>>>>>>> REPLACE

docusaurus/docs/file.md
<<<<<<< SEARCH
outdated content
=======
updated content
>>>>>>> REPLACE
```"""
    result, success = apply_search_replace_to_content(source, patch)
    assert result == "First section with new text. Second section with updated content."
    assert success is True


def test_apply_search_replace_to_content_empty_source():
    # Test with empty source
    source = ""
    patch = """docusaurus/docs/file.md
```markdown
<<<<<<< SEARCH
old text
=======
new text
>>>>>>> REPLACE
```"""
    result, success = apply_search_replace_to_content(source, patch)
    assert result == ""
    assert success is True


def test_apply_search_replace_to_content_empty_patch():
    # Test with empty patch
    source = "Original content"
    patch = ""
    result, success = apply_search_replace_to_content(source, patch)
    assert result == "Original content"
    assert success is True


def test_apply_search_replace_to_content_with_matching_filename():
    # Test with matching filename
    source = "This is the original content with old text."
    patch = """docusaurus/docs/file.md
```markdown
<<<<<<< SEARCH
old text
=======
new text
>>>>>>> REPLACE
```"""
    result, success = apply_search_replace_to_content(source, patch, target_filename="docusaurus/docs/file.md")
    assert result == "This is the original content with new text."
    assert success is True


def test_apply_search_replace_to_content_with_non_matching_filename():
    # Test with non-matching filename
    source = "This is the original content with old text."
    patch = """docusaurus/docs/file.md
```markdown
<<<<<<< SEARCH
old text
=======
new text
>>>>>>> REPLACE
```"""
    result, success = apply_search_replace_to_content(
        source, patch, target_filename="docusaurus/docs/different_file.md"
    )
    assert result == "This is the original content with old text."  # Content unchanged
    assert success is False


def test_apply_search_replace_to_content_with_empty_patch_and_filename():
    # Test with empty patch
    source = "Original content"
    patch = ""
    result, success = apply_search_replace_to_content(source, patch, target_filename="docusaurus/docs/file.md")
    assert result == "Original content"
    assert success is True  # Empty patches return True regardless of target_filename
