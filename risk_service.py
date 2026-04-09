import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from utils import validate_language, safe_json_loads
from prompts import RISK_SYSTEM_PROMPT, RISK_USER_PROMPT_TEMPLATE, language_rule
from openai_service import generate_json
from analysis_service import get_analysis_or_raise


SEVERITY_SCORE = {
    "low": 10,
    "medium": 25,
    "high": 45,
    "critical": 65,
}


def _rules_based_risk_score(loopholes: List[Dict[str, Any]], user_decision: str) -> int:
    score = 0

    for loophole in loopholes:
        severity = str(loophole.get("severity", "low")).lower()
        score += SEVERITY_SCORE.get(severity, 10)

    decision_text = user_decision.lower()

    if any(term in decision_text for term in ["sign", "accept", "proceed", "agree"]):
        score += 15
    if any(term in decision_text for term in ["ignore", "do nothing", "skip", "delay"]):
        score += 20
    if any(term in decision_text for term in ["terminate", "cancel", "exit", "reject"]):
        score += 10
    if any(term in decision_text for term in ["without changes", "as is", "without amendment"]):
        score += 20

    return max(0, min(score, 100))


def _risk_level(score: int) -> str:
    if score >= 76:
        return "critical"
    if score >= 56:
        return "high"
    if score >= 31:
        return "medium"
    return "low"


def evaluate_decision_risk(db: Session, document_id: int, language: str, user_decision: str) -> Dict[str, Any]:
    language = validate_language(language)
    analysis = get_analysis_or_raise(db, document_id)

    summary = analysis.summary
    loopholes = safe_json_loads(analysis.loopholes_json, [])
    legal_provisions = safe_json_loads(analysis.legal_provisions_json, [])
    clause_references = safe_json_loads(analysis.clause_references_json, [])

    prompt = RISK_USER_PROMPT_TEMPLATE.format(
        language_rule=language_rule(language),
        summary=summary,
        loopholes=json.dumps(loopholes, ensure_ascii=False),
        legal_provisions=json.dumps(legal_provisions, ensure_ascii=False),
        clause_references=json.dumps(clause_references, ensure_ascii=False),
        user_decision=user_decision,
    )

    result = generate_json(RISK_SYSTEM_PROMPT, prompt)

    ai_score = int(result.get("ai_risk_score", 0))
    ai_score = max(0, min(ai_score, 100))

    rules_score = _rules_based_risk_score(loopholes, user_decision)

    final_score = round((ai_score * 0.6) + (rules_score * 0.4))
    final_score = max(0, min(final_score, 100))

    result["ai_risk_score"] = ai_score
    result["rules_risk_score"] = rules_score
    result["final_risk_score"] = final_score
    result["risk_level"] = _risk_level(final_score)

    return result