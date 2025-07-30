# hierarchical_indexer.py

import json
import os
from typing import Dict, List, Any, Optional
from langchain.docstore.document import Document
from config import ProjectConfig

class HierarchicalIndexer:
    """Creates hierarchical indexes for different query types and processing levels."""
    
    def __init__(self, project_config: ProjectConfig, metadata_dir: str = "./vector_db"):
        self.project_config = project_config
        self.metadata_dir = metadata_dir
        self.hierarchy_file = os.path.join(metadata_dir, "hierarchical_index.json")
        
    def create_hierarchical_index(self, documents: List[Document]) -> Dict[str, Any]:
        """Create multiple index levels for different query types."""
        
        hierarchy = {
            "file_level": self._create_file_summaries(documents),
            "component_level": self._create_component_index(documents),
            "business_level": self._create_business_logic_index(documents),
            "ui_level": self._create_ui_flow_index(documents),
            "dependency_level": self._create_dependency_index(documents),
            "api_level": self._create_api_index(documents)
        }
        
        # Save hierarchy to file
        os.makedirs(self.metadata_dir, exist_ok=True)
        with open(self.hierarchy_file, 'w') as f:
            json.dump(hierarchy, f, indent=2)
        
        return hierarchy
    
    def _create_file_summaries(self, documents: List[Document]) -> Dict[str, Any]:
        """Create file-level summaries and statistics."""
        file_summaries = {}
        
        for doc in documents:
            source = doc.metadata.get('source')
            if not source:
                continue
                
            if source not in file_summaries:
                file_summaries[source] = {
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
                    "file_type": doc.metadata.get('file_type', ''),
                    "first_chunk_preview": ""
                }
            
            file_info = file_summaries[source]
            file_info["chunk_count"] += 1
            file_info["total_tokens"] += doc.metadata.get('estimated_tokens', 0)
            
            # Collect complexity scores
            complexity = doc.metadata.get('complexity_score', 0)
            if complexity > 0:
                file_info["complexity_scores"].append(complexity)
            
            # Collect various metadata
            file_info["chunk_types"].add(doc.metadata.get('type', 'unknown'))
            
            functions = doc.metadata.get('function_names', [])
            file_info["functions"].update(functions)
            
            classes = doc.metadata.get('class_names', [])
            file_info["classes"].update(classes)
            
            dependencies = doc.metadata.get('dependencies', [])
            file_info["dependencies"].update(dependencies)
            
            business_indicators = doc.metadata.get('business_logic_indicators', [])
            file_info["business_indicators"].update(business_indicators)
            
            ui_elements = doc.metadata.get('ui_elements', [])
            file_info["ui_elements"].update(ui_elements)
            
            api_endpoints = doc.metadata.get('api_endpoints', [])
            file_info["api_endpoints"].update(api_endpoints)
            
            # Store first chunk as preview
            if not file_info["first_chunk_preview"]:
                preview = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                file_info["first_chunk_preview"] = preview
        
        # Convert sets to lists for JSON serialization and calculate averages
        for source, info in file_summaries.items():
            info["chunk_types"] = list(info["chunk_types"])
            info["functions"] = list(info["functions"])
            info["classes"] = list(info["classes"])
            info["dependencies"] = list(info["dependencies"])
            info["business_indicators"] = list(info["business_indicators"])
            info["ui_elements"] = list(info["ui_elements"])
            info["api_endpoints"] = list(info["api_endpoints"])
            
            # Calculate average complexity
            if info["complexity_scores"]:
                info["avg_complexity"] = sum(info["complexity_scores"]) / len(info["complexity_scores"])
                info["max_complexity"] = max(info["complexity_scores"])
            else:
                info["avg_complexity"] = 0
                info["max_complexity"] = 0
        
        return file_summaries
    
    def _create_component_index(self, documents: List[Document]) -> Dict[str, List[str]]:
        """Create component-level index (classes, functions, etc.)."""
        component_index = {
            "classes": {},
            "functions": {},
            "interfaces": {},
            "modules": {}
        }
        
        for doc in documents:
            source = doc.metadata.get('source', '')
            chunk_hierarchy = doc.metadata.get('chunk_hierarchy', '')
            
            # Index by component type
            if chunk_hierarchy == 'class':
                classes = doc.metadata.get('class_names', [])
                for class_name in classes:
                    if class_name not in component_index["classes"]:
                        component_index["classes"][class_name] = []
                    component_index["classes"][class_name].append(source)
            
            elif chunk_hierarchy == 'function':
                functions = doc.metadata.get('function_names', [])
                for func_name in functions:
                    if func_name not in component_index["functions"]:
                        component_index["functions"][func_name] = []
                    component_index["functions"][func_name].append(source)
            
            elif chunk_hierarchy == 'module':
                module_name = source.split('/')[-1].split('.')
                if module_name not in component_index["modules"]:
                    component_index["modules"][module_name] = []
                component_index["modules"][module_name].append(source)
        
        return component_index
    
    def _create_business_logic_index(self, documents: List[Document]) -> Dict[str, List[Dict[str, str]]]:
        """Create business logic focused index."""
        business_index = {
            "validation_rules": [],
            "business_processes": [],
            "calculations": [],
            "workflows": [],
            "authentication": [],
            "authorization": []
        }
        
        for doc in documents:
            source = doc.metadata.get('source', '')
            business_indicators = doc.metadata.get('business_logic_indicators', [])
            validations = doc.metadata.get('validation_rules', [])
            
            for indicator in business_indicators:
                if indicator in business_index:
                    business_index[indicator].append({
                        "source": source,
                        "chunk_index": doc.metadata.get('chunk_index', 0),
                        "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    })
            
            if validations:
                business_index["validation_rules"].append({
                    "source": source,
                    "chunk_index": doc.metadata.get('chunk_index', 0),
                    "validations": validations,
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
        
        return business_index
    
    def _create_ui_flow_index(self, documents: List[Document]) -> Dict[str, Any]:
        """Create UI/screen flow focused index."""
        ui_index = {
            "screens": {},
            "navigation_flows": [],
            "ui_components": {},
            "user_interactions": []
        }
        
        for doc in documents:
            source = doc.metadata.get('source', '')
            ui_elements = doc.metadata.get('ui_elements', [])
            screen_refs = doc.metadata.get('screen_references', [])
            
            # Index UI elements
            for element in ui_elements:
                if element not in ui_index["ui_components"]:
                    ui_index["ui_components"][element] = []
                ui_index["ui_components"][element].append({
                    "source": source,
                    "chunk_index": doc.metadata.get('chunk_index', 0)
                })
            
            # Index screen references
            for screen in screen_refs:
                if screen not in ui_index["screens"]:
                    ui_index["screens"][screen] = []
                ui_index["screens"][screen].append({
                    "source": source,
                    "chunk_index": doc.metadata.get('chunk_index', 0),
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            
            # Detect navigation patterns
            content_lower = doc.page_content.lower()
            navigation_keywords = ['navigate', 'startactivity', 'router.push', 'href', 'onclick']
            if any(keyword in content_lower for keyword in navigation_keywords):
                ui_index["navigation_flows"].append({
                    "source": source,
                    "chunk_index": doc.metadata.get('chunk_index', 0),
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
        
        return ui_index
    
    def _create_dependency_index(self, documents: List[Document]) -> Dict[str, Any]:
        """Create dependency mapping index."""
        dependency_index = {
            "import_graph": {},
            "external_dependencies": set(),
            "internal_dependencies": set()
        }
        
        project_files = set()
        all_dependencies = set()
        
        # First pass: collect all files and dependencies
        for doc in documents:
            source = doc.metadata.get('source', '')
            if source:
                project_files.add(source)
            
            dependencies = doc.metadata.get('dependencies', [])
            all_dependencies.update(dependencies)
        
        # Second pass: categorize dependencies and build graph
        for doc in documents:
            source = doc.metadata.get('source', '')
            dependencies = doc.metadata.get('dependencies', [])
            
            if source and dependencies:
                dependency_index["import_graph"][source] = dependencies
                
                for dep in dependencies:
                    # Check if it's an internal or external dependency
                    is_internal = any(dep.lower() in pf.lower() for pf in project_files)
                    
                    if is_internal:
                        dependency_index["internal_dependencies"].add(dep)
                    else:
                        dependency_index["external_dependencies"].add(dep)
        
        # Convert sets to lists for JSON serialization
        dependency_index["external_dependencies"] = list(dependency_index["external_dependencies"])
        dependency_index["internal_dependencies"] = list(dependency_index["internal_dependencies"])
        
        return dependency_index
    
    def _create_api_index(self, documents: List[Document]) -> Dict[str, List[Dict[str, str]]]:
        """Create API endpoints and database operations index."""
        api_index = {
            "endpoints": [],
            "database_operations": [],
            "external_apis": []
        }
        
        for doc in documents:
            source = doc.metadata.get('source', '')
            api_endpoints = doc.metadata.get('api_endpoints', [])
            db_operations = doc.metadata.get('db_operations', [])
            
            for endpoint in api_endpoints:
                api_index["endpoints"].append({
                    "endpoint": endpoint,
                    "source": source,
                    "chunk_index": doc.metadata.get('chunk_index', 0),
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            
            for db_op in db_operations:
                api_index["database_operations"].append({
                    "operation": db_op,
                    "source": source,
                    "chunk_index": doc.metadata.get('chunk_index', 0),
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
        
        return api_index
    
    def load_hierarchy(self) -> Optional[Dict[str, Any]]:
        """Load existing hierarchical index."""
        if os.path.exists(self.hierarchy_file):
            try:
                with open(self.hierarchy_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def get_relevant_hierarchy_level(self, intent: str) -> Optional[str]:
        """Get the most relevant hierarchy level for a given intent."""
        intent_to_level = {
            "overview": "file_level",
            "impact_analysis": "dependency_level",
            "business_logic": "business_level",
            "ui_flow": "ui_level",
            "technical": "component_level",
            "api": "api_level"
        }
        return intent_to_level.get(intent)
