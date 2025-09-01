# core/query_intent_classifier.py - ENHANCED VERSION

import re
from typing import Tuple, Dict, List, Optional
from config import ProjectConfig
from logger import log_highlight, log_to_sublog

class QueryIntentClassifier:
    """Enhanced classifier supporting questionnaire-level complexity."""
    
    # core/query_intent_classifier.py - ENHANCED PATTERN_MAP
    PATTERN_MAP: Dict[str, List[str]] = {
        "overview": [
            # EXISTING patterns...
            r"\b(overview|structure|architecture|summary|top level|entry point|project files|high level|all files|main flow|overall)\b",
            r"\b(what does this project do|project purpose|main purpose|what is this|project description|project overview)\b",
            r"\b(what is the main|main activity|MainActivity|application purpose|app does what|name of.*application)\b",
            # 🚀 NEW: Missing patterns for better coverage
            r"\b(application name|project name|app name|what.*app.*called)\b",
            r"\b(usage|use case|end.?user|how.*use|purpose|functionality)\b",
            r"\b(features|capabilities|what.*can.*do|main.*function)\b"
        ],
        
        "location_usage": [
            # Enhanced patterns with method signature keywords
            r"\b(where is|where are|location of|definition of|find|locate)\b.*\b(class|method|function|component|file|screen|logic)\b",
            r"\b(which file|which module|which package|in what file|where should I)\b",
            r"\b(how many times|invoked|called|used|imported)\b",
            r"\b(add.*feature|write.*logic|implement.*functionality|modify.*code)\b",
            # 🚀 NEW: Method signature related patterns
            r"\b(method signature|function signature|parameters|return type)\b",
            r"\b(override|implement|extend)\b.*\b(method|function)\b"
        ],
        
        "code_relationship": [  # NEW: Level 3 - Relationships & flow
            r"\b(inherit|inheritance|extends|implements|override|call hierarchy|dependency|dependencies)\b",
            r"\b(calls|called by|invokes|invoked by|interacts with|communicates with)\b", 
            r"\b(upstream|downstream|parent|child|base class|derived class)\b",
            r"\b(data flow|execution flow|control flow|passes data)\b"
        ],
        
        "semantic_reasoning": [  # NEW: Level 4 - Deep understanding
            r"\b(architectural role|design pattern|system role|responsibility|collaborate)\b",
            r"\b(complete flow|end to end|lifecycle|user interaction|backend processing)\b",
            r"\b(state management|data transformation|error handling|exception handling)\b",
            r"\b(ripple effect|breaking change|impact|modify.*return type|change.*logic)\b"
        ],
        
        "deep_architecture": [  # NEW: Level 5 - Advanced reasoning
            r"\b(integration|third.party|external service|API|diagnostic|debug|troubleshoot)\b",
            r"\b(concurrency|thread safety|performance|scalability|bottleneck|race condition)\b",
            r"\b(retry mechanism|circuit breaker|fallback|high availability)\b",
            r"\b(framework decision|pattern choice|trade.off|maintainability|testability)\b"
        ],
        
        # EXISTING intents remain
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
        
        # Check for project overview questions first (highest priority)
        overview_patterns = [
            r"\b(what does this project do|project purpose|main purpose|what is this|project description|project overview)\b",
            r"\b(what is the main|main activity|MainActivity|application purpose|app does what)\b"
        ]
        
        for pat in overview_patterns:
            if re.search(pat, query, re.IGNORECASE):
                log_to_sublog(".", 'intent_classification.log',
                              f"[HIGH CONFIDENCE] Query: '{query}' matched 'overview' via pattern '{pat}'.")
                return 'overview', 0.95  # High confidence for project overview questions
        
        # Check other patterns
        for label, patterns in self.PATTERN_MAP.items():
            for pat in patterns:
                if re.search(pat, query, re.IGNORECASE):
                    confidence = 0.9 if label == 'overview' else 0.8
                    log_to_sublog(".", 'intent_classification.log',
                                  f"[SELECTED] Query: '{query}' matched '{label}' via pattern '{pat}'.")
                    return label, confidence
        
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
