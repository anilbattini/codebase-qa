# prompt_router.py  (v3 – adds detail_level)

from typing import Tuple
from logger import log_to_sublog


class PromptRouter:
    # ------------------------------------------------------------------ #
    # PUBLIC API
    # ------------------------------------------------------------------ #
    def build_enhanced_query(
        self,
        *,
        query: str,
        rewritten: str,
        intent: str,
        context: str,
        detail_level: str,          #  <-- NEW  ('simple' | 'moderate' | 'elaborate')
        provider: str,
        llm,
    ) -> Tuple[str, str]:
        """
        CLOUD  → returns (system_prompt, user_prompt)
        LOCAL  → returns (single_prompt, '')
        """
        detail_level = detail_level.lower().strip() or "moderate"
        if detail_level not in self._detail_directives:
            detail_level = "moderate"

        # ---------- 1. pick base intent template ---------
        system_prompt, user_body = self._cloud_templates.get(
            intent, self._cloud_templates["general"]
        )

        # ---------- 2. append the detail directive ---------
        detail_directive = self._detail_directives[detail_level]
        user_prompt = f"{user_body.format(query=query, rewritten=rewritten, context=context)}\n\n{detail_directive}"

        # ---------- 3. return cloud  vs. local  ----------
        if provider == "cloud" and hasattr(llm, "invoke_with_system_user"):
            return system_prompt, user_prompt            # two-part
        single_prompt = f"{system_prompt}\n\n{user_prompt}"  # local
        return single_prompt, ""

    def build_enhanced_context(
        self,
        *,
        reranked_docs,
        query: str,
        intent: str,
        context_builder,
        create_full_context,
    ) -> str:
        base_ctx = create_full_context(reranked_docs)
        if not context_builder:
            return base_ctx

        try:
            advanced_ctx = context_builder.build_enhanced_context(
                reranked_docs, query, intent
            )
            if advanced_ctx and len(advanced_ctx) > len(base_ctx):
                log_to_sublog(".", "prompt_router.log", "Using advanced context")
                return advanced_ctx
        except Exception as e:
            log_to_sublog(".", "prompt_router.log", f"Context builder error: {e}")

        return base_ctx

    # ------------------------------------------------------------------ #
    # TEMPLATE LIBRARY  (unchanged base text)
    # ------------------------------------------------------------------ #
    _cloud_templates = {
        "overview": (
            "You are a senior codebase analyst. Answer using ONLY the code context.",
            """Rewritten query: {rewritten}

CONTEXT:
{context}

TASK:
Give a confident, high-level overview:
• What the project does
• Key components & entry points
• Main build / manifest facts
Avoid hedging; answer directly."""
        ),
        "validation": (
            "You are a senior codebase analyst focused on input validation.",
            """Rewritten query: {rewritten}

CONTEXT:
{context}

TASK:
State the exact validation rules for the field/screen in question.
Cite file names or functions. Do not speculate."""
        ),
        "ui_flow": (
            "You are a senior Android navigation expert.",
            """Rewritten query: {rewritten}

CONTEXT:
{context}

TASK:
Describe the navigation flow:
• Source and destination screens
• Key intents / fragments / routes
Keep it sequential and specific."""
        ),
        "business_logic": (
            "You are a senior backend analyst.",
            """Rewritten query: {rewritten}

CONTEXT:
{context}

TASK:
Explain the business rule or calculation requested.
Show the functions or classes that implement it."""
        ),
        "general": (
            "You are a senior codebase analyst.",
            """Rewritten query: {rewritten}

CONTEXT:
{context}

TASK:
Answer the question directly and cite files/functions where relevant."""
        ),
    }

    # ------------------------------------------------------------------ #
    # DETAIL-LEVEL DIRECTIVES  (NEW)
    # ------------------------------------------------------------------ #
    _detail_directives = {
        "simple": (
            "RESPONSE STYLE: Provide a concise 1-3 sentence answer only. "
            "No bullet lists, no additional explanations."
        ),
        "moderate": (
            "RESPONSE STYLE: Provide a direct answer with essential context. "
            "Limit to ~200 words; bullet lists allowed; avoid fluff."
        ),
        "elaborate": (
            "RESPONSE STYLE: Provide an in-depth, step-by-step explanation. "
            "Include code excerpts or file names where helpful; use lists or "
            "sub-sections for clarity; no hard length limit."
        ),
    }
