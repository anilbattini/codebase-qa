import re
import ast
from typing import List, Dict, Optional, Set, Union


class MetadataExtractor:
    def __init__(self, project_config):
        self.project_config = project_config
        self.chunk_types = project_config.get_chunk_types()
        self.ext = None

    def create_enhanced_metadata(self, chunk: str, file_path: str, chunk_index: int) -> Dict:
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        self.ext = ext
        metadata = {
            "source": file_path,
            "chunk_index": chunk_index,
            "file_type": ext,
        }

        # Populate all fields
        metadata["screen_name"] = self.extract_screen_name(file_path)
        metadata["function_names"] = self.extract_function_names(chunk)
        metadata["class_names"] = self.extract_class_names(chunk)
        metadata["dependencies"] = self.extract_dependencies(chunk)
        metadata["input_fields"] = self.extract_input_fields(chunk)
        metadata["ui_elements"] = self.extract_ui_elements(chunk)
        metadata["validation_rules"] = self.extract_validation_rules(chunk)
        metadata["business_logic_indicators"] = self.extract_business_indicators(chunk)

        # Remove empty/null fields
        clean_meta = {k: v for k, v in metadata.items() if v}
        return clean_meta

    # -------------------------------
    # Screen Name
    # -------------------------------

    def extract_screen_name(self, file_path: str) -> Optional[str]:
        match = re.search(r'([A-Z][a-zA-Z]+Screen)', file_path)
        return match.group(1) if match else None

    # -------------------------------
    # Class and Function Names
    # -------------------------------

    def extract_function_names(self, chunk: str) -> List[str]:
        funcs = set()
        try:
            if self.ext == 'py':
                tree = ast.parse(chunk)
                funcs.update(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
            elif self.ext in ['kt', 'java']:
                funcs.update(re.findall(r'fun\s+(\w+)', chunk))
            elif self.ext in ['js', 'ts']:
                funcs.update(re.findall(r'function\s+(\w+)', chunk))
        except Exception:
            pass
        return list(funcs)

    def extract_class_names(self, chunk: str) -> List[str]:
        classes = set()
        try:
            if self.ext == 'py':
                tree = ast.parse(chunk)
                classes.update(n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
            elif self.ext in ['kt', 'java', 'js', 'ts']:
                classes.update(re.findall(r'class\s+(\w+)', chunk))
        except Exception:
            pass
        return list(classes)

    # -------------------------------
    # Dependencies
    # -------------------------------

    def extract_dependencies(self, chunk: str) -> List[str]:
        deps = set()
        lines = chunk.splitlines()

        for line in lines:
            line = line.strip()

            if self.ext in ['py', 'ts', 'js', 'kt', 'java']:
                if line.startswith("import"):
                    words = line.replace("import ", "").split()
                    if "from" in line:
                        match = re.search(r'from\s+([^\s]+)', line)
                        if match:
                            deps.add(match.group(1))
                    elif words:
                        deps.add(words[0])
                elif "require(" in line:
                    match = re.search(r'require\(["\']([^"\']+)["\']', line)
                    if match:
                        deps.add(match.group(1))
        return list(deps)

    # -------------------------------
    # UI Elements and Inputs
    # -------------------------------

    def extract_input_fields(self, chunk: str) -> List[str]:
        inputs = set()
        try:
            if self.ext == 'xml':
                # Android XML UI elements
                matches = re.findall(
                    r'<(?:EditText|TextInputLayout|AutoCompleteTextView)[^>]*android:id="[^@]*@(\+id/[\w_]+)',
                    chunk
                )
                inputs.update([m.split('/')[-1] for m in matches])
            elif self.ext in ['kt', 'java']:
                matches = re.findall(r'TextField\s*\([^)]*value\s*=\s*(\w+)', chunk)
                inputs.update(matches)
            elif self.ext in ['tsx', 'jsx', 'html']:
                matches = re.findall(r'<input[^>]+(?:id|name)=["\']([\w_]+)["\']', chunk)
                inputs.update(matches)
        except Exception:
            pass
        return list(inputs)

    def extract_ui_elements(self, chunk: str) -> List[str]:
        tags = ['Button', 'TextView', 'EditText', 'TextField', 'ListView', 'RecyclerView', 'Image']
        matched = set()
        for tag in tags:
            if re.search(tag, chunk, re.IGNORECASE):
                matched.add(tag)
        return list(matched)

    # -------------------------------
    # Validation Heuristics
    # -------------------------------

    def extract_validation_rules(self, chunk: str) -> List[str]:
        rules = set()
        if re.search(r'\.isEmpty\(|==\s*""', chunk):
            rules.add("required_check")
        if re.search(r'\.contains\("@"\)', chunk):
            rules.add("email_format_check")
        if re.search(r'\.matches\([^)]+\)', chunk):
            rules.add("regex_match")
        if "setError(" in chunk:
            rules.add("set_error_triggered")
        if re.search(r'length\s*[<>=]{1,2}\s*\d+', chunk):
            rules.add("length_check")
        if "validate" in chunk.lower():
            rules.add("custom_validator")
        return list(rules)

    # -------------------------------
    # Business Logic Indicators
    # -------------------------------

    def extract_business_indicators(self, chunk: str) -> List[str]:
        logic_tags = {
            "calculation": ["calc", "price", "total", "subtotal", "tax", "value"],
            "validation_logic": ["validate", "setError", "isValid", "required", "error"],
            "workflow": ["next", "step", "action", "proceed", "confirm", "back"],
            "authorization": ["auth", "token", "permission", "granted", "allowed"]
        }

        indicators = set()
        content_lower = chunk.lower()

        for tag, keywords in logic_tags.items():
            if any(word in content_lower for word in keywords):
                indicators.add(tag)

        return list(indicators)
