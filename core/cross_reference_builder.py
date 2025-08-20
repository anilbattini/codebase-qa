# core/cross_reference_builder.py

import os
import json
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from langchain.docstore.document import Document

from config import ProjectConfig
from logger import log_highlight, log_to_sublog

class CrossReferenceBuilder:
    """
    Builds comprehensive cross-reference maps for Level 2-4 query capabilities.
    Creates usage maps, call graphs, dependency chains, and invocation counts.
    🔧 FIXED: Safe handling of unhashable types (lists, dicts) in sets.
    """

    def __init__(self, project_config: ProjectConfig, project_dir: str = "."):
        self.project_config = project_config
        self.project_dir = project_dir
        
        # Core reference data structures
        self.symbol_definitions = {}      # symbol_name -> {file, line, type, signature}
        self.symbol_usages = defaultdict(list)  # symbol_name -> [{file, line, context}]
        self.file_dependencies = defaultdict(set)  # file -> {dependencies}
        self.call_graph = defaultdict(set)  # function -> {called_functions}
        self.reverse_call_graph = defaultdict(set)  # function -> {caller_functions}
        self.inheritance_tree = defaultdict(set)  # class -> {child_classes}
        self.reverse_inheritance_tree = defaultdict(set)  # class -> {parent_classes}
        self.method_overrides = defaultdict(list)  # base_method -> [override_info]
        self.interface_implementations = defaultdict(list)  # interface -> [implementing_classes]
        self.import_usage_map = defaultdict(list)  # import -> [usage_contexts]
        self.design_pattern_instances = defaultdict(list)  # pattern -> [instances]

    def _safe_add_to_set(self, target_set: set, item):
        """🔧 FIX: Safely add item to set, handling unhashable types."""
        try:
            target_set.add(item)
        except TypeError as e:
            # Handle unhashable types
            if isinstance(item, list):
                target_set.add(tuple(item))
            elif isinstance(item, dict):
                target_set.add(tuple(sorted(item.items())))
            elif isinstance(item, set):
                target_set.add(tuple(sorted(item)))
            else:
                target_set.add(str(item))
            
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         f"Converted unhashable type {type(item)} to hashable: {item}")

    def build_cross_references(self, documents: List[Document]) -> Dict:
        """
        Build comprehensive cross-reference maps from enhanced document metadata.
        Returns structured reference data for Level 2-4 queries.
        """
        log_highlight("CrossReferenceBuilder.build_cross_references")
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     "=== BUILDING CROSS-REFERENCES ===")
        
        total_docs = len(documents)
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     f"Processing {total_docs} documents for cross-references")

        try:
            # Phase 1: Extract all symbol definitions
            self._extract_symbol_definitions(documents)
            
            # Phase 2: Build usage maps and call relationships
            self._build_usage_maps(documents)
            
            # Phase 3: Build inheritance relationships
            self._build_inheritance_relationships(documents)
            
            # Phase 4: Build import usage patterns
            self._build_import_usage_patterns(documents)
            
            # Phase 5: Detect design pattern instances
            self._detect_design_pattern_instances(documents)
            
            # Phase 6: Generate cross-reference statistics
            stats = self._generate_statistics()
            
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         "=== CROSS-REFERENCE BUILD COMPLETE ===")
            
            return self._serialize_references()
            
        except Exception as e:
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         f"ERROR: Cross-reference build failed: {e}")
            import traceback
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         f"Traceback: {traceback.format_exc()}")
            raise

    def _extract_symbol_definitions(self, documents: List[Document]):
        """Extract all symbol definitions from method signatures and metadata."""
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     "Phase 1: Extracting symbol definitions...")
        
        for doc in documents:
            try:
                metadata = getattr(doc, 'metadata', {})
                if not isinstance(metadata, dict):
                    continue
                    
                source_file = metadata.get('source', 'unknown')
                
                # Extract method definitions
                method_signatures = metadata.get('method_signatures', [])
                if isinstance(method_signatures, list):
                    for method_sig in method_signatures:
                        if isinstance(method_sig, dict):
                            method_name = method_sig.get('name')
                            if method_name and isinstance(method_name, str):
                                self.symbol_definitions[method_name] = {
                                    'file': source_file,
                                    'type': 'method',
                                    'signature': method_sig,
                                    'parameters': method_sig.get('parameters', []),
                                    'return_type': method_sig.get('return_type', 'unknown'),
                                    'line_number': method_sig.get('line_number')
                                }
                
                # Extract class definitions
                class_names = metadata.get('class_names', [])
                if isinstance(class_names, list):
                    for class_name in class_names:
                        if class_name and isinstance(class_name, str):
                            self.symbol_definitions[class_name] = {
                                'file': source_file,
                                'type': 'class',
                                'inheritance': metadata.get('inheritance_info', {}),
                                'methods': [sig.get('name') for sig in method_signatures if isinstance(sig, dict) and sig.get('name')]
                            }
                            
            except Exception as e:
                log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                             f"Error extracting symbols from document: {e}")
                continue
        
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     f"Extracted {len(self.symbol_definitions)} symbol definitions")

    def _build_usage_maps(self, documents: List[Document]):
        """Build comprehensive usage maps and call relationships."""
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     "Phase 2: Building usage maps and call relationships...")
        
        for doc in documents:
            try:
                metadata = getattr(doc, 'metadata', {})
                if not isinstance(metadata, dict):
                    continue
                    
                source_file = metadata.get('source', 'unknown')
                
                # Build call graph from call sites
                call_sites = metadata.get('call_sites', [])
                method_signatures = metadata.get('method_signatures', [])
                
                if isinstance(call_sites, list):
                    for call_site in call_sites:
                        if isinstance(call_site, dict):
                            called_function = call_site.get('called_function')
                            context = call_site.get('line_context', '')
                            
                            if called_function and isinstance(called_function, str):
                                # Record usage
                                self.symbol_usages[called_function].append({
                                    'file': source_file,
                                    'context': context,
                                    'chunk_index': metadata.get('chunk_index', 0)
                                })
                                
                                # Build call graph (caller -> called)
                                if isinstance(method_signatures, list):
                                    for method in method_signatures:
                                        if isinstance(method, dict):
                                            caller = method.get('name')
                                            if caller and isinstance(caller, str) and caller != called_function:
                                                # 🔧 FIX: Use safe add method
                                                self._safe_add_to_set(self.call_graph[caller], called_function)
                                                self._safe_add_to_set(self.reverse_call_graph[called_function], caller)
                
                # Build file dependencies
                dependencies = metadata.get('dependencies', [])
                if isinstance(dependencies, list):
                    for dep in dependencies:
                        if dep and isinstance(dep, str):
                            # 🔧 FIX: Use safe add method
                            self._safe_add_to_set(self.file_dependencies[source_file], dep)
                            
            except Exception as e:
                log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                             f"Error building usage maps from document: {e}")
                continue
        
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     f"Built usage maps for {len(self.symbol_usages)} symbols")
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     f"Built call graph with {len(self.call_graph)} caller nodes")

    def _build_inheritance_relationships(self, documents: List[Document]):
        """Build inheritance and interface implementation relationships."""
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     "Phase 3: Building inheritance relationships...")
        
        for doc in documents:
            try:
                metadata = getattr(doc, 'metadata', {})
                if not isinstance(metadata, dict):
                    continue
                    
                source_file = metadata.get('source', 'unknown')
                inheritance_info = metadata.get('inheritance_info', {})
                class_names = metadata.get('class_names', [])
                
                # Build inheritance tree
                if isinstance(inheritance_info, dict):
                    extends = inheritance_info.get('extends', [])
                    implements = inheritance_info.get('implements', [])
                    inherits_from = inheritance_info.get('inherits_from', [])
                    
                    # Ensure these are lists
                    if not isinstance(extends, list): extends = [extends] if extends else []
                    if not isinstance(implements, list): implements = [implements] if implements else []
                    if not isinstance(inherits_from, list): inherits_from = [inherits_from] if inherits_from else []
                    
                    if isinstance(class_names, list):
                        for class_name in class_names:
                            if class_name and isinstance(class_name, str):
                                # Handle extends/inherits relationships
                                for parent in extends + inherits_from:
                                    if parent and isinstance(parent, str):
                                        # 🔧 FIX: Use safe add method
                                        self._safe_add_to_set(self.inheritance_tree[parent], class_name)
                                        self._safe_add_to_set(self.reverse_inheritance_tree[class_name], parent)
                                
                                # Handle interface implementations
                                for interface in implements:
                                    if interface and isinstance(interface, str):
                                        self.interface_implementations[interface].append({
                                            'class': class_name,
                                            'file': source_file
                                        })
                                        
            except Exception as e:
                log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                             f"Error building inheritance relationships from document: {e}")
                continue
        
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     f"Built inheritance relationships for {len(self.inheritance_tree)} classes")

    def _build_import_usage_patterns(self, documents: List[Document]):
        """Build import to usage mapping for library usage analysis."""
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     "Phase 4: Building import usage patterns...")
        
        for doc in documents:
            try:
                metadata = getattr(doc, 'metadata', {})
                if not isinstance(metadata, dict):
                    continue
                    
                source_file = metadata.get('source', 'unknown')
                dependencies = metadata.get('dependencies', [])
                call_sites = metadata.get('call_sites', [])
                api_usage = metadata.get('api_usage', [])
                
                if isinstance(dependencies, list):
                    for dependency in dependencies:
                        if dependency and isinstance(dependency, str):
                            usage_contexts = []
                            
                            # Find calls that might be using this import
                            if isinstance(call_sites, list):
                                for call_site in call_sites:
                                    if isinstance(call_site, dict):
                                        called_function = call_site.get('called_function', '')
                                        if isinstance(called_function, str) and dependency.lower() in called_function.lower():
                                            usage_contexts.append(call_site.get('line_context', ''))
                            
                            # Add API usage patterns
                            if isinstance(api_usage, list):
                                for api in api_usage:
                                    if isinstance(api, dict) and api.get('type') and dependency.lower() in str(api).lower():
                                        usage_contexts.append(api.get('pattern', ''))
                            
                            if usage_contexts:
                                self.import_usage_map[dependency].append({
                                    'file': source_file,
                                    'usages': usage_contexts
                                })
                                
            except Exception as e:
                log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                             f"Error building import usage patterns from document: {e}")
                continue
        
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     f"Mapped usage patterns for {len(self.import_usage_map)} imports")

    def _detect_design_pattern_instances(self, documents: List[Document]):
        """Detect and catalog design pattern instances."""
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     "Phase 5: Detecting design pattern instances...")
        
        for doc in documents:
            try:
                metadata = getattr(doc, 'metadata', {})
                if not isinstance(metadata, dict):
                    continue
                    
                source_file = metadata.get('source', 'unknown')
                design_patterns = metadata.get('design_patterns', [])
                class_names = metadata.get('class_names', [])
                method_signatures = metadata.get('method_signatures', [])
                
                if isinstance(design_patterns, list):
                    for pattern in design_patterns:
                        if pattern and isinstance(pattern, str):
                            pattern_instance = {
                                'file': source_file,
                                'classes': class_names if isinstance(class_names, list) else [],
                                'methods': [sig.get('name') for sig in method_signatures 
                                          if isinstance(sig, dict) and sig.get('name')] if isinstance(method_signatures, list) else [],
                                'chunk_index': metadata.get('chunk_index', 0)
                            }
                            self.design_pattern_instances[pattern].append(pattern_instance)
                            
            except Exception as e:
                log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                             f"Error detecting design patterns from document: {e}")
                continue
        
        total_patterns = sum(len(instances) for instances in self.design_pattern_instances.values())
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     f"Detected {total_patterns} design pattern instances across {len(self.design_pattern_instances)} pattern types")

    def _generate_statistics(self) -> Dict:
        """Generate comprehensive statistics about the cross-references."""
        stats = {
            'total_symbols': len(self.symbol_definitions),
            'total_usages': sum(len(usages) for usages in self.symbol_usages.values()),
            'total_files_with_dependencies': len(self.file_dependencies),
            'total_call_relationships': sum(len(callees) for callees in self.call_graph.values()),
            'total_inheritance_relationships': len(self.inheritance_tree),
            'total_interface_implementations': sum(len(impls) for impls in self.interface_implementations.values()),
            'total_imports_tracked': len(self.import_usage_map),
            'total_design_patterns': len(self.design_pattern_instances)
        }
        
        log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                     f"=== CROSS-REFERENCE STATISTICS ===")
        for key, value in stats.items():
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         f"{key}: {value}")
        
        return stats

    def _serialize_references(self) -> Dict:
        """Serialize all cross-reference data for storage and querying."""
        return {
            'symbol_definitions': self.symbol_definitions,
            'symbol_usages': {k: list(v) for k, v in self.symbol_usages.items()},
            'file_dependencies': {k: list(v) for k, v in self.file_dependencies.items()},
            'call_graph': {k: list(v) for k, v in self.call_graph.items()},
            'reverse_call_graph': {k: list(v) for k, v in self.reverse_call_graph.items()},
            'inheritance_tree': {k: list(v) for k, v in self.inheritance_tree.items()},
            'reverse_inheritance_tree': {k: list(v) for k, v in self.reverse_inheritance_tree.items()},
            'interface_implementations': dict(self.interface_implementations),
            'import_usage_map': dict(self.import_usage_map),
            'design_pattern_instances': dict(self.design_pattern_instances),
            'statistics': self._generate_statistics()
        }

    def save_cross_references(self, cross_references: Dict):
        """Save cross-reference data to structured files."""
        try:
            output_dir = self.project_config.get_db_dir()
            
            # Main cross-reference file
            cross_ref_file = os.path.join(output_dir, "cross_references.json")
            with open(cross_ref_file, 'w', encoding='utf-8') as f:
                json.dump(cross_references, f, indent=2, ensure_ascii=False)
            
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         f"Saved cross-references to: {cross_ref_file}")
            
            # Separate quick-lookup files for performance
            self._save_quick_lookup_files(cross_references, output_dir)
            
        except Exception as e:
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         f"Error saving cross-references: {e}")
            import traceback
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         f"Traceback: {traceback.format_exc()}")

    def _save_quick_lookup_files(self, cross_references: Dict, output_dir: str):
        """Save separate quick-lookup files for common queries."""
        try:
            # Symbol usage lookup (for "where is X used" queries)
            usage_file = os.path.join(output_dir, "symbol_usage_index.json")
            with open(usage_file, 'w', encoding='utf-8') as f:
                json.dump(cross_references['symbol_usages'], f, indent=2)
            
            # Call graph lookup (for call hierarchy queries)
            call_graph_file = os.path.join(output_dir, "call_graph_index.json")
            with open(call_graph_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'call_graph': cross_references['call_graph'],
                    'reverse_call_graph': cross_references['reverse_call_graph']
                }, f, indent=2)
            
            # Inheritance lookup (for inheritance queries)
            inheritance_file = os.path.join(output_dir, "inheritance_index.json")
            with open(inheritance_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'inheritance_tree': cross_references['inheritance_tree'],
                    'reverse_inheritance_tree': cross_references['reverse_inheritance_tree'],
                    'interface_implementations': cross_references['interface_implementations']
                }, f, indent=2)
            
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         "Created quick-lookup index files for fast querying")
                         
        except Exception as e:
            log_to_sublog(self.project_dir, "cross_reference_builder.log", 
                         f"Error saving quick-lookup files: {e}")
