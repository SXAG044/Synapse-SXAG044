import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models import ChatSession, ChatMessage
from utils import validate_language, safe_json_loads
from prompts import CHAT_SYSTEM_PROMPT, CHAT_USER_PROMPT_TEMPLATE, language_rule
from openai_service import generate_json
from analysis_service import get_analysis_or_raise


def start_chat_session(db: Session, document_id: int, language: str) -> ChatSession:
    language = validate_language(language)
    session = ChatSession(
        document_id=document_id,
        language=language,
        title="Legal Chat Session"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _get_recent_history(session: ChatSession, limit: int = 10) -> List[Dict[str, str]]:
    ordered = sorted(session.messages, key=lambda x: x.created_at)
    recent = ordered[-limit:]
    return [{"role": msg.role, "content": msg.content} for msg in recent]


def ask_question(db: Session, session_id: int, question: str, language: str) -> Dict[str, Any]:
    language = validate_language(language)

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise ValueError("Chat session not found.")

    analysis = get_analysis_or_raise(db, session.document_id)

    summary = analysis.summary
    loopholes = safe_json_loads(analysis.loopholes_json, [])
    legal_provisions = safe_json_loads(analysis.legal_provisions_json, [])
    clause_references = safe_json_loads(analysis.clause_references_json, [])
    chat_history = _get_recent_history(session)

    user_message = ChatMessage(session_id=session.id, role="user", content=question)
    db.add(user_message)
    db.commit()

    prompt = CHAT_USER_PROMPT_TEMPLATE.format(
        language_rule=language_rule(language),
        summary=summary,
        loopholes=json.dumps(loopholes, ensure_ascii=False),
        legal_provisions=json.dumps(legal_provisions, ensure_ascii=False),
        clause_references=json.dumps(clause_references, ensure_ascii=False),
        chat_history=json.dumps(chat_history, ensure_ascii=False),
        question=question,
    )

    result = generate_json(CHAT_SYSTEM_PROMPT, prompt)

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result.get("answer", "")
    )
    db.add(assistant_message)
    db.commit()

    return result