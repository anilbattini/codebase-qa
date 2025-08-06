import re
import json
import os
from typing import List, Dict, Optional
from langchain.docstore.document import Document
from config import ProjectConfig
from logger import log_highlight, log_to_sublog

class ContextBuilder:
    """Builds an enhanced prompt context using hierarchy index and chunk anchors."""

    def __init__(self, project_config: ProjectConfig, max_tokens: int = 4000, project_dir: str = "."):
        self.project_config = project_config
        self.max_tokens = max_tokens
        self.project_dir = project_dir
        self.index_path = os.path.join(project_dir, "vector_db", "hierarchical_index.json")

    def build_enhanced_context(
        self,
        query: str,
        retrieved_docs: List[Document],
        intent: str,
        query_hints: Dict[str, List[str]]
    ) -> str:
        log_highlight("ContextBuilder.build_enhanced_context")
        context_parts = []
        token_count = 0
        hierarchy = self._load_hierarchy()
        sublog_msg = f"\n[build_enhanced_context] intent={intent} query={query}\n"
        found_strong_context = False

        # Intent: VALIDATION
        if intent == "validation" and hierarchy:
            field, screen = self._extract_field_and_screen(query)
            val_block = self._build_validation_snippet(hierarchy, screen, field)
            if val_block:
                context_parts.append(val_block)
                found_strong_context = True
                token_count += len(val_block.split())

        # Intent: OVERVIEW
        elif intent == "overview" and hierarchy:
            file_summaries = hierarchy.get("file_level", {})
            top_files = sorted(
                ((fname, info) for fname, info in file_summaries.items() if isinstance(info, dict)),
                key=lambda x: -x[1].get("avg_complexity", 0)
            )[:3]
            context_parts.append("## 🧾 Project Overview\n")
            for fname, info in top_files:
                preview = info.get('first_chunk_preview') or ""
                context_parts.append(f"▶️ {fname}:\n{preview}\n\n")
                token_count += len(preview.split())
            if top_files:
                found_strong_context = True

        # Intent: UI_FLOW
        elif intent == "ui_flow" and hierarchy and "ui_level" in hierarchy:
            flows = hierarchy["ui_level"].get("navigation_flows", [])[:5]
            if flows:
                context_parts.append("## 🔀 Navigation Actions:\n")
                for nav in flows:
                    preview = nav.get("preview", "")
                    src_loc = nav.get("source", "")
                    context_parts.append(f"• {src_loc}: {preview}\n")
                    token_count += len(preview.split())
                found_strong_context = True

        # Intent: BUSINESS_LOGIC
        elif intent == "business_logic" and hierarchy and "business_level" in hierarchy:
            biz = hierarchy["business_level"]
            logic_keys = ["business_processes", "validation_rules", "calculations"]
            context_parts.append("## 📊 Business Logic Summary\n")
            for key in logic_keys:
                for chunk in biz.get(key, [])[:2]:
                    snippet = chunk.get("preview", "")
                    source = chunk.get("source", "")
                    context_parts.append(f"• ({key}) {source}:\n{snippet}\n")
                    token_count += len(snippet.split())
            found_strong_context = True

        # Fallback: retrieved document chunks
        if not found_strong_context and retrieved_docs:
            context_parts.append("\n## 🔍 Retrieved Code Chunks (Similarity)\n")
            
            # Sort documents by relevance (strong anchors first, then by semantic score)
            sorted_docs = []
            weak_docs = []
            
            for doc in retrieved_docs:
                if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                    anchors = [doc.metadata.get(k) for k in ("screen_name", "class_names", "function_names", "component_name")]
                    semantic_score = doc.metadata.get("semantic_score", 0.0)
                    
                    if any(anchors):
                        # Add semantic score to prioritize better chunks
                        doc.metadata["_sort_score"] = semantic_score + 10.0  # Boost for anchors
                        sorted_docs.append(doc)
                    else:
                        doc.metadata["_sort_score"] = semantic_score
                        weak_docs.append(doc)
                else:
                    weak_docs.append(doc)
            
            # Sort by semantic score within each category
            sorted_docs.sort(key=lambda x: x.metadata.get("_sort_score", 0.0), reverse=True)
            weak_docs.sort(key=lambda x: x.metadata.get("_sort_score", 0.0), reverse=True)
            
            # Use strong anchors first, then weak ones if needed
            docs_to_use = sorted_docs + weak_docs
            
            for i, doc in enumerate(docs_to_use):
                if token_count > self.max_tokens * 0.8:
                    context_parts.append(f"...[Context window limit: {token_count} tokens]...")
                    break
                
                if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                    anchors = [doc.metadata.get(k) for k in ("screen_name", "class_names", "function_names", "component_name")]
                    semantic_score = doc.metadata.get("semantic_score", 0.0)
                    
                    if any(anchors):
                        formatted = self._format_document_with_enhanced_context(doc, intent)
                        context_parts.append(formatted)
                        token_count += len(formatted.split())
                    else:
                        # Only include weak chunks if we have no strong ones, and only high semantic score
                        if not sorted_docs and semantic_score > 2.0:
                            formatted = self._format_document_with_enhanced_context(doc, intent)
                            context_parts.append(formatted)
                            token_count += len(formatted.split())
                            log_to_sublog(self.project_dir, "context_building.log",
                                f"⚠️ Weak/anchorless chunk served as fallback, doc={doc.metadata.get('source', '?')}, score={semantic_score}"
                            )
                else:
                    # Handle case where doc is not a proper Document object
                    log_to_sublog(self.project_dir, "context_building.log",
                        f"⚠️ Invalid document object type: {type(doc)}"
                    )
            
            # Check if we found any strong semantic anchors
            if not sorted_docs and weak_docs:
                context_parts.append("\n⚠️ No context blocks with strong semantic anchors found. Results may be less relevant.\n")
            elif sorted_docs:
                avg_score = sum(d.metadata.get("semantic_score", 0.0) for d in sorted_docs) / len(sorted_docs)
                context_parts.append(f"\n✅ Found {len(sorted_docs)} chunks with strong semantic anchors (avg score: {avg_score:.1f})\n")

        # Log context details
        sublog_msg += "".join(context_parts[:2]) + "...\n"
        log_to_sublog(self.project_dir, "context_building.log", sublog_msg)
        return "\n".join(context_parts)

    # ---------------- Utils ----------------

    def _load_hierarchy(self) -> Optional[Dict]:
        try:
            with open(self.index_path, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def _extract_field_and_screen(self, query: str) -> (str, str):
        """Heuristic extraction for validation queries."""
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
        """Build validation context from screen-input mapping."""
        mapping = hierarchy.get("screen_input_validation_map", {})
        if screen and field and screen in mapping and field in mapping[screen]:
            rules = mapping[screen][field]
            if rules:
                return f"## ✅ Validation Rules\n• `{field}` in `{screen}` is validated by: {', '.join(rules)}\n\n"
            else:
                return f"## ✅ Validation Rules\n• `{field}` in `{screen}` has no explicit validation rules.\n\n"
        return ""

    def _format_document_with_enhanced_context(self, doc: Document, intent: str) -> str:
        source = doc.metadata.get("source", "unknown")
        chunk_type = doc.metadata.get("chunk_hierarchy") or doc.metadata.get("type", "unknown")
        screen = doc.metadata.get("screen_name", "")
        role = f" [{screen}]" if screen else ""
        formatted = f"\n### 📄 {source}{role} ({chunk_type})\n\n{doc.page_content.strip()}\n"
        return formatted

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - Inline anchor-warnings/diagnostics from fallback context: now always logged via logger.py forensics only, never user-visible unless no strong anchors found.
# - Manual per-file or per-intent ad-hoc context creation: replaced by config/hierarchy-driven extraction only.
# - Individual token-count cutoffs per intent: replaced by a single global context window enforcement/summary block.
# ADDED
# - All context assembly, formatting, and anchor preference is now driven by semantic hierarchy/context blocks, with robust fallback if needed.
# - All logging and sublogs (e.g., for context block strength, anchor coverage) now handled exclusively by logger.py imports.
# - Explicit marker for "no strong anchors found" if all fallback yields only weak chunks.
