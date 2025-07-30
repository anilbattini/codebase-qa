# chunker_factory.py

import os
import re
from typing import Dict, List, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import ProjectConfig

class UniversalChunker:
    """Language-agnostic code chunker that adapts based on project configuration."""

    def __init__(self, project_config: ProjectConfig):
        self.config = project_config
        self.chunk_types = project_config.get_chunk_types()

    def detect_chunk_type(self, chunk: str) -> str:
        """Detect chunk type based on configurable patterns."""
        if not isinstance(chunk, str) or not chunk:
            return "other"

        chunk_lower = chunk.strip().lower()

        for chunk_type, patterns in self.chunk_types.items():
            for pattern in patterns:
                if chunk_lower.startswith(pattern.lower()) or pattern.lower() in chunk_lower:
                    return chunk_type

        return "other"

    def extract_chunk_name(self, chunk: str, file_ext: str) -> str:
        """Extract meaningful names from chunks based on language patterns."""
        if not isinstance(chunk, str) or not chunk:
            return None

        # Generic patterns that work across languages
        patterns = [
            r'(?:class|interface|enum|component)\s+(\w+)',
            r'(?:function|def|fun|const|let|var)\s+(\w+)',
            r'(?:export\s+(?:default\s+)?(?:class|function)\s+)(\w+)',
            r'(@\w+\s*)?(?:public|private|protected)?\s*(\w+)\s*\(',
        ]

        for pattern in patterns:
            match = re.search(pattern, chunk, re.IGNORECASE)
            if match:
                return match.group(2) if match.lastindex == 2 else match.group(1)

        return None

    def create_universal_chunker(self, file_ext: str):
        """Create a chunker function based on file extension and config."""

        def chunk_content(content: str) -> List[Dict[str, Any]]:
            if not content or not isinstance(content, str):
                return []

            # Determine chunking strategy based on file extension
            if file_ext in ['.py']:
                pattern = r'(?=^\s*(?:@\w+\s*)*(?:class|def|async\s+def)\s+\w+)'
            elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
                pattern = r'(?=^\s*(?:export\s+)?(?:async\s+)?(?:function|const|let|var|class)\s+\w+)'
            elif file_ext in ['.kt', '.kts', '.java']:
                pattern = r'(?=^\s*(?:public|private|protected)?\s*(?:class|interface|fun|object)\s+\w+)'
            elif file_ext in ['.html', '.vue', '.svelte']:
                pattern = r'(?=<(?:template|script|style|component))|(?=^\s*(?:function|const|export))'
            else:
                # Fallback to generic splitting
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50,
                    separators=["\n\n", "\n", " ", ""]
                )
                chunks = splitter.split_text(content)
                return [{"content": chunk, "type": "text", "name": None} for chunk in chunks if chunk.strip()]

            # Split content using regex pattern
            raw_chunks = re.split(pattern, content, flags=re.MULTILINE)

            # Process and format chunks
            formatted_chunks = []
            for chunk in raw_chunks:
                if chunk and chunk.strip() and len(chunk.strip()) > 50:
                    chunk_content = chunk.strip()
                    formatted_chunks.append({
                        "content": chunk_content,
                        "type": self.detect_chunk_type(chunk_content),
                        "name": self.extract_chunk_name(chunk_content, file_ext)
                    })

            return formatted_chunks

        return chunk_content

def get_chunker(file_extension: str, project_config: ProjectConfig = None):
    """Factory function to get appropriate chunker based on config."""
    if not project_config:
        project_config = ProjectConfig()  # Use auto-detection

    chunker = UniversalChunker(project_config)
    return chunker.create_universal_chunker(file_extension)

def get_auto_chunker(filepath: str, content: str, project_config: ProjectConfig = None):
    """Auto-detect and return appropriate chunker."""
    if not project_config:
        project_config = ProjectConfig()

    ext = os.path.splitext(filepath)[1].lower()
    return get_chunker(ext, project_config)

def summarize_chunk(chunk: str, filename: str, project_config: ProjectConfig = None) -> str:
    """Create language-aware summaries."""
    if not chunk or not isinstance(chunk, str):
        return f"From {filename}: No content"

    if not project_config:
        project_config = ProjectConfig()

    first_line = chunk.strip().splitlines()[0] if chunk.strip() else "No content"

    # Add project-specific context to summary
    keywords = project_config.get_summary_keywords()
    summary_context = f"[{project_config.project_type.upper()}]" if keywords else ""

    return f"{summary_context} From {filename}: {first_line[:80]}"
