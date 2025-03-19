#!/bin/bash

# Usage: ./uvrun.sh path/to/file.py

if [ -z "$1" ]; then
  echo "Error: Please provide a path to a Python file"
  echo "Usage: ./uvrun.sh path/to/file.py"
  exit 1
fi

FILE_PATH="$1"

# Check if this is a test file
if [[ "$FILE_PATH" == *"test_"* ]] || [[ "$FILE_PATH" == "tests/"* ]]; then
  echo "Running test file with pytest: $FILE_PATH"
  uv run -m pytest "$FILE_PATH" "${@:2}"
else
  # For non-test files, add the project root to PYTHONPATH
  echo "Running Python file: $FILE_PATH"
  PYTHONPATH="$PYTHONPATH:$(pwd)" uv run "$FILE_PATH" "${@:2}"
fi
