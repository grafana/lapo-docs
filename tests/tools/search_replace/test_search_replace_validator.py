import pytest
from pytest import raises
from src.tools.search_replace.search_replace_validator import validate_patch


def test_valid_patch_1():
    patch = """docusaurus/docs/how-to-guides/data-source-plugins/fetch-data-from-frontend.md
```typescript
<<<<<<< SEARCH
export class DataSource extends DataSourceApi {
  baseUrl: string;
  constructor(instanceSettings: DataSourceInstanceSettings) {
    super(instanceSettings);
    // notice we are storing the URL from the instanceSettings
    this.baseUrl = instanceSettings.url!;
=======
export class DataSource extends DataSourceApi {
  proxyUrl: string;
  constructor(instanceSettings: DataSourceInstanceSettings) {
    super(instanceSettings);
    // notice we are storing the URL from the instanceSettings
    this.proxyUrl = instanceSettings.url!;
>>>>>>> REPLACE
```
"""

    result = validate_patch(patch)
    assert result == "OK"


def test_valid_patch_2():
    valid_patch = """docs/example.md
```markdown
<<<<<<< SEARCH
old content
=======
new content
>>>>>>> REPLACE
```"""
    result = validate_patch(valid_patch)
    assert result == "OK"


def test_multiple_valid_blocks():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/example.md
```markdown
<<<<<<< SEARCH
content2
=======
new2
>>>>>>> REPLACE

docs/example3.md
```markdown
<<<<<<< SEARCH
content2
=======
new2
>>>>>>> REPLACE

docs/example5.md
```markdown
<<<<<<< SEARCH
content2
=======
new2
>>>>>>> REPLACE
```"""
    result = validate_patch(patch)
    assert result == "OK"


def test_multiple_invalid_blocks():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

```markdown
<<<<<<< SEARCH
content2
=======
new2
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing file path at the start of patch" in str(excinfo.value)


def test_missing_file_path():
    patch = """```markdown
<<<<<<< SEARCH
content
=======
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing file path at the start of patch" in str(excinfo.value)


def test_missing_code_fence():
    patch = """docs/test.md
<<<<<<< SEARCH
content
=======
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing begin code fence markers" in str(excinfo.value)


def test_missing_search_marker():
    patch = """docs/test.md
```markdown
content
=======
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing '<<<<<<< SEARCH' marker" in str(excinfo.value)


def test_missing_divider():
    patch = """docs/test.md
```markdown
<<<<<<< SEARCH
content
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing '=======' divider" in str(excinfo.value)


def test_missing_replace_marker():
    patch = """docs/test.md
```markdown
<<<<<<< SEARCH
content
=======
new
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing '>>>>>>> REPLACE' marker" in str(excinfo.value)


def test_missing_closing_fence():
    patch = """docs/test.md
```markdown
<<<<<<< SEARCH
content
=======
new
>>>>>>> REPLACE
"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing closing code fence" in str(excinfo.value)


def test_empty_search_section():
    patch = """docs/test.md
```markdown
<<<<<<< SEARCH
=======
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Search section is empty" in str(excinfo.value)


def test_empty_replace_section():
    patch = """docs/test.md
```markdown
<<<<<<< SEARCH
content
=======

>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Replace section is empty" in str(excinfo.value)


def test_empty_patch():
    patch = ""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Patch is empty" in str(excinfo.value)


def test_missing_divider_in_correct_position():
    patch = """docs/test.md
```markdown
=======
content
<<<<<<< SEARCH
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing '=======' divider" in str(excinfo.value)


def test_multiblock_missing_file_path():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

```markdown
<<<<<<< SEARCH
content2
=======
new2
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing file path at the start of patch" in str(excinfo.value)


def test_multiblock_missing_code_fence():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/test.md
<<<<<<< SEARCH
content
=======
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing begin code fence markers" in str(excinfo.value)


def test_multiblock_missing_search_marker():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/test.md
```markdown
content
=======
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing '<<<<<<< SEARCH' marker" in str(excinfo.value)


def test_multiblock_missing_divider():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/test.md
```markdown
<<<<<<< SEARCH
content
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing '=======' divider" in str(excinfo.value)


def test_multiblock_missing_replace_marker():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/test.md
```markdown
<<<<<<< SEARCH
content
=======
new
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing '>>>>>>> REPLACE' marker" in str(excinfo.value)


def test_multiblock_missing_closing_fence():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/test.md
```markdown
<<<<<<< SEARCH
content
=======
new
>>>>>>> REPLACE
"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing closing code fence" in str(excinfo.value)


def test_multiblock_empty_search_section():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/test.md
```markdown
<<<<<<< SEARCH
=======
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Search section is empty" in str(excinfo.value)


def test_multiblock_empty_replace_section():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/test.md
```markdown
<<<<<<< SEARCH
content
=======

>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Replace section is empty" in str(excinfo.value)


def test_multiblock_missing_divider_in_wrong_position():
    patch = """docs/example.md
```markdown
<<<<<<< SEARCH
content1
=======
new1
>>>>>>> REPLACE
```

docs/test.md
```markdown
=======
content
<<<<<<< SEARCH
new
>>>>>>> REPLACE
```"""
    with raises(ValueError) as excinfo:
        validate_patch(patch)
    assert "Missing '=======' divider" in str(excinfo.value)
