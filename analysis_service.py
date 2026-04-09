import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models import Document, Analysis
from utils import validate_language, chunk_text
from prompts import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT_TEMPLATE, language_rule
from openai_service import generate_json


def _default_analysis_result() -> Dict[str, Any]:
    return {
        "document_type": "UNKNOWN",
        "summary": "",
        "keywords": [],
        "parties": [],
        "obligations": [],
        "loopholes": [],
        "legal_provisions": [],
        "clause_references": [],
    }


def _merge_chunk_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged = _default_analysis_result()

    summaries = []
    keywords = []
    parties = []
    obligations = []
    loopholes = []
    legal_provisions = []
    clause_references = []
    doc_types = []

    for item in results:
        summaries.append(item.get("summary", "").strip())
        keywords.extend(item.get("keywords", []))
        parties.extend(item.get("parties", []))
        obligations.extend(item.get("obligations", []))
        loopholes.extend(item.get("loopholes", []))
        legal_provisions.extend(item.get("legal_provisions", []))
        clause_references.extend(item.get("clause_references", []))
        if item.get("document_type"):
            doc_types.append(item["document_type"])

    merged["document_type"] = doc_types[0] if doc_types else "UNKNOWN"
    merged["summary"] = "\n\n".join([s for s in summaries if s]).strip()
    merged["keywords"] = list(dict.fromkeys([str(k).strip() for k in keywords if str(k).strip()]))[:25]
    merged["parties"] = list(dict.fromkeys([str(p).strip() for p in parties if str(p).strip()]))[:20]
    merged["obligations"] = list(dict.fromkeys([str(o).strip() for o in obligations if str(o).strip()]))[:30]
    merged["loopholes"] = loopholes[:20]
    merged["legal_provisions"] = legal_provisions[:20]
    merged["clause_references"] = clause_references[:20]

    return merged


def analyze_document(db: Session, document_id: int, language: str) -> Dict[str, Any]:
    language = validate_language(language)

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError("Document not found.")

    text = document.extracted_text
    chunks = chunk_text(text, chunk_size=9000, overlap=700)

    chunk_results = []
    for chunk in chunks:
        prompt = ANALYSIS_USER_PROMPT_TEMPLATE.format(
            language_rule=language_rule(language),
            text=chunk,
        )
        result = generate_json(ANALYSIS_SYSTEM_PROMPT, prompt)
        chunk_results.append(result)

    merged = _merge_chunk_results(chunk_results)

    existing = db.query(Analysis).filter(Analysis.document_id == document_id).first()
    if not existing:
        existing = Analysis(document_id=document_id)
        db.add(existing)

    existing.document_type = merged.get("document_type", "UNKNOWN")
    existing.summary = merged.get("summary", "")
    existing.keywords_json = json.dumps(merged.get("keywords", []), ensure_ascii=False)
    existing.loopholes_json = json.dumps(merged.get("loopholes", []), ensure_ascii=False)
    existing.legal_provisions_json = json.dumps(merged.get("legal_provisions", []), ensure_ascii=False)
    existing.clause_references_json = json.dumps(merged.get("clause_references", []), ensure_ascii=False)
    existing.parties_json = json.dumps(merged.get("parties", []), ensure_ascii=False)
    existing.obligations_json = json.dumps(merged.get("obligations", []), ensure_ascii=False)
    existing.analysis_json = json.dumps(merged, ensure_ascii=False)

    db.commit()
    db.refresh(existing)

    return merged


def get_analysis_or_raise(db: Session, document_id: int) -> Analysis:
    analysis = db.query(Analysis).filter(Analysis.document_id == document_id).first()
    if not analysis:
        raise ValueError("Analysis not found. Run /analyze-document first.")
    return analysis