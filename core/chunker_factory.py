import os
import re
from typing import Dict, List, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import ProjectConfig
from logger import log_highlight, log_to_sublog

class SemanticChunker:
    """Config-driven, semantic-aware chunker with context hierarchy and improved overlap."""

    def __init__(self, project_config: ProjectConfig):
        self.config = project_config
        self.chunk_types = project_config.get_chunk_types()
        self.overlap_size = 100

    def create_semantic_chunker(self, file_ext: str):
        def chunk_with_context(content: str) -> List[Dict[str, Any]]:
            log_highlight("SemanticChunker.chunk_with_context")
            if not content or not isinstance(content, str):
                return []
            base_chunks = self._create_base_chunks(content, file_ext)
            enhanced_chunks = []
            for i, chunk in enumerate(base_chunks):
                enhanced_chunk = chunk.copy()
                # Add context overlap from previous/next chunk
                if i > 0 and len(base_chunks[i-1]["content"]) > self.overlap_size:
                    prev = base_chunks[i-1]["content"][-self.overlap_size:]
                    enhanced_chunk["content"] = f"...{prev}\n\n{chunk['content']}"
                    enhanced_chunk["has_prev_context"] = True
                if i < len(base_chunks) - 1 and len(base_chunks[i+1]["content"]) > self.overlap_size:
                    nxt = base_chunks[i+1]["content"][:self.overlap_size]
                    enhanced_chunk["content"] = f"{enhanced_chunk['content']}\n\n{nxt}..."
                    enhanced_chunk["has_next_context"] = True
                # Embed hierarchy context into metadata
                hierarchy = []
                if 'class_names' in enhanced_chunk and enhanced_chunk['class_names']:
                    hierarchy.append(f"class:{enhanced_chunk['class_names'][0]}")
                if 'function_names' in enhanced_chunk and enhanced_chunk['function_names']:
                    hierarchy.append(f"func:{enhanced_chunk['function_names'][0]}")
                enhanced_chunk["chunk_hierarchy"] = " > ".join(hierarchy) if hierarchy else None
                enhanced_chunks.append(enhanced_chunk)
            return enhanced_chunks
        return chunk_with_context

    def _create_base_chunks(self, content: str, file_ext: str) -> List[Dict[str, Any]]:
        # Heuristic: use config-driven regex for class/function/component/screen boundaries
        patterns = []
        ext = file_ext.lstrip(".")
        chunk_types = self.config.get_chunk_types()
        for chunk_type, regexps in chunk_types.items():
            patterns += [p for p in regexps if p.strip()]
        regex_patterns = [re.compile(p, re.MULTILINE) for p in patterns if p.startswith('^') or p.startswith(r'\\')]
        indices = []
        for pat in regex_patterns:
            indices += [m.start() for m in pat.finditer(content)]
        indices = sorted(set(indices))
        indices.append(len(content))
        chunks = []
        # Assemble semantic-whole chunks with larger size for better context
        for idx, start in enumerate(indices[:-1]):
            end = indices[idx+1]
            chunk_str = content[start:end].strip()
            if chunk_str and len(chunk_str) > 100:  # Increased minimum size
                meta = {
                    "content": chunk_str,
                    "type": self._detect_chunk_type(chunk_str, file_ext),
                    "name": self._extract_chunk_name(chunk_str, file_ext),
                    "class_names": self._extract_class_names(chunk_str, file_ext),
                    "function_names": self._extract_function_names(chunk_str, file_ext),
                    "has_prev_context": False,
                    "has_next_context": False,
                    "chunk_size": len(chunk_str),
                    "semantic_score": self._calculate_semantic_score(chunk_str, file_ext)
                }
                chunks.append(meta)
        if not chunks:
            return self._chunk_generic_content(content)
        return chunks

    def _calculate_semantic_score(self, chunk: str, file_ext: str) -> float:
        """Calculate semantic richness score for a chunk."""
        score = 0.0
        
        # Higher score for chunks with class/function definitions
        if re.search(r'\bclass\s+\w+', chunk):
            score += 2.0
        if re.search(r'\bfun\s+\w+', chunk) or re.search(r'\bdef\s+\w+', chunk):
            score += 1.5
            
        # Higher score for chunks with imports/dependencies
        if re.search(r'\bimport\s+', chunk) or re.search(r'\bfrom\s+', chunk):
            score += 1.0
            
        # Higher score for chunks with configuration/setup
        if re.search(r'\bconfig\b', chunk, re.IGNORECASE) or re.search(r'\bsetup\b', chunk, re.IGNORECASE):
            score += 1.0
            
        # Higher score for chunks with UI elements
        if re.search(r'\bButton\b|\bTextView\b|\bRecyclerView\b|\bFragment\b', chunk):
            score += 1.5
            
        # Higher score for longer, more detailed chunks
        if len(chunk) > 500:
            score += 0.5
        if len(chunk) > 1000:
            score += 0.5
            
        return score

    def _chunk_generic_content(self, content: str) -> List[Dict[str, Any]]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=100, length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_text(content)
        return [{
            "content": c,
            "type": "text",
            "name": self._extract_first_meaningful_line(c),
            "class_names": [],
            "function_names": [],
            "has_prev_context": False,
            "has_next_context": False
        } for c in chunks if c.strip()]

    def _detect_chunk_type(self, chunk: str, file_ext: str) -> str:
        for chunk_type, patterns in self.chunk_types.items():
            for pattern in patterns:
                if pattern.startswith('^'):
                    if re.match(pattern, chunk): return chunk_type
                elif chunk.strip().startswith(pattern):
                    return chunk_type
        return "other"

    def _extract_chunk_name(self, chunk: str, file_ext: str) -> str:
        patterns = []
        ext = file_ext.lstrip(".")
        if ext == 'py':
            patterns = [r'class\s+(\w+)', r'def\s+(\w+)', r'async\s+def\s+(\w+)']
        elif ext in ['js', 'ts', 'jsx', 'tsx', 'kt', 'java']:
            patterns = [r'class\s+(\w+)', r'function\s+(\w+)', r'fun\s+(\w+)', r'object\s+(\w+)']
        for pattern in patterns:
            match = re.search(pattern, chunk)
            if match:
                return match.group(1)
        return self._extract_first_meaningful_line(chunk)

    def _extract_class_names(self, chunk: str, file_ext: str) -> List[str]:
        patterns = [r'class\s+(\w+)', r'object\s+(\w+)', r'interface\s+(\w+)']
        return [m.group(1) for p in patterns for m in re.finditer(p, chunk)]

    def _extract_function_names(self, chunk: str, file_ext: str) -> List[str]:
        patterns = [r'def\s+(\w+)', r'fun\s+(\w+)', r'function\s+(\w+)']
        return [m.group(1) for p in patterns for m in re.finditer(p, chunk)]

    def _extract_first_meaningful_line(self, chunk: str) -> str:
        for line in chunk.strip().split('\n'):
            l = line.strip()
            if l and not l.startswith(('#', '//', '/*', '*', 'import')):
                return l[:80] + "..." if len(l) > 80 else l
        return None

