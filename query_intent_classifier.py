import re
from typing import Tuple, Dict, List, Optional
from config import ProjectConfig
from logger import log_highlight, log_to_sublog

class QueryIntentClassifier:
    """Classifies user queries into supported RAG intents (overview, validation, ui_flow, impact, etc.) with logging."""

    # Extend or refine as needed; data-driven for easy add/remove
    PATTERN_MAP: Dict[str, List[str]] = {
        "overview": [
            r"\b(overview|structure|architecture|summary|top level|entry point|project files|high level|all files|main flow|overall)\b",
        ],
        "validation": [
            r"\b(validate|input field|required|constraint|rules|check for|form field|input rule|not null|input error)\b",
        ],
        "ui_flow": [
            r"\b(navigation|screen flow|routing|ui flow|navigate|fragment flow|activity flow|page flow|screen transitions|which screen|from.*to.*screen|user journey)\b"
        ],
        "business_logic": [
            r"\b(business logic|process|calculation|rule engine|invoicing|business process|workflow|authorization|permission|role check|policy|auth)\b"
        ],
        "impact_analysis": [
            r"\b(impact|what if|affect|break|consequence|dependency|dependencies|refactor|change in|modifying)\b"
        ]
    }

    def __init__(self, project_config: Optional[ProjectConfig] = None):
        self.project_config = project_config or ProjectConfig()
        log_highlight("QueryIntentClassifier initialized")

    def classify_intent(self, query: str) -> Tuple[str, float]:
        """Returns (intent_label, confidence_score) for user query."""
        log_highlight("QueryIntentClassifier.classify_intent")
        for label, patterns in self.PATTERN_MAP.items():
            for pat in patterns:
                if re.search(pat, query, re.IGNORECASE):
                    log_to_sublog(".", 'intent_classification.log',
                                  f"[SELECTED] Query: '{query}' matched '{label}' via pattern '{pat}'.")
                    return label, 1.0
        # No strong match, fallback to default (can add LLM classifier for advanced disambiguation)
        log_to_sublog(".", 'intent_classification.log',
                      f"[FALLBACK] Query: '{query}'—no pattern match. Defaulting to technical.")
        return 'technical', 0.5

    def get_query_context_hints(self, intent: str, query: str) -> Dict[str, List[str]]:
        """Provides context hints or anchor terms based on intent for use in retrieval/context phase."""
        hints = {}
        if intent in ['validation', 'business_logic']:
            extracted = re.findall(r'"([\w_]+)"|\'([\w_]+)\'|(\w+Field|\w+Input|[A-Z][a-zA-Z0-9]+Screen)', query)
            hints['fields_or_screens'] = [item for group in extracted for item in group if item]
        elif intent == 'overview':
            hints['overview_keywords'] = [k for k in self.project_config.get_summary_keywords()]
        elif intent == 'ui_flow':
            hints['ui_keywords'] = ["navigate", "screen", "fragment", "activity", "route"]
        return hints

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - No more in-method print() or ad-hoc diagnostic logging; all logs routed through logger.py.
# - Any duplicated intent label logic elsewhere—get_query_context_hints is the only place for context hint extraction.
# ADDED
# - Table-driven intent pattern map (easy to add/edit; per-stack hints come from config).
# - Centralized logging for all classification/fallback decisions.
# - get_query_context_hints acts as single place to extract retrieval/context anchor hints per intent.
