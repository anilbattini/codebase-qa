# core/metadata_extractor.py

import re
import ast
from typing import List, Dict, Optional, Set, Union, Tuple
from config import ProjectConfig
from logger import log_highlight, log_to_sublog

class MetadataExtractor:
    """
    Enhanced semantic metadata extractor for codebase chunks.
    Now extracts Level 2-4 capabilities: method signatures, inheritance, call sites, usage patterns.
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

        try:
            # Existing semantic anchors (keep all existing functionality)
            metadata["screen_name"] = self.extract_screen_name(file_path, chunk)
            metadata["function_names"] = self.extract_function_names(chunk)
            metadata["class_names"] = self.extract_class_names(chunk)
            metadata["component_name"] = self.extract_component_name(file_path, chunk)
            metadata["dependencies"] = self.extract_dependencies(chunk)
            metadata["input_fields"] = self.extract_input_fields(chunk)
            metadata["ui_elements"] = self.extract_ui_elements(chunk)
            metadata["validation_rules"] = self.extract_validation_rules(chunk)
            metadata["business_logic_indicators"] = self.extract_business_indicators(chunk)

            # 🆕 NEW: Level 2-4 Enhanced Capabilities
            metadata["method_signatures"] = self.extract_method_signatures(chunk, file_path, chunk_index)
            metadata["inheritance_info"] = self.extract_inheritance_info(chunk, file_path, chunk_index)
            metadata["call_sites"] = self.extract_call_sites(chunk, file_path, chunk_index)
            metadata["interface_implementations"] = self.extract_interface_implementations(chunk, file_path, chunk_index)
            metadata["design_patterns"] = self.detect_design_patterns(chunk, file_path, chunk_index)
            metadata["error_handling_patterns"] = self.extract_error_handling_patterns(chunk, file_path, chunk_index)
            metadata["api_usage"] = self.extract_api_usage_patterns(chunk, file_path, chunk_index)

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"ERROR in create_enhanced_metadata for {file_path} chunk {chunk_index}: {e}")
            import traceback
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Traceback: {traceback.format_exc()}")

        # Check for semantic anchors
        anchors = [metadata.get("screen_name"), metadata.get("class_names"), 
                  metadata.get("function_names"), metadata.get("component_name")]
        if not any(anchors):
            log_to_sublog(self.project_dir, "chunking_metadata.log",
                         f"[CHUNK WARNING] No semantic anchor found for {file_path} chunk {chunk_index}.")

        # Remove empty/null fields
        clean_meta = {k: v for k, v in metadata.items() if v}
        return clean_meta

    # 🆕 NEW METHODS for Level 2-4 Capabilities

    def extract_method_signatures(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> List[Dict[str, str]]:
        """Extract method signatures with parameters and return types."""
        signatures = []
        
        try:
            if self.ext == 'py':
                signatures.extend(self._extract_python_signatures(chunk))
            elif self.ext in ['kt', 'kts', 'java']:
                signatures.extend(self._extract_kotlin_java_signatures(chunk))
            elif self.ext in ['js', 'ts', 'jsx', 'tsx']:
                signatures.extend(self._extract_js_ts_signatures(chunk))
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Error extracting signatures in {file_path} chunk {chunk_index}: {e}")
            import traceback
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Traceback: {traceback.format_exc()}")
        
        return signatures

    def _extract_python_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract Python function signatures."""
        signatures = []
        try:
            tree = ast.parse(chunk)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    signature = {
                        "name": node.name,
                        "parameters": [arg.arg for arg in node.args.args],
                        "return_type": ast.unparse(node.returns) if node.returns else "None",
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "line_number": node.lineno
                    }
                    signatures.append(signature)
        except Exception:
            # Fallback to regex for incomplete code
            signatures.extend(self._extract_python_signatures_regex(chunk))
        return signatures

    def _extract_python_signatures_regex(self, chunk: str) -> List[Dict[str, str]]:
        """Fallback regex-based Python signature extraction."""
        signatures = []
        pattern = r'def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?:'
        for match in re.finditer(pattern, chunk):
            params_str = match.group(2)
            # 🔧 FIX: Safe parameter parsing
            parameters = []
            if params_str and params_str.strip():
                for p in params_str.split(','):
                    p = p.strip()
                    if p and ':' in p:
                        parameters.append(p.split(':')[0].strip())
                    elif p:
                        parameters.append(p)
            
            signature = {
                "name": match.group(1),
                "parameters": parameters,
                "return_type": match.group(3).strip() if match.group(3) else "None",
                "is_async": False
            }
            signatures.append(signature)
        return signatures

    def _extract_kotlin_java_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract Kotlin/Java method signatures."""
        signatures = []
        
        # Kotlin function pattern
        kt_pattern = r'fun\s+(\w+)\s*\(([^)]*)\)\s*:\s*([^{=\n]+)?'
        for match in re.finditer(kt_pattern, chunk):
            signature = {
                "name": match.group(1),
                "parameters": self._parse_kt_parameters(match.group(2)),
                "return_type": match.group(3).strip() if match.group(3) else "Unit",
                "language": "kotlin"
            }
            signatures.append(signature)
        
        # Java method pattern  
        java_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(\w+)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(java_pattern, chunk):
            signature = {
                "name": match.group(2),
                "parameters": self._parse_java_parameters(match.group(3)),
                "return_type": match.group(1),
                "language": "java"
            }
            signatures.append(signature)
        
        return signatures

    def _parse_kt_parameters(self, params_str: str) -> List[str]:
        """Parse Kotlin parameter string - 🔧 FIX: Safe handling."""
        if not params_str or not params_str.strip():
            return []
        params = []
        try:
            for param in params_str.split(','):
                param = param.strip()
                if param and ':' in param:
                    params.append(param.split(':')[0].strip())
                elif param:
                    params.append(param)
        except Exception:
            # Return empty if parsing fails
            pass
        return params

    def _parse_java_parameters(self, params_str: str) -> List[str]:
        """Parse Java parameter string - 🔧 FIX: Safe handling."""
        if not params_str or not params_str.strip():
            return []
        params = []
        try:
            for param in params_str.split(','):
                param = param.strip()
                if param and ' ' in param:
                    params.append(param.split()[-1])  # Get parameter name
                elif param:
                    params.append(param)
        except Exception:
            # Return empty if parsing fails
            pass
        return params

    def _extract_js_ts_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract JavaScript/TypeScript function signatures."""
        signatures = []
        
        # Function declaration pattern
        func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{=\n]+))?'
        for match in re.finditer(func_pattern, chunk):
            params_str = match.group(2)
            parameters = []
            if params_str and params_str.strip():
                try:
                    for p in params_str.split(','):
                        p = p.strip()
                        if p and ':' in p:
                            parameters.append(p.split(':')[0].strip())
                        elif p:
                            parameters.append(p)
                except Exception:
                    pass
                    
            signature = {
                "name": match.group(1),
                "parameters": parameters,
                "return_type": match.group(3).strip() if match.group(3) else "any",
                "language": "javascript"
            }
            signatures.append(signature)
        
        return signatures

    def extract_inheritance_info(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> Dict[str, List[str]]:
        """Extract class inheritance and interface implementation info."""
        inheritance = {
            "extends": [],
            "implements": [],
            "inherits_from": []
        }
        
        try:
            if self.ext in ['kt', 'kts', 'java']:
                # Kotlin/Java inheritance
                extends_pattern = r'class\s+\w+\s*:\s*([^{,\n]+)'
                for match in re.finditer(extends_pattern, chunk):
                    inheritance["extends"].append(match.group(1).strip())
                
                implements_pattern = r'implements\s+([^{]+)'
                for match in re.finditer(implements_pattern, chunk):
                    # 🔧 FIX: Safe splitting
                    try:
                        inheritance["implements"].extend([i.strip() for i in match.group(1).split(',') if i.strip()])
                    except Exception:
                        pass
                        
            elif self.ext == 'py':
                # Python inheritance
                class_pattern = r'class\s+\w+\s*\(([^)]+)\):'
                for match in re.finditer(class_pattern, chunk):
                    try:
                        inheritance["inherits_from"].extend([i.strip() for i in match.group(1).split(',') if i.strip()])
                    except Exception:
                        pass
                        
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Error extracting inheritance in {file_path} chunk {chunk_index}: {e}")
        
        return {k: v for k, v in inheritance.items() if v}

    def extract_call_sites(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> List[Dict[str, str]]:
        """Extract method/function call sites for building call graphs."""
        call_sites = []
        
        try:
            # Generic function call pattern
            call_pattern = r'(\w+)\s*\([^)]*\)'
            for match in re.finditer(call_pattern, chunk):
                call_name = match.group(1)
                # Filter out keywords and common patterns
                if call_name not in ['if', 'for', 'while', 'switch', 'return', 'new', 'super']:
                    call_sites.append({
                        "called_function": call_name,
                        "line_context": self._get_line_context(chunk, match.start())
                    })
                    
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Error extracting call sites in {file_path} chunk {chunk_index}: {e}")
        
        return call_sites[:10]  # Limit to prevent noise

    def _get_line_context(self, chunk: str, position: int) -> str:
        """Get the line containing the given position."""
        try:
            lines = chunk[:position].split('\n')
            return lines[-1].strip() if lines else ""
        except Exception:
            return ""

    def extract_interface_implementations(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> List[str]:
        """Extract interface implementations."""
        interfaces = []
        
        try:
            if self.ext in ['kt', 'kts', 'java']:
                # Look for interface implementations
                impl_pattern = r'implements\s+([^{]+)'
                for match in re.finditer(impl_pattern, chunk):
                    try:
                        interfaces.extend([i.strip() for i in match.group(1).split(',') if i.strip()])
                    except Exception:
                        pass
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Error extracting interfaces in {file_path} chunk {chunk_index}: {e}")
                
        return interfaces

    def detect_design_patterns(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> List[str]:
        """Lightweight design pattern detection using rules."""
        patterns = []
        
        try:
            # Singleton pattern
            if re.search(r'private\s+static.*instance', chunk, re.IGNORECASE) and \
               re.search(r'getInstance\(\)', chunk):
                patterns.append("Singleton")
            
            # Factory pattern
            if re.search(r'create\w*\(', chunk, re.IGNORECASE) or \
               re.search(r'factory', chunk, re.IGNORECASE):
                patterns.append("Factory")
            
            # Observer pattern
            if re.search(r'(listener|observer|subscribe)', chunk, re.IGNORECASE):
                patterns.append("Observer")
            
            # Builder pattern
            if re.search(r'\.build\(\)', chunk) or \
               re.search(r'builder', chunk, re.IGNORECASE):
                patterns.append("Builder")
            
            # Adapter pattern
            if re.search(r'adapter', chunk, re.IGNORECASE):
                patterns.append("Adapter")
                
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Error detecting patterns in {file_path} chunk {chunk_index}: {e}")
            
        return patterns

    def extract_error_handling_patterns(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> List[str]:
        """Extract error handling patterns."""
        patterns = []
        
        try:
            if 'try' in chunk and 'catch' in chunk:
                patterns.append("try_catch")
            if 'throw' in chunk:
                patterns.append("exception_throwing")
            if re.search(r'\.orElse\(', chunk):
                patterns.append("optional_handling")
            if 'finally' in chunk:
                patterns.append("finally_block")
            if re.search(r'(retry|circuit.*breaker)', chunk, re.IGNORECASE):
                patterns.append("resilience_pattern")
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Error extracting error patterns in {file_path} chunk {chunk_index}: {e}")
            
        return patterns

    def extract_api_usage_patterns(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> List[Dict[str, str]]:
        """Extract API usage patterns for external service detection."""
        api_patterns = []
        
        try:
            # HTTP calls
            if re.search(r'(http|Http|HTTP)', chunk):
                api_patterns.append({"type": "http_client", "pattern": "HTTP calls detected"})
            
            # Database patterns
            if re.search(r'(query|Query|SQL|sql)', chunk):
                api_patterns.append({"type": "database", "pattern": "Database operations detected"})
            
            # REST patterns
            if re.search(r'(@GET|@POST|@PUT|@DELETE|\.get\(|\.post\()', chunk):
                api_patterns.append({"type": "rest_api", "pattern": "REST API operations detected"})
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", 
                         f"Error extracting API patterns in {file_path} chunk {chunk_index}: {e}")
            
        return api_patterns

    # Keep all existing methods unchanged for backward compatibility
    def extract_screen_name(self, file_path: str, chunk: str = "") -> Optional[str]:
        """Existing method - unchanged for backward compatibility."""
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
        """Existing method - unchanged for backward compatibility."""
        patterns = []
        if hasattr(self.project_config, "get_entity_patterns"):
            pats = self.project_config.get_entity_patterns().get("component", [])
            patterns.extend(pats)

        for pattern in patterns:
            match = re.search(pattern, chunk)
            if match: return match.group(1)
        return None

    def extract_function_names(self, chunk: str) -> List[str]:
        """Existing method - enhanced but backward compatible."""
        funcs = set()
        try:
            if self.ext == 'py':
                tree = ast.parse(chunk)
                funcs.update(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
            elif self.ext in ['kt', 'kts', 'java']:
                pats = [r'fun\s+(\w+)', r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(']
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
        """Existing method - unchanged for backward compatibility."""
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
        """Existing method - hardened for stable dependency tokens."""
        deps = set()
        try:
            lines = chunk.splitlines()
            for line in lines:
                line = line.strip()
                if self.ext in ['py', 'ts', 'js', 'kt', 'kts', 'java', 'swift']:
                    if line.startswith("import"):
                        if "from" in line:
                            match = re.search(r'from\s+([^\s]+)', line)
                            if match:
                                deps.add(match.group(1))
                        else:
                            parts = line.replace("import ", "").split()
                            if parts:
                                token = parts
                                # Normalize to top-level package/module token
                                if '.' in token:
                                    token = token.split('.')
                                deps.add(token)
                    elif "require(" in line:
                        match = re.search(r'require\(["\']([^"\']+)["\']', line)
                        if match:
                            deps.add(match.group(1))
        except Exception:
            pass
        return list(deps)


    def extract_input_fields(self, chunk: str) -> List[str]:
        """Existing method - unchanged for backward compatibility."""
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
        """Existing method - unchanged for backward compatibility."""
        tags = ['Button', 'TextView', 'EditText', 'TextField', 'ListView', 'RecyclerView', 'Image', 'Input', 'Select', 'Form', 'Table', 'Dropdown']
        matched = set()
        try:
            for tag in tags:
                if re.search(tag, chunk, re.IGNORECASE):
                    matched.add(tag)
        except Exception:
            pass
        return list(matched)

    def extract_validation_rules(self, chunk: str) -> List[str]:
        """Existing method - unchanged for backward compatibility."""
        rules = set()
        try:
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
        except Exception:
            pass
        return list(rules)

    def extract_business_indicators(self, chunk: str) -> List[str]:
        """Existing method - unchanged for backward compatibility."""
        logic_tags = {
            "calculation": ["calc", "price", "total", "subtotal", "tax", "amount", "sum", "net", "fee", "value"],
            "validation_logic": ["validate", "setError", "isValid", "required", "error", "fail", "assert", "check"],
            "workflow": ["next", "step", "action", "proceed", "confirm", "back", "continue", "submit", "cancel", "approve"],
            "authorization": ["auth", "token", "permission", "granted", "allowed", "jwt", "session"],
        }

        indicators = set()
        try:
            content_lower = chunk.lower()
            for tag, keywords in logic_tags.items():
                if any(word in content_lower for word in keywords):
                    indicators.add(tag)
        except Exception:
            pass
        return list(indicators)
