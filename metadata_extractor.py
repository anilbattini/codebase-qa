# metadata_extractor.py

import os
import re
from typing import Dict, List, Any, Optional
from config import ProjectConfig

class MetadataExtractor:
    """Enhanced metadata extraction for better context building."""
    
    def __init__(self, project_config: ProjectConfig):
        self.project_config = project_config
        
    def create_enhanced_metadata(self, chunk: str, path: str, chunk_index: int) -> Dict[str, Any]:
        """Create comprehensive metadata for better retrieval."""
        ext = os.path.splitext(path)[1]
        
        # Calculate complexity metrics
        complexity = self._calculate_complexity(chunk)
        
        # Extract imports/dependencies
        dependencies = self._extract_all_dependencies(chunk, ext)
        
        # Extract API endpoints, database queries, etc.
        apis = self._extract_api_endpoints(chunk)
        db_operations = self._extract_db_operations(chunk)
        
        # Extract UI elements for mobile/web projects
        ui_elements = self._extract_ui_elements(chunk)
        
        return {
            "source": path,
            "chunk_index": chunk_index,
            "file_type": ext,
            "complexity_score": complexity,
            "dependencies": dependencies,
            "api_endpoints": apis,
            "db_operations": db_operations,
            "ui_elements": ui_elements,
            "business_logic_indicators": self._identify_business_logic(chunk),
            "validation_rules": self._extract_validations(chunk),
            "screen_references": self._extract_screen_references(chunk),
            "estimated_tokens": len(chunk.split()),
            "project_type": self.project_config.project_type,
            "chunk_hierarchy": self._determine_hierarchy_level(chunk),
            "function_names": self._extract_function_names(chunk, ext),
            "class_names": self._extract_class_names(chunk, ext),
        }
    
    def _calculate_complexity(self, chunk: str) -> int:
        """Calculate code complexity score."""
        complexity = 0
        
        # Cyclomatic complexity indicators
        decision_keywords = ['if', 'else', 'elif', 'while', 'for', 'switch', 'case', 'catch', 'try']
        for keyword in decision_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', chunk, re.IGNORECASE))
        
        # Nesting level (approximate)
        lines = chunk.split('\n')
        max_indent = 0
        for line in lines:
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent // 4)  # Assuming 4-space indentation
        
        complexity += max_indent
        
        return min(complexity, 20)  # Cap at 20
    
    def _extract_all_dependencies(self, chunk: str, ext: str) -> List[str]:
        """Extract all types of dependencies from code."""
        dependencies = []
        
        # Import patterns by language
        patterns = {
            '.py': [r'import\s+(\w+)', r'from\s+(\w+)', r'@(\w+)'],
            '.js': [r'import.*from\s+["\']([^"\']+)["\']', r'require\(["\']([^"\']+)["\']'],
            '.ts': [r'import.*from\s+["\']([^"\']+)["\']', r'import\s+["\']([^"\']+)["\']'],
            '.kt': [r'import\s+([\w.]+)', r'@(\w+)'],
            '.java': [r'import\s+([\w.]+)', r'@(\w+)'],
        }
        
        if ext in patterns:
            for pattern in patterns[ext]:
                matches = re.findall(pattern, chunk, re.IGNORECASE)
                dependencies.extend(matches)
        
        return list(set(dependencies))  # Remove duplicates
    
    def _extract_api_endpoints(self, chunk: str) -> List[str]:
        """Extract API endpoints and routes."""
        endpoints = []
        
        # Common API patterns
        patterns = [
            r'@(?:Get|Post|Put|Delete|Patch)\s*\(["\']([^"\']+)["\']',  # Annotations
            r'app\.(?:get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']',  # Express.js
            r'@app\.route\s*\(["\']([^"\']+)["\']',  # Flask
            r'path\s*\(["\']([^"\']+)["\']',  # Django URLs
            r'Route\s*\(["\']([^"\']+)["\']',  # Laravel/ASP.NET
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, chunk, re.IGNORECASE)
            endpoints.extend(matches)
        
        return endpoints
    
    def _extract_db_operations(self, chunk: str) -> List[str]:
        """Extract database operations."""
        operations = []
        
        # Database operation patterns
        db_patterns = [
            r'SELECT\s+.*FROM\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'UPDATE\s+(\w+)\s+SET',
            r'DELETE\s+FROM\s+(\w+)',
            r'\.save\(\)',
            r'\.create\(\)',
            r'\.update\(\)',
            r'\.delete\(\)',
            r'\.find\w*\(',
            r'\.query\(',
        ]
        
        for pattern in db_patterns:
            if re.search(pattern, chunk, re.IGNORECASE):
                match = re.search(pattern, chunk, re.IGNORECASE)
                if match and match.groups():
                    operations.append(match.group(1))
                else:
                    operations.append(pattern.replace('\\', '').replace('()', ''))
        
        return list(set(operations))
    
    def _extract_ui_elements(self, chunk: str) -> List[str]:
        """Extract UI elements and screen components."""
        ui_elements = []
        
        # UI element patterns
        ui_patterns = [
            r'findViewById\s*\(\s*R\.id\.(\w+)',  # Android
            r'@\+id/(\w+)',  # Android XML
            r'android:id="@\+id/(\w+)"',  # Android XML
            r'<(\w+).*id=["\']([^"\']+)["\']',  # HTML/XML
            r'className=["\']([^"\']+)["\']',  # React
            r'class=["\']([^"\']+)["\']',  # HTML
            r'#(\w+)',  # CSS ID selectors
            r'\.(\w+)',  # CSS class selectors
        ]
        
        for pattern in ui_patterns:
            matches = re.findall(pattern, chunk, re.IGNORECASE)
            if isinstance(matches[0], tuple) if matches else False:
                ui_elements.extend([match[1] if len(match) > 1 else match[0] for match in matches])
            else:
                ui_elements.extend(matches)
        
        return list(set(ui_elements))
    
    def _identify_business_logic(self, chunk: str) -> List[str]:
        """Identify business logic patterns in code chunks."""
        business_indicators = []
        
        # Common business logic patterns
        patterns = {
            "validation": r"(?:validate|check|verify|ensure)[\w_]*\s*\(",
            "calculation": r"(?:calculate|compute|sum|total|amount|price|cost)[\w_]*\s*\(",
            "workflow": r"(?:process|handle|execute|perform|workflow)[\w_]*\s*\(",
            "decision": r"if\s+.*(?:status|state|condition|flag|approved|valid)",
            "data_transformation": r"(?:transform|convert|map|format|serialize)[\w_]*\s*\(",
            "authentication": r"(?:login|auth|token|password|credential)[\w_]*",
            "authorization": r"(?:permission|role|access|authorize)[\w_]*",
            "payment": r"(?:pay|charge|bill|invoice|transaction)[\w_]*",
            "notification": r"(?:notify|alert|email|sms|push)[\w_]*",
        }
        
        for category, pattern in patterns.items():
            if re.search(pattern, chunk, re.IGNORECASE):
                business_indicators.append(category)
        
        return business_indicators
    
    def _extract_validations(self, chunk: str) -> List[str]:
        """Extract validation rules and constraints."""
        validations = []
        
        validation_patterns = [
            r'required\s*[:=]\s*true',
            r'minLength\s*[:=]\s*(\d+)',
            r'maxLength\s*[:=]\s*(\d+)',
            r'pattern\s*[:=]\s*["\']([^"\']+)["\']',
            r'@NotNull',
            r'@NotEmpty',
            r'@Valid',
            r'@Min\((\d+)\)',
            r'@Max\((\d+)\)',
            r'@Email',
            r'@Size\(',
            r'\.required\(\)',
            r'\.email\(\)',
            r'\.min\((\d+)\)',
            r'\.max\((\d+)\)',
        ]
        
        for pattern in validation_patterns:
            matches = re.findall(pattern, chunk, re.IGNORECASE)
            if matches:
                validations.extend(matches if isinstance(matches[0], str) else [str(m) for m in matches])
        
        return validations
    
    def _extract_screen_references(self, chunk: str) -> List[str]:
        """Extract screen/page references."""
        screens = []
        
        screen_patterns = [
            r'navigate(?:To)?\s*\(\s*["\']([^"\']+)["\']',  # Navigation calls
            r'startActivity\s*\(\s*.*\.class',  # Android activities
            r'Fragment\s*\(\s*["\']([^"\']+)["\']',  # Fragment references
            r'@Route\s*\(["\']([^"\']+)["\']',  # Route annotations
            r'router\s*\.\s*push\s*\(["\']([^"\']+)["\']',  # Router push
            r'href\s*=\s*["\']([^"\']+)["\']',  # HTML links
        ]
        
        for pattern in screen_patterns:
            matches = re.findall(pattern, chunk, re.IGNORECASE)
            screens.extend(matches)
        
        return screens
    
    def _determine_hierarchy_level(self, chunk: str) -> str:
        """Determine the hierarchical level of the code chunk."""
        chunk_lower = chunk.lower().strip()
        
        if any(chunk_lower.startswith(keyword) for keyword in ['package ', 'module ', 'namespace ']):
            return 'module'
        elif any(keyword in chunk_lower for keyword in ['class ', 'interface ', 'enum ']):
            return 'class'
        elif any(keyword in chunk_lower for keyword in ['function ', 'def ', 'fun ', 'method ']):
            return 'function'
        elif any(keyword in chunk_lower for keyword in ['var ', 'let ', 'const ', 'val ']):
            return 'variable'
        else:
            return 'code_block'
    
    def _extract_function_names(self, chunk: str, ext: str) -> List[str]:
        """Extract function names from code."""
        functions = []
        
        patterns = {
            '.py': [r'def\s+(\w+)\s*\('],
            '.js': [r'function\s+(\w+)\s*\(', r'const\s+(\w+)\s*=\s*\(', r'(\w+)\s*:\s*function'],
            '.ts': [r'function\s+(\w+)\s*\(', r'const\s+(\w+)\s*=\s*\(', r'(\w+)\s*\([^)]*\)\s*:\s*\w+\s*{'],
            '.kt': [r'fun\s+(\w+)\s*\('],
            '.java': [r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\('],
        }
        
        if ext in patterns:
            for pattern in patterns[ext]:
                matches = re.findall(pattern, chunk)
                functions.extend(matches)
        
        return functions
    
    def _extract_class_names(self, chunk: str, ext: str) -> List[str]:
        """Extract class names from code."""
        classes = []
        
        patterns = [
            r'class\s+(\w+)',
            r'interface\s+(\w+)',
            r'enum\s+(\w+)',
            r'object\s+(\w+)',  # Kotlin
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, chunk, re.IGNORECASE)
            classes.extend(matches)
        
        return classes
