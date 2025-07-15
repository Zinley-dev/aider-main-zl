"""
Custom prompt components for dynamic system reminder generation
"""

from typing import List, Dict, Optional

class PromptComponents:
    """
    Centralized prompt components for dynamic system reminder generation
    """
    
    # Base SEARCH/REPLACE rules that are always included
    BASE_RULES = """# *SEARCH/REPLACE block* Rules:

Every *SEARCH/REPLACE block* must use this format:
1. The *FULL* file path alone on a line, verbatim. No bold asterisks, no quotes around it, no escaping of characters, etc.
2. The opening fence and code language, eg: ```python
3. The start of search block: <<<<<<< SEARCH
4. A contiguous chunk of lines to search for in the existing source code
5. The dividing line: =======
6. The lines to replace into the source code
7. The end of the replace block: >>>>>>> REPLACE
8. The closing fence: ```

Use the *FULL* file path, as shown to you by the user.
Every *SEARCH* section must *EXACTLY MATCH* the existing file content, character for character, including all comments, docstrings, etc.
If the file contains code or other data wrapped/escaped in json/xml/quotes or other containers, you need to propose edits to the literal contents of the file, including the container markup.

*SEARCH/REPLACE* blocks will *only* replace the first match occurrence.
Including multiple unique *SEARCH/REPLACE* blocks if needed.
Include enough lines in each SEARCH section to uniquely match each set of lines that need to change.

Keep *SEARCH/REPLACE* blocks concise.
Break large *SEARCH/REPLACE* blocks into a series of smaller blocks that each change a small portion of the file.
Include just the changing lines, and a few surrounding lines if needed for uniqueness.
Do not include long runs of unchanging lines in *SEARCH/REPLACE* blocks.

Only create *SEARCH/REPLACE* blocks for files that the user has added to the chat!

To move code within a file, use 2 *SEARCH/REPLACE* blocks: 1 to delete it from its current location, 1 to insert it in the new location.

Pay attention to which filenames the user wants you to edit, especially if they are asking you to create a new file.

If you want to put code in a new file, use a *SEARCH/REPLACE block* with:
- A new file path, including dir name if needed
- An empty `SEARCH` section
- The new file's contents in the `REPLACE` section"""

    # Critical behavioral instructions that are always included
    CRITICAL_INSTRUCTIONS = """
--- SPREADSHEET FORMAT RULES ---
**COMPACT SPREADSHEET JSON FORMAT FOR AI AGENTS**

You are working with a compact JSON format for spreadsheets that minimizes token usage while preserving all functionality. This format is optimized for AI processing.

**COMPACT JSON STRUCTURE:**

{
  "sheets": [
    {
      "n": "Sheet1",                // sheet name (abbreviated from "name")
      "c": {                        // cells (abbreviated from "cells")
        "A1": "Header 1",           // simple value form (string/number/boolean)
        "B1": { "v": "Header 2" },  // object form with value
        "A2": { "v": 10 },          // number value
        "B2": { "v": 20 },
        "C2": {                     // formula cell with style
          "f": "=A2+B2",            // formula (abbreviated from "formula")
          "s": {                    // style (abbreviated from "style")
            "b": "bold",            // bold (abbreviated from "fontWeight")
            "bg": "#e8f5e8",        // background color
            "tc": "#2e7d32",        // text color
            "ta": "r"               // text align: "l" (left), "ctr" (center), "r" (right)
          }
        }
      },
      "cols": [100, 120, 150],      // column widths (only if non-default)
      "rows": [24, 30, 24]          // row heights (only if non-default)
    }
  ],
  "active": 0                       // active sheet index (not id)
}

**KEY DIFFERENCES FROM FULL FORMAT:**

1. **ABBREVIATED PROPERTY NAMES:**
   - "n" instead of "name"
   - "c" instead of "cells"
   - "v" instead of "value.raw"
   - "f" instead of "formula"
   - "s" instead of "style"
   - "b" instead of "fontWeight"
   - "bg" instead of "backgroundColor"
   - "tc" instead of "textColor"
   - "ta" instead of "textAlign" ("l", "ctr", "r")
   - "fz" instead of "fontSize"
   - "bd" instead of "border"
   - "ff" instead of "fontFamily"
   - "td" instead of "textDecoration"

2. **SIMPLIFIED CELL REPRESENTATION:**
   - Cell ID is the key (e.g., "A1", "B2") - MUST use Excel notation only
   - NEVER use "columns", "rows", or other non-cell identifiers as keys
   - Only valid cell IDs: A1, B2, C3, AA1, AB2, etc.
   - No redundant "id", "row", "col" properties
   - Direct primitive values allowed ("A1": "Header 1")
   - Object form for formulas/styles ("A1": { "f": "=SUM(B1:B10)" })

3. **OMITTED DEFAULTS:**
   - No "computed" values (calculated at runtime)
   - Default column width (100px) and row height (24px) not listed
   - Empty arrays/objects not included
   - Empty cells not included at all

4. **STYLE SHORTHAND CODES:**
   - "b": 1 or "bold" for bold text
   - "ta": "l" (left), "ctr" (center), "r" (right)
   - All other style properties use abbreviated keys

**COMPREHENSIVE FORMULA SUPPORT:**

All Excel/Google Sheets formulas are supported with the same syntax:
- Always start with "=" sign: "=A1+B1"
- Arithmetic: "=A1+B1", "=A1*B1", "=A1/B1", "=A1-B1", "=A1^2"
- Functions: SUM, AVERAGE, COUNT, MAX, MIN, IF, CONCATENATE, VLOOKUP, INDEX, MATCH
- Range notation: A1:A10, B1:C5
- Logical: AND, OR, NOT
- Text: CONCATENATE, LEFT, RIGHT, MID, LEN, UPPER, LOWER, TRIM
- Date/Time: TODAY, NOW, DATE, TIME, YEAR, MONTH, DAY
- Lookup: VLOOKUP, HLOOKUP, INDEX, MATCH, OFFSET
- Math: ROUND, CEILING, FLOOR, ABS, MOD, POWER, SQRT
- Error handling: IFERROR, ISERROR, ISBLANK, ISNUMBER, ISTEXT

**FORMULA EXAMPLES:**
"C2": { "f": "=A2+B2" }                                    // Simple arithmetic
"D2": { "f": "=SUM(A1:A10)" }                             // Sum range
"E2": { "f": "=AVERAGE(B1:B5)" }                          // Average
"F2": { "f": "=IF(A2>10,\"High\",\"Low\")" }             // Conditional
"G2": { "f": "=CONCATENATE(A2,\" \",B2)" }               // Text joining
"H2": { "f": "=VLOOKUP(A2,D1:F10,2,FALSE)" }            // Lookup
"I2": { "f": "=IFERROR(A2/B2,\"N/A\")" }                 // Error handling
"J2": { "f": "=ROUND(A2*1.08,2)" }                       // Math function
"K2": { "f": "=COUNT(A1:A10)" }                          // Count non-empty
"L2": { "f": "=MAX(A1:A10)" }                            // Maximum value
"M2": { "f": "=MIN(A1:A10)" }                            // Minimum value
"N2": { "f": "=TODAY()" }                                // Current date
"O2": { "f": "=A2&\" \"&B2" }                           // Text concatenation operator

**COMPREHENSIVE FUNCTION REFERENCE GUIDE:**

**MATH & STATISTICAL**
1. SUM(number1, [number2,…]) – Adds all the numbers. Example: =SUM(A1:A10)
2. AVERAGE(number1, [number2,…]) – Returns arithmetic mean. Example: =AVERAGE(B1:B5)
3. COUNT(value1, [value2,…]) – Counts numeric cells. Example: =COUNT(A1:C10)
4. COUNTA(value1, [value2,…]) – Counts non-empty cells. Example: =COUNTA(A1:C10)
5. COUNTIF(range, criteria) – Counts cells meeting a condition. Example: =COUNTIF(A1:A10,">0")
6. COUNTIFS(range1, criteria1, [range2, criteria2,…]) – Multiple criteria. Example: =COUNTIFS(A1:A10,">0",B1:B10,"<5")
7. MAX(number1,[number2,…]) – Largest value. Example: =MAX(B2:B20)
8. MIN(number1,[number2,…]) – Smallest value. Example: =MIN(B2:B20)
9. MEDIAN(number1,[number2,…]) – Middle value. Example: =MEDIAN(C1:C15)
10. MODE(number1,[number2,…]) – Most frequent value. Example: =MODE(C1:C15)
11. STDEV(range) – Sample standard deviation. Example: =STDEV(D1:D30)
12. STDEV.P(range) – Population standard deviation. Example: =STDEV.P(D1:D30)
13. VAR(range) – Sample variance. Example: =VAR(E1:E30)
14. VAR.P(range) – Population variance. Example: =VAR.P(E1:E30)
15. ROUND(number, digits) – Rounds to digits. Example: =ROUND(PI(),2)
16. ROUNDUP(number,digits) – Always round up. Example: =ROUNDUP(2.3,0)
17. ROUNDDOWN(number,digits) – Always round down. Example: =ROUNDDOWN(2.9,0)
18. CEILING(number, significance) – Round up to nearest significance. Example: =CEILING(5.2,1)
19. FLOOR(number, significance) – Round down. Example: =FLOOR(5.9,1)
20. ABS(number) – Absolute value. Example: =ABS(-7)
21. SQRT(number) – Square root. Example: =SQRT(25)
22. POWER(base, exponent) – Exponentiation. Example: =POWER(2,8)
23. EXP(power) – e^power. Example: =EXP(1)
24. LN(number) – Natural logarithm. Example: =LN(10)
25. LOG(number, [base]) – Logarithm. Example: =LOG(100,10)
26. LOG10(number) – Base-10 log. Example: =LOG10(1000)
27. Trigonometry: SIN(angle), COS(angle), TAN(angle) where angle in radians. Example: =SIN(PI()/2)
28. Inverse trig: ASIN(value), ACOS(value), ATAN(value)
29. PI() – Returns π ≈ 3.14159
30. Random: RAND() (0–1), RANDBETWEEN(min,max)
31. MOD(dividend, divisor) – Remainder. Example: =MOD(10,3)
32. GCD(number1,number2) – Greatest common divisor. Example: =GCD(54,24)
33. LCM(number1,number2) – Least common multiple. Example: =LCM(6,8)

**TEXT**
1. CONCATENATE(text1,[text2,…]) / CONCAT() – Joins strings. Example: =CONCAT("Hello"," ",B1)
2. LEFT(text, [num_chars]) – Returns leftmost characters. Example: =LEFT(A1,3)
3. RIGHT(text, [num_chars]) – Returns rightmost characters. Example: =RIGHT(A1,2)
4. MID(text, start, length) – Extracts substring. Example: =MID(A1,2,3)
5. LEN(text) – String length. Example: =LEN(A1)
6. UPPER(text), LOWER(text), PROPER(text) – Change case.
7. TRIM(text) – Removes extra spaces. Example: =TRIM(A1)
8. FIND(search, text, [start]) – Case-sensitive position. Example: =FIND("@",A1)
9. SEARCH(search, text, [start]) – Case-insensitive position. Example: =SEARCH("cat",A1)
10. REPLACE(text, start, length, new_text) – Replace part. Example: =REPLACE(A1,1,3,"XYZ")
11. SUBSTITUTE(text, old, new, [instance]) – Replace occurrences. Example: =SUBSTITUTE(A1,"-","/")
12. TEXT(number, format) – Formats number. Example: =TEXT(0.25,"0.0%")
13. VALUE(text) – Converts text to number. Example: =VALUE("123")

**DATE / TIME** (serial date system)
1. NOW() – Returns current date & time.
2. TODAY() – Returns current date.
3. DATE(year, month, day) – Creates date serial. Example: =DATE(2025,1,31)
4. TIME(hour, minute, second) – Creates time serial. Example: =TIME(13,30,0)
5. YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, WEEKDAY – Extract components. Example: =YEAR(A1)
6. DATEDIF(start_date,end_date,unit) – Date difference. Example: =DATEDIF(A1,B1,"D")

**LOGICAL**
1. IF(condition, true_value, [false_value]) – Conditional.
2. IFS(condition1,value1,condition2,value2,…) – Multiple conditions.
3. AND(logical1,[logical2,…]), OR(...), NOT(logical) – Logical operators.
4. Constants TRUE and FALSE can be used directly.

**LOOKUP & REFERENCE**
1. VLOOKUP(search_key, table_range, index, [is_sorted]) – Vertical lookup.
2. HLOOKUP(search_key, table_range, index, [is_sorted]) – Horizontal lookup.
3. INDEX(range, row, [column]) – Returns cell value by position.
4. MATCH(search_key, range, [match_type]) – Finds position of value.
5. CHOOSE(index, option1, option2, …) – Returns nth argument.
6. LOOKUP(search_key, search_range, [result_range]) – Legacy lookup.

**INFORMATION**
Functions: ISNUMBER(value), ISTEXT(value), ISBLANK(value), ISERROR(value), ISNA(value), TYPE(value)

**FINANCIAL**
PMT(rate, periods, present_value, [future_value],[type]); PV(rate, periods, payment, [future_value],[type]); FV(rate, periods, payment, present_value, [type]); RATE(periods, payment, present_value, [future_value],[type],[guess]); NPV(rate, value1, [value2,…]); IRR(values, [guess])

**ARRAY / TRANSFORM**
TRANSPOSE(range); SORT(range, [sort_index],[sort_order]); UNIQUE(range)

**ENGINEERING / CONVERSION**
CONVERT(value, from_unit, to_unit) – Unit conversion. Example: =CONVERT(100,"km","m")
BIN2DEC(binary); DEC2BIN(decimal); HEX2DEC(hex); DEC2HEX(decimal)

These examples assume US locale (comma separators) and 1900-based date system.

**COMPLETE STYLE PROPERTIES:**

All styling options available with shorthand keys:
- "b": font weight (1/"bold" or "100"-"900")
- "bg": background color (hex: "#ffffff", "#ff0000", etc.)
- "tc": text color (hex: "#000000", "#ffffff", etc.)
- "ta": text align ("l"=left, "ctr"=center, "r"=right)
- "fz": font size (number: 10, 12, 14, 16, 18, 20, etc.)
- "bd": border ("1px solid #ccc", "2px dashed #000", etc.)
- "ff": font family ("Arial", "Times", "Courier", etc.)
- "td": text decoration ("none", "underline", "line-through")

**COLOR PALETTE REFERENCE:**

**Background Colors (use with "bg"):**
- Light colors: "#ffffff", "#f8f9fa", "#e9ecef", "#dee2e6"
- Blue tones: "#e3f2fd", "#bbdefb", "#90caf9", "#2196f3", "#1976d2"
- Green tones: "#e8f5e8", "#c8e6c9", "#a5d6a7", "#4caf50", "#388e3c"
- Red tones: "#ffebee", "#ffcdd2", "#ef9a9a", "#f44336", "#d32f2f"
- Yellow tones: "#fffde7", "#fff9c4", "#fff59d", "#ffeb3b", "#f9a825"
- Orange tones: "#fff3e0", "#ffe0b2", "#ffcc80", "#ff9800", "#f57c00"
- Purple tones: "#f3e5f5", "#e1bee7", "#ce93d8", "#9c27b0", "#7b1fa2"
- Gray tones: "#f5f5f5", "#e0e0e0", "#9e9e9e", "#424242", "#212121"

**Text Colors (use with "tc"):**
- Standard: "#000000", "#ffffff", "#212529", "#6c757d"
- Blue: "#0d6efd", "#0a58ca", "#084298"
- Green: "#198754", "#146c43", "#0f5132"
- Red: "#dc3545", "#b02a37", "#842029"
- Yellow: "#ffc107", "#e09900", "#b08000"
- Orange: "#fd7e14", "#e55a12", "#cc4807"
- Purple: "#6f42c1", "#59359a", "#432874"

**EXAMPLES:**

**Simple Text Cell:**
"A1": "Product Name"  // Direct primitive form

**Styled Header:**
"A1": {
  "v": "Product Name",
  "s": {
    "b": "bold",
    "bg": "#2196f3",
    "tc": "#ffffff",
    "ta": "ctr",
    "fz": 14
  }
}

**Formula Cell:**
"C2": {
  "f": "=A2+B2"
}

**Styled Formula Cell:**
"F6": {
  "f": "=SUM(A1:A10)",
  "s": {
    "bg": "#e8f5e8",
    "tc": "#2e7d32",
    "b": "bold",
    "ta": "r",
    "bd": "2px solid #4caf50"
  }
}

**Advanced Examples:**

**Financial Cell with Conditional Formatting:**
"D5": {
  "f": "=IF(C5>0,C5,ABS(C5))",
  "s": {
    "bg": "#e8f5e8",
    "tc": "#2e7d32",
    "b": "600",
    "ta": "r",
    "fz": 12,
    "ff": "Arial"
  }
}

**Header with Custom Border:**
"A1": {
  "v": "Q4 Report",
  "s": {
    "b": "bold",
    "bg": "#1976d2",
    "tc": "#ffffff",
    "ta": "ctr",
    "fz": 16,
    "bd": "3px solid #0d47a1",
    "ff": "Arial"
  }
}

**Percentage Cell:**
"E3": {
  "f": "=D3/C3*100",
  "s": {
    "bg": "#fff3e0",
    "tc": "#e65100",
    "ta": "r",
    "fz": 11
  }
}

**Date Cell:**
"F1": {
  "f": "=TODAY()",
  "s": {
    "bg": "#f5f5f5",
    "tc": "#424242",
    "ta": "ctr",
    "fz": 10
  }
}

**Status Indicator:**
"G2": {
  "f": "=IF(F2>90,\"Complete\",\"In Progress\")",
  "s": {
    "bg": "#4caf50",
    "tc": "#ffffff",
    "b": "bold",
    "ta": "ctr",
    "bd": "1px solid #388e3c"
  }
}

**Multiple Sheet Example:**
{
  "sheets": [
    {
      "n": "Summary",
      "c": {
        "A1": { "v": "Total Sales", "s": { "b": "bold", "bg": "#2196f3", "tc": "#ffffff" } },
        "B1": { "f": "=SUM(Data.B:B)", "s": { "ta": "r", "fz": 14 } }
      }
    },
    {
      "n": "Data",
      "c": {
        "A1": "Item",
        "B1": "Amount",
        "A2": "Product A",
        "B2": { "v": 1500 }
      },
      "cols": [120, 100]
    }
  ],
  "active": 0
}

**DATA TYPE HANDLING:**
- Text: "A1": "Hello World" or { "v": "Hello World" }
- Numbers: "A1": 123 or { "v": 123 }
- Booleans: "A1": true or { "v": true }
- Formulas: { "f": "=A1+B1" }
- Empty: Simply omit the cell from the "c" object

**COLUMN/ROW MANAGEMENT:**
- Only include "cols" array if widths differ from default (100px)
- Only include "rows" array if heights differ from default (24px)
- Arrays are indexed: cols[0] = column A, cols[1] = column B, etc.
- Example: "cols": [150, 100, 200] means A=150px, B=100px, C=200px

**RESPONSE FORMAT:**

When asked to create or modify a spreadsheet:
1. Use this compact format ONLY
2. Include only non-empty cells
3. Use direct primitive form when possible (no style/formula)
4. Use object form for cells with formulas or styles
5. Include "cols" and "rows" arrays only if they contain non-default values
6. CRITICAL: Always use proper Excel cell notation (A1, B2, etc.) - NO OTHER KEYS ALLOWED
7. NEVER include keys like "columns", "rows", "metadata" in the "c" object
8. Ensure formulas start with "=" and use correct syntax
9. Apply appropriate styling for headers, data, and calculations
10. Use hex colors for consistent appearance
11. Include multiple sheets when logical for data organization
12. VALIDATE: All keys in "c" object must match pattern [A-Z]+[0-9]+

**IMPORTANT NOTES:**
- Cell IDs MUST ONLY use Excel notation: A1, B1, C1, etc.
- CRITICAL: NEVER use "columns", "rows", or any non-cell identifier as a key in the "c" object
- Invalid keys like "columns", "rows", "metadata" will cause parser errors
- Valid cell ID pattern: [A-Z]+[1-9][0-9]* (e.g., A1, B2, AA1, AB123)
- Formulas still start with "=" sign
- All formulas and functions work exactly the same
- All style capabilities are preserved, just with shorter keys
- Complex formulas with nested functions are fully supported
- Cross-sheet references work: =Sheet2.A1 or =Data.B:B
- Array formulas and advanced Excel functions are supported
- Color accessibility: ensure good contrast between background and text
- For financial data: green for positive, red for negative values
- Headers should be bold with colored backgrounds for clarity
- Right-align numbers, left-align text, center-align headers

-- END FORMAT RULES ---
"""

    # File type specific instructions
    FILE_TYPE_INSTRUCTIONS = {
        '.py': "For Python files: Follow PEP 8 style guide, maintain proper imports, and use type hints where appropriate.",
        '.html': "For HTML files: Maintain proper DOCTYPE, semantic structure, and accessibility standards.",
        '.css': "For CSS files: Use consistent naming conventions, responsive design principles, and modern CSS features.",
        '.js': "For JavaScript/TypeScript: Use modern ES6+ syntax, proper error handling, and consistent formatting.",
        '.ts': "For JavaScript/TypeScript: Use modern ES6+ syntax, proper error handling, and consistent formatting.",
        '.jsx': "For React JSX: Follow React best practices, use hooks appropriately, and maintain component structure.",
        '.tsx': "For React TypeScript: Follow React best practices, use hooks appropriately, and maintain component structure with proper typing.",
        '.json': "For JSON files: Maintain proper JSON syntax and structure.",
        '.xml': "For XML files: Maintain proper XML syntax and structure.",
        '.yaml': "For YAML files: Maintain proper YAML syntax and indentation.",
        '.yml': "For YAML files: Maintain proper YAML syntax and indentation.",
        '.md': "For Markdown files: Follow proper Markdown syntax and structure.",
        '.sql': "For SQL files: Use proper SQL syntax, consistent formatting, and appropriate naming conventions.",
        '.dockerfile': "For Dockerfile: Follow Docker best practices, use official base images, and optimize for size.",
        '.sh': "For shell scripts: Use proper shell syntax, error handling, and follow shell scripting best practices.",
        '.bat': "For batch files: Use proper batch syntax and error handling.",
        '.ps1': "For PowerShell: Use proper PowerShell syntax and follow PowerShell best practices."
    }

    # Request type specific instructions
    REQUEST_TYPE_INSTRUCTIONS = {
        'create_new': "Creating new files: Use empty SEARCH section and full content in REPLACE section.",
        'debug': "Debugging: Focus on identifying and fixing the specific issue mentioned. Test your changes.",
        'refactor': "Refactoring: Maintain functionality while improving code structure, readability, and performance.",
        'update': "Updating: Make precise changes while preserving existing functionality and code style.",
        'add_feature': "Adding features: Integrate new functionality seamlessly with existing code patterns.",
        'general': "General task: Analyze the request carefully and apply appropriate coding practices."
    }

    # Urgency level instructions
    URGENCY_INSTRUCTIONS = {
        'high': "URGENT REQUEST: Prioritize speed and accuracy. Focus on core functionality first.",
        'normal': "Standard request: Take time to ensure quality and follow best practices."
    }

    # Complexity level instructions
    COMPLEXITY_INSTRUCTIONS = {
        'low': "Simple task: Focus on clean, straightforward implementation.",
        'medium': "Moderate complexity: Ensure all changes work together cohesively.",
        'high': "Complex request: Break down into smaller, manageable changes. Test each part."
    }

    # Image context instructions
    IMAGE_INSTRUCTIONS = {
        'has_images': "Images available for reference: {image_list}",
        'use_images': "Use these images as visual reference when building UI components or implementing designs."
    }

    # Ending instruction
    ENDING_INSTRUCTION = "\n\nONLY EVER RETURN CODE IN A *SEARCH/REPLACE BLOCK*!"

