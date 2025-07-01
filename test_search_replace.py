#!/usr/bin/env python3
"""
Comprehensive tests for SEARCH/REPLACE parsing and application
"""

import pytest
import tempfile
import os
from api_server import parse_and_apply_search_replace, simple_search_replace_parser

class TestSearchReplaceEdgeCases:
    """Test edge cases for SEARCH/REPLACE parsing"""
    
    def test_whitespace_preservation(self):
        """Test that whitespace is preserved correctly"""
        response = """
<<<<<<< SEARCH
    def function():
        return "old"
=======
    def function():
        return "new"
>>>>>>> REPLACE
"""
        
        result = simple_search_replace_parser(response)
        assert len(result) == 1
        search, replace = result[0]
        assert search.startswith('    def function():')
        assert replace.startswith('    def function():')
        assert 'return "new"' in replace
    
    def test_multiline_with_empty_lines(self):
        """Test SEARCH/REPLACE with empty lines"""
        response = """
<<<<<<< SEARCH
def function():

    return "old"

=======
def function():

    return "new"

>>>>>>> REPLACE
"""
        
        result = simple_search_replace_parser(response)
        assert len(result) == 1
        search, replace = result[0]
        assert '\n\n' in search  # Empty lines preserved
        assert '\n\n' in replace
    
    def test_special_characters(self):
        """Test SEARCH/REPLACE with special characters"""
        response = """
<<<<<<< SEARCH
print("Hello $world & <universe>")
=======
print("Hello $world & <universe>!")
>>>>>>> REPLACE
"""
        
        result = simple_search_replace_parser(response)
        assert len(result) == 1
        search, replace = result[0]
        assert '$world & <universe>' in search
        assert '$world & <universe>!' in replace
    
    def test_malformed_blocks(self):
        """Test handling of malformed SEARCH/REPLACE blocks"""
        response = """
<<<<<<< SEARCH
incomplete block without replace
=======
"""
        
        result = simple_search_replace_parser(response)
        assert len(result) == 0  # Should handle gracefully
    
    def test_nested_search_patterns(self):
        """Test handling when search text contains similar markers"""
        response = """
<<<<<<< SEARCH
# This comment contains <<<<<<< and >>>>>>>
def func():
    pass
=======
# This comment contains <<<<<<< and >>>>>>>
def func():
    return True
>>>>>>> REPLACE
"""
        
        result = simple_search_replace_parser(response)
        assert len(result) == 1
        search, replace = result[0]
        assert 'comment contains' in search
        assert 'return True' in replace


class TestFileApplication:
    """Test applying SEARCH/REPLACE to actual files"""
    
    def setup_method(self):
        """Create test files"""
        # Python file
        self.python_content = '''def hello():
    print("Hello")
    return "world"

def goodbye():
    print("Goodbye")
    return "farewell"

class TestClass:
    def method(self):
        return "old method"
'''
        
        # HTML file
        self.html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <style>
        .header {
            color: blue;
        }
    </style>
</head>
<body>
    <h1>Original Title</h1>
    <p>Some content here</p>
</body>
</html>'''
        
        # CSS file
        self.css_content = '''.container {
    width: 100%;
    padding: 20px;
}

.header h1 {
    color: #2563eb;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 16px;
}

.footer {
    background: gray;
}'''
    
    def test_python_function_replacement(self):
        """Test replacing Python function content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.python_content)
            temp_file = f.name
        
        try:
            response = '''
<<<<<<< SEARCH
def hello():
    print("Hello")
    return "world"
=======
def hello():
    print("Hello, Universe!")
    return "cosmos"
>>>>>>> REPLACE
'''
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            assert 'Hello, Universe!' in result
            assert 'return "cosmos"' in result
            assert 'def goodbye():' in result  # Other functions preserved
            assert 'class TestClass:' in result  # Other code preserved
            
        finally:
            os.unlink(temp_file)
    
    def test_html_element_replacement(self):
        """Test replacing HTML elements"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.html_content)
            temp_file = f.name
        
        try:
            response = '''
<<<<<<< SEARCH
    <h1>Original Title</h1>
=======
    <h1>Updated Title</h1>
