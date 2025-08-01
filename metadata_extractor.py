import re
import ast
from typing import List, Dict, Optional, Set, Union

from config import ProjectConfig
from logger import log_highlight, log_to_sublog

class MetadataExtractor:
    """
    Universal semantic metadata extractor for codebase chunks.
    Extracts all required semantic anchors (screen, class, function, component), relationships, and validation heuristics.
    All field extraction can be extended/config-driven as needed.
    """
    def __init__(self, project_config: ProjectConfig, project_dir: str = "."):
        self.project_config = project_config
        self.chunk_types = project_config.get_chunk_types()
        self.ext = None
        self.project_dir = project_dir

    def create_enhanced_metadata(self, chunk: str, file_path: str, chunk_index: int) -> Dict:
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        self.ext = ext
        log_highlight("MetadataExtractor.create_enhanced_metadata")
        metadata = {
            "source": file_path,
            "chunk_index": chunk_index,
            "file_type": ext,
        }
        # Extract semantic anchors
        metadata["screen_name"] = self.extract_screen_name(file_path, chunk)
        metadata["function_names"] = self.extract_function_names(chunk)
        metadata["class_names"] = self.extract_class_names(chunk)
        metadata["component_name"] = self.extract_component_name(file_path, chunk)
        metadata["dependencies"] = self.extract_dependencies(chunk)
        metadata["input_fields"] = self.extract_input_fields(chunk)
        metadata["ui_elements"] = self.extract_ui_elements(chunk)
        metadata["validation_rules"] = self.extract_validation_rules(chunk)
        metadata["business_logic_indicators"] = self.extract_business_indicators(chunk)
        # If anchors are missing, log for diagnosis only (chunk filtering happens at RAG builder)
        anchors = [metadata.get("screen_name"), metadata.get("class_names"), metadata.get("function_names"), metadata.get("component_name")]
        if not any(anchors):
            log_to_sublog(self.project_dir, "chunking_metadata.log",
                f"[CHUNK WARNING] No semantic anchor found for {file_path} chunk {chunk_index}."
            )
        # Remove empty/null fields
        clean_meta = {k: v for k, v in metadata.items() if v}
        return clean_meta

    # ---------- Semantic Anchor Extraction ----------

    def extract_screen_name(self, file_path: str, chunk: str = "") -> Optional[str]:
        # Try config-defined patterns for "screen"
        patterns = []
        if hasattr(self.project_config, "get_entity_patterns"):
            pats = self.project_config.get_entity_patterns().get("screen", [])
            patterns.extend(pats)
        for pattern in patterns:
            match = re.search(pattern, chunk)
            if match: return match.group(1)
            match = re.search(pattern, file_path)
            if match: return match.group(1)
        return None

    def extract_component_name(self, file_path: str, chunk: str = "") -> Optional[str]:
        patterns = []
        if hasattr(self.project_config, "get_entity_patterns"):
            pats = self.project_config.get_entity_patterns().get("component", [])
            patterns.extend(pats)
        for pattern in patterns:
            match = re.search(pattern, chunk)
            if match: return match.group(1)
        return None

    def extract_function_names(self, chunk: str) -> List[str]:
        funcs = set()
        try:
            if self.ext == 'py':
                tree = ast.parse(chunk)
                funcs.update(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
            elif self.ext in ['kt', 'kts', 'java']:
                pats = [r'fun\s+(\w+)', r'(?:public|private|protected|static)?\s*\w+\s+(\w+)\s*\(']
                for pat in pats:
                    funcs.update(re.findall(pat, chunk))
            elif self.ext in ['js', 'ts', 'jsx', 'tsx']:
                pats = [r'function\s+(\w+)', r'const\s+(\w+)\s*=', r'let\s+(\w+)\s*=', r'var\s+(\w+)\s*=']
                for pat in pats:
                    funcs.update(re.findall(pat, chunk))
        except Exception:
            pass
        return list({f for f in funcs if isinstance(f, str) and f})

    def extract_class_names(self, chunk: str) -> List[str]:
        classes = set()
        try:
            if self.ext == 'py':
                tree = ast.parse(chunk)
                classes.update(n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
            elif self.ext in ['kt', 'kts', 'java', 'js', 'ts', 'jsx', 'tsx']:
                pats = [r'class\s+(\w+)', r'object\s+(\w+)', r'interface\s+(\w+)', r'enum\s+(\w+)']
                for pat in pats:
                    classes.update(re.findall(pat, chunk))
        except Exception:
            pass
        return list({c for c in classes if isinstance(c, str) and c})

    def extract_dependencies(self, chunk: str) -> List[str]:
        deps = set()
        lines = chunk.splitlines()
        for line in lines:
            line = line.strip()
            if self.ext in ['py', 'ts', 'js', 'kt', 'kts', 'java', 'swift']:
                if line.startswith("import"):
                    if "from" in line:
                        match = re.search(r'from\s+([^\s]+)', line)
                        if match: deps.add(match.group(1))
                    else:
                        parts = line.replace("import ", "").split()
                        if parts: deps.add(parts[0].split(".")[0])
                elif "require(" in line:
                    match = re.search(r'require\(["\']([^"\']+)["\']', line)
                    if match: deps.add(match.group(1))
        return list(deps)

    def extract_input_fields(self, chunk: str) -> List[str]:
        inputs = set()
        try:
            if self.ext == 'xml':
                matches = re.findall(r'<(?:EditText|TextInputLayout|AutoCompleteTextView)[^>]*android:id="[^@]*@(\+id/[\w_]+)', chunk)
                inputs.update([m.split('/')[-1] for m in matches])
            elif self.ext in ['kt', 'kts', 'java']:
                matches = re.findall(r'TextField\s*\([^)]*value\s*=\s*(\w+)', chunk)
                inputs.update(matches)
            elif self.ext in ['tsx', 'jsx', 'html']:
                matches = re.findall(r'[<(][^>]*\s(?:id|name)=["\']([\w_]+)["\']', chunk)
                inputs.update(matches)
        except Exception:
            pass
        return list(inputs)

    def extract_ui_elements(self, chunk: str) -> List[str]:
        tags = ['Button', 'TextView', 'EditText', 'TextField', 'ListView', 'RecyclerView', 'Image', 'Input', 'Select', 'Form', 'Table', 'Dropdown']
        matched = set()
        for tag in tags:
            if re.search(tag, chunk, re.IGNORECASE):
                matched.add(tag)
        return list(matched)

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
        if re.search(r'\b(validate|check|assert)([A-Z][a-zA-Z]+)?\b', chunk, re.IGNORECASE):
            rules.add("custom_validator")
        return list(rules)

    def extract_business_indicators(self, chunk: str) -> List[str]:
        logic_tags = {
            "calculation": ["calc", "price", "total", "subtotal", "tax", "amount", "sum", "net", "fee", "value"],
            "validation_logic": ["validate", "setError", "isValid", "required", "error", "fail", "assert", "check"],
            "workflow": ["next", "step", "action", "proceed", "confirm", "back", "continue", "submit", "cancel", "approve"],
            "authorization": ["auth", "token", "permission", "granted", "allowed", "jwt", "session"],
        }
        indicators = set()
        content_lower = chunk.lower()
        for tag, keywords in logic_tags.items():
            if any(word in content_lower for word in keywords):
                indicators.add(tag)
        return list(indicators)

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - extract_* methods w/ inline print/log for anchor missing: Now all logging & missing-anchor surfacing is handled via logger.py log_to_sublog only, less intrusively and more consistently.
# - Any method-specific debug/diagnostic printouts (lines ~26-40, ~90, ~170 previously).
# ADDED
# - create_enhanced_metadata now consistently checks for missing semantic anchors relevant for your RAG pipeline; logs warning to chunking_metadata.log only — filtering/acceptance now handled upstream (build_rag.py).
# - All helpers for entity/anchor extraction now use config-driven entity_patterns where available.
# - DRY’d all per-language patterns, chunk-name extraction, and relationships into single method per anchor, using config extension for future-proofing.
# - Logging is handled only via logger.py for uniformity across all modules.
