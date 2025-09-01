# core/metadata_extractor.py

import re
import ast
from typing import List, Dict, Optional, Set, Union, Tuple
from config.config import ProjectConfig
from logger import log_highlight, log_to_sublog

class MetadataExtractor:
    """
    Enhanced semantic metadata extractor for codebase chunks.
    Now extracts Level 2-4 capabilities with robust error handling across all languages.
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

            # 🆕 ENHANCED: Level 2-4 Enhanced Capabilities with robust error handling
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

    # 🆕 ENHANCED METHODS for Level 2-4 Capabilities with robust error handling

    def extract_method_signatures(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> List[Dict[str, str]]:
        """Extract method signatures with parameters and return types - ENHANCED for all languages."""
        signatures = []
        try:
            if self.ext == 'py':
                signatures.extend(self._extract_python_signatures(chunk))
            elif self.ext in ['kt', 'kts', 'java']:
                signatures.extend(self._extract_kotlin_java_signatures(chunk))
            elif self.ext in ['js', 'ts', 'jsx', 'tsx']:
                signatures.extend(self._extract_js_ts_signatures(chunk))
            elif self.ext in ['swift']:
                signatures.extend(self._extract_swift_signatures(chunk))
            elif self.ext in ['c', 'cpp', 'cc', 'cxx']:
                signatures.extend(self._extract_cpp_signatures(chunk))
            elif self.ext in ['cs']:
                signatures.extend(self._extract_csharp_signatures(chunk))
            elif self.ext in ['go']:
                signatures.extend(self._extract_go_signatures(chunk))
            elif self.ext in ['rs']:
                signatures.extend(self._extract_rust_signatures(chunk))

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Error extracting signatures in {file_path} chunk {chunk_index}: {e}")
            import traceback
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Traceback: {traceback.format_exc()}")

        return signatures[:20]  # Limit to prevent excessive metadata

    # 🔧 ENHANCED PYTHON SIGNATURE EXTRACTION

    def _extract_python_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract Python function signatures with robust error handling."""
        signatures = []
        try:
            tree = ast.parse(chunk)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    try:
                        signature = {
                            "name": node.name,
                            "parameters": self._parse_python_parameters(node.args),
                            "return_type": ast.unparse(node.returns) if node.returns else "None",
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                            "line_number": getattr(node, 'lineno', 0),
                            "language": "python"
                        }
                        signatures.append(signature)
                    except Exception as e:
                        log_to_sublog(self.project_dir, "metadata_extractor.log",
                                      f"Error parsing Python function {getattr(node, 'name', 'unknown')}: {e}")

        except (SyntaxError, ValueError):
            # Fallback to regex for incomplete/invalid code
            signatures.extend(self._extract_python_signatures_regex(chunk))
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Python signature extraction failed: {e}")

        return signatures

    def _parse_python_parameters(self, args_node) -> List[str]:
        """Parse Python function arguments safely."""
        parameters = []
        try:
            # Regular arguments
            for arg in args_node.args:
                if hasattr(arg, 'arg'):
                    parameters.append(arg.arg)
                elif hasattr(arg, 'id'):
                    parameters.append(arg.id)

            # *args
            if args_node.vararg:
                param_name = args_node.vararg.arg if hasattr(args_node.vararg, 'arg') else str(args_node.vararg)
                parameters.append(f"*{param_name}")

            # **kwargs
            if args_node.kwarg:
                param_name = args_node.kwarg.arg if hasattr(args_node.kwarg, 'arg') else str(args_node.kwarg)
                parameters.append(f"**{param_name}")

            # Keyword-only arguments
            for kwonlyarg in getattr(args_node, 'kwonlyargs', []):
                if hasattr(kwonlyarg, 'arg'):
                    parameters.append(kwonlyarg.arg)

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Error parsing Python parameters: {e}")

        return parameters[:10]  # Limit to prevent excessive metadata

    def _extract_python_signatures_regex(self, chunk: str) -> List[Dict[str, str]]:
        """Fallback regex-based Python signature extraction with enhanced error handling."""
        signatures = []
        try:
            # Enhanced patterns for Python functions
            patterns = [
                r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?:',
                r'(\w+)\s*=\s*lambda\s+([^:]*):',  # Lambda functions
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, chunk, re.MULTILINE):
                    try:
                        func_name = match.group(1)
                        params_str = match.group(2) if len(match.groups()) > 1 else ""
                        return_type = match.group(3) if len(match.groups()) > 2 and match.group(3) else "None"

                        parameters = self._parse_python_parameters_string(params_str)

                        signature = {
                            "name": func_name,
                            "parameters": parameters,
                            "return_type": return_type.strip() if return_type else "None",
                            "is_async": "async" in match.group(0),
                            "language": "python"
                        }
                        signatures.append(signature)

                    except Exception as e:
                        log_to_sublog(self.project_dir, "metadata_extractor.log",
                                      f"Error parsing Python regex match: {e}")

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Python regex signature extraction failed: {e}")

        return signatures

    def _parse_python_parameters_string(self, params_str: str) -> List[str]:
        """Parse Python parameter string with enhanced error handling."""
        if not params_str or not params_str.strip():
            return []

        parameters = []
        try:
            # Handle complex Python parameter syntax
            param_parts = []
            bracket_count = 0
            paren_count = 0
            current_param = ""

            for char in params_str + ",":  # Add comma to process last param
                if char == ',' and bracket_count == 0 and paren_count == 0:
                    if current_param.strip():
                        param_parts.append(current_param.strip())
                    current_param = ""
                else:
                    if char in '([{':
                        bracket_count += 1
                    elif char in ')]}':
                        bracket_count -= 1
                    elif char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                    current_param += char

            for param in param_parts:
                param = param.strip()
                if not param:
                    continue

                # Handle different parameter types
                if '=' in param:  # Default parameter
                    param_name = param.split('=')[0].strip()
                elif ':' in param:  # Type annotation
                    param_name = param.split(':')[0].strip()
                else:
                    param_name = param

                # Clean up parameter name
                param_name = param_name.replace('*', '').replace('**', '').strip()
                if param_name and param_name.replace('_', '').replace('self', '').isalnum():
                    parameters.append(param_name)

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Python parameter string parsing failed for '{params_str}': {e}")

        return parameters[:10]

    # 🔧 ENHANCED KOTLIN/JAVA SIGNATURE EXTRACTION

    def _extract_kotlin_java_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract Kotlin/Java method signatures with enhanced error handling."""
        signatures = []
        try:
            # Kotlin function pattern (enhanced)
            kt_patterns = [
                r'fun\s+(?:<[^>]*>\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{=\n]+))?',
                r'(?:override\s+)?fun\s+(?:<[^>]*>\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{=\n]+))?',
                r'(?:suspend\s+)?fun\s+(?:<[^>]*>\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{=\n]+))?',
            ]

            for pattern in kt_patterns:
                for match in re.finditer(pattern, chunk, re.MULTILINE):
                    try:
                        signature = {
                            "name": match.group(1),
                            "parameters": self._parse_kt_parameters(match.group(2)),
                            "return_type": match.group(3).strip() if match.group(3) else "Unit",
                            "language": "kotlin"
                        }
                        signatures.append(signature)
                    except Exception as e:
                        log_to_sublog(self.project_dir, "metadata_extractor.log",
                                      f"Error parsing Kotlin function: {e}")

            # Java method pattern (enhanced)
            java_patterns = [
                r'(?:public|private|protected)?\s*(?:static)?\s*(?:<[^>]*>\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)',
                r'(?:public|private|protected)?\s*(?:abstract|final)?\s*(?:static)?\s*(?:<[^>]*>\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)',
            ]

            for pattern in java_patterns:
                for match in re.finditer(pattern, chunk, re.MULTILINE):
                    try:
                        signature = {
                            "name": match.group(2),
                            "parameters": self._parse_java_parameters(match.group(3)),
                            "return_type": match.group(1),
                            "language": "java"
                        }
                        signatures.append(signature)
                    except Exception as e:
                        log_to_sublog(self.project_dir, "metadata_extractor.log",
                                      f"Error parsing Java method: {e}")

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Kotlin/Java signature extraction failed: {e}")

        return signatures

    def _parse_kt_parameters(self, params_str: str) -> List[str]:
        """Parse Kotlin parameter string - 🔧 ENHANCED: Handle complex types safely."""
        if not params_str or not params_str.strip():
            return []

        params = []
        try:
            # Handle complex Kotlin parameter syntax: generics, lambdas, etc.
            param_parts = []
            bracket_count = 0
            current_param = ""

            for char in params_str + ",":  # Add comma to process last param
                if char == ',' and bracket_count == 0:
                    if current_param.strip():
                        param_parts.append(current_param.strip())
                    current_param = ""
                else:
                    if char in '()<>[]{}':
                        bracket_count += 1 if char in '([{<' else -1
                    current_param += char

            for param in param_parts:
                param = param.strip()
                if not param:
                    continue

                if ':' in param:
                    param_name = param.split(':')[0].strip()
                    if param_name and param_name.isidentifier():
                        params.append(param_name)
                elif param.strip() and param.strip().isidentifier():
                    params.append(param.strip())

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Parameter parsing failed for '{params_str}': {e}")

        return params[:10]  # Limit to prevent excessive metadata

    def _parse_java_parameters(self, params_str: str) -> List[str]:
        """Parse Java parameter string - 🔧 ENHANCED: Handle complex types safely."""
        if not params_str or not params_str.strip():
            return []

        params = []
        try:
            # Split on commas, but respect generics and arrays
            param_parts = []
            bracket_count = 0
            current_param = ""

            for char in params_str + ",":
                if char == ',' and bracket_count == 0:
                    if current_param.strip():
                        param_parts.append(current_param.strip())
                    current_param = ""
                else:
                    if char in '<>[]()':
                        bracket_count += 1 if char in '<[(' else -1
                    current_param += char

            for param in param_parts:
                param = param.strip()
                if not param:
                    continue

                # Extract parameter name from "Type paramName" pattern
                parts = param.split()
                if len(parts) >= 2:
                    param_name = parts[-1]  # Last part is usually the name
                    # Remove array brackets and other decorators
                    param_name = re.sub(r'[\[\]\.]+', '', param_name)
                    if param_name.isidentifier():
                        params.append(param_name)
                elif len(parts) == 1 and parts[0].isidentifier():
                    params.append(parts[0])

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Java parameter parsing failed for '{params_str}': {e}")

        return params[:10]  # Limit to prevent excessive metadata

    # 🆕 ENHANCED JAVASCRIPT/TYPESCRIPT SIGNATURE EXTRACTION

    def _extract_js_ts_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract JavaScript/TypeScript function signatures with enhanced error handling."""
        signatures = []
        try:
            # Enhanced patterns for JS/TS functions
            patterns = [
                r'function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{=\n]+))?',  # function declarations
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\(([^)]*)\)\s*(?::\s*([^{=\n]+))?',  # function expressions
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*([^{=\n]+))?\s*=>',  # arrow functions
                r'(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{=\n]+))?\s*{',  # method definitions
                r'(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{=\n]+))?',  # class methods
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, chunk, re.MULTILINE):
                    try:
                        func_name = match.group(1)
                        params_str = match.group(2) if len(match.groups()) > 1 else ""
                        return_type = match.group(3) if len(match.groups()) > 2 and match.group(3) else "any"

                        parameters = self._parse_js_ts_parameters(params_str)

                        signature = {
                            "name": func_name,
                            "parameters": parameters,
                            "return_type": return_type.strip() if return_type else "any",
                            "is_async": "async" in match.group(0),
                            "language": "javascript" if self.ext in ['js', 'jsx'] else "typescript"
                        }
                        signatures.append(signature)

                    except Exception as e:
                        log_to_sublog(self.project_dir, "metadata_extractor.log",
                                      f"Error parsing JS/TS function: {e}")

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"JS/TS signature extraction failed: {e}")

        return signatures

    def _parse_js_ts_parameters(self, params_str: str) -> List[str]:
        """Parse JavaScript/TypeScript parameter string with enhanced error handling."""
        if not params_str or not params_str.strip():
            return []

        parameters = []
        try:
            # Handle complex JS/TS parameter syntax: destructuring, generics, etc.
            param_parts = []
            bracket_count = 0
            brace_count = 0
            current_param = ""

            for char in params_str + ",":  # Add comma to process last param
                if char == ',' and bracket_count == 0 and brace_count == 0:
                    if current_param.strip():
                        param_parts.append(current_param.strip())
                    current_param = ""
                else:
                    if char in '([<':
                        bracket_count += 1
                    elif char in ')]>':
                        bracket_count -= 1
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                    current_param += char

            for param in param_parts:
                param = param.strip()
                if not param:
                    continue

                # Handle different parameter patterns
                if param.startswith('{'):  # Destructuring
                    # Try to extract variable names from destructuring
                    destructured = re.findall(r'(\w+)(?:\s*:\s*\w+)?', param)
                    parameters.extend(destructured[:3])  # Limit destructured params
                elif param.startswith('['):  # Array destructuring
                    array_params = re.findall(r'(\w+)', param)
                    parameters.extend(array_params[:3])  # Limit array params
                elif '=' in param:  # Default parameter
                    param_name = param.split('=')[0].strip()
                    if ':' in param_name:
                        param_name = param_name.split(':')[0].strip()
                    param_name = param_name.replace('...', '').strip()  # Rest parameter
                    if param_name and param_name.isidentifier():
                        parameters.append(param_name)
                elif ':' in param:  # Type annotation
                    param_name = param.split(':')[0].strip()
                    param_name = param_name.replace('...', '').strip()  # Rest parameter
                    if param_name and param_name.isidentifier():
                        parameters.append(param_name)
                else:
                    param_name = param.replace('...', '').strip()  # Rest parameter
                    if param_name and param_name.isidentifier():
                        parameters.append(param_name)

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"JS/TS parameter parsing failed for '{params_str}': {e}")

        return parameters[:10]  # Limit to prevent excessive metadata

    # 🆕 ENHANCED SWIFT SIGNATURE EXTRACTION

    def _extract_swift_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract Swift function signatures with enhanced error handling."""
        signatures = []
        try:
            # Swift function patterns
            patterns = [
                r'func\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^{]+))?',
                r'(?:override\s+)?func\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^{]+))?',
                r'(?:private|public|internal|fileprivate)?\s*func\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^{]+))?',
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, chunk, re.MULTILINE):
                    try:
                        signature = {
                            "name": match.group(1),
                            "parameters": self._parse_swift_parameters(match.group(2)),
                            "return_type": match.group(3).strip() if match.group(3) else "Void",
                            "language": "swift"
                        }
                        signatures.append(signature)

                    except Exception as e:
                        log_to_sublog(self.project_dir, "metadata_extractor.log",
                                      f"Error parsing Swift function: {e}")

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Swift signature extraction failed: {e}")

        return signatures

    def _parse_swift_parameters(self, params_str: str) -> List[str]:
        """Parse Swift parameter string with enhanced error handling."""
        if not params_str or not params_str.strip():
            return []

        parameters = []
        try:
            param_parts = []
            bracket_count = 0
            current_param = ""

            for char in params_str + ",":
                if char == ',' and bracket_count == 0:
                    if current_param.strip():
                        param_parts.append(current_param.strip())
                    current_param = ""
                else:
                    if char in '([<':
                        bracket_count += 1
                    elif char in ')]>':
                        bracket_count -= 1
                    current_param += char

            for param in param_parts:
                param = param.strip()
                if not param:
                    continue

                # Swift parameter format: [external_name] internal_name: Type
                parts = param.split(':')
                if len(parts) >= 1:
                    name_part = parts[0].strip()
                    # Handle external and internal names
                    name_tokens = name_part.split()
                    if len(name_tokens) >= 2:
                        internal_name = name_tokens[-1]  # Last token is internal name
                    else:
                        internal_name = name_tokens[0] if name_tokens else param
                    
                    if internal_name and internal_name.isidentifier() and internal_name != '_':
                        parameters.append(internal_name)

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Swift parameter parsing failed for '{params_str}': {e}")

        return parameters[:10]

    # 🆕 ADDITIONAL LANGUAGE SUPPORT

    def _extract_cpp_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract C++ function signatures."""
        signatures = []
        try:
            patterns = [
                r'(?:virtual\s+)?(?:inline\s+)?(\w+(?:\s*\*|\s*&)?)\s+(\w+)\s*\(([^)]*)\)',
                r'(?:template\s*<[^>]*>\s+)?(\w+(?:\s*\*|\s*&)?)\s+(\w+)\s*\(([^)]*)\)',
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, chunk, re.MULTILINE):
                    try:
                        signature = {
                            "name": match.group(2),
                            "parameters": self._parse_cpp_parameters(match.group(3)),
                            "return_type": match.group(1).strip(),
                            "language": "cpp"
                        }
                        signatures.append(signature)
                    except Exception:
                        pass

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", f"C++ extraction failed: {e}")

        return signatures

    def _parse_cpp_parameters(self, params_str: str) -> List[str]:
        """Parse C++ parameters safely."""
        if not params_str or not params_str.strip():
            return []
        
        parameters = []
        try:
            for param in params_str.split(','):
                param = param.strip()
                if param and param != 'void':
                    # Extract parameter name (usually the last identifier)
                    tokens = param.split()
                    if tokens:
                        param_name = tokens[-1].replace('*', '').replace('&', '').strip()
                        if param_name.isidentifier():
                            parameters.append(param_name)
        except Exception:
            pass
        
        return parameters[:10]

    def _extract_csharp_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract C# method signatures."""
        signatures = []
        try:
            pattern = r'(?:public|private|protected|internal)?\s*(?:static|virtual|override)?\s*(\w+(?:\[\])?)\s+(\w+)\s*\(([^)]*)\)'
            for match in re.finditer(pattern, chunk, re.MULTILINE):
                try:
                    signature = {
                        "name": match.group(2),
                        "parameters": self._parse_csharp_parameters(match.group(3)),
                        "return_type": match.group(1),
                        "language": "csharp"
                    }
                    signatures.append(signature)
                except Exception:
                    pass
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", f"C# extraction failed: {e}")

        return signatures

    def _parse_csharp_parameters(self, params_str: str) -> List[str]:
        """Parse C# parameters safely."""
        if not params_str or not params_str.strip():
            return []
        
        parameters = []
        try:
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # Handle "Type paramName" format
                    parts = param.split()
                    if len(parts) >= 2:
                        param_name = parts[-1]
                        if param_name.isidentifier():
                            parameters.append(param_name)
        except Exception:
            pass
        
        return parameters[:10]

    def _extract_go_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract Go function signatures."""
        signatures = []
        try:
            pattern = r'func\s+(?:\([^)]*\))?\s*(\w+)\s*\(([^)]*)\)\s*(?:\(([^)]*)\)|(\w+(?:\s*\*)?[\w\[\]]*))?\s*{'
            for match in re.finditer(pattern, chunk, re.MULTILINE):
                try:
                    signature = {
                        "name": match.group(1),
                        "parameters": self._parse_go_parameters(match.group(2)),
                        "return_type": match.group(3) or match.group(4) or "void",
                        "language": "go"
                    }
                    signatures.append(signature)
                except Exception:
                    pass
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", f"Go extraction failed: {e}")

        return signatures

    def _parse_go_parameters(self, params_str: str) -> List[str]:
        """Parse Go parameters safely."""
        if not params_str or not params_str.strip():
            return []
        
        parameters = []
        try:
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # Go format: "name type" or "name1, name2 type"
                    parts = param.split()
                    if len(parts) >= 2:
                        # Multiple names with same type
                        names = parts[:-1]
                        for name in names:
                            name = name.replace(',', '').strip()
                            if name.isidentifier():
                                parameters.append(name)
        except Exception:
            pass
        
        return parameters[:10]

    def _extract_rust_signatures(self, chunk: str) -> List[Dict[str, str]]:
        """Extract Rust function signatures."""
        signatures = []
        try:
            pattern = r'fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^{]+))?'
            for match in re.finditer(pattern, chunk, re.MULTILINE):
                try:
                    signature = {
                        "name": match.group(1),
                        "parameters": self._parse_rust_parameters(match.group(2)),
                        "return_type": match.group(3).strip() if match.group(3) else "()",
                        "language": "rust"
                    }
                    signatures.append(signature)
                except Exception:
                    pass
        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log", f"Rust extraction failed: {e}")

        return signatures

    def _parse_rust_parameters(self, params_str: str) -> List[str]:
        """Parse Rust parameters safely."""
        if not params_str or not params_str.strip():
            return []
        
        parameters = []
        try:
            for param in params_str.split(','):
                param = param.strip()
                if param and param != '&self' and param != 'self':
                    # Rust format: "name: type"
                    if ':' in param:
                        param_name = param.split(':')[0].strip()
                        param_name = param_name.replace('&mut ', '').replace('mut ', '').strip()
                        if param_name.isidentifier():
                            parameters.append(param_name)
        except Exception:
            pass
        
        return parameters[:10]

    # Keep all existing methods unchanged for backward compatibility
    # (All the existing extract_screen_name, extract_component_name, etc. methods remain the same)

    def extract_inheritance_info(self, chunk: str, file_path: str = "", chunk_index: int = 0) -> Dict[str, List[str]]:
        """Extract class inheritance and interface implementation info with enhanced error handling."""
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
                    try:
                        inheritance["extends"].append(match.group(1).strip())
                    except Exception:
                        pass

                implements_pattern = r'implements\s+([^{]+)'
                for match in re.finditer(implements_pattern, chunk):
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

            elif self.ext in ['js', 'ts', 'jsx', 'tsx']:
                # JavaScript/TypeScript inheritance
                extends_pattern = r'class\s+\w+\s+extends\s+(\w+)'
                for match in re.finditer(extends_pattern, chunk):
                    try:
                        inheritance["extends"].append(match.group(1))
                    except Exception:
                        pass

                implements_pattern = r'class\s+\w+.*?implements\s+([^{]+)'
                for match in re.finditer(implements_pattern, chunk):
                    try:
                        inheritance["implements"].extend([i.strip() for i in match.group(1).split(',') if i.strip()])
                    except Exception:
                        pass

        except Exception as e:
            log_to_sublog(self.project_dir, "metadata_extractor.log",
                          f"Error extracting inheritance in {file_path} chunk {chunk_index}: {e}")

        return {k: v for k, v in inheritance.items() if v}

    # Continue with all the other existing methods...
    # (The rest of the methods remain the same as in the original file)

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

        return list({f for f in funcs if isinstance(f, str) and f})[:15]  # Limit results

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

        return list({c for c in classes if isinstance(c, str) and c})[:10]

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
                                token = parts[0]
                                # Normalize to top-level package/module token
                                if '.' in token:
                                    token = token.split('.')[0]
                                deps.add(token)
                    elif "require(" in line:
                        match = re.search(r'require\(["\']([^"\']+)["\']', line)
                        if match:
                            deps.add(match.group(1))
        except Exception:
            pass

        return list(deps)[:15]  # Limit results

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

        return list(inputs)[:10]

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
