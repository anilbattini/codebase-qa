# config.py

import os
from typing import Dict, List, Tuple

class ProjectConfig:
    """Configuration class for different project types and languages."""

    # Language configurations
    LANGUAGE_CONFIGS = {
        "android": {
            "extensions": (".kt", ".kts", ".java", ".xml", ".gradle", ".properties", ".toml"),
            "priority_files": ["activity", "fragment", "manifest", "mainactivity"],
            "priority_extensions": [".kt", ".java"],
            "secondary_extensions": [".xml"],
            "ignore_patterns": ["build/", "*.apk", "*.dex", ".gradle/"],
            "project_indicators": ["AndroidManifest.xml", "app/build.gradle"],
            "chunk_types": {
                "class": ["class ", "interface ", "enum "],
                "function": ["fun ", "def ", "public ", "private "],
                "import": ["import ", "package "],
                "annotation": ["@", "annotation"]
            },
            "summary_keywords": ["android", "activity", "fragment", "kotlin", "java"]
        },

        "javascript": {
            "extensions": (".js", ".ts", ".jsx", ".tsx", ".json", ".mjs"),
            "priority_files": ["index", "app", "main", "server"],
            "priority_extensions": [".js", ".ts"],
            "secondary_extensions": [".json"],
            "ignore_patterns": ["node_modules/", "dist/", "build/", "*.min.js"],
            "project_indicators": ["package.json", "tsconfig.json"],
            "chunk_types": {
                "class": ["class ", "interface "],
                "function": ["function ", "const ", "let ", "var ", "=>"],
                "import": ["import ", "require(", "export "],
                "type": ["type ", "interface "]
            },
            "summary_keywords": ["javascript", "typescript", "react", "node", "express"]
        },

        "python": {
            "extensions": (".py", ".pyx", ".pyi", ".txt", ".md", ".yml", ".yaml"),
            "priority_files": ["main", "app", "__init__", "server", "manage"],
            "priority_extensions": [".py"],
            "secondary_extensions": [".txt", ".md"],
            "ignore_patterns": ["__pycache__/", "*.pyc", ".pytest_cache/", "venv/"],
            "project_indicators": ["requirements.txt", "setup.py", "pyproject.toml"],
            "chunk_types": {
                "class": ["class "],
                "function": ["def ", "async def "],
                "import": ["import ", "from "],
                "decorator": ["@"]
            },
            "summary_keywords": ["python", "django", "flask", "fastapi"]
        },

        "web": {
            "extensions": (".html", ".css", ".scss", ".sass", ".js", ".ts", ".vue", ".svelte"),
            "priority_files": ["index", "app", "main"],
            "priority_extensions": [".js", ".ts", ".vue"],
            "secondary_extensions": [".html", ".css"],
            "ignore_patterns": ["node_modules/", "dist/", "build/"],
            "project_indicators": ["index.html", "package.json"],
            "chunk_types": {
                "component": ["component", "export default"],
                "function": ["function ", "const ", "=>"],
                "style": ["@media", ".class", "#id"],
                "import": ["import ", "require"]
            },
            "summary_keywords": ["web", "frontend", "react", "vue", "angular"]
        }
    }

    def __init__(self, project_type: str = None, custom_config: Dict = None):
        self.project_type = project_type or self.auto_detect_project_type()
        self.config = custom_config or self.LANGUAGE_CONFIGS.get(self.project_type, self.LANGUAGE_CONFIGS["python"])

    def auto_detect_project_type(self, project_dir: str = ".") -> str:
        """Auto-detect project type based on file indicators."""
        for project_type, config in self.LANGUAGE_CONFIGS.items():
            for indicator in config["project_indicators"]:
                if os.path.exists(os.path.join(project_dir, indicator)):
                    return project_type
        return "python"  # Default fallback

    def get_extensions(self) -> Tuple[str, ...]:
        return self.config["extensions"]

    def get_priority_files(self) -> List[str]:
        return self.config["priority_files"]

    def get_ignore_patterns(self) -> List[str]:
        return self.config["ignore_patterns"]

    def get_chunk_types(self) -> Dict[str, List[str]]:
        return self.config["chunk_types"]

    def get_summary_keywords(self) -> List[str]:
        return self.config["summary_keywords"]
