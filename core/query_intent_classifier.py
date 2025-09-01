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
            r"\b(impact|what if|affect|break|consequence|refactor|change in|modifying)\b"
        ]
    }

    def __init__(self, project_config: Optional[ProjectConfig] = None):
        self.project_config = project_config or ProjectConfig()
        log_highlight("QueryIntentClassifier initialized")
        
    def classify_intent(self, query: str) -> Tuple[str, float]:
        """Enhanced classification with higher confidence scores."""
        
        # Priority order: More specific intents first
        priority_order = [
            ('deep_architecture', 0.95),
            ('semantic_reasoning', 0.90), 
            ('code_relationship', 0.85),
            ('location_usage', 0.80),
            ('overview', 0.85),
            ('impact_analysis', 0.80),
            ('business_logic', 0.75),
            ('ui_flow', 0.75),
            ('validation', 0.75)
        ]
        
        for intent, base_confidence in priority_order:
            if intent in self.PATTERN_MAP:
                for pattern in self.PATTERN_MAP[intent]:
                    if re.search(pattern, query, re.IGNORECASE):
                        log_to_sublog(".", 'intent_classification.log',
                                    f"[MATCHED] Query: '{query}' -> '{intent}' (confidence: {base_confidence})")
                        return intent, base_confidence
        
        # Fallback with better confidence
        log_to_sublog(".", 'intent_classification.log',
                     f"[FALLBACK] Query: '{query}' -> 'technical' (confidence: 0.6)")
        return 'technical', 0.6  # Increased from 0.5
    
    
    def rerank_docs_by_intent(self, source_documents, query, intent):
        """
        Enhanced reranking supporting dynamic intent types via classifier patterns.
        
        Args:
            source_documents: List of retrieved Document objects
            query: Original user query string
            intent: Classified intent label
            classifier: QueryIntentClassifier instance for pattern access
            
        Returns:
            List[Document]: Top 5 reranked documents based on intent-specific scoring
        """
        
        def score(doc):
            """
            Calculate relevance score for document based on query and intent.
            
            Args:
                doc: Document object with metadata and content
                
            Returns:
                float: Computed relevance score
            """
            source = doc.metadata.get("source", "").lower()
            content = doc.page_content.lower()
            meta = doc.metadata
            score = 0.0
            
            # Base query token matching
            query_tokens = [token.strip() for token in query.lower().split() if len(token.strip()) > 2]
            for token in query_tokens:
                if token in content:
                    score += 1.0
                if token in source:
                    score += 0.5
            
            # Intent-specific scoring - dynamically handle all intents from classifier
            if intent in self.PATTERN_MAP:
                score += self._apply_intent_specific_scoring(intent, meta, source)
            else:
                # Fallback scoring for unknown intents
                score += self._apply_fallback_scoring(meta)
            
            return score
        
        # Sort and return top documents
        sorted_docs = sorted(source_documents, key=score, reverse=True)
        return sorted_docs[:5]

    # core/chat_handler.py - ENHANCED _apply_intent_specific_scoring
    def _apply_intent_specific_scoring(self, intent: str, meta: dict, source: str) -> float:
        """🚀 ENHANCED: Leverage rich metadata for superior scoring."""
        intent_score = 0.0
        
        # core/chat_handler.py - ADD to _apply_intent_specific_scoring

        if intent == "overview":
            # 🚀 ENHANCED: Comprehensive priority file detection
            priority_files = ["readme", "agent.md", "main", "manifest", "app.py", "index", "home"]
            if any(pf in source for pf in priority_files):
                intent_score += 5.0
            
            # NEW: Boost based on file-level metadata richness
            file_metadata_richness = 0
            if meta.get("class_names"):
                file_metadata_richness += len(meta["class_names"])
            if meta.get("function_names"):
                file_metadata_richness += len(meta["function_names"])
            if meta.get("business_logic_indicators"):
                file_metadata_richness += len(meta["business_logic_indicators"])
    
            # Files with rich metadata are good for overview
            if file_metadata_richness >= 5:
                intent_score += 3.0

                
        elif intent == "location_usage":
            # Enhanced with method signatures and call sites
            if meta.get("method_signatures"):
                intent_score += 4.0
            if meta.get("call_sites"):
                intent_score += 3.0
            # NEW: Boost based on semantic score from chunker
            semantic_score = meta.get("semantic_score", 0)
            if isinstance(semantic_score, (int, float)) and semantic_score > 2.0:
                intent_score += 2.0
                
        elif intent == "code_relationship":
            # Leverage inheritance and call graph data
            inheritance_info = meta.get("inheritance_info", {})
            if isinstance(inheritance_info, dict):
                if inheritance_info.get("extends") or inheritance_info.get("implements"):
                    intent_score += 5.0
            # NEW: Boost based on call sites richness
            call_sites = meta.get("call_sites", [])
            if isinstance(call_sites, list) and len(call_sites) >= 3:
                intent_score += 4.0
                
        elif intent == "semantic_reasoning":
            # Leverage design patterns and architectural indicators
            design_patterns = meta.get("design_patterns", [])
            if isinstance(design_patterns, list) and design_patterns:
                intent_score += 5.0  # Very important for architectural questions
            # NEW: Boost based on error handling sophistication
            error_patterns = meta.get("error_handling_patterns", [])
            if isinstance(error_patterns, list) and len(error_patterns) >= 2:
                intent_score += 3.0
            # NEW: Boost based on chunk hierarchy depth
            chunk_hierarchy = meta.get("chunk_hierarchy", "")
            if isinstance(chunk_hierarchy, str) and ">" in chunk_hierarchy:
                intent_score += 2.0
                
        elif intent == "deep_architecture":
            # Leverage API patterns and complex system indicators
            api_usage = meta.get("api_usage", [])
            if isinstance(api_usage, list):
                # Multiple API types indicate complex integration
                if len(api_usage) >= 2:
                    intent_score += 6.0
                elif api_usage:
                    intent_score += 3.0
            # NEW: Boost based on design pattern sophistication
            design_patterns = meta.get("design_patterns", [])
            if isinstance(design_patterns, list) and len(design_patterns) >= 2:
                intent_score += 4.0
        
        # Continue with existing logic...
        return intent_score


    def _apply_fallback_scoring(self, meta: dict) -> float:
        """
        Apply fallback scoring for unknown intents.
        
        Args:
            meta: Document metadata dictionary
            
        Returns:
            float: Fallback score based on general relevance indicators
        """
        fallback_score = 1.0
        
        # Boost documents with rich metadata
        if meta.get("function_names"):
            fallback_score += 1.0
        if meta.get("class_names"):
            fallback_score += 1.0
            
        return fallback_score
