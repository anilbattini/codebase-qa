# chunker_factory.py (Enhanced Version)

import os
import re
from typing import Dict, List, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import ProjectConfig

class SemanticChunker:
    """Enhanced chunker with semantic awareness and better overlap handling."""
    
    def __init__(self, project_config: ProjectConfig):
        self.config = project_config
        self.chunk_types = project_config.get_chunk_types()
        self.overlap_size = 100
        
    def create_semantic_chunker(self, file_ext: str):
        """Create a semantically-aware chunker function."""
        def chunk_with_context(content: str) -> List[Dict[str, Any]]:
            if not content or not isinstance(content, str):
                return []
            
            # Get base chunks using the original logic
            base_chunks = self._create_base_chunks(content, file_ext)
            
            # Add contextual overlap between chunks
            enhanced_chunks = []
            for i, chunk in enumerate(base_chunks):
                enhanced_chunk = chunk.copy()
                
                # Add overlap from previous chunk
                if i > 0 and len(base_chunks[i-1]["content"]) > self.overlap_size:
                    prev_content = base_chunks[i-1]["content"][-self.overlap_size:]
                    enhanced_chunk["content"] = f"...{prev_content}\n\n{chunk['content']}"
                    enhanced_chunk["has_prev_context"] = True
                
                # Add overlap from next chunk
                if i < len(base_chunks) - 1 and len(base_chunks[i+1]["content"]) > self.overlap_size:
                    next_content = base_chunks[i+1]["content"][:self.overlap_size]
                    enhanced_chunk["content"] = f"{enhanced_chunk['content']}\n\n{next_content}..."
                    enhanced_chunk["has_next_context"] = True
                
                # Add semantic relationships
                enhanced_chunk["semantic_relations"] = self._find_semantic_relations(
                    enhanced_chunk["content"], file_ext
                )
                
                enhanced_chunks.append(enhanced_chunk)
                
            return enhanced_chunks
        return chunk_with_context
    
    def _create_base_chunks(self, content: str, file_ext: str) -> List[Dict[str, Any]]:
        """Create base chunks using improved logic."""
        # Language-specific patterns
        if file_ext in ['.py']:
            pattern = r'(?=^\s*(?:@\w+\s*)*(?:class|def|async\s+def)\s+\w+)'
        elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            pattern = r'(?=^\s*(?:export\s+)?(?:async\s+)?(?:function|const|let|var|class)\s+\w+)'
        elif file_ext in ['.kt', '.kts', '.java']:
            pattern = r'(?=^\s*(?:@\w+\s*)*(?:public|private|protected)?\s*(?:class|interface|fun|object)\s+\w+)'
        elif file_ext in ['.html', '.vue', '.svelte']:
            return self._chunk_template_content(content)
        elif file_ext == '.xml':
            return self._chunk_xml_content(content)
        else:
            # Fallback to RecursiveCharacterTextSplitter with better parameters
            return self._chunk_generic_content(content)
        
        # Split content using regex pattern
        raw_chunks = re.split(pattern, content, flags=re.MULTILINE)
        
        # Process and format chunks
        formatted_chunks = []
        for chunk in raw_chunks:
            if chunk and chunk.strip() and len(chunk.strip()) > 30:  # Lowered threshold
                chunk_content = chunk.strip()
                formatted_chunks.append({
                    "content": chunk_content,
                    "type": self._detect_chunk_type(chunk_content),
                    "name": self._extract_chunk_name(chunk_content, file_ext),
                    "has_prev_context": False,
                    "has_next_context": False
                })
        
        return formatted_chunks
    
    def _chunk_template_content(self, content: str) -> List[Dict[str, Any]]:
        """Enhanced template file chunking (HTML, Vue, Svelte)."""
        chunks = []
        
        # For Vue/Svelte single file components
        if '<template>' in content or '<script>' in content or '<style>' in content:
            sections = {
                'template': r'<template[^>]*>(.*?)</template>',
                'script': r'<script[^>]*>(.*?)</script>',
                'style': r'<style[^>]*>(.*?)</style>'
            }
            
            for section_name, pattern in sections.items():
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if match.strip():
                        chunks.append({
                            "content": match.strip(),
                            "type": f"{section_name}_section",
                            "name": section_name,
                            "has_prev_context": False,
                            "has_next_context": False
                        })
        
        # For regular HTML
        else:
            # Split by major HTML sections
            html_sections = re.split(r'(?=<(?:div|section|article|main|header|footer|nav)[^>]*>)', content)
            for section in html_sections:
                if section.strip() and len(section.strip()) > 50:
                    chunks.append({
                        "content": section.strip(),
                        "type": "html_section",
                        "name": self._extract_html_section_name(section),
                        "has_prev_context": False,
                        "has_next_context": False
                    })
        
        # Always include full content as context
        chunks.append({
            "content": content,
            "type": "full_template",
            "name": "complete_template",
            "has_prev_context": False,
            "has_next_context": False
        })
        
        return chunks if chunks else [{"content": content, "type": "template", "name": None, "has_prev_context": False, "has_next_context": False}]
    
    def _chunk_xml_content(self, content: str) -> List[Dict[str, Any]]:
        """Enhanced XML chunking with better semantic awareness."""
        chunks = []
        
        # Android strings.xml special handling
        if "strings.xml" in content or "<string" in content:
            string_pattern = r'<string[^>]*name\s*=\s*["\']([^"\']+)["\'][^>]*>([^<]*)</string>'
            matches = re.findall(string_pattern, content, re.DOTALL)
            
            for name, value in matches:
                clean_value = ' '.join(value.split())
                chunk_content = f'<string name="{name}">{clean_value}</string>'
                chunks.append({
                    "content": chunk_content,
                    "type": "string_resource",
                    "name": name,
                    "has_prev_context": False,
                    "has_next_context": False
                })
        
        # Android layout files
        elif any(keyword in content for keyword in ['android:', 'LinearLayout', 'RelativeLayout', 'ConstraintLayout']):
            # Extract major layout components
            layout_pattern = r'(<[^>]*Layout[^>]*>.*?</[^>]*Layout>)'
            layouts = re.findall(layout_pattern, content, re.DOTALL)
            
            for layout in layouts:
                if len(layout.strip()) > 100:
                    chunks.append({
                        "content": layout.strip(),
                        "type": "layout_component",
                        "name": self._extract_xml_element_name(layout),
                        "has_prev_context": False,
                        "has_next_context": False
                    })
        
        # Generic XML handling
        else:
            # Split by major XML elements
            element_pattern = r'(<[^/>][^>]*>.*?</[^>]+>)'
            elements = re.findall(element_pattern, content, re.DOTALL)
            
            for element in elements:
                if element.strip() and len(element.strip()) > 50:
                    chunks.append({
                        "content": element.strip(),
                        "type": "xml_element",
                        "name": self._extract_xml_element_name(element),
                        "has_prev_context": False,
                        "has_next_context": False
                    })
        
        # Always include full content
        chunks.append({
            "content": content,
            "type": "xml_full",
            "name": "complete_xml",
            "has_prev_context": False,
            "has_next_context": False
        })
        
        return chunks if chunks else [{"content": content, "type": "xml", "name": None, "has_prev_context": False, "has_next_context": False}]
    
    def _chunk_generic_content(self, content: str) -> List[Dict[str, Any]]:
        """Enhanced generic content chunking."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Increased chunk size
            chunk_overlap=100,  # Added overlap
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
        chunks = splitter.split_text(content)
        return [
            {
                "content": chunk,
                "type": "text",
                "name": self._extract_first_meaningful_line(chunk),
                "has_prev_context": False,
                "has_next_context": False
            }
            for chunk in chunks if chunk.strip()
        ]
    
    def _find_semantic_relations(self, chunk: str, file_ext: str) -> List[str]:
        """Find semantic relationships within the chunk."""
        relations = []
        
        # Function calls
        function_calls = re.findall(r'(\w+)\s*$$', chunk)
        if function_calls:
            relations.extend([f"calls:{func}" for func in set(function_calls)])
        
        # Class instantiations
        if file_ext in ['.py', '.java', '.kt']:
            class_instantiations = re.findall(r'new\s+(\w+)\s*$$|(\w+)\s*$$', chunk)
            for match in class_instantiations:
                class_name = match or match[1]
                if class_name and class_name.isupper():  # Likely a class name
                    relations.append(f"instantiates:{class_name}")
        
        # Import relationships
        imports = re.findall(r'import\s+(?:.*?\s+)?(\w+)', chunk)
        if imports:
            relations.extend([f"imports:{imp}" for imp in set(imports)])
        
        return relations
    
    def _detect_chunk_type(self, chunk: str) -> str:
        """Enhanced chunk type detection."""
        if not isinstance(chunk, str) or not chunk:
            return "other"
        
        chunk_lower = chunk.strip().lower()
        
        # Check configured patterns first
        for chunk_type, patterns in self.chunk_types.items():
            for pattern in patterns:
                if chunk_lower.startswith(pattern.lower()) or pattern.lower() in chunk_lower:
                    return chunk_type
        
        # Additional detection logic
        if any(keyword in chunk_lower for keyword in ['test', 'spec', 'describe', 'it(']):
            return "test"
        elif any(keyword in chunk_lower for keyword in ['config', 'setting', 'option']):
            return "configuration"
        elif any(keyword in chunk_lower for keyword in ['@get', '@post', '@put', '@delete', 'router']):
            return "api_endpoint"
        elif any(keyword in chunk_lower for keyword in ['select', 'insert', 'update', 'delete', 'query']):
            return "database"
        
        return "other"
    
    def _extract_chunk_name(self, chunk: str, file_ext: str) -> str:
        """Enhanced chunk name extraction."""
        if not isinstance(chunk, str) or not chunk:
            return None
        
        # Language-specific patterns
        patterns = []
        
        if file_ext == '.py':
            patterns = [
                r'class\s+(\w+)',
                r'def\s+(\w+)',
                r'async\s+def\s+(\w+)'
            ]
        elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            patterns = [
                r'class\s+(\w+)',
                r'function\s+(\w+)',
                r'const\s+(\w+)\s*=',
                r'let\s+(\w+)\s*=',
                r'var\s+(\w+)\s*='
            ]
        elif file_ext in ['.kt', '.kts']:
            patterns = [
                r'class\s+(\w+)',
                r'fun\s+(\w+)',
                r'object\s+(\w+)',
                r'interface\s+(\w+)'
            ]
        elif file_ext == '.java':
            patterns = [
                r'class\s+(\w+)',
                r'interface\s+(\w+)',
                r'enum\s+(\w+)',
                r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*$$'
            ]
        
        # Try patterns in order
        for pattern in patterns:
            match = re.search(pattern, chunk, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Fallback: return first meaningful line
        return self._extract_first_meaningful_line(chunk)
    
    def _extract_first_meaningful_line(self, chunk: str) -> str:
        """Extract the first meaningful line as a fallback name."""
        lines = chunk.strip().split('\n')
        for line in lines:
            clean_line = line.strip()
            if clean_line and not clean_line.startswith(('#', '//', '/*', '*', 'import', 'from')):
                return clean_line[:50] + "..." if len(clean_line) > 50 else clean_line
        return None
    
    def _extract_html_section_name(self, section: str) -> str:
        """Extract meaningful name from HTML section."""
        # Look for id, class, or tag name
        id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', section)
        if id_match:
            return id_match.group(1)
        
        class_match = re.search(r'class\s*=\s*["\']([^"\']+)["\']', section)
        if class_match:
            return class_match.group(1).split()  # First class name
        
        tag_match = re.search(r'<(\w+)', section)
        if tag_match:
            return tag_match.group(1)
        
        return None
    
    def _extract_xml_element_name(self, element: str) -> str:
        """Enhanced XML element name extraction."""
        patterns = [
            r'android:id="@\+id/([^"]+)"',
            r'name="([^"]+)"',
            r'<(\w+)[^>]*>'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, element)
            if match:
                return match.group(1)
        
        return None

# Factory functions (updated)
def get_chunker(file_extension: str, project_config: ProjectConfig = None):
    """Factory function to get appropriate chunker based on config."""
    if not project_config:
        project_config = ProjectConfig()
    
    chunker = SemanticChunker(project_config)
    return chunker.create_semantic_chunker(file_extension)

def get_auto_chunker(filepath: str, content: str, project_config: ProjectConfig = None):
    """Auto-detect and return appropriate chunker."""
    if not project_config:
        project_config = ProjectConfig()
    
    ext = os.path.splitext(filepath)[1].lower()
    return get_chunker(ext, project_config)

def summarize_chunk(chunk: str, filename: str, project_config: ProjectConfig = None) -> str:
    """Create enhanced language-aware summaries."""
    if not chunk or not isinstance(chunk, str):
        return f"From {filename}: No content"
    
    if not project_config:
        project_config = ProjectConfig()
    
    # Get first meaningful line
    first_line = chunk.strip().splitlines() if chunk.strip() else "No content"
    
    # Add project-specific context
    summary_context = f"[{project_config.project_type.upper()}]"
    
    # Truncate filename for display
    display_filename = filename.split('/')[-1] if '/' in filename else filename
    
    return f"{summary_context} From {display_filename}: {first_line[:80]}..." if len(first_line) > 80 else f"{summary_context} From {display_filename}: {first_line}"
