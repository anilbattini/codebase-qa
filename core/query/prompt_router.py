# core/prompt_router.py

from typing import Tuple, Optional, Any, Dict, Union
from logger import log_to_sublog

class PromptRouter:
    """
    Intent-driven prompt routing with specialized templates for RAG Codebase QA.
    
    Provides intent-specific prompts that preserve original user questions while
    leveraging enhanced context and rewritten queries for optimal LLM performance.
    
    Supports both Ollama (single prompt) and Cloud (system/user prompt) providers.
    """
    
    def __init__(self):
        """Initialize prompt router with intent-specific template mapping."""
        self._template_registry = self._initialize_template_registry()
    
    def build_enhanced_query(self, 
                           query: str, 
                           rewritten: str, 
                           intent: str, 
                           context: str, 
                           detail_level: str = "moderate",
                           provider: str = "ollama",
                           llm: Any = None,
                           project_dir: str = ".") -> Tuple[str, Optional[str]]:
        """
        Build intent-specific prompts optimized for provider architecture.
        
        Args:
            query: Original user question (preserved in final prompt)
            rewritten: Enhanced query for context (informational only)
            intent: Classified intent from QueryIntentClassifier
            context: Retrieved and formatted document context
            detail_level: Response detail level (simple/moderate/elaborate)
            provider: Target LLM provider (ollama/cloud)
            llm: LLM instance (for future provider-specific optimizations)
            project_dir: Project directory for logging
            
        Returns:
            Tuple[str, Optional[str]]: 
                - Ollama: (complete_prompt, None)
                - Cloud: (system_prompt, user_prompt)
        """
        
        log_to_sublog(project_dir, "prompt_router.log", 
                     f"Building {provider} prompt for intent: {intent}, detail_level: {detail_level}")
        
        # Get intent-specific template with fallback
        template = self._get_template_for_intent(intent)
        detail_instructions = self._get_detail_instructions(detail_level)
        
        if provider == 'cloud':
            return self._build_cloud_prompt(query, context, rewritten, template, detail_instructions)
        else:
            return self._build_ollama_prompt(query, context, rewritten, template, detail_instructions), None
    
    def _initialize_template_registry(self) -> Dict[str, Union[str, Dict[str, str]]]:
        """Initialize the template registry for all supported intents."""
        return {
            'overview': self._create_overview_template(),
            'location_usage': self._create_location_usage_template(),
            'code_relationship': self._create_code_relationship_template(),
            'semantic_reasoning': self._create_semantic_reasoning_template(),
            'deep_architecture': self._create_deep_architecture_template(),
            'validation': self._create_validation_template(),
            'ui_flow': self._create_ui_flow_template(),
            'business_logic': self._create_business_logic_template(),
            'impact_analysis': self._create_impact_analysis_template(),
            'technical': self._create_technical_template(),
        }
    
    def _get_template_for_intent(self, intent: str) -> Union[str, Dict[str, str]]:
        """Get template for intent with fallback to technical template."""
        return self._template_registry.get(intent, self._template_registry['technical'])
    
    def _build_ollama_prompt(self, query: str, context: str, rewritten: str, 
                           template: str, detail_instructions: str) -> str:
        """Build single comprehensive prompt for Ollama."""
        if isinstance(template, dict):
            # Handle cloud templates gracefully for Ollama
            template = self._convert_cloud_template_to_ollama(template)
        
        return template.format(
            original_question=query,
            context=context,
            rewritten_query=rewritten,
            detail_instructions=detail_instructions
        )
    
    def _build_cloud_prompt(self, query: str, context: str, rewritten: str,
                          template: Dict[str, str], detail_instructions: str) -> Tuple[str, str]:
        """Build system/user prompt pair for cloud providers."""
        if isinstance(template, str):
            # Handle Ollama templates gracefully for cloud
            template = self._convert_ollama_template_to_cloud(template)
        
        system_prompt = template['system'].format(
            detail_instructions=detail_instructions
        )
        user_prompt = template['user'].format(
            original_question=query,
            context=context,
            rewritten_query=rewritten
        )
        return system_prompt, user_prompt
    
    def _get_detail_instructions(self, detail_level: str) -> str:
        """Get response detail instructions based on level."""
        detail_map = {
            'simple': "Provide a concise, direct answer in 1-2 sentences with essential file paths only.",
            'moderate': "Provide a clear answer with specific file locations, class/function names, and brief explanations.",
            'elaborate': "Provide a comprehensive answer with detailed explanations, complete file paths, code examples, implementation guidance, and architectural context."
        }
        return detail_map.get(detail_level, detail_map['moderate'])
    
    # Intent-Specific Template Definitions
    
    def _create_overview_template(self) -> Dict[str, str]:
        """Template for project overview and structural questions."""
        return {
            'system': """You are an expert codebase analyst specializing in project architecture and overview.
{detail_instructions}
Focus on project structure, main components, and high-level architecture.""",
            'user': """CONTEXT:
{context}

ORIGINAL QUESTION: {original_question}

Enhanced Query Context: {rewritten_query}

Provide a comprehensive overview using ONLY the provided context. Include specific file paths, main components, and architectural insights."""
        }
    
    def _create_location_usage_template(self) -> Dict[str, str]:
        """Template for code location and implementation guidance."""
        return {
            'system': """You are a code navigation expert helping developers find implementation locations.
{detail_instructions}
Provide exact file paths, class names, and implementation guidance.""",
            'user': """CONTEXT:
{context}

QUESTION: {original_question}

Enhanced Context: {rewritten_query}

Provide specific guidance on:
1. Exact file paths where changes should be made
2. Relevant class/function names to modify or extend  
3. Implementation approach with code structure
4. Related files that might need updates

Use ONLY the provided context."""
        }
    
    def _create_code_relationship_template(self) -> Dict[str, str]:
        """Template for code relationships, inheritance, and call hierarchies."""
        return {
            'system': """You are an expert in code dependencies, inheritance, and call hierarchies.
{detail_instructions}
Focus on relationships between classes, methods, and modules.""",
            'user': """CONTEXT:
{context}

QUESTION: {original_question}

Enhanced Context: {rewritten_query}

Explain code relationships including:
1. Inheritance hierarchies and overrides
2. Method call flows and dependencies
3. Component interactions and data flow
4. Cross-module relationships

Use ONLY the provided context."""
        }
    
    def _create_semantic_reasoning_template(self) -> str:
        """Template for architectural understanding and design patterns."""
        return """You are a software architect analyzing system design and code patterns.

CRITICAL: Answer this EXACT question: "{original_question}"

=== CONTEXT ===
{context}

=== QUERY ENHANCEMENT ===
{rewritten_query}

=== INSTRUCTIONS ===
{detail_instructions}

ANALYSIS FOCUS:
1. Design patterns and architectural decisions
2. Component responsibilities and interactions
3. System flow and data transformation
4. Best practices and design principles

RULES:
- Answer the ORIGINAL question only
- Use ONLY the provided context
- Provide architectural insights with specific examples
- If context is insufficient, clearly state what's missing

Answer: {original_question}"""
    
    def _create_deep_architecture_template(self) -> Dict[str, str]:
        """Template for advanced architecture, integration, and debugging."""
        return {
            'system': """You are a senior software engineer focusing on integration, debugging, and advanced architecture.
{detail_instructions}
Analyze concurrency, performance, diagnostics, and complex system interactions.""",
            'user': """CONTEXT:
{context}

QUESTION: {original_question}

Enhanced Context: {rewritten_query}

Provide deep technical analysis covering:
1. Integration patterns and external dependencies
2. Performance considerations and bottlenecks
3. Debugging strategies and diagnostic approaches
4. Concurrency handling and thread safety
5. Architectural trade-offs and design decisions

Use ONLY the provided context."""
        }
    
    def _create_validation_template(self) -> str:
        """Template for validation, constraints, and input handling."""
        return """You are a QA engineer specializing in input validation and error handling.

QUESTION: {original_question}

=== CONTEXT ===
{context}

=== ENHANCEMENT ===
{rewritten_query}

=== INSTRUCTIONS ===
{detail_instructions}

VALIDATION FOCUS:
1. Input validation rules and constraints
2. Error handling and exception management
3. Data integrity and business rules
4. Form validation and user input processing

RULES:
- Answer the original question precisely
- Use ONLY the provided context
- Focus on validation logic and error handling
- Provide specific code examples when available"""
    
    def _create_ui_flow_template(self) -> str:
        """Template for UI navigation and screen flow analysis."""
        return """You are a UI/UX expert analyzing navigation flows and screen interactions.

QUESTION: {original_question}

=== CONTEXT ===
{context}

=== ENHANCEMENT ===
{rewritten_query}

=== INSTRUCTIONS ===
{detail_instructions}

UI FLOW ANALYSIS:
1. Screen navigation and routing logic
2. User journey and interaction patterns
3. State management across screens
4. Component lifecycle and transitions

RULES:
- Answer the original question about UI flow
- Use ONLY the provided context
- Focus on navigation and user experience
- Include specific screen/component names"""
    
    def _create_business_logic_template(self) -> str:
        """Template for business logic and process analysis."""
        return """You are a business analyst explaining processes and business logic.

QUESTION: {original_question}

=== CONTEXT ===
{context}

=== ENHANCEMENT ===
{rewritten_query}

=== INSTRUCTIONS ===
{detail_instructions}

BUSINESS LOGIC FOCUS:
1. Business rules and process workflows
2. Authorization and permission handling  
3. Data processing and calculations
4. Policy enforcement and compliance

RULES:
- Answer the original question about business logic
- Use ONLY the provided context
- Focus on business rules and processes
- Explain workflow and decision logic"""
    
    def _create_impact_analysis_template(self) -> str:
        """Template for impact analysis and dependency assessment."""
        return """You are an impact analyst focusing on dependencies and change consequences.

QUESTION: {original_question}

=== CONTEXT ===
{context}

=== ENHANCEMENT ===
{rewritten_query}

=== INSTRUCTIONS ===
{detail_instructions}

IMPACT ANALYSIS:
1. Direct and indirect dependencies
2. Potential breaking changes and ripple effects
3. Affected components and modules
4. Risk assessment and mitigation strategies

RULES:
- Answer the original question about impact
- Use ONLY the provided context
- Focus on dependencies and consequences
- Identify potential risks and affected areas"""
    
    def _create_technical_template(self) -> str:
        """Template for general technical questions."""
        return """You are a senior developer addressing technical questions about the codebase.

QUESTION: {original_question}

=== CONTEXT ===
{context}

=== ENHANCEMENT ===
{rewritten_query}

=== INSTRUCTIONS ===
{detail_instructions}

TECHNICAL ANALYSIS:
1. Code implementation details
2. Algorithm and data structure choices
3. Performance and optimization considerations
4. Technical architecture and patterns

RULES:
- Answer the original question precisely
- Use ONLY the provided context
- Provide detailed technical explanations
- Include relevant code examples and file paths"""
    
    # Template Conversion Utilities
    
    def _convert_cloud_template_to_ollama(self, cloud_template: Dict[str, str]) -> str:
        """Convert cloud system/user template to single Ollama prompt."""
        system_part = cloud_template.get('system', '').replace('{detail_instructions}', '{detail_instructions}')
        user_part = cloud_template.get('user', '')
        
        return f"""{system_part}

{user_part}

Answer the question using ONLY the provided context."""
    
    def _convert_ollama_template_to_cloud(self, ollama_template: str) -> Dict[str, str]:
        """Convert single Ollama template to cloud system/user format."""
        return {
            'system': """You are an expert codebase analyst.
{detail_instructions}
Use ONLY the provided context to answer questions accurately.""",
            'user': """CONTEXT:
{context}

QUESTION: {original_question}

Enhanced Context: {rewritten_query}

Please provide a detailed answer using only the context above."""
        }
