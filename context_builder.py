# context_builder.py

import re
from typing import List, Dict, Any, Optional
from langchain.docstore.document import Document
from config import ProjectConfig

class ContextBuilder:
    """Builds enhanced context with intelligent prioritization and token management."""
    
    def __init__(self, project_config: ProjectConfig, max_tokens: int = 4000):
        self.project_config = project_config
        self.max_tokens = max_tokens
        
    def build_enhanced_context(self, query: str, retrieved_docs: List[Document], 
                             intent: str, query_hints: Dict[str, List[str]]) -> str:
        """Build context with intelligent prioritization based on intent."""
        
        # Prioritize documents based on intent and query
        prioritized_docs = self._prioritize_documents(retrieved_docs, intent, query_hints, query)
        
        # Build context parts
        context_parts = []
        token_count = 0
        
        # Add project overview for certain intents
        if intent in ["overview", "impact_analysis"]:
            overview = self._get_project_overview(prioritized_docs)
            if overview:
                context_parts.append(f"## Project Overview\n{overview}\n\n")
                token_count += len(overview.split())
        
        # Add intent-specific context
        if intent == "impact_analysis":
            dependency_context = self._build_dependency_context(query, prioritized_docs)
            if dependency_context:
                context_parts.append(f"## Dependencies & Relationships\n{dependency_context}\n\n")
                token_count += len(dependency_context.split())
        
        # Add relevant documents with enhanced metadata context
        context_parts.append("## Relevant Code Sections\n\n")
        
        for i, doc in enumerate(prioritized_docs):
            if token_count >= self.max_tokens * 0.8:  # Reserve 20% for the actual query
                break
                
            doc_context = self._format_document_with_enhanced_context(doc, intent)
            doc_tokens = len(doc_context.split())
            
            if token_count + doc_tokens < self.max_tokens * 0.8:
                context_parts.append(f"### Source {i+1}: {doc.metadata.get('source', 'Unknown')}\n")
                context_parts.append(doc_context + "\n\n")
                token_count += doc_tokens
            else:
                # Try to include a truncated version
                available_tokens = int((self.max_tokens * 0.8) - token_count)
                if available_tokens > 50:
                    truncated = self._truncate_document_context(doc_context, available_tokens)
                    context_parts.append(f"### Source {i+1}: {doc.metadata.get('source', 'Unknown')} (truncated)\n")
                    context_parts.append(truncated + "\n\n")
                break
        
        return "".join(context_parts)
    
    def _prioritize_documents(self, docs: List[Document], intent: str, 
                            query_hints: Dict[str, List[str]], query: str) -> List[Document]:
        """Prioritize documents based on intent, hints, and relevance."""
        
        def calculate_priority_score(doc: Document) -> float:
            score = 0.0
            metadata = doc.metadata
            content = doc.page_content.lower()
            source = metadata.get('source', '').lower()
            
            # Base relevance score (query term matching)
            query_terms = query.lower().split()
            for term in query_terms:
                if term in content:
                    score += 1
                if term in source:
                    score += 0.5
            
            # Intent-specific scoring
            if intent == "overview":
                # Prioritize main files and high-level components
                priority_files = self.project_config.get_priority_files()
                if any(pf in source for pf in priority_files):
                    score += 5
                if metadata.get('chunk_hierarchy') in ['module', 'class']:
                    score += 3
                
            elif intent == "impact_analysis":
                # Prioritize files with dependencies
                if metadata.get('dependencies'):
                    score += 4
                if metadata.get('api_endpoints'):
                    score += 2
                
            elif intent == "business_logic":
                # Prioritize business logic indicators
                business_indicators = metadata.get('business_logic_indicators', [])
                score += len(business_indicators) * 2
                if metadata.get('validation_rules'):
                    score += 3
                
            elif intent == "ui_flow":
                # Prioritize UI-related chunks
                ui_elements = metadata.get('ui_elements', [])
                score += len(ui_elements) * 1.5
                if metadata.get('screen_references'):
                    score += 4
                
            elif intent == "technical":
                # Prioritize function and implementation details
                if metadata.get('chunk_hierarchy') == 'function':
                    score += 3
                complexity = metadata.get('complexity_score', 0)
                score += complexity * 0.5
            
            # Query hints scoring
            search_terms = query_hints.get('search_terms', [])
            for term in search_terms:
                if term.lower() in content or term.lower() in source:
                    score += 2
            
            # File priority from hints
            file_priorities = query_hints.get('file_priorities', [])
            if any(fp in source for fp in file_priorities):
                score += 3
            
            # Chunk type priorities from hints
            preferred_chunk_types = query_hints.get('chunk_types', [])
            if metadata.get('type') in preferred_chunk_types:
                score += 2
            
            # Penalty for very long or very short chunks
            chunk_length = len(doc.page_content)
            if chunk_length < 50:
                score -= 2
            elif chunk_length > 2000:
                score -= 1
            
            return score
        
        # Sort by priority score (descending)
        return sorted(docs, key=calculate_priority_score, reverse=True)
    
    def _get_project_overview(self, docs: List[Document]) -> Optional[str]:
        """Generate project overview from available documents."""
        # Look for main files, READMEs, or high-level components
        overview_docs = []
        
        for doc in docs[:10]:  # Check top 10 docs
            source = doc.metadata.get('source', '').lower()
            chunk_type = doc.metadata.get('chunk_hierarchy', '')
            
            # Priority for overview generation
            if (any(indicator in source for indicator in ['main', 'app', 'readme', 'index']) or
                chunk_type in ['module', 'class'] or
                any(pf in source for pf in self.project_config.get_priority_files())):
                overview_docs.append(doc)
        
        if not overview_docs:
            return None
        
        # Build overview from selected documents
        overview_parts = []
        for doc in overview_docs[:3]:  # Top 3 for overview
            source_name = doc.metadata.get('source', '').split('/')[-1]
            content_preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            overview_parts.append(f"**{source_name}**: {content_preview}")
        
        return "\n".join(overview_parts)
    
    def _build_dependency_context(self, query: str, docs: List[Document]) -> Optional[str]:
        """Build dependency context for impact analysis."""
        dependency_info = []
        
        # Extract target from query
        target_matches = re.findall(r'\b[A-Z][a-zA-Z0-9_]*\b', query)
        
        for doc in docs[:5]:
            dependencies = doc.metadata.get('dependencies', [])
            if dependencies:
                source = doc.metadata.get('source', '').split('/')[-1]
                dependency_info.append(f"**{source}** depends on: {', '.join(dependencies)}")
        
        return "\n".join(dependency_info) if dependency_info else None
    
    def _format_document_with_enhanced_context(self, doc: Document, intent: str) -> str:
        """Format document with enhanced metadata context."""
        metadata = doc.metadata
        
        # Basic info
        context_parts = []
        
        # File info
        file_type = metadata.get('file_type', '')
        chunk_type = metadata.get('type', 'unknown')
        context_parts.append(f"**File Type**: {file_type} | **Chunk Type**: {chunk_type}")
        
        # Intent-specific metadata
        if intent == "business_logic":
            business_indicators = metadata.get('business_logic_indicators', [])
            validations = metadata.get('validation_rules', [])
            if business_indicators:
                context_parts.append(f"**Business Logic**: {', '.join(business_indicators)}")
            if validations:
                context_parts.append(f"**Validations**: {', '.join(str(v) for v in validations)}")
        
        elif intent == "ui_flow":
            ui_elements = metadata.get('ui_elements', [])
            screen_refs = metadata.get('screen_references', [])
            if ui_elements:
                context_parts.append(f"**UI Elements**: {', '.join(ui_elements)}")
            if screen_refs:
                context_parts.append(f"**Screen References**: {', '.join(screen_refs)}")
        
        elif intent == "technical":
            complexity = metadata.get('complexity_score', 0)
            functions = metadata.get('function_names', [])
            classes = metadata.get('class_names', [])
            context_parts.append(f"**Complexity Score**: {complexity}")
            if functions:
                context_parts.append(f"**Functions**: {', '.join(functions)}")
            if classes:
                context_parts.append(f"**Classes**: {', '.join(classes)}")
        
        # Dependencies (always relevant)
        dependencies = metadata.get('dependencies', [])
        if dependencies:
            context_parts.append(f"**Dependencies**: {', '.join(dependencies)}")
        
        # API endpoints (if relevant)
        apis = metadata.get('api_endpoints', [])
        if apis:
            context_parts.append(f"**API Endpoints**: {', '.join(apis)}")
        
        # Combine metadata and content
        metadata_text = "\n".join(context_parts)
        return f"{metadata_text}\n\n``````"
    
    def _truncate_document_context(self, doc_context: str, max_tokens: int) -> str:
        """Truncate document context to fit within token limit."""
        words = doc_context.split()
        if len(words) <= max_tokens:
            return doc_context
        
        # Keep the metadata part and truncate the code
        lines = doc_context.split('\n')
        metadata_lines = []
        code_start_idx = -1
        
        for i, line in enumerate(lines):
            # Fixed line - properly terminated string literal
            if line and isinstance(line, str) and line.startswith('```'):
                code_start_idx = i
                break
            metadata_lines.append(line)
        
        if code_start_idx == -1:
            # No code block found, just truncate
            return ' '.join(words[:max_tokens]) + "..."
        
        # Calculate remaining tokens for code
        metadata_text = '\n'.join(metadata_lines)
        metadata_tokens = len(metadata_text.split())
        remaining_tokens = max_tokens - metadata_tokens - 10  # Buffer
        
        if remaining_tokens > 0:
            code_lines = lines[code_start_idx:]
            code_text = '\n'.join(code_lines)
            code_words = code_text.split()
            
            if len(code_words) > remaining_tokens:
                truncated_code = ' '.join(code_words[:remaining_tokens]) + "\n... (truncated)"
                return metadata_text + "\n\n" + truncated_code
            else:
                return doc_context
        else:
            return metadata_text + "\n\n(Code content truncated due to length)"
