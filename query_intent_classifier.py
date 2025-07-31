import re
from typing import Dict, List, Tuple
from config import ProjectConfig

class QueryIntentClassifier:
    """Classifies user query intent for better retrieval and processing."""

    def __init__(self, project_config: ProjectConfig):
        self.project_config = project_config
        self.intent_patterns = {
            "overview": {
                "patterns": [
                    r"what.*(?:does|is).*(?:this|the).*(?:project|app|application|codebase)",
                    r"overview.*(?:of|for).*(?:project|app|application)",
                    r"describe.*(?:project|app|application)",
                    r"purpose.*(?:of|for).*(?:this|the)",
                ],
                "keywords": ["overview", "about", "purpose", "what does", "describe", "explain"]
            },
            "impact_analysis": {
                "patterns": [
                    r"impact.*(?:of|if).*(?:chang|modif|remov|delet)",
                    r"what.*(?:happen|break|affect).*if.*(?:chang|remov|delet)",
                    r"consequence.*(?:of|if).*(?:chang|modif)",
                    r"dependencies.*(?:of|for|on)",
                ],
                "keywords": ["impact", "affect", "break", "change", "dependencies", "consequence"]
            },
            "business_logic": {
                "patterns": [
                    r"business.*logic.*(?:in|for|of)",
                    r"(?:validation|rule|process).*(?:in|for|of)",
                    r"how.*(?:work|process|handle|validate)",
                    r"logic.*(?:behind|in|for)",
                ],
                "keywords": ["business logic", "validation", "rules", "process", "algorithm", "workflow"]
            },
            "validation": {
                "patterns": [
                    r"validation.*(?:for|on|in|of)",
                    r"what.*is.*validation.*for",
                    r"input.*validation",
                    r"validate.*input",
                ],
                "keywords": ["validation", "validate", "input validation", "field validation", "rule"]
            },
            "ui_flow": {
                "patterns": [
                    r"(?:screen|page|view|ui).*(?:flow|navigation|switch)",
                    r"how.*(?:navigate|move|go).*(?:to|from|between)",
                    r"user.*(?:flow|journey|path)",
                    r"navigation.*(?:to|from|between)",
                ],
                "keywords": ["screen", "page", "navigation", "ui", "flow", "interface", "user flow"]
            },
            "technical": {
                "patterns": [
                    r"how.*(?:implement|work|code|built)",
                    r"(?:implementation|architecture|design).*(?:of|for)",
                ],
                "keywords": ["implementation", "architecture", "how it works", "technical", "function", "method"]
            },
        }

    def classify_intent(self, query: str) -> Tuple[str, float]:
        query_lower = query.lower().strip()
        intent_scores = {}
        for intent, config in self.intent_patterns.items():
            score = 0
            for pattern in config["patterns"]:
                if re.search(pattern, query_lower):
                    score += 2
            for keyword in config["keywords"]:
                if keyword.lower() in query_lower:
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            max_possible_score = max(len(config["patterns"]) * 2 + len(config["keywords"]) for config in self.intent_patterns.values())
            confidence = best_intent[1] / max_possible_score
            return best_intent[0], confidence
        return "general", 0.1

    def get_query_context_hints(self, intent: str, query: str) -> Dict[str, List[str]]:
        # Same logic as before, but now able to route "validation" and "ui_flow" intents
        hints = {
            "search_terms": [],
            "file_priorities": [],
            "chunk_types": []
        }
        if intent == "overview":
            hints["search_terms"] = ["main", "app", "application"] + self.project_config.get_priority_files()
            hints["chunk_types"] = ["class", "module"]
        elif intent == "impact_analysis":
            file_mentions = self._extract_file_mentions(query)
            hints["search_terms"] = file_mentions + ["import", "dependency", "require"]
            hints["chunk_types"] = ["import", "function", "class"]
        elif intent == "business_logic":
            hints["search_terms"] = ["validate", "process", "business", "logic", "rule"]
            hints["chunk_types"] = ["function", "validation"]
        elif intent == "validation":  # <--- NEW
            hints["search_terms"] = ["validate", "required", "input", "error"]
            hints["chunk_types"] = ["validation", "input"]
        elif intent == "ui_flow":
            hints["search_terms"] = ["screen", "activity", "fragment", "page", "navigate", "route"]
            hints["chunk_types"] = ["navigation", "ui_element"]
        elif intent == "technical":
            hints["search_terms"] = ["function", "method", "algorithm", "implement"]
            hints["chunk_types"] = ["function", "class", "algorithm"]
        return hints

    def _extract_file_mentions(self, query: str) -> List[str]:
        file_mentions = re.findall(r'\b[A-Z][a-zA-Z0-9_]*[a-zA-Z0-9]\b', query)
        extensions = self.project_config.get_extensions()
        for ext in extensions:
            pattern = rf'\b\w+{re.escape(ext)}\b'
            file_mentions.extend(re.findall(pattern, query, re.IGNORECASE))
        return list(set(file_mentions))

    def suggest_better_query(self, query: str, intent: str) -> str:
        suggestions = {
            "overview": f"What does this {self.project_config.project_type} project do and what are its main components?",
            "impact_analysis": f"What files and components depend on [COMPONENT_NAME] and would be affected if it changes?",
            "business_logic": f"What is the business logic and validation rules in [SCREEN/COMPONENT_NAME]?",
            "validation": f"What input validations are there for [INPUT_FIELD] in [SCREEN_NAME]?",
            "ui_flow": f"How does the user navigate between screens in this {self.project_config.project_type} app?",
            "technical": f"How is [FEATURE/COMPONENT] implemented in this {self.project_config.project_type} project?",
        }
        return suggestions.get(intent, query)
