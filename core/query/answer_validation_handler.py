# answer_validation_handler.py

import re
from datetime import datetime
import json
from logger import log_to_sublog

class AnswerValidationHandler:
    """
    Handles all answer validation, quality assessment, and diagnostic operations.
    Separated from ChatHandler for better modularity and maintainability.
    """
    
    def __init__(self, project_dir):
        self.project_dir = project_dir

    def validate_answer_quality(self, query: str, answer: str, context_docs: list) -> dict:
        """Enhanced local validation building on existing quality analysis."""
        base_analysis = self._analyze_answer_quality(query, answer, context_docs)
        code_quality_score = self._validate_code_specific_quality(query, answer, context_docs)
        relevancy_score = self._calculate_code_relevancy(query, answer)
        completeness_score = self._calculate_answer_completeness(query, answer, context_docs)
        accuracy_score = self._validate_technical_accuracy(answer, context_docs)

        overall_score = (
            relevancy_score * 0.35 +
            completeness_score * 0.25 +
            accuracy_score * 0.25 +
            code_quality_score * 0.15
        )

        return {
            "validation_method": "enhanced_builtin_codebase_qa",
            "overall_score": overall_score,
            "quality_flag": self._determine_quality_flag(overall_score),
            "scores": {
                "relevancy": relevancy_score,
                "completeness": completeness_score,
                "accuracy": accuracy_score,
                "code_quality": code_quality_score,
                "base_metrics": base_analysis
            },
            "validation_time": 0.05
        }

    def _validate_code_specific_quality(self, query: str, answer: str, context_docs: list) -> float:
        """Enhanced code-specific quality validation."""
        score = 0.0

        if any(keyword in query.lower() for keyword in ['where', 'file', 'location']):
            if re.search(r'\b\w+\.(java|kt|py|js|xml|gradle|properties)\b', answer):
                score += 0.3

        if any(keyword in query.lower() for keyword in ['how', 'what', 'method', 'function', 'class']):
            if re.search(r'\b[A-Z][a-zA-Z0-9]*\b', answer):
                score += 0.2
            if re.search(r'\w+\(\)', answer):
                score += 0.2
            if re.search(r'\bfun\s+\w+\b', answer):
                score += 0.1

        code_block_count = answer.count('```')
        if code_block_count >= 2:
            score += 0.2
        elif code_block_count == 1:
            score += 0.1

        inline_code_count = answer.count('`') - (code_block_count * 3)
        if inline_code_count >= 2:
            score += 0.1

        android_terms = ['Activity', 'Fragment', 'AndroidManifest', 'build.gradle', 'MainActivity']
        android_mentions = sum(1 for term in android_terms if term in answer)
        if android_mentions > 0:
            score += min(android_mentions * 0.05, 0.15)

        return min(score, 1.0)

    def _calculate_code_relevancy(self, query: str, answer: str) -> float:
        """Calculate relevancy between query and answer using term overlap."""
        stop_words = {'what', 'is', 'the', 'a', 'an', 'this', 'that', 'how', 'where', 'when', 'why'}

        query_terms = set([
            term.lower() for term in re.findall(r'\b\w+\b', query)
            if len(term) > 2 and term.lower() not in stop_words
        ])

        answer_terms = set([
            term.lower() for term in re.findall(r'\b\w+\b', answer)
            if len(term) > 2 and term.lower() not in stop_words
        ])

        if not query_terms:
            return 0.5

        common_terms = query_terms & answer_terms
        relevancy = len(common_terms) / len(query_terms)

        code_terms = ['class', 'method', 'function', 'file', 'app', 'application', 'project']
        code_matches = sum(1 for term in code_terms if term in query.lower() and term in answer.lower())

        return min(relevancy + (code_matches * 0.1), 1.0)

    def _calculate_answer_completeness(self, query: str, answer: str, context_docs: list) -> float:
        """Calculate answer completeness based on length and context utilization."""
        answer_length = len(answer)
        if answer_length < 50:
            length_score = 0.2
        elif answer_length > 2000:
            length_score = 0.7
        else:
            optimal_range = min(answer_length / 1000, 1.0)
            length_score = 0.4 + (optimal_range * 0.6)

        context_score = 0.5
        if context_docs:
            context_words = set()
            for doc in context_docs:
                if hasattr(doc, 'page_content'):
                    context_words.update(doc.page_content.lower().split())

            answer_words = set(answer.lower().split())
            if context_words:
                context_overlap = len(answer_words & context_words) / len(context_words)
                context_score = min(context_overlap * 2, 1.0)

        return (length_score * 0.6 + context_score * 0.4)

    def _validate_technical_accuracy(self, answer: str, context_docs: list) -> float:
        """Validate technical accuracy based on code patterns and context consistency."""
        score = 0.5

        technical_patterns = [
            r'\b[A-Z][a-zA-Z0-9]*\.java\b',
            r'\b[A-Z][a-zA-Z0-9]*\.kt\b',
            r'\b[A-Z][a-zA-Z0-9]*Activity\b',
            r'\b[A-Z][a-zA-Z0-9]*Fragment\b',
            r'\bpackage\s+[\w\.]+\b',
            r'\bclass\s+\w+\b',
            r'\bfun\s+\w+\b',
            r'\bpublic\s+\w+\b'
        ]

        pattern_matches = sum(1 for pattern in technical_patterns if re.search(pattern, answer))
        technical_score = min(pattern_matches * 0.1, 0.3)

        consistency_score = 0.5
        if context_docs:
            context_files = set()
            for doc in context_docs:
                if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                    context_files.add(doc.metadata['source'])

            answer_lower = answer.lower()
            file_mentions = sum(1 for file_path in context_files
                              if any(part in answer_lower for part in file_path.split('/')))

            if context_files:
                consistency_score = min(file_mentions / len(context_files), 1.0)

        return min(score + technical_score + (consistency_score * 0.2), 1.0)

    def _determine_quality_flag(self, overall_score: float) -> str:
        """Determine quality flag based on overall score."""
        if overall_score >= 0.8:
            return "high_quality"
        elif overall_score >= 0.6:
            return "acceptable"
        else:
            return "needs_improvement"

    def log_quality_metrics(self, validation_results: dict):
        """Log quality metrics for monitoring and analysis."""
        quality_log = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": validation_results.get("overall_score", 0.0),
            "quality_flag": validation_results.get("quality_flag", "unknown"),
            "individual_scores": validation_results.get("scores", {}),
            "validation_time": validation_results.get("validation_time", 0.0)
        }

        log_to_sublog(self.project_dir, "quality_metrics.log",
            f"QUALITY_METRIC: {json.dumps(quality_log)}")

        if validation_results.get("overall_score", 0.0) < 0.5:
            log_to_sublog(self.project_dir, "quality_alerts.log",
                f"QUALITY_ALERT: Low score detected - {quality_log}")

    def diagnose_quality_issue(self, query: str, rewritten: str, retrieved_docs: list, answer: str) -> dict:
        """Comprehensive pipeline diagnostics to identify quality bottlenecks."""
        diagnosis = {
            "rewriting_quality": {},
            "retrieval_quality": {},
            "answer_quality": {},
            "recommended_fixes": []
        }

        diagnosis["rewriting_quality"] = self._analyze_rewriting_quality(query, rewritten)
        diagnosis["retrieval_quality"] = self._analyze_retrieval_coverage(query, rewritten, retrieved_docs)
        diagnosis["answer_quality"] = self._analyze_answer_quality(query, answer, retrieved_docs)
        diagnosis["recommended_fixes"] = self._generate_fix_recommendations(diagnosis)

        return diagnosis

    def _analyze_rewriting_quality(self, original: str, rewritten: str) -> dict:
        """Detect if rewriting breaks important entities or concepts."""
        original_entities = re.findall(r'\b[A-Z][a-zA-Z0-9]+\b', original)
        original_entities.extend(re.findall(r'\b[a-z_]+[A-Z][a-zA-Z0-9]*\b', original))

        preserved_entities = []
        missing_entities = []
        for entity in original_entities:
            if entity.lower() in rewritten.lower():
                preserved_entities.append(entity)
            else:
                missing_entities.append(entity)

        original_words = set(original.lower().split())
        rewritten_words = set(rewritten.lower().split())

        return {
            "original_entities": original_entities,
            "preserved_entities": preserved_entities,
            "missing_entities": missing_entities,
            "entity_preservation_rate": len(preserved_entities) / max(len(original_entities), 1),
            "semantic_overlap": len(original_words & rewritten_words) / len(original_words | rewritten_words),
            "rewriting_issue": len(missing_entities) > 0 or len(preserved_entities) / max(len(original_entities), 1) < 0.7
        }

    def _analyze_retrieval_coverage(self, query: str, rewritten: str, docs: list) -> dict:
        """Analyze if retrieval found relevant documents for the query."""
        query_terms = set(query.lower().split())
        rewritten_terms = set(rewritten.lower().split())
        all_search_terms = query_terms | rewritten_terms

        doc_contents = [doc.page_content.lower() for doc in docs if hasattr(doc, 'page_content')]
        combined_content = ' '.join(doc_contents)

        terms_found = []
        terms_missing = []
        for term in all_search_terms:
            if len(term) > 2:
                if term in combined_content:
                    terms_found.append(term)
                else:
                    terms_missing.append(term)

        entities_in_query = re.findall(r'\b[A-Z][a-zA-Z0-9]+\b', query)
        entities_found_in_docs = []
        for entity in entities_in_query:
            if entity in combined_content:
                entities_found_in_docs.append(entity)

        return {
            "total_docs_retrieved": len(docs),
            "terms_coverage_rate": len(terms_found) / max(len(all_search_terms), 1),
            "missing_terms": terms_missing,
            "entities_in_query": entities_in_query,
            "entities_found_in_docs": entities_found_in_docs,
            "entity_coverage_rate": len(entities_found_in_docs) / max(len(entities_in_query), 1),
            "retrieval_issue": len(terms_missing) > len(terms_found) or len(entities_found_in_docs) < len(entities_in_query)
        }

    def _analyze_answer_quality(self, query: str, answer: str, retrieved_docs: list) -> dict:
        """Comprehensive answer quality analysis using query context and retrieved documents."""
        answer_length = len(answer)
        word_count = len(answer.split())
        sentence_count = len(re.split(r'[.!?]+', answer.strip()))
        avg_sentence_length = word_count / max(sentence_count, 1)

        uncertainty_phrases = [
            "i don't know", "not sure", "unclear", "unknown", "might be",
            "possibly", "perhaps", "it seems", "appears to", "based on the provided context",
            "i cannot", "unable to", "insufficient information", "hard to say"
        ]

        confidence_phrases = [
            "definitely", "certainly", "clearly", "specifically", "exactly",
            "the code shows", "implementation demonstrates", "function does",
            "located in", "found in", "implemented in"
        ]

        uncertainty_count = sum(1 for phrase in uncertainty_phrases if phrase in answer.lower())
        confidence_count = sum(1 for phrase in confidence_phrases if phrase in answer.lower())
        confidence_ratio = confidence_count / max(confidence_count + uncertainty_count, 1)

        code_references = len(re.findall(r'\b[A-Z][a-zA-Z0-9]+\b', answer))
        file_references = len(re.findall(r'\b\w+\.(java|kt|py|js|ts|xml|json|md|gradle)\b', answer))
        method_references = len(re.findall(r'\b\w+$$$$', answer))
        code_blocks = answer.count('```') // 2
        inline_code = answer.count('`') - (code_blocks * 6)

        context_utilization = 0.0
        context_overlap_words = []

        if retrieved_docs:
            combined_context = ' '.join([
                doc.page_content[:300] for doc in retrieved_docs
                if hasattr(doc, 'page_content')
            ])

            if combined_context:
                context_words = set(
                    word.lower().strip('.,!?()[]')
                    for word in combined_context.split()
                    if len(word) > 3
                )

                answer_words = set(
                    word.lower().strip('.,!?()[]')
                    for word in answer.split()
                    if len(word) > 3
                )

                context_overlap_words = list(context_words & answer_words)
                context_utilization = len(context_overlap_words) / max(len(context_words), 1)

        has_code_examples = code_blocks > 0 or inline_code > 4
        has_file_paths = file_references > 0 or '/' in answer or '\\' in answer
        has_specific_references = code_references > 0 or method_references > 0

        query_lower = query.lower()
        location_query = any(keyword in query_lower for keyword in ['where', 'file', 'location', 'directory', 'path'])
        how_query = any(keyword in query_lower for keyword in ['how', 'implement', 'work', 'process'])
        what_query = any(keyword in query_lower for keyword in ['what', 'describe', 'explain'])

        quality_score = 0.0
        quality_factors = []
        quality_issues = []

        if 200 <= answer_length <= 2000:
            quality_score += 0.2
            quality_factors.append("appropriate_length")
        elif answer_length < 50:
            quality_issues.append("too_short")
        elif answer_length > 3000:
            quality_issues.append("too_long")
        else:
            quality_score += 0.1

        if confidence_ratio > 0.6:
            quality_score += 0.2
            quality_factors.append("confident_tone")
        elif confidence_ratio < 0.3:
            quality_issues.append("uncertain_tone")
        else:
            quality_score += 0.1

        if has_specific_references:
            quality_score += 0.2
            quality_factors.append("specific_references")
        if has_code_examples:
            quality_score += 0.1
            quality_factors.append("includes_examples")

        if context_utilization > 0.3:
            quality_score += 0.2
            quality_factors.append("good_context_usage")
        elif context_utilization < 0.1:
            quality_issues.append("poor_context_usage")
        else:
            quality_score += 0.1

        if location_query and has_file_paths:
            quality_score += 0.1
            quality_factors.append("includes_locations")
        if how_query and has_code_examples:
            quality_score += 0.1
            quality_factors.append("how_query_with_examples")

        if quality_score >= 0.7:
            quality_flag = "high_quality"
        elif quality_score >= 0.4:
            quality_flag = "acceptable"
        else:
            quality_flag = "needs_improvement"

        return {
            "answer_length": answer_length,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "uncertainty_count": uncertainty_count,
            "confidence_count": confidence_count,
            "confidence_ratio": round(confidence_ratio, 3),
            "code_references": code_references,
            "file_references": file_references,
            "method_references": method_references,
            "code_blocks": code_blocks,
            "inline_code_snippets": max(inline_code // 2, 0),
            "context_utilization": round(context_utilization, 3),
            "context_overlap_words": len(context_overlap_words),
            "retrieved_docs_count": len(retrieved_docs),
            "has_code_examples": has_code_examples,
            "has_file_paths": has_file_paths,
            "has_specific_references": has_specific_references,
            "quality_score": round(quality_score, 3),
            "quality_factors": quality_factors,
            "quality_issues": quality_issues,
            "quality_flag": quality_flag,
            "query_analysis": {
                "is_location_query": location_query,
                "is_how_query": how_query,
                "is_what_query": what_query
            }
        }

    def log_pipeline_diagnosis(self, diagnosis: dict, query: str):
        """Log detailed pipeline diagnosis for monitoring."""
        diagnosis_log = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100] + "..." if len(query) > 100 else query,
            "rewriting_issue": diagnosis["rewriting_quality"]["rewriting_issue"],
            "entity_preservation_rate": diagnosis["rewriting_quality"]["entity_preservation_rate"],
            "retrieval_issue": diagnosis["retrieval_quality"]["retrieval_issue"],
            "retrieval_coverage_rate": diagnosis["retrieval_quality"]["terms_coverage_rate"],
            "entity_coverage_rate": diagnosis["retrieval_quality"]["entity_coverage_rate"],
            "recommended_fixes": diagnosis["recommended_fixes"]
        }

        log_to_sublog(self.project_dir, "pipeline_diagnosis.log",
            f"PIPELINE_DIAGNOSIS: {json.dumps(diagnosis_log)}")

        if (diagnosis["rewriting_quality"]["entity_preservation_rate"] < 0.5 or
            diagnosis["retrieval_quality"]["entity_coverage_rate"] < 0.3):
            log_to_sublog(self.project_dir, "quality_alerts.log",
                f"CRITICAL_QUALITY_ISSUE: {diagnosis_log}")

    def _generate_fix_recommendations(self, diagnosis: dict) -> list:
        """Generate targeted, actionable fix recommendations based on comprehensive diagnosis."""
        fixes = []
        priority_fixes = []

        rewriting_quality = diagnosis.get("rewriting_quality", {})
        retrieval_quality = diagnosis.get("retrieval_quality", {})
        answer_quality = diagnosis.get("answer_quality", {})

        if rewriting_quality.get("entity_preservation_rate", 1.0) < 0.5:
            priority_fixes.append({
                "type": "rewriting",
                "severity": "critical",
                "action": "Fix entity destruction in rewriting",
                "details": f"Only {rewriting_quality.get('entity_preservation_rate', 0):.0%} of entities preserved. Missing: {rewriting_quality.get('missing_entities', [])}",
                "implementation": "Update rewrite prompt with entity preservation examples"
            })

        if retrieval_quality.get("entity_coverage_rate", 1.0) < 0.3:
            priority_fixes.append({
                "type": "retrieval",
                "severity": "critical",
                "action": "Implement entity-focused retrieval fallback",
                "details": f"Only {retrieval_quality.get('entity_coverage_rate', 0):.0%} of query entities found in documents",
                "implementation": "Add adaptive retrieval for missing entities"
            })

        if retrieval_quality.get("terms_coverage_rate", 1.0) < 0.4:
            priority_fixes.append({
                "type": "retrieval",
                "severity": "high",
                "action": "Increase retrieval scope",
                "details": f"Only {retrieval_quality.get('terms_coverage_rate', 0):.0%} of search terms found in documents",
                "implementation": "Increase k parameter or use alternative search strategy"
            })

        answer_flag = answer_quality.get("quality_flag", "unknown")
        if answer_flag == "needs_improvement":
            quality_issues = answer_quality.get("quality_issues", [])
            if "too_short" in quality_issues:
                fixes.append({
                    "type": "answer_generation",
                    "severity": "medium",
                    "action": "Increase answer detail level",
                    "details": f"Answer too short ({answer_quality.get('answer_length', 0)} chars)",
                    "implementation": "Use 'elaborate' detail level or more comprehensive prompts"
                })

        all_fixes = priority_fixes + fixes

        if not all_fixes:
            return [{
                "type": "system",
                "severity": "info",
                "action": "No issues detected",
                "details": "All quality metrics within acceptable ranges",
                "implementation": "System performing well, monitor for changes"
            }]

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_fixes.sort(key=lambda x: severity_order.get(x["severity"], 3))

        return all_fixes
