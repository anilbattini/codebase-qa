# core/context_builder.py

from config import ProjectConfig
from langchain.docstore.document import Document
from logger import log_highlight, log_to_sublog
from typing import Dict, List, Optional
import json
import os
import re

class ContextBuilder:
    """
    Builds comprehensive context using hierarchy index, chunk anchors, 
    and cross-reference relationships. Now supports Level 3-4 capabilities.
    🔧 EXTENDED without breaking existing functionality.
    """

    def __init__(self, project_config: ProjectConfig, project_dir: str = "."):
        self.project_config = project_config
        self.project_dir = project_dir
        self.hierarchy_index = None
        
        # 🆕 NEW: Load cross-reference data for advanced context
        self.cross_references = self._load_cross_references()
        
        # 🆕 NEW: Context assembly strategies
        self.strategies = {
            'hierarchical': self._build_hierarchical_context,
            'call_flow': self._build_call_flow_context,
            'inheritance': self._build_inheritance_context,
            'impact': self._build_impact_context
        }

    def load_context_data(self) -> bool:
        """
        🆕 NEW: Load cross-reference and hierarchical data for context assembly.
        Returns True if data loaded successfully, False otherwise.
        """
        try:
            # Load cross-references (Phase 2 data)
            self.cross_references = self._load_cross_references()
            
            # Load hierarchical index (existing data)
            self._load_hierarchy()
            
            # Check if we have any context data available
            has_cross_refs = self.cross_references is not None
            has_hierarchy = self.hierarchy_index is not None
            
            if has_cross_refs:
                log_to_sublog(self.project_dir, "context_builder.log", 
                            "✅ Cross-reference data loaded successfully")
            
            if has_hierarchy:
                log_to_sublog(self.project_dir, "context_builder.log", 
                            "✅ Hierarchical index loaded successfully")
            
            # Return True if we have at least one type of context data
            success = has_cross_refs or has_hierarchy
            
            log_to_sublog(self.project_dir, "context_builder.log", 
                        f"Context data loading result: cross_refs={has_cross_refs}, hierarchy={has_hierarchy}, success={success}")
            
            return success
            
        except Exception as e:
            log_to_sublog(self.project_dir, "context_builder.log", 
                        f"Failed to load context  {e}")
            # Set defaults to ensure class works
            self.cross_references = None
            self.hierarchy_index = None
            return False


    def build_enhanced_context(self, documents: List[Document], query: str, 
                             intent: str = 'general') -> str:
        """
        🔧 EXTENDED: Now supports multi-strategy context assembly.
        Maintains backward compatibility with existing code.
        """
        
        # Phase 1: Always build original hierarchical context for backward compatibility
        original_context = self._build_original_hierarchical_context(documents, query, intent)
        
        # Phase 2: 🆕 NEW: Add advanced context layers if cross-references available
        if self.cross_references:
            try:
                enhanced_context = self._build_enhanced_layered_context(documents, query, intent)
                return self.format_context_for_llm(enhanced_context)
            except Exception as e:
                log_to_sublog(self.project_dir, "context_builder.log", 
                             f"Advanced context assembly failed: {e}")
                # Fallback to original context
                return original_context
        
        # Fallback: Return original context if no cross-references available
        return original_context

    def _build_original_hierarchical_context(self, documents: List[Document], 
                                           query: str, intent: str) -> str:
        """
        🔧 PRESERVED: Original functionality maintained for backward compatibility.
        """
        
        # Load hierarchy data
        self._load_hierarchy()
        
        # Initialize context parts
        context_parts = []
        
        # Extract field and screen for validation queries (existing logic)
        field_name, screen_name = self._extract_field_and_screen(query)
        
        # Build validation snippet if applicable (existing logic)
        if field_name and screen_name:
            validation_snippet = self._build_validation_snippet(field_name, screen_name)
            if validation_snippet:
                context_parts.append("Validation Context:")
                context_parts.append(validation_snippet)
                context_parts.append("")
        
        # Format documents with enhanced context (existing logic)
        context_parts.append("Retrieved Documents:")
        for i, doc in enumerate(documents):
            formatted_doc = self._format_document_with_enhanced_context(doc, self.hierarchy_index)
            context_parts.append(f"Document {i+1}:")
            context_parts.append(formatted_doc)
            context_parts.append("")
        
        return "\n".join(context_parts)

    def _build_enhanced_layered_context(self, documents: List[Document], 
                                      query: str, intent: str) -> Dict:
        """
        🆕 NEW: Build enhanced multi-layered context using cross-references.
        """
        
        # Analyze what symbols are involved
        doc_analysis = self._analyze_documents(documents)
        
        # Select appropriate strategies based on intent
        selected_strategies = self._select_strategies(intent, doc_analysis)
        
        # Build context using selected strategies
        context_layers = {}
        for strategy_name in selected_strategies:
            if strategy_name in self.strategies:
                context_layers[strategy_name] = self.strategies[strategy_name](
                    documents, doc_analysis
                )
        
        # Create structured enhanced context
        return {
            'documents': documents,
            'context_layers': context_layers,
            'ranked_order': self._rank_context_layers(context_layers, intent),
            'total_relevance_score': sum(layer.get('relevance_score', 0.5) for layer in context_layers.values()),
            'metadata': {
                'intent': intent,
                'strategies_used': list(context_layers.keys()),
                'total_documents': len(documents),
                'context_depth': len(context_layers)
            }
        }

    def _load_cross_references(self) -> Optional[Dict]:
        """🆕 NEW: Load cross-reference data from Phase 2."""
        try:
            db_dir = self.project_config.get_db_dir()
            cross_ref_file = os.path.join(db_dir, "cross_references.json")
            if os.path.exists(cross_ref_file):
                with open(cross_ref_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log_to_sublog(self.project_dir, "context_builder.log", 
                         f"Could not load cross-references: {e}")
        return None

    def _analyze_documents(self, documents: List[Document]) -> Dict:
        """🆕 NEW: Analyze documents to extract symbols and metadata."""
        analysis = {'functions': [], 'classes': [], 'files': []}
        
        for doc in documents:
            metadata = getattr(doc, 'metadata', {})
            if isinstance(metadata, dict):
                analysis['functions'].extend(metadata.get('function_names', []))
                analysis['classes'].extend(metadata.get('class_names', []))
                analysis['files'].append(metadata.get('source', ''))
        
        # Remove duplicates
        analysis['functions'] = list(set(analysis['functions']))
        analysis['classes'] = list(set(analysis['classes']))
        analysis['files'] = list(set(filter(None, analysis['files'])))
        
        return analysis

    def _select_strategies(self, intent: str, doc_analysis: Dict) -> List[str]:
        """🆕 NEW: Select appropriate context strategies based on intent."""
        
        # Base strategies for different intents
        strategy_map = {
            'overview': ['hierarchical'],
            'validation': ['hierarchical', 'call_flow'],
            'ui_flow': ['hierarchical', 'call_flow'],
            'impact': ['impact', 'call_flow', 'hierarchical'],
            'inheritance': ['inheritance', 'hierarchical'],
            'call_hierarchy': ['call_flow', 'inheritance'],
            'general': ['hierarchical']
        }
        
        strategies = strategy_map.get(intent, ['hierarchical'])
        
        # Add strategies based on available data
        if len(doc_analysis.get('functions', [])) > 0 and 'call_flow' not in strategies:
            strategies.append('call_flow')
        
        if len(doc_analysis.get('classes', [])) > 0 and 'inheritance' not in strategies:
            strategies.append('inheritance')
        
        return strategies

    def _build_hierarchical_context(self, documents: List[Document], 
                                   doc_analysis: Dict) -> Dict:
        """🆕 NEW: Build hierarchical context layer."""
        
        # Group files by modules
        modules = {}
        for file_path in doc_analysis.get('files', []):
            module = self._extract_module_from_path(file_path)
            if module:
                if module not in modules:
                    modules[module] = []
                modules[module].append(file_path)
        
        return {
            'type': 'hierarchical',
            'modules': modules,
            'relevance_score': 1.0,
            'description': f'Hierarchical structure for {len(modules)} modules'
        }

    def _build_call_flow_context(self, documents: List[Document], 
                                doc_analysis: Dict) -> Dict:
        """🆕 NEW: Build call flow context layer."""
        
        if not self.cross_references:
            return {'type': 'call_flow', 'flows': {}, 'relevance_score': 0.3, 'description': 'Call flow data not available'}
        
        call_flows = {}
        
        for function in doc_analysis.get('functions', []):
            calls = self.cross_references.get('call_graph', {}).get(function, [])
            called_by = self.cross_references.get('reverse_call_graph', {}).get(function, [])
            
            if calls or called_by:
                call_flows[function] = {
                    'calls': calls[:5],  # Limit for readability
                    'called_by': called_by[:5]
                }
        
        return {
            'type': 'call_flow',
            'flows': call_flows,
            'relevance_score': 0.9,
            'description': f'Call relationships for {len(call_flows)} functions'
        }

    def _build_inheritance_context(self, documents: List[Document], 
                                  doc_analysis: Dict) -> Dict:
        """🆕 NEW: Build inheritance context layer."""
        
        if not self.cross_references:
            return {'type': 'inheritance', 'relationships': {}, 'relevance_score': 0.3, 'description': 'Inheritance data not available'}
        
        inheritance_info = {}
        
        for class_name in doc_analysis.get('classes', []):
            children = self.cross_references.get('inheritance_tree', {}).get(class_name, [])
            parents = self.cross_references.get('reverse_inheritance_tree', {}).get(class_name, [])
            
            if children or parents:
                inheritance_info[class_name] = {
                    'children': children,
                    'parents': parents
                }
        
        return {
            'type': 'inheritance',
            'relationships': inheritance_info,
            'relevance_score': 0.85,
            'description': f'Inheritance relationships for {len(inheritance_info)} classes'
        }

    def _build_impact_context(self, documents: List[Document], 
                             doc_analysis: Dict) -> Dict:
        """🆕 NEW: Build impact analysis context layer."""
        
        if not self.cross_references:
            return {'type': 'impact', 'impact_analysis': {}, 'relevance_score': 0.3, 'description': 'Impact analysis data not available'}
        
        impact_analysis = {
            'direct_impacts': [],
            'indirect_impacts': [],
            'affected_modules': set()
        }
        
        # Analyze potential impacts for each symbol
        for symbol in doc_analysis.get('functions', []) + doc_analysis.get('classes', []):
            # Direct impacts - things that directly use this symbol
            direct_usages = self.cross_references.get('symbol_usages', {}).get(symbol, [])
            for usage in direct_usages[:5]:  # Limit to top 5
                impact_analysis['direct_impacts'].append({
                    'symbol': symbol,
                    'impacted_file': usage.get('file'),
                    'usage_context': usage.get('context', '')[:100]  # Truncate
                })
                
                # Track affected modules
                module = self._extract_module_from_path(usage.get('file', ''))
                if module:
                    impact_analysis['affected_modules'].add(module)
        
        impact_analysis['affected_modules'] = list(impact_analysis['affected_modules'])
        
        return {
            'type': 'impact',
            'impact_analysis': impact_analysis,
            'relevance_score': 0.95,
            'description': f'Impact analysis: {len(impact_analysis["direct_impacts"])} direct impacts'
        }

    def _rank_context_layers(self, layers: Dict, intent: str) -> List[Dict]:
        """🆕 NEW: Rank context layers by relevance to query intent."""
        
        intent_weights = {
            'call_hierarchy': {'call_flow': 1.2, 'inheritance': 0.9},
            'impact': {'impact': 1.3, 'call_flow': 1.1},
            'inheritance': {'inheritance': 1.2, 'call_flow': 0.9},
        }
        
        ranked = []
        for layer_name, layer_data in layers.items():
            base_score = layer_data.get('relevance_score', 0.5)
            weight = intent_weights.get(intent, {}).get(layer_name, 1.0)
            final_score = base_score * weight
            
            ranked.append({
                'layer': layer_name,
                'score': final_score,
                'description': layer_data.get('description', '')
            })
        
        return sorted(ranked, key=lambda x: x['score'], reverse=True)

    def format_context_for_llm(self, enhanced_context) -> str:
        """
        🆕 NEW: Format enhanced multi-layered context for LLM consumption.
        Handles both string and dict formats for backward compatibility.
        """
        
        # Backward compatibility: if it's already a string, return as-is
        if isinstance(enhanced_context, str):
            return enhanced_context
        
        # If it's not a dict, convert to string
        if not isinstance(enhanced_context, dict):
            return str(enhanced_context)
        
        parts = []
        metadata = enhanced_context.get('metadata', {})
        
        # Context summary header
        parts.append("=== CONTEXT ANALYSIS ===")
        parts.append(f"Query Intent: {metadata.get('intent', 'general')}")
        parts.append(f"Context Layers: {len(enhanced_context.get('context_layers', {}))}")
        parts.append("")
        
        # Add each context layer in ranked order
        ranked_order = enhanced_context.get('ranked_order', [])
        for layer_info in ranked_order:
            layer_name = layer_info.get('layer', 'unknown')
            score = layer_info.get('score', 0)
            layer_data = enhanced_context.get('context_layers', {}).get(layer_name, {})
            
            parts.append(f"=== {layer_name.upper()} CONTEXT (Score: {score:.2f}) ===")
            parts.append(layer_data.get('description', 'No description available'))
            
            # Add layer-specific formatting
            if layer_name == 'call_flow':
                flows = layer_data.get('flows', {})
                for function, flow_info in flows.items():
                    parts.append(f"📞 Function: {function}")
                    if flow_info.get('calls'):
                        parts.append(f"  ➡️  Calls: {', '.join(flow_info['calls'])}")
                    if flow_info.get('called_by'):
                        parts.append(f"  ⬅️  Called by: {', '.join(flow_info['called_by'])}")
            
            elif layer_name == 'inheritance':
                relationships = layer_data.get('relationships', {})
                for class_name, info in relationships.items():
                    parts.append(f"🏗️  Class: {class_name}")
                    if info.get('parents'):
                        parts.append(f"  ⬆️  Inherits from: {', '.join(info['parents'])}")
                    if info.get('children'):
                        parts.append(f"  ⬇️  Extended by: {', '.join(info['children'])}")
            
            elif layer_name == 'impact':
                impact_data = layer_data.get('impact_analysis', {})
                direct_impacts = impact_data.get('direct_impacts', [])
                if direct_impacts:
                    parts.append(f"🎯 Direct Impacts:")
                    for impact in direct_impacts[:3]:  # Show top 3
                        parts.append(f"  • {impact.get('impacted_file', 'unknown')} uses {impact.get('symbol', 'unknown')}")
            
            elif layer_name == 'hierarchical':
                modules = layer_data.get('modules', {})
                if modules:
                    parts.append(f"📁 Module Structure:")
                    for module, files in list(modules.items())[:3]:  # Show top 3 modules
                        parts.append(f"  • {module}: {len(files)} files")
            
            parts.append("")
        
        # Add document content section
        documents = enhanced_context.get('documents', [])
        if documents:
            parts.append("=== RELEVANT CODE CHUNKS ===")
            for i, doc in enumerate(documents[:3]):  # Limit to top 3 documents
                metadata = getattr(doc, 'metadata', {})
                if isinstance(metadata, dict):
                    source = metadata.get('source', 'unknown')
                    parts.append(f"📄 Document {i+1}: {source}")
                    
                    # Add content snippet (first 150 chars)
                    content = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    parts.append(f"Content: {content}")
                parts.append("")
        
        return "\n".join(parts)

    def _extract_module_from_path(self, file_path: str) -> Optional[str]:
        """🆕 NEW: Extract module/package name from file path."""
        if not file_path:
            return None
            
        # Remove file extension and normalize path
        path_parts = file_path.replace('\\', '/').split('/')
        
        # Look for common module indicators
        for i, part in enumerate(path_parts):
            if part in ['src', 'main', 'java', 'kotlin', 'app']:
                if i + 1 < len(path_parts):
                    return path_parts[i + 1]
        
        # Fallback: use parent directory
        if len(path_parts) >= 2:
            return path_parts[-2]
        
        return None

    # 🔧 PRESERVE: Keep all existing methods unchanged for backward compatibility
    
    def _load_hierarchy(self):
        """🔧 PRESERVED: Existing method - unchanged."""
        try:
            hierarchy_file = self.project_config.get_hierarchy_file()
            if os.path.exists(hierarchy_file):
                with open(hierarchy_file, 'r', encoding='utf-8') as f:
                    self.hierarchy_index = json.load(f)
        except Exception as e:
            log_to_sublog(self.project_dir, "context_builder.log", 
                         f"Could not load hierarchy: {e}")
            self.hierarchy_index = None

    def _extract_field_and_screen(self, query: str) -> tuple:
        """🔧 PRESERVED: Existing method - unchanged."""
        field_match = re.search(r'\b(\w+)\s+field\b', query.lower())
        screen_match = re.search(r'\b(\w+)\s+screen\b', query.lower())
        
        field_name = field_match.group(1) if field_match else None
        screen_name = screen_match.group(1) if screen_match else None
        
        return field_name, screen_name

    def _build_validation_snippet(self, field_name: str, screen_name: str) -> Optional[str]:
        """🔧 PRESERVED: Existing method - unchanged."""
        if not self.hierarchy_index:
            return None
        
        screen_input_map = self.hierarchy_index.get('screen_input_validation_map', {})
        if screen_name in screen_input_map:
            screen_data = screen_input_map[screen_name]
            if field_name in screen_data.get('input_fields', {}):
                field_data = screen_data['input_fields'][field_name]
                return f"Field '{field_name}' in '{screen_name}' screen: {field_data}"
        
        return None

    def _format_document_with_enhanced_context(self, doc, hierarchy_context) -> str:
        """🔧 PRESERVED: Existing method - unchanged."""
        metadata = getattr(doc, 'metadata', {})
        if not isinstance(metadata, dict):
            return doc.page_content
        
        source = metadata.get('source', 'Unknown')
        class_names = metadata.get('class_names', [])
        function_names = metadata.get('function_names', [])
        
        formatted_parts = [f"Source: {source}"]
        
        if class_names:
            formatted_parts.append(f"Classes: {', '.join(class_names[:3])}")
        
        if function_names:
            formatted_parts.append(f"Functions: {', '.join(function_names[:3])}")
        
        formatted_parts.append(f"Content: {doc.page_content}")
        
        return "\n".join(formatted_parts)
