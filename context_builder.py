import re
import json
import os
from typing import List, Dict, Optional
from langchain.docstore.document import Document
from config import ProjectConfig


class ContextBuilder:
    """Builds enhanced prompt context using hierarchical index and vector retrieval."""

    def __init__(self, project_config: ProjectConfig, max_tokens: int = 4000):
        self.project_config = project_config
        self.max_tokens = max_tokens
        self.index_path = os.path.join("vector_db", "hierarchical_index.json")

    def build_enhanced_context(
        self,
        query: str,
        retrieved_docs: List[Document],
        intent: str,
        query_hints: Dict[str, List[str]]
    ) -> str:
        context_parts = []
        token_count = 0

        # Try loading hierarchical index (if exists)
        hierarchy = self._load_hierarchy()

        # ───────────────────────────────────────────────
        # INTENT: VALIDATION (inject screen-field rules)
        # ───────────────────────────────────────────────
        if intent == "validation" and hierarchy:
            field, screen = self._extract_field_and_screen(query)
            val_block = self._build_validation_snippet(hierarchy, screen, field)
            if val_block:
                context_parts.append(val_block)
                token_count += len(val_block.split())

        # ───────────────────────────────────────────────
        # INTENT: OVERVIEW → inject top file summaries
        # ───────────────────────────────────────────────
        if intent == "overview" and hierarchy:
            file_summaries = hierarchy.get("file_level", {})
            top_files = sorted(list(file_summaries.items()), key=lambda x: -x[1].get("avg_complexity", 0))[:3]

            context_parts.append("## 🧾 Project Overview\n")
            for fname, info in top_files:
                preview = info.get('first_chunk_preview') or info.get('summary') or ""
                context_parts.append(f"▶️ {fname}:\n{preview}\n\n")
                token_count += len(preview.split())

        # ───────────────────────────────────────────────
        # INTENT: UI_FLOW → show screen navigation flows
        # ───────────────────────────────────────────────
        if intent == "ui_flow" and hierarchy and "ui_level" in hierarchy:
            flows = hierarchy["ui_level"].get("navigation_flows", [])[:5]
            context_parts.append("## 🔀 Navigation Actions:\n")
            for nav in flows:
                preview = nav.get("preview", "")
                src_loc = nav.get("source", "")
                context_parts.append(f"• {src_loc}: {preview}\n")
                token_count += len(preview.split())

        # ───────────────────────────────────────────────
        # INTENT: BUSINESS_LOGIC → inject logic indicator blocks
        # ───────────────────────────────────────────────
        if intent == "business_logic" and hierarchy and "business_level" in hierarchy:
            biz = hierarchy["business_level"]
            logic_keys = ["business_processes", "validation_rules", "calculations"]
            context_parts.append("## 📊 Business Logic Summary\n")
            for key in logic_keys:
                for chunk in biz.get(key, [])[:2]:
                    snippet = chunk.get("preview", "")
                    source = chunk.get("source", "")
                    context_parts.append(f"• ({key}) {source}:\n{snippet}\n")
                    token_count += len(snippet.split())

        # ───────────────────────────────────────────────
        # FALLBACK: include retrieved document chunks
        # (handled across all intents)
        # ───────────────────────────────────────────────
        if retrieved_docs:
            context_parts.append("\n## 🔍 Retrieved Code Chunks (Similarity)\n")
            for i, doc in enumerate(retrieved_docs):
                if token_count > self.max_tokens * 0.8:
                    break
                formatted = self._format_document_with_enhanced_context(doc, intent)
                token_count += len(formatted.split())
                context_parts.append(formatted)

        return "\n".join(context_parts)

    # ───────────────────────────────────────────────
    # Utils
    # ───────────────────────────────────────────────

    def _load_hierarchy(self) -> Optional[Dict]:
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def _extract_field_and_screen(self, query: str) -> (str, str):
        """Basic heuristic extraction for ‘validation’ questions."""
        field = ""
        screen = ""
        field_match = re.search(r'(?:field|input|of)\s+["\']?(\w+)["\']?', query)
        if field_match:
            field = field_match.group(1)
        screen_match = re.search(r'in\s+([A-Z]\w*Screen)', query)
        if screen_match:
            screen = screen_match.group(1)
        return field.strip(), screen.strip()

    def _build_validation_snippet(self, hierarchy, screen: str, field: str) -> str:
        """Build a validation summary from screen-validation map."""
        mapping = hierarchy.get("screen_input_validation_map", {})
        if screen and field and screen in mapping and field in mapping[screen]:
            rules = mapping[screen][field]
            if rules:
                return (f"## ✅ Validation Rules\n"
                        f"• `{field}` in `{screen}` is validated by: {', '.join(rules)}\n\n")
            else:
                return f"## ✅ Validation Rules\n• `{field}` in `{screen}` has no explicit validation rules.\n\n"
        return ""

    def _format_document_with_enhanced_context(self, doc: Document, intent: str) -> str:
        """Format a chunk for prompt context with source + preview."""
        source = doc.metadata.get("source", "unknown")
        chunk_type = doc.metadata.get("chunk_hierarchy") or doc.metadata.get("type", "unknown")
        screen = doc.metadata.get("screen_name", "")
        role = f" [{screen}]" if screen else ""

        formatted = f"\n### 📄 {source}{role} ({chunk_type})\n\n{doc.page_content.strip()}\n"
        return formatted