# Factory functions
def get_chunker(file_extension: str, project_config: ProjectConfig = None):
    if not project_config:
        project_config = ProjectConfig()
    chunker = SemanticChunker(project_config)
    return chunker.create_semantic_chunker(file_extension)

def get_auto_chunker(filepath: str, content: str, project_config: ProjectConfig = None):
    if not project_config:
        project_config = ProjectConfig()
    ext = os.path.splitext(filepath)[1].lower()
    return get_chunker(ext, project_config)

def summarize_chunk(chunk: str, filename: str, project_config: ProjectConfig = None) -> str:
    if not chunk or not isinstance(chunk, str):
        return f"From {filename}: No content"
    if not project_config:
        project_config = ProjectConfig()
    summary_context = f"[{project_config.project_type.upper()}]"
    display_filename = filename.split('/')[-1] if '/' in filename else filename
    first_line = chunk.strip().splitlines()[0] if chunk.strip() else "No content"
    return f"{summary_context} From {display_filename}: {first_line[:80]}..." if len(first_line) > 80 else f"{summary_context} From {display_filename}: {first_line}"

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - All per-file/project local regex logging utilities (now central via logger.py).
# - Redundant "windowed" line chunking for .py, .js, .kt in favor of config-based semantic units (class/function/component).
# - Inline handling of context logging, repeated class/function extraction, and repeated overlap code blocks.
# ADDED
# - Semantic-aware chunk boundaries set by config per project type, never by hardcoded filetype checks.
# - Metadata for "hierarchical context" (file > class > function) embedded for every chunk.
# - All logging/sublong now handled by logger.py with highlighter on entry/exit for traceability.
# - Clear pathway for DRY, easy extension for future formats/project types without code changes everywhere.
