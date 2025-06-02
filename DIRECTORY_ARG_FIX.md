# Fix for --directory Argument Recognition Issue

## Problem Description

The `--directory` argument in aider was experiencing intermittent recognition failures, where sometimes the argument parser would report:
```
aider: error: unrecognized arguments: --directory
```

This issue was inconsistent - it would work sometimes but fail other times, and reinstalling aider would temporarily fix the problem.

## Root Cause

The issue was caused by the way aider handles argument parsing in multiple stages:

1. The code creates multiple parser instances with `get_parser()`
2. It uses `parse_known_args()` with stderr suppression to do initial parsing
3. The configargparse library can get into an inconsistent state when parsers are created and parsed multiple times with stderr suppression
4. This causes the parser to "forget" about the `--directory` argument definition

## Solution

The fix involves two key changes in `aider/main.py`:

### 1. Filter --directory from Initial Parsing

Since `--directory` is handled manually early in the `main()` function (to change directories before loading config files), we filter it out from the initial parsing attempts:

```python
# Parse argv without --directory to avoid parser confusion
argv_without_directory = []
skip_next = False
for i, arg in enumerate(argv):
    if skip_next:
        skip_next = False
        continue
    if arg == "--directory":
        skip_next = True
        continue
    elif arg.startswith("--directory="):
        continue
    argv_without_directory.append(arg)

# Use filtered argv for initial parsing
args, unknown = parser.parse_known_args(argv_without_directory)
```

### 2. Manually Set the Directory Attribute

After the final `parse_args()` call (which uses the original argv), we ensure the directory attribute is set:

```python
# Manually set the directory attribute if it was provided
if directory_arg:
    args.directory = directory_arg
```

## Why This Works

1. The `--directory` argument is processed manually at the beginning of `main()` to change directories before any config file loading
2. By filtering it out during the intermediate parsing stages, we avoid parser state confusion
3. The final `parse_args()` call includes the full argv with `--directory`, ensuring proper validation
4. Setting the attribute manually provides a fallback to ensure it's always available

## Testing

The fix includes:
- A standalone test script (`test_directory_fix.py`) that runs aider multiple times to catch intermittent issues
- Unit tests (`tests/test_directory_argument.py`) for the pytest suite
- Tests for both `--directory path` and `--directory=path` syntax
- Error handling tests for non-existent directories and files

## Impact

This fix ensures that the `--directory` argument is consistently recognized across all invocations of aider, eliminating the need for reinstallation when the issue occurs. 