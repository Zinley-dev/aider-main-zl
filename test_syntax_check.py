#!/usr/bin/env python
"""Test to check if main.py has correct syntax and imports"""
import ast
import sys

def check_syntax_and_scope():
    """Check that main.py has valid syntax and proper scope handling"""
    
    try:
        # Read and parse the main.py file
        with open("aider/main.py", "r") as f:
            source = f.read()
        
        # Parse the AST to check for syntax errors
        tree = ast.parse(source)
        
        # Look for the main function
        main_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                main_func = node
                break
        
        if not main_func:
            print("✗ ERROR: Could not find main function")
            return False
        
        # Check for nested get_io function
        get_io_func = None
        for node in ast.walk(main_func):
            if isinstance(node, ast.FunctionDef) and node.name == "get_io":
                get_io_func = node
                break
        
        if not get_io_func:
            print("✗ ERROR: Could not find get_io function")
            return False
        
        # Look for InputOutput usage in get_io
        uses_inputoutput = False
        for node in ast.walk(get_io_func):
            if isinstance(node, ast.Name) and node.id == "InputOutput":
                uses_inputoutput = True
                break
        
        if not uses_inputoutput:
            print("✗ ERROR: get_io doesn't use InputOutput")
            return False
        
        # Check that InputOutput is imported at module level
        has_module_import = False
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                if node.module == "aider.io":
                    for alias in node.names:
                        if alias.name == "InputOutput":
                            has_module_import = True
                            break
        
        if not has_module_import:
            print("✗ ERROR: InputOutput not imported at module level")
            return False
        
        print("✓ Syntax is valid")
        print("✓ main function found")
        print("✓ get_io function found")
        print("✓ InputOutput is imported at module level")
        print("✓ get_io uses InputOutput")
        
        # Check for local imports of InputOutput in the directory handling code
        source_lines = source.split('\n')
        for i, line in enumerate(source_lines):
            if "from aider.io import InputOutput" in line and i > 50:  # After module imports
                print(f"✗ WARNING: Found local import of InputOutput at line {i+1}")
                print(f"   This could cause scope issues!")
                return False
        
        print("✓ No local imports of InputOutput found")
        
        return True
        
    except SyntaxError as e:
        print(f"✗ SYNTAX ERROR: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Checking main.py syntax and InputOutput scope...")
    success = check_syntax_and_scope()
    
    if success:
        print("\n✓ All checks passed! InputOutput scope should work correctly.")
    else:
        print("\n✗ Checks failed!")
    
    sys.exit(0 if success else 1) 