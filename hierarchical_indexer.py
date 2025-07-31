import os
import json
from typing import Any, Dict, List, Optional
from langchain.docstore.document import Document
from config import ProjectConfig


class HierarchicalIndexer:
    def __init__(self, project_config: ProjectConfig, metadata_dir: str = "./vector_db"):
        self.project_config = project_config
        self.metadata_dir = metadata_dir
        self.hierarchy_file = os.path.join(metadata_dir, "hierarchical_index.json")

    def create_hierarchical_index(self, documents: List[Document]) -> Dict[str, Any]:
        hierarchy = {
            "file_level": self._create_file_index(documents),
            "component_level": self._create_component_index(documents),
            "business_level": self._create_business_logic_index(documents),
            "ui_level": self._create_ui_flow_index(documents),
            "dependency_level": self._create_dependency_index(documents),
            "api_level": self._create_api_index(documents),
        }

        os.makedirs(self.metadata_dir, exist_ok=True)
        with open(self.hierarchy_file, "w") as f:
            json.dump(hierarchy, f, indent=2)

        return hierarchy

    def _create_component_index(self, docs: List[Document]) -> Dict[str, Dict[str, List[str]]]:
        component_index = {
            "classes": {}, "functions": {}, "interfaces": {}, "modules": {}
        }

        for doc in docs:
            source = doc.metadata.get("source", "")
            if not isinstance(source, str):
                continue

            hierarchy_type = doc.metadata.get("chunk_hierarchy", "")

            try:
                if hierarchy_type == "class":
                    for class_name in doc.metadata.get("class_names", []):
                        if isinstance(class_name, str) and class_name:
                            component_index["classes"].setdefault(class_name, []).append(source)

                elif hierarchy_type == "function":
                    for func_name in doc.metadata.get("function_names", []):
                        if isinstance(func_name, str) and func_name:
                            component_index["functions"].setdefault(func_name, []).append(source)

                elif hierarchy_type == "module":
                    module_name = self._extract_module_name(source)
                    if module_name:
                        component_index["modules"].setdefault(module_name, []).append(source)

            except Exception as e:
                print(f"[WARN] Component indexing error in {source}: {e}")

        return component_index

    def _extract_module_name(self, source: str) -> Optional[str]:
        try:
            filename = os.path.basename(source.replace("\\", "/"))
            return filename.rsplit(".", 1)[0] if filename else None
        except Exception as e:
            print(f"[WARN] Failed to extract module name from {source}: {e}")
            return None

    def _create_file_index(self, docs: List[Document]) -> Dict[str, Any]:
        index = {}

        for doc in docs:
            source = doc.metadata.get("source", "")
            if not isinstance(source, str):
                continue

            summary = index.setdefault(source, {
                "chunk_count": 0,
                "total_tokens": 0,
                "complexity_scores": [],
                "chunk_types": set(),
                "functions": set(),
                "classes": set(),
                "dependencies": set(),
                "business_indicators": set(),
                "ui_elements": set(),
                "api_endpoints": set(),
                "file_type": doc.metadata.get("file_type", ""),
                "first_chunk_preview": ""
            })

            summary["chunk_count"] += 1
            summary["total_tokens"] += doc.metadata.get("estimated_tokens", 0)

            summary["chunk_types"].add(doc.metadata.get("type", "unknown"))
            summary["functions"].update(doc.metadata.get("function_names", []))
            summary["classes"].update(doc.metadata.get("class_names", []))
            summary["dependencies"].update(doc.metadata.get("dependencies", []))
            summary["business_indicators"].update(doc.metadata.get("business_logic_indicators", []))
            summary["ui_elements"].update(doc.metadata.get("ui_elements", []))
            summary["api_endpoints"].update(doc.metadata.get("api_endpoints", []))

            score = doc.metadata.get("complexity_score")
            if isinstance(score, (int, float)):
                summary["complexity_scores"].append(score)

            if not summary["first_chunk_preview"] and hasattr(doc, "page_content"):
                content = doc.page_content
                if isinstance(content, str):
                    summary["first_chunk_preview"] = content[:300] + "..." if len(content) > 300 else content

        # Finalize
        for file_data in index.values():
            file_data["chunk_types"] = list(file_data["chunk_types"])
            file_data["functions"] = list(file_data["functions"])
            file_data["classes"] = list(file_data["classes"])
            file_data["dependencies"] = list(file_data["dependencies"])
            file_data["business_indicators"] = list(file_data["business_indicators"])
            file_data["ui_elements"] = list(file_data["ui_elements"])
            file_data["api_endpoints"] = list(file_data["api_endpoints"])

            scores = file_data.pop("complexity_scores", [])
            file_data["avg_complexity"] = round(sum(scores) / len(scores), 2) if scores else 0
            file_data["max_complexity"] = max(scores) if scores else 0

        return index

    def _create_business_logic_index(self, docs: List[Document]) -> Dict[str, List[Dict[str, Any]]]:
        index = {
            "validation_rules": [], "business_processes": [], "calculations": [],
            "workflows": [], "authentication": [], "authorization": []
        }

        for doc in docs:
            source = doc.metadata.get("source", "")
            indicators = doc.metadata.get("business_logic_indicators", [])

            if not isinstance(source, str) or not isinstance(indicators, list):
                continue

            for indicator in indicators:
                if indicator in index:
                    preview = getattr(doc, "page_content", "")[:200]
                    index[indicator].append({
                        "source": source,
                        "chunk_index": doc.metadata.get("chunk_index", 0),
                        "preview": preview + "..." if len(preview) >= 200 else preview
                    })

            for rule in doc.metadata.get("validation_rules", []):
                index["validation_rules"].append({
                    "source": source,
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "rule": rule
                })

        return index

    def _create_ui_flow_index(self, docs: List[Document]) -> Dict[str, Any]:
        index = {
            "screens": {},
            "navigation_flows": [],
            "ui_components": {},
            "user_interactions": []
        }

        nav_keywords = ["navigate", "startactivity", "router.push", "href", "onclick"]

        for doc in docs:
            source = doc.metadata.get("source", "")
            if not isinstance(source, str):
                continue

            content = getattr(doc, "page_content", "")
            chunk_index = doc.metadata.get("chunk_index", 0)

            # UI Components
            for elem in doc.metadata.get("ui_elements", []):
                if isinstance(elem, str):
                    index["ui_components"].setdefault(elem, []).append({
                        "source": source,
                        "chunk_index": chunk_index
                    })

            # Screens
            for screen in doc.metadata.get("screen_references", []):
                if isinstance(screen, str):
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

    def _create_dependency_index(self, docs: List[Document]) -> Dict[str, Any]:
        index = {
            "import_graph": {},
            "external_dependencies": set(),
            "internal_dependencies": set()
        }

        all_files = {doc.metadata.get("source") for doc in docs if isinstance(doc.metadata.get("source"), str)}

        for doc in docs:
            source = doc.metadata.get("source", "")
            deps = doc.metadata.get("dependencies", [])

            if not isinstance(source, str) or not isinstance(deps, list):
                continue

            index["import_graph"][source] = deps

            for dep in deps:
                if any(dep.lower() in file.lower() for file in all_files):
                    index["internal_dependencies"].add(dep)
                else:
                    index["external_dependencies"].add(dep)

        index["internal_dependencies"] = list(index["internal_dependencies"])
        index["external_dependencies"] = list(index["external_dependencies"])

        return index

    def _create_api_index(self, docs: List[Document]) -> Dict[str, List[Dict[str, str]]]:
        index = {"endpoints": [], "database_operations": [], "external_apis": []}

        for doc in docs:
            source = doc.metadata.get("source", "")
            if not isinstance(source, str):
                continue

            content = getattr(doc, "page_content", "")
            chunk_index = doc.metadata.get("chunk_index", 0)

            for endpoint in doc.metadata.get("api_endpoints", []):
                if isinstance(endpoint, str):
                    index["endpoints"].append({
                        "endpoint": endpoint,
                        "source": source,
                        "chunk_index": chunk_index,
                        "preview": content[:200] + "..." if len(content) > 200 else content
                    })

            for dbop in doc.metadata.get("db_operations", []):
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
                print(f"[WARN] Failed to load hierarchy: {e}")
        return None

    def get_relevant_hierarchy_level(self, intent: str) -> Optional[str]:
        return {
            "overview": "file_level",
            "impact_analysis": "dependency_level",
            "business_logic": "business_level",
            "ui_flow": "ui_level",
            "technical": "component_level",
            "api": "api_level"
        }.get(intent)
