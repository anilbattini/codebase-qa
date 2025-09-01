# core/context_builder.py

from config.config import ProjectConfig
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
    🔧 ENHANCED: Removed artificial truncations for full content access.
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
        
    
    def create_full_context(self, docs: List) -> str:
        """
        Create full context from retrieved documents WITHOUT truncation.
        🔧 FIX: Provides complete document content to LLM.
        """
        if not docs:
            return "No relevant context found for this query."
        
        context_parts = []
        total_chars = 0
        max_total_context = 8000  # Reasonable limit for LLM context window
        
        # Log the actual context being sent
        log_to_sublog(self.project_dir, "preparing_full_context.log", 
                        f"\n\nLooping through retrieved docs and logging context and metadata.")
            
        for i, doc in enumerate(docs, 1):
            # Extract full content safely
            content = getattr(doc, 'page_content', '') or str(doc)
            metadata = getattr(doc, 'metadata', {})
            
            # Log the actual context being sent
            log_to_sublog(self.project_dir, "preparing_full_context.log", 
                        f"\n\nIteration{i}: Content:\n {content} \n\nMetadata:\n {metadata}")
            
            # Get source information
            source = metadata.get('source', 'unknown')
            chunk_info = metadata.get('chunk_index', f'chunk_{i}')
            
            # Use FULL content, not truncated
            if content and len(content.strip()) > 0:
                formatted_section = (
                    f"📄 Document {i}: {source}\n"
                    f"{content}\n"
                    f"{'─' * 50}\n"
                )
                
                # Only limit total context if it becomes excessive
                if total_chars + len(formatted_section) < max_total_context:
                    context_parts.append(formatted_section)
                    total_chars += len(formatted_section)
                else:
                    # If we hit limit, at least include a meaningful portion
                    remaining_space = max_total_context - total_chars - 200
                    if remaining_space > 500:  # Only if we have meaningful space left
                        truncated_content = content[:remaining_space] + f"\n[Content truncated - {len(content)} total chars]"
                        formatted_section = (
                            f"📄 Document {i}: {source}\n"
                            f"{truncated_content}\n"
                            f"{'─' * 50}\n"
                        )
                        context_parts.append(formatted_section)
                    break
        
        final_context = '\n'.join(context_parts)
        
        # Log the actual context being sent
        log_to_sublog(self.project_dir, "chat_handler.log", 
                    f"Final context: {len(final_context)} chars, {len(context_parts)} documents")
        
        return final_context

    def _filter_valid_documents(self, documents: List[Document]) -> List[Document]:
        """Filter out invalid/error documents but preserve content length."""
        valid = []
        for d in documents:
            try:
                txt = (d.page_content or "").strip()
                if not txt or len(txt) < 20:  # Reduced from 40 to catch more content
                    continue
                if "error_during_filtering" in txt.lower():
                    continue
                valid.append(d)
            except Exception:
                continue
        return valid

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

    def build_enhanced_context(self, documents: List[Document], query: str, intent: str = 'general') -> str:
        """🔧 ENHANCED with full content preservation and debugging."""
        documents = self._filter_valid_documents(documents)
        
        # 🆕 DEBUG: Log document quality
        error_docs = [d for d in documents if "error_during_filtering" in str(d.metadata.get('source', ''))]
        valid_docs = [d for d in documents if "error_during_filtering" not in str(d.metadata.get('source', ''))]
        
        log_to_sublog(self.project_dir, "context_builder.log",
                      f"Document quality check: {len(valid_docs)} valid, {len(error_docs)} error docs")
        
        if len(error_docs) > len(valid_docs):
            log_to_sublog(self.project_dir, "context_builder.log",
                          "WARNING: More error documents than valid ones - check document processing")
        
        # Use only valid documents for context building
        documents = valid_docs
        
        # Phase 1: Always build original hierarchical context for backward compatibility
        original_context = self._build_original_hierarchical_context(documents, query, intent)
        
        # 🆕 DEBUG: Check cross-reference availability
        log_to_sublog(self.project_dir, "context_builder.log",
                      f"Cross-references available: {self.cross_references is not None}")
        
        # Phase 2: Add advanced context layers if cross-references available
        if self.cross_references:
            try:
                enhanced_context = self._build_enhanced_layered_context(documents, query, intent)
                log_to_sublog(self.project_dir, "context_builder.log",
                              f"Enhanced context layers: {len(enhanced_context.get('context_layers', {}))}")
                return self.format_context_for_llm(enhanced_context)
            except Exception as e:
                log_to_sublog(self.project_dir, "context_builder.log",
                              f"Advanced context assembly failed: {e}")
                # Fallback to original context
                return original_context
        
        return original_context

    def _build_original_hierarchical_context(self, documents: List[Document], 
                                           query: str, intent: str) -> str:
        """
        🔧 ENHANCED: Original functionality maintained but with FULL CONTENT preservation.
        """
        documents = self._filter_valid_documents(documents)
        
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
        
        # Format documents with FULL CONTENT (🔧 FIXED: No truncation)
        context_parts.append("Retrieved Documents:")
        total_content_length = 0
        max_total_length = 12000  # Reasonable limit for context window
        
        for i, doc in enumerate(documents):
            formatted_doc = self._format_document_with_full_content(doc, self.hierarchy_index)
            
            # Only limit if we're approaching context window limits
            if total_content_length + len(formatted_doc) < max_total_length:
                context_parts.append(f"Document {i+1}:")
                context_parts.append(formatted_doc)
                context_parts.append("")
                total_content_length += len(formatted_doc)
            else:
                # If we must truncate, do it intelligently
                remaining_space = max_total_length - total_content_length - 200
                if remaining_space > 1000:  # Only if meaningful space remains
                    truncated_doc = self._format_document_with_intelligent_truncation(
                        doc, self.hierarchy_index, remaining_space)
                    context_parts.append(f"Document {i+1} (truncated due to length):")
                    context_parts.append(truncated_doc)
                    context_parts.append("")
                break
        
        log_to_sublog(self.project_dir, "context_builder.log",
                      f"Original context built: {len(context_parts)} parts, {total_content_length} total chars")
        
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
                    documents, doc_analysis)
        
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
                    'usage_context': usage.get('context', '')[:200]  # Keep more context
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
        🔧 ENHANCED: Format enhanced multi-layered context with FULL CONTENT preservation.
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
                        parts.append(f"  ➡️ Calls: {', '.join(flow_info['calls'])}")
                    if flow_info.get('called_by'):
                        parts.append(f"  ⬅️ Called by: {', '.join(flow_info['called_by'])}")
            
            elif layer_name == 'inheritance':
                relationships = layer_data.get('relationships', {})
                for class_name, info in relationships.items():
                    parts.append(f"🏗️ Class: {class_name}")
                    if info.get('parents'):
                        parts.append(f"  ⬆️ Inherits from: {', '.join(info['parents'])}")
                    if info.get('children'):
                        parts.append(f"  ⬇️ Extended by: {', '.join(info['children'])}")
            
            elif layer_name == 'impact':
                impact_data = layer_data.get('impact_analysis', {})
                direct_impacts = impact_data.get('direct_impacts', [])
                if direct_impacts:
                    parts.append(f"🎯 Direct Impacts:")
                    for impact in direct_impacts[:5]:  # Show top 5
                        parts.append(f"  • {impact.get('impacted_file', 'unknown')} uses {impact.get('symbol', 'unknown')}")
            
            elif layer_name == 'hierarchical':
                modules = layer_data.get('modules', {})
                if modules:
                    parts.append(f"📁 Module Structure:")
                    for module, files in list(modules.items())[:5]:  # Show top 5 modules
                        parts.append(f"  • {module}: {len(files)} files")
            
            parts.append("")
        
        # Add document content section - 🔧 FIXED: FULL CONTENT
        documents = enhanced_context.get('documents', [])
        if documents:
            parts.append("=== RELEVANT CODE CHUNKS ===")
            total_content_chars = 0
            max_context_length = 10000  # Reasonable total limit
            
            for i, doc in enumerate(documents):
                metadata = getattr(doc, 'metadata', {})
                if isinstance(metadata, dict):
                    source = metadata.get('source', 'unknown')
                    parts.append(f"📄 Document {i+1}: {source}")
                    
                    # 🚀 NEW: Add rich metadata summary
                    metadata_summary = []
                    if metadata.get("design_patterns"):
                        metadata_summary.append(f"Patterns: {', '.join(metadata['design_patterns'])}")
                    if metadata.get("method_signatures"):
                        method_count = len(metadata["method_signatures"])
                        metadata_summary.append(f"Methods: {method_count}")
                    if metadata.get("inheritance_info", {}).get("extends"):
                        metadata_summary.append(f"Extends: {', '.join(metadata['inheritance_info']['extends'])}")
                    
                    if metadata_summary:
                        parts.append(f"📋 Meta {' | '.join(metadata_summary)}")
                    
                    # 🔧 FIXED: Use FULL content instead of truncated preview
                    content = doc.page_content or ""
                    
                    # Only truncate if absolutely necessary for context window
                    if total_content_chars + len(content) < max_context_length:
                        parts.append(f"Content: {content}")
                        total_content_chars += len(content)
                    else:
                        # Intelligent truncation if we must
                        remaining_space = max_context_length - total_content_chars - 100
                        if remaining_space > 500:
                            truncated_content = content[:remaining_space] + f"\n[Content truncated - showing {remaining_space} of {len(content)} chars]"
                            parts.append(f"Content: {truncated_content}")
                        else:
                            parts.append(f"Content: [Content too long - {len(content)} chars available but context limit reached]")
                        break
                    
                    parts.append("")
        
        final_context = "\n".join(parts)
        
        # Log the context size for monitoring
        log_to_sublog(self.project_dir, "context_builder.log",
                      f"Formatted context for LLM: {len(final_context)} characters")
        
        return final_context

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

    # 🔧 ENHANCED: Keep all existing methods but fix truncation issues

    def _format_document_with_full_content(self, doc, hierarchy_context) -> str:
        """🔧 ENHANCED: Format document with FULL content instead of truncated."""
        metadata = getattr(doc, 'metadata', {})
        if not isinstance(metadata, dict):
            return doc.page_content
        
        source = metadata.get('source', 'Unknown')
        class_names = metadata.get('class_names', [])
        function_names = metadata.get('function_names', [])
        
        formatted_parts = [f"Source: {source}"]
        
        if class_names:
            formatted_parts.append(f"Classes: {', '.join(class_names[:5])}")
        if function_names:
            formatted_parts.append(f"Functions: {', '.join(function_names[:5])}")
        
        # 🔧 FIXED: Use FULL content instead of truncated
        formatted_parts.append(f"Content: {doc.page_content}")
        
        return "\n".join(formatted_parts)

    def _format_document_with_intelligent_truncation(self, doc, hierarchy_context, max_length: int) -> str:
        """🆕 NEW: Intelligent truncation that preserves important parts."""
        metadata = getattr(doc, 'metadata', {})
        if not isinstance(metadata, dict):
            content = doc.page_content
            if len(content) <= max_length:
                return content
            return content[:max_length] + f"\n[Truncated - {len(content)} total chars]"
        
        source = metadata.get('source', 'Unknown')
        class_names = metadata.get('class_names', [])
        function_names = metadata.get('function_names', [])
        
        header_parts = [f"Source: {source}"]
        
        if class_names:
            header_parts.append(f"Classes: {', '.join(class_names[:5])}")
        if function_names:
            header_parts.append(f"Functions: {', '.join(function_names[:5])}")
        
        header = "\n".join(header_parts)
        available_space = max_length - len(header) - 100  # Reserve space for header and truncation note
        
        content = doc.page_content
        if len(content) <= available_space:
            return f"{header}\nContent: {content}"
        
        # Try to find a good breaking point (end of function, class, etc.)
        truncated_content = content[:available_space]
        
        # Look for natural break points
        break_points = ['\n\n', '\n}', '\nclass ', '\ndef ', '\nfun ']
        best_break = available_space
        
        for bp in break_points:
            last_occurrence = truncated_content.rfind(bp)
            if last_occurrence > available_space * 0.7:  # At least 70% of content
                best_break = last_occurrence + len(bp)
                break
        
        final_content = content[:best_break]
        return f"{header}\nContent: {final_content}\n[Truncated - showing {best_break} of {len(content)} total chars]"

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

    # Deprecated method kept for backward compatibility
    def _format_document_with_enhanced_context(self, doc, hierarchy_context) -> str:
        """🔧 DEPRECATED: Redirects to full content method for backward compatibility."""
        return self._format_document_with_full_content(doc, hierarchy_context)