>>>>>>> REPLACE
'''
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            assert '<h1>Updated Title</h1>' in result
            assert '<title>Test Page</title>' in result  # Other content preserved
            assert '<p>Some content here</p>' in result
            
        finally:
            os.unlink(temp_file)
    
    def test_css_style_replacement(self):
        """Test replacing CSS styles"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as f:
            f.write(self.css_content)
            temp_file = f.name
        
        try:
            response = '''
<<<<<<< SEARCH
.header h1 {
    color: #2563eb;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 16px;
}
=======
.header h1 {
    color: #dc2626;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 16px;
}
>>>>>>> REPLACE
'''
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            assert 'color: #dc2626;' in result
            assert '.container {' in result  # Other styles preserved
            assert '.footer {' in result
            
        finally:
            os.unlink(temp_file)
    
    def test_multiple_replacements_same_file(self):
        """Test multiple SEARCH/REPLACE blocks in same file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.python_content)
            temp_file = f.name
        
        try:
            response = '''
<<<<<<< SEARCH
def hello():
    print("Hello")
    return "world"
=======
def hello():
    print("Hi there!")
    return "planet"
>>>>>>> REPLACE

<<<<<<< SEARCH
    def method(self):
        return "old method"
=======
    def method(self):
        return "new method"
>>>>>>> REPLACE
'''
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            assert 'print("Hi there!")' in result
            assert 'return "planet"' in result
            assert 'return "new method"' in result
            assert 'def goodbye():' in result  # Untouched function preserved
            
        finally:
            os.unlink(temp_file)
    
    def test_replacement_not_found(self):
        """Test handling when search text is not found"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.python_content)
            temp_file = f.name
        
        try:
            response = '''
<<<<<<< SEARCH
def nonexistent_function():
    pass
=======
def new_function():
    return True
>>>>>>> REPLACE
'''
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            # Should return original content when search text not found
            assert result == self.python_content
            
        finally:
            os.unlink(temp_file)
    
    def test_partial_match_handling(self):
        """Test handling of partial matches"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.python_content)
            temp_file = f.name
        
        try:
            # Try to match with different indentation
            response = '''
<<<<<<< SEARCH
def hello():
print("Hello")
return "world"
=======
def hello():
    print("Modified Hello")
    return "modified world"
>>>>>>> REPLACE
'''
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            # Should not modify when indentation doesn't match exactly
            assert 'Modified Hello' not in result
            assert self.python_content == result
            
        finally:
            os.unlink(temp_file)


class TestComplexScenarios:
    """Test complex real-world scenarios"""
    
    def test_javascript_function_modification(self):
        """Test modifying JavaScript function"""
        js_content = '''
function calculateTotal(items) {
    let total = 0;
    for (let item of items) {
        total += item.price;
    }
    return total;
}

function displayResults(total) {
    console.log(`Total: $${total}`);
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_content)
            temp_file = f.name
        
        try:
            response = '''
<<<<<<< SEARCH
function calculateTotal(items) {
    let total = 0;
    for (let item of items) {
        total += item.price;
    }
    return total;
}
=======
function calculateTotal(items) {
    let total = 0;
    for (let item of items) {
        total += item.price * (1 + item.tax || 0);
    }
    return Math.round(total * 100) / 100;
}
>>>>>>> REPLACE
'''
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            assert 'item.tax ||' in result
            assert 'Math.round(total * 100) / 100' in result
            assert 'displayResults' in result  # Other functions preserved
            
        finally:
            os.unlink(temp_file)
    
    def test_json_modification(self):
        """Test modifying JSON-like content"""
        json_content = '''{
    "name": "Test App",
    "version": "1.0.0",
    "dependencies": {
        "react": "^18.0.0",
        "axios": "^0.24.0"
    },
    "scripts": {
        "start": "npm start",
        "build": "npm run build"
    }
}'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            temp_file = f.name
        
        try:
            response = '''
<<<<<<< SEARCH
    "dependencies": {
        "react": "^18.0.0",
        "axios": "^0.24.0"
    },
=======
    "dependencies": {
        "react": "^18.0.0",
        "axios": "^0.24.0",
        "lodash": "^4.17.21"
    },
>>>>>>> REPLACE
'''
            
            result = parse_and_apply_search_replace(response, temp_file)
            
            assert '"lodash": "^4.17.21"' in result
            assert '"name": "Test App"' in result  # Other content preserved
            assert '"scripts":' in result
            
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 