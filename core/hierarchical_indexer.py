import os
import json
from typing import Any, Dict, List, Optional
from langchain.docstore.document import Document
from config.config import ProjectConfig

from logger import log_highlight, log_to_sublog
from config.config import ProjectConfig

class HierarchicalIndexer:
    """
    Builds semantic, multi-level indices for a project. Surfaces missing anchors/attributes for RAG pipeline health.
    All status and incomplete/weak points are logged project-locally.
    """

    def __init__(self, project_config: ProjectConfig, metadata_dir: str = None):
        self.project_config = project_config
        self.metadata_dir = metadata_dir or project_config.get_db_dir()
        self.hierarchy_file = project_config.get_hierarchy_file()

    def create_hierarchical_index(self, documents: List[Document]) -> Dict[str, Any]:
        log_highlight("HierarchicalIndexer.create_hierarchical_index")
        # Build and log a summary of missing anchors/statistics
        level_stats = self._collect_metadata_stats(documents)
        
        hierarchy = {
            "file_level": self._create_file_index(documents, level_stats["missing_files"]),
            "component_level": self._create_component_index(documents, level_stats["missing_components"]),
            "business_level": self._create_business_logic_index(documents, level_stats["missing_business"]),
            "ui_level": self._create_ui_flow_index(documents, level_stats["missing_ui"]),
            "dependency_level": self._create_dependency_index(documents, level_stats["missing_deps"]),
            "api_level": self._create_api_index(documents, level_stats["missing_apis"]),
            "screen_input_validation_map": self._build_screen_input_validation_map(documents)
        }
        self.project_config.create_directories()
        with open(self.hierarchy_file, "w") as f:
            json.dump(hierarchy, f, indent=2)
        # Log missing/weak info for diagnosis
        log_to_sublog(self.project_config.project_dir, "hierarchy_status.log",
            f"Missing file anchors: {level_stats['missing_files']}\n"
            f"Missing component anchors: {level_stats['missing_components']}\n"
            f"Missing business logic: {level_stats['missing_business']}\n"
            f"Missing UI anchors: {level_stats['missing_ui']}\n"
            f"Missing dependencies: {level_stats['missing_deps']}\n"
            f"Missing API information: {level_stats['missing_apis']}\n"
        )
        return hierarchy

