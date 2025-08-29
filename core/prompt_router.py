# prompt_router.py  (v2)

from typing import Tuple
from logger import log_to_sublog   # keep your existing logger

class PromptRouter:
    """
    1. build_enhanced_query → returns the right prompt(s) for cloud or local.
    2. build_enhanced_context → always delivers the richest context available.
    """

    # ------------ PUBLIC  -------------------------------------------------

    def build_enhanced_query(
        self,
        *,
        query: str,
        rewritten: str,
        intent: str,
        context: str,
        provider: str,
        llm,
    ) -> Tuple[str, str]:
        """
        • CLOUD  → (system_prompt, user_prompt)  (use llm.invoke_with_system_user)
        • LOCAL  → (single_prompt, '')          (pass to llm as one string)

        The local single_prompt is just:  system_prompt + "\n\n" + user_prompt
        """
        system_prompt, user_prompt_tmpl = self._cloud_templates.get(
            intent, self._cloud_templates["general"]
        )

        user_prompt = user_prompt_tmpl.format(
            query=query, rewritten=rewritten, context=context
        )

        if provider == "cloud" and hasattr(llm, "invoke_with_system_user"):
            return system_prompt, user_prompt  # → two-part message
        # ---- LOCAL / OLLAMA ----
        single_prompt = f"{system_prompt}\n\n{user_prompt}"
        return single_prompt, ""               # second value unused

    def build_enhanced_context(
        self,
        *,
        reranked_docs,
        query: str,
        intent: str,
        context_builder,
        create_full_context,
    ) -> str:
        """
        1. Start with the vanilla full-content context.
        2. If the advanced builder succeeds *and* is longer ⇒ use it.
        """
        base_ctx = create_full_context(reranked_docs)

        if context_builder is None:
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

    # ------------ INTENT-SPECIFIC TEMPLATES -------------------------------

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
Cite file names or functions where they appear. Do not speculate."""
        ),
        "ui_flow": (
            "You are a senior Android navigation expert.",
            """Rewritten query: {rewritten}

CONTEXT:
{context}

TASK:
Describe the screen-to-screen navigation flow:
• Source and destination
• Key intents / fragments / routes
Keep it sequential and specific."""
        ),
        "business_logic": (
            "You are a senior backend analyst.",
            """Rewritten query: {rewritten}

CONTEXT:
{context}

TASK:
Explain the business rule or calculation being asked about.
Show the functions or classes that implement it."""
        ),
        # fallback
        "general": (
            "You are a senior codebase analyst.",
            """Rewritten query: {rewritten}

CONTEXT:
{context}

TASK:
Answer the question directly and cite files/functions where relevant."""
        ),
    }