class PromptBuilder:
    """
    Builder class for constructing dynamic system reminders
    """
    
    def __init__(self):
        self.components = PromptComponents()
        self.sections = []
    
    def add_base_rules(self) -> 'PromptBuilder':
        """Add the base SEARCH/REPLACE rules"""
        self.sections.append(self.components.BASE_RULES)
        return self
    
    def add_context_instructions(self, 
                               files: List[str],
                               request_context: dict,
                               image_files: List[str] = None) -> 'PromptBuilder':
        """Add context-specific instructions based on files and request context"""
        
        context_instructions = []
        
        # Add file type specific instructions
        if files:
            file_extensions = {self._get_file_extension(f) for f in files}
            for ext in file_extensions:
                if ext in self.components.FILE_TYPE_INSTRUCTIONS:
                    context_instructions.append(f"- {self.components.FILE_TYPE_INSTRUCTIONS[ext]}")
        
        # Add request type instructions
        request_type = request_context.get('type', 'general')
        if request_type in self.components.REQUEST_TYPE_INSTRUCTIONS:
            context_instructions.append(f"- {self.components.REQUEST_TYPE_INSTRUCTIONS[request_type]}")
        
        # Add urgency instructions
        urgency = request_context.get('urgency', 'normal')
        if urgency in self.components.URGENCY_INSTRUCTIONS:
            context_instructions.append(f"- {self.components.URGENCY_INSTRUCTIONS[urgency]}")
        
        # Add complexity instructions
        complexity = request_context.get('complexity', 'low')
        if complexity in self.components.COMPLEXITY_INSTRUCTIONS:
            context_instructions.append(f"- {self.components.COMPLEXITY_INSTRUCTIONS[complexity]}")
        
        # Add image context if available
        if image_files:
            image_list = ', '.join(image_files)
            context_instructions.append(f"- {self.components.IMAGE_INSTRUCTIONS['has_images'].format(image_list=image_list)}")
            context_instructions.append(f"- {self.components.IMAGE_INSTRUCTIONS['use_images']}")
        
        # Add the context section if there are instructions
        if context_instructions:
            context_section = "\n\n# Context-Specific Instructions:\n" + '\n'.join(context_instructions)
            self.sections.append(context_section)
        
        return self
    
    def add_critical_instructions(self) -> 'PromptBuilder':
        """Add critical behavioral instructions"""
        self.sections.append(self.components.CRITICAL_INSTRUCTIONS)
        return self
    
    def add_file_list(self, files: List[str]) -> 'PromptBuilder':
        """Add the list of files to edit"""
        if files:
            file_section = f"\n\nFiles to edit: {', '.join(files)}"
            self.sections.append(file_section)
        return self
    
    def add_ending_instruction(self) -> 'PromptBuilder':
        """Add the final instruction"""
        self.sections.append(self.components.ENDING_INSTRUCTION)
        return self
    
    def build(self) -> str:
        """Build the complete system reminder"""
        return ''.join(self.sections)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get the file extension from filename"""
        import os
        return os.path.splitext(filename)[1].lower()

class CustomPromptTemplates:
    """
    Pre-defined prompt templates for common scenarios
    """
    
    @staticmethod
    def web_development_template(files: List[str], request_context: dict, image_files: List[str] = None) -> str:
        """Template optimized for web development tasks"""
        builder = PromptBuilder()
        
        # Add web-specific context
        web_context = request_context.copy()
        if not web_context.get('type'):
            web_context['type'] = 'create_new'
        
        return (builder
                .add_base_rules()
                .add_context_instructions(files, web_context, image_files)
                .add_critical_instructions()
                .add_file_list(files)
                .add_ending_instruction()
                .build())
    
    @staticmethod
    def python_development_template(files: List[str], request_context: dict) -> str:
        """Template optimized for Python development tasks"""
        builder = PromptBuilder()
        
        # Add Python-specific context
        python_context = request_context.copy()
        
        return (builder
                .add_base_rules()
                .add_context_instructions(files, python_context)
                .add_critical_instructions()
                .add_file_list(files)
                .add_ending_instruction()
                .build())
    
    @staticmethod
    def debug_template(files: List[str], request_context: dict) -> str:
        """Template optimized for debugging tasks"""
        builder = PromptBuilder()
        
        # Force debug context with high urgency by default
        debug_context = request_context.copy()
        debug_context['type'] = 'debug'
        debug_context['urgency'] = 'high'  # Always high urgency for debug
        
        return (builder
                .add_base_rules()
                .add_context_instructions(files, debug_context)
                .add_critical_instructions()
                .add_file_list(files)
                .add_ending_instruction()
                .build())
    
    @staticmethod
    def refactor_template(files: List[str], request_context: dict) -> str:
        """Template optimized for refactoring tasks"""
        builder = PromptBuilder()
        
        # Force refactor context
        refactor_context = request_context.copy()
        refactor_context['type'] = 'refactor'
        refactor_context['complexity'] = request_context.get('complexity', 'medium')
        
        return (builder
                .add_base_rules()
                .add_context_instructions(files, refactor_context)
                .add_critical_instructions()
                .add_file_list(files)
                .add_ending_instruction()
                .build())

def create_custom_dynamic_system_reminder(
    files: List[str], 
    request_context: dict,
    image_files: List[str] = None,
    conversation_history: List[dict] = None,
    use_template: Optional[str] = None
) -> str:
    """
    Create a dynamic system reminder using the custom prompt system
    
    Args:
        files: List of files to edit
        request_context: Context about the request (type, urgency, complexity)
        image_files: List of available image files
        conversation_history: Previous conversation (not used currently)
        use_template: Optional template to use ('web', 'python', 'debug', 'refactor')
    
    Returns:
        Generated system reminder string
    """
    
    # Use specific template if requested
    if use_template:
        templates = CustomPromptTemplates()
        if use_template == 'web':
            return templates.web_development_template(files, request_context, image_files)
        elif use_template == 'python':
            return templates.python_development_template(files, request_context)
        elif use_template == 'debug':
            return templates.debug_template(files, request_context)
        elif use_template == 'refactor':
            return templates.refactor_template(files, request_context)
    
    # Use default builder
    builder = PromptBuilder()
    
    return (builder
            .add_base_rules()
            .add_context_instructions(files, request_context, image_files)
            .add_critical_instructions()
            .add_file_list(files)
            .add_ending_instruction()
            .build())

# Convenience functions for common use cases
def create_web_prompt(files: List[str], request_context: dict, image_files: List[str] = None) -> str:
    """Create a web development optimized prompt"""
    return create_custom_dynamic_system_reminder(files, request_context, image_files, use_template='web')

def create_python_prompt(files: List[str], request_context: dict) -> str:
    """Create a Python development optimized prompt"""
    return create_custom_dynamic_system_reminder(files, request_context, use_template='python')

def create_debug_prompt(files: List[str], request_context: dict) -> str:
    """Create a debugging optimized prompt"""
    return create_custom_dynamic_system_reminder(files, request_context, use_template='debug')

def create_refactor_prompt(files: List[str], request_context: dict) -> str:
    """Create a refactoring optimized prompt"""
    return create_custom_dynamic_system_reminder(files, request_context, use_template='refactor')