# --------------- CODE CHANGE SUMMARY ---------------
# FIXED
# - Log path resolution: Changed log_to_sublog call from self.project_config.get_logs_dir() to self.project_config.project_dir
# - Centralized logging: hierarchy_status.log now created in the correct project-specific logs directory

    def _collect_metadata_stats(self, docs: List[Document]) -> Dict[str, List[str]]:
        """Scan for missing/empty anchor attributes for each hierarchy level."""
        files, components, business, ui, deps, apis = [], [], [], [], [], []
        for doc in docs:
            meta = doc.metadata
            if not meta.get("source"): files.append(str(meta))
            if not meta.get("class_names") and not meta.get("function_names"): components.append(str(meta))
            if not meta.get("business_logic_indicators"): business.append(meta.get("source", "unknown"))
            if not meta.get("ui_elements") and not meta.get("screen_name"): ui.append(meta.get("source", "unknown"))
            if not meta.get("dependencies"): deps.append(meta.get("source", "unknown"))
            if not meta.get("api_endpoints") and not meta.get("db_operations"): apis.append(meta.get("source", "unknown"))
        return {
            "missing_files": files,
            "missing_components": components,
            "missing_business": business,
            "missing_ui": ui,
            "missing_deps": deps,
            "missing_apis": apis,
        }

    def _build_screen_input_validation_map(self, docs: List[Document]) -> Dict[str, Dict[str, List[str]]]:
        # Map screen_name -> input field -> [validation_rules]
        mapping = {}
        for doc in docs:
            screen = doc.metadata.get("screen_name")
            if not screen:
                continue
            inputs = doc.metadata.get("input_fields", [])
            validations = doc.metadata.get("validation_rules", [])
            if not isinstance(inputs, list): continue
            if not (inputs or validations): continue
            screen_map = mapping.setdefault(screen, {})
            for input_field in inputs:
                if input_field not in screen_map:
                    screen_map[input_field] = []
                if isinstance(validations, list) and validations:
                    screen_map[input_field].extend([v for v in validations if v not in screen_map[input_field]])
        return mapping

    def _create_component_index(self, docs: List[Document], missing: List[str]) -> Dict[str, Dict[str, List[str]]]:
        # By class/function/module/component
        component_index = {"classes": {}, "functions": {}, "interfaces": {}, "modules": {}, "missing": missing}
        for doc in docs:
            meta = doc.metadata
            source = meta.get("source", "")
            t = meta.get("chunk_hierarchy") or meta.get("type", "")
            try:
                if t == "class":
                    for class_name in meta.get("class_names", []):
                        if class_name:
                            component_index["classes"].setdefault(class_name, []).append(source)
                elif t == "function":
                    for func_name in meta.get("function_names", []):
                        if func_name:
                            component_index["functions"].setdefault(func_name, []).append(source)
                elif t == "interface":
                    for i_name in meta.get("interface_names", []):
                        if i_name:
                            component_index["interfaces"].setdefault(i_name, []).append(source)
                elif t == "module":
                    module_name = self._extract_module_name(source)
                    if module_name:
                        component_index["modules"].setdefault(module_name, []).append(source)
            except Exception as e:
                log_to_sublog(self.project_config.get_logs_dir(), "hierarchy_status.log",
                              f"[WARN] ComponentIndex error: {e}, meta: {meta}")
        return component_index

    def _extract_module_name(self, source: str) -> Optional[str]:
        try:
            filename = os.path.basename(source.replace("\\", "/"))
            return filename.rsplit(".", 1)[0] if filename else None
        except Exception as e:
            log_to_sublog(self.project_config.get_logs_dir(), "hierarchy_status.log",
                          f"[WARN] Failed to extract module name from {source}: {e}")
            return None

    def _create_file_index(self, docs: List[Document], missing: List[str]) -> Dict[str, Any]:
        index = {}
        for doc in docs:
            meta = doc.metadata
            source = meta.get("source", "")
            if not isinstance(source, str):
                continue
            summary = index.setdefault(source, {
                "chunk_count": 0,
                "total_tokens": 0,
                "chunk_types": set(),
                "functions": set(),
                "classes": set(),
                "dependencies": set(),
                "business_indicators": set(),
                "ui_elements": set(),
                "api_endpoints": set(),
                "file_type": meta.get("file_type", ""),
                "first_chunk_preview": ""
            })
            summary["chunk_count"] += 1
            # accumulate types, anchors
            summary["chunk_types"].add(meta.get("type", "unknown"))
            summary["functions"].update(meta.get("function_names", []))
            summary["classes"].update(meta.get("class_names", []))
            summary["dependencies"].update(meta.get("dependencies", []))
            summary["business_indicators"].update(meta.get("business_logic_indicators", []))
            summary["ui_elements"].update(meta.get("ui_elements", []))
            summary["api_endpoints"].update(meta.get("api_endpoints", []))
            if not summary["first_chunk_preview"] and hasattr(doc, "page_content"):
                content = doc.page_content
                if isinstance(content, str):
                    summary["first_chunk_preview"] = content[:300] + "..." if len(content) > 300 else content
        # flatten sets, add missing
        for file_data in index.values():
            file_data["chunk_types"] = list(file_data["chunk_types"])
            file_data["functions"] = list(file_data["functions"])
            file_data["classes"] = list(file_data["classes"])
            file_data["dependencies"] = list(file_data["dependencies"])
            file_data["business_indicators"] = list(file_data["business_indicators"])
            file_data["ui_elements"] = list(file_data["ui_elements"])
            file_data["api_endpoints"] = list(file_data["api_endpoints"])
        index["missing"] = missing
        return index

    def _create_business_logic_index(self, docs: List[Document], missing: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        index = {
            "validation_rules": [], "business_processes": [], "calculations": [],
            "workflows": [], "authentication": [], "authorization": [], "missing": missing
        }
        for doc in docs:
            meta = doc.metadata
            source = meta.get("source", "")
            indicators = meta.get("business_logic_indicators", [])
            if not isinstance(source, str) or not isinstance(indicators, list):
                continue
            for indicator in indicators:
                if indicator in index:
                    preview = getattr(doc, "page_content", "")[:200]
                    index[indicator].append({
                        "source": source,
                        "chunk_index": meta.get("chunk_index", 0),
                        "preview": preview + "..." if len(preview) >= 200 else preview
                    })
            for rule in meta.get("validation_rules", []):
                index["validation_rules"].append({
                    "source": source,
                    "chunk_index": meta.get("chunk_index", 0),
                    "rule": rule
                })
        return index

    def _create_ui_flow_index(self, docs: List[Document], missing: List[str]) -> Dict[str, Any]:
        index = {
            "screens": {},
            "navigation_flows": [],
            "ui_components": {},
            "user_interactions": [],
            "missing": missing
        }
        nav_keywords = ["navigate", "startactivity", "router.push", "href", "onclick"]
        for doc in docs:
            meta = doc.metadata
            source = meta.get("source", "")
            content = getattr(doc, "page_content", "")
            chunk_index = meta.get("chunk_index", 0)
            # UI Components
            for elem in meta.get("ui_elements", []):
                if isinstance(elem, str):
                    index["ui_components"].setdefault(elem, []).append({
                        "source": source,
                        "chunk_index": chunk_index
                    })
            # Screens
            if isinstance(meta.get("screen_name"), str):
                screen = meta.get("screen_name")
                preview = content[:200] + "..." if len(content) > 200 else content
                index["screens"].setdefault(screen, []).append({
                    "source": source, "chunk_index": chunk_index, "preview": preview
                })
            # Navigation
            if isinstance(content, str) and any(k in content.lower() for k in nav_keywords):
                index["navigation_flows"].append({
                    "source": source, "chunk_index": chunk_index, "preview": content[:200] + "..." if len(content) > 200 else content
                })
        return index

    def _create_dependency_index(self, docs: List[Document], missing: List[str]) -> Dict[str, Any]:
        index = {
            "import_graph": {},
            "external_dependencies": set(),
            "internal_dependencies": set(),
            "missing": missing
        }
        all_files = {doc.metadata.get("source") for doc in docs if isinstance(doc.metadata.get("source"), str)}
        for doc in docs:
            meta = doc.metadata
            source = meta.get("source", "")
            deps = meta.get("dependencies", [])
            if not isinstance(source, str) or not isinstance(deps, list):
                continue
            index["import_graph"][source] = deps
            for dep in deps:
                if any(dep.lower() in file.lower() for file in all_files):
                    index["internal_dependencies"].add(dep)
                else:
                    index["external_dependencies"].add(dep)
        # flatten sets
        index["internal_dependencies"] = list(index["internal_dependencies"])
        index["external_dependencies"] = list(index["external_dependencies"])
        return index

    def _create_api_index(self, docs: List[Document], missing: List[str]) -> Dict[str, List[Dict[str, str]]]:
        index = {"endpoints": [], "database_operations": [], "external_apis": [], "missing": missing}
        for doc in docs:
            meta = doc.metadata
            source = meta.get("source", "")
            content = getattr(doc, "page_content", "")
            chunk_index = meta.get("chunk_index", 0)
            for endpoint in meta.get("api_endpoints", []):
                if isinstance(endpoint, str):
                    index["endpoints"].append({
                        "endpoint": endpoint,
                        "source": source,
                        "chunk_index": chunk_index,
                        "preview": content[:200] + "..." if len(content) > 200 else content
                    })
            for dbop in meta.get("db_operations", []):
                if isinstance(dbop, str):
                    index["database_operations"].append({
                        "operation": dbop,
                        "source": source,
                        "chunk_index": chunk_index,
                        "preview": content[:200] + "..." if len(content) > 200 else content
                    })
        return index

    def load_hierarchy(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.hierarchy_file):
            try:
                with open(self.hierarchy_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                log_to_sublog(self.project_config.get_logs_dir(), "hierarchy_status.log",
                              f"[WARN] Failed to load hierarchy: {e}")
                return None
        return None

    def get_relevant_hierarchy_level(self, intent: str) -> Optional[str]:
        return {
            "overview": "file_level",
            "impact_analysis": "dependency_level",
            "business_logic": "business_level",
            "ui_flow": "ui_level",
            "technical": "component_level",
            "api": "api_level"
        }.get(intent, None)


# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - All old methods with minimal metadata checks, lack of missing anchor surfacing, lines ~20-85: replaced by _collect_metadata_stats and augmented indexing.
# - Silent failures for missing metadata or orphans: now logged in hierarchy_status.log, lines ~24-32.
# ADDED
# - _collect_metadata_stats (lines 20–36): Gathers and logs all documents missing semantic anchors at every hierarchy level, logs to sublog for diagnosis.
# - All _create_*_index methods now take `missing` list and surface/fill "missing" key in index output for easy root-cause review.
# - Central log_highlight and log_to_sublog usage (all project-local, import from logger.py).
# - All log/diagnostic/summary helpers pulled from logger.py for DRY-ness and consistency.
