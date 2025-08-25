# core/cross_reference_query.py

import os
import json
from typing import Dict, List, Optional
from config import ProjectConfig
from logger import log_to_sublog

class CrossReferenceQuery:
    """
    Fast querying interface for cross-reference data.
    Enables Level 2-4 query capabilities with optimized lookups.
    """

    def __init__(self, project_config: ProjectConfig, project_dir: str = "."):
        self.project_config = project_config
        self.project_dir = project_dir
        self.cross_references = None
        self.symbol_usage_index = None
        self.call_graph_index = None
        self.inheritance_index = None

    def load_cross_references(self) -> bool:
        try:
            db_dir = self.project_config.get_db_dir()
            cross_ref_file = os.path.join(db_dir, "cross_references.json")
            if os.path.exists(cross_ref_file):
                with open(cross_ref_file, 'r', encoding='utf-8') as f:
                    self.cross_references = json.load(f)
            usage_file = os.path.join(db_dir, "symbol_usage_index.json")
            if os.path.exists(usage_file):
                with open(usage_file, 'r', encoding='utf-8') as f:
                    self.symbol_usage_index = json.load(f)
            call_graph_file = os.path.join(db_dir, "call_graph_index.json")
            if os.path.exists(call_graph_file):
                with open(call_graph_file, 'r', encoding='utf-8') as f:
                    self.call_graph_index = json.load(f)
            inheritance_file = os.path.join(db_dir, "inheritance_index.json")
            if os.path.exists(inheritance_file):
                with open(inheritance_file, 'r', encoding='utf-8') as f:
                    self.inheritance_index = json.load(f)
            ok = any([self.cross_references, self.symbol_usage_index, self.call_graph_index, self.inheritance_index])
            log_to_sublog(self.project_dir, "cross_reference_query.log", f"Cross-reference data loaded: {ok}")
            return ok
        except Exception as e:
            log_to_sublog(self.project_dir, "cross_reference_query.log", f"Failed to load cross-reference {e}")
            return False

    def find_api_interactions(self, api_endpoint: str) -> Dict:
        """Level 3: Components interacting with APIEndpoint."""
        if not self.cross_references:
            return {'api_endpoint': api_endpoint, 'interactions': []}
        results = []
        api_usage_map = self.cross_references.get('api_usage', {}) or {}
        try:
            for doc_key, doc_usages in api_usage_map.items():
                if isinstance(doc_usages, list):
                    for usage in doc_usages:
                        if api_endpoint.lower() in str(usage).lower():
                            results.append(usage)
        except Exception:
            pass
        return {'api_endpoint': api_endpoint, 'interactions': results}


    def find_symbol_definition(self, symbol_name: str) -> Optional[Dict]:
        """Level 2: Where is ClassName/MethodName defined?"""
        if not self.cross_references:
            return None
            
        definitions = self.cross_references.get('symbol_definitions', {})
        return definitions.get(symbol_name)

    def count_symbol_usage(self, symbol_name: str) -> Dict:
        """Level 2: How many times is MethodName invoked?"""
        if not self.symbol_usage_index:
            return {'count': 0, 'files': []}
            
        usages = self.symbol_usage_index.get(symbol_name, [])
        files = list(set(usage.get('file', 'unknown') for usage in usages))
        
        return {
            'symbol': symbol_name,
            'count': len(usages),
            'files': files,
            'usages': usages
        }

    def find_import_usage(self, library_name: str) -> Dict:
        """Level 2: Which files import LibraryName and what functionality?"""
        if not self.cross_references:
            return {'files': [], 'usages': []}
            
        import_map = self.cross_references.get('import_usage_map', {})
        return {
            'library': library_name,
            'usage_data': import_map.get(library_name, [])
        }

    def get_method_signature(self, method_name: str) -> Optional[Dict]:
        """Level 2: Input parameters and return types of FunctionName."""
        definition = self.find_symbol_definition(method_name)
        if definition and definition.get('type') == 'method':
            return definition.get('signature', {})
        return None

    def get_inheritance_hierarchy(self, class_name: str) -> Dict:
        """Level 3: Classes inheriting from BaseClassName."""
        if not self.inheritance_index:
            return {'children': [], 'parents': []}
            
        inheritance_tree = self.inheritance_index.get('inheritance_tree', {})
        reverse_tree = self.inheritance_index.get('reverse_inheritance_tree', {})
        
        return {
            'class': class_name,
            'children': inheritance_tree.get(class_name, []),
            'parents': reverse_tree.get(class_name, []),
            'interface_implementations': self._get_interface_implementations(class_name)
        }

    def get_call_hierarchy(self, function_name: str) -> Dict:
        """Level 3: Complete call hierarchy of FunctionName."""
        if not self.call_graph_index:
            return {'calls': [], 'called_by': []}
            
        call_graph = self.call_graph_index.get('call_graph', {})
        reverse_call_graph = self.call_graph_index.get('reverse_call_graph', {})
        
        return {
            'function': function_name,
            'calls': call_graph.get(function_name, []),
            'called_by': reverse_call_graph.get(function_name, []),
            'complete_hierarchy': self._build_complete_call_hierarchy(function_name)
        }


    def get_module_dependencies(self, module_name: str) -> Dict:
        """Level 3: Internal and external dependencies of ModuleName."""
        if not self.cross_references:
            return {'internal': [], 'external': []}
            
        file_deps = self.cross_references.get('file_dependencies', {})
        module_deps = file_deps.get(module_name, [])
        
        # Classify as internal vs external
        internal_deps = []
        external_deps = []
        
        for dep in module_deps:
            if self._is_internal_dependency(dep):
                internal_deps.append(dep)
            else:
                external_deps.append(dep)
        
        return {
            'module': module_name,
            'internal_dependencies': internal_deps,
            'external_dependencies': external_deps
        }

    def analyze_design_patterns(self, class_name: str) -> Dict:
        """Level 4: Design patterns followed by ClassName."""
        if not self.cross_references:
            return {'patterns': []}
            
        pattern_instances = self.cross_references.get('design_pattern_instances', {})
        
        patterns_found = []
        for pattern_name, instances in pattern_instances.items():
            for instance in instances:
                if class_name in instance.get('classes', []):
                    patterns_found.append({
                        'pattern': pattern_name,
                        'instance': instance
                    })
        
        return {
            'class': class_name,
            'patterns': patterns_found
        }

    def _get_interface_implementations(self, class_name: str) -> List:
        """Get interface implementations for a class."""
        if not self.inheritance_index:
            return []
            
        implementations = self.inheritance_index.get('interface_implementations', {})
        result = []
        
        for interface, impls in implementations.items():
            for impl in impls:
                if impl.get('class') == class_name:
                    result.append(interface)
        
        return result

    def _build_complete_call_hierarchy(self, function_name: str, visited: set = None) -> Dict:
        """Build complete call hierarchy recursively."""
        if visited is None:
            visited = set()
            
        if function_name in visited:
            return {'recursive': True}
            
        visited.add(function_name)
        
        if not self.call_graph_index:
            return {}
            
        call_graph = self.call_graph_index.get('call_graph', {})
        calls = call_graph.get(function_name, [])
        
        hierarchy = {}
        for called_func in calls:
            hierarchy[called_func] = self._build_complete_call_hierarchy(called_func, visited.copy())
        
        return hierarchy

    def _is_internal_dependency(self, dependency: str) -> bool:
        """Determine if a dependency is internal to the project."""
        # Simple heuristic: if it's a relative import or matches project structure
        return (dependency.startswith('.') or 
                dependency.startswith('/') or 
                not ('.' in dependency and len(dependency.split('.')) > 2))
