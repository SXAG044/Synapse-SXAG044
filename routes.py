import json
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Document
from schemas import (
    UploadResponse,
    AnalyzeRequest,
    AnalysisResponse,
    ChatStartRequest,
    ChatStartResponse,
    ChatRequest,
    ChatResponse,
    DecisionRiskRequest,
    DecisionRiskResponse,
)
from utils import preview_text, validate_language, safe_json_loads
from document_service import save_upload_file, extract_text_from_file
from analysis_service import analyze_document, get_analysis_or_raise
from chat_service import start_chat_session, ask_question
from risk_service import evaluate_decision_risk

router = APIRouter()


@router.get("/")
def home():
    return {"message": "Legal document analyzer backend is running."}


@router.post("/upload-document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    language: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        language = validate_language(language)
        file_path = save_upload_file(file)
        extracted_text = extract_text_from_file(file_path)

        document = Document(
            filename=file.filename,
            language=language,
            file_path=file_path,
            extracted_text=extracted_text,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return UploadResponse(
            document_id=document.id,
            filename=document.filename,
            language=document.language,
            extracted_text_preview=preview_text(document.extracted_text),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze-document", response_model=AnalysisResponse)
def analyze_document_route(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    try:
        result = analyze_document(db, payload.document_id, payload.language)
        return AnalysisResponse(
            document_id=payload.document_id,
            language=payload.language.lower(),
            document_type=result.get("document_type", "UNKNOWN"),
            summary=result.get("summary", ""),
            keywords=result.get("keywords", []),
            loopholes=result.get("loopholes", []),
            legal_provisions=result.get("legal_provisions", []),
            clause_references=result.get("clause_references", []),
            parties=result.get("parties", []),
            obligations=result.get("obligations", []),
            raw_analysis=result,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start-chat", response_model=ChatStartResponse)
def start_chat(payload: ChatStartRequest, db: Session = Depends(get_db)):
    try:
        session = start_chat_session(db, payload.document_id, payload.language)
        return ChatStartResponse(
            session_id=session.id,
            document_id=session.document_id,
            language=session.language,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = ask_question(db, payload.session_id, payload.question, payload.language)
        return ChatResponse(
            session_id=payload.session_id,
            language=payload.language.lower(),
            answer=result.get("answer", ""),
            legal_provisions=result.get("legal_provisions", []),
            clause_references=result.get("clause_references", []),
            follow_up_suggestions=result.get("follow_up_suggestions", []),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decision-risk", response_model=DecisionRiskResponse)
def decision_risk(payload: DecisionRiskRequest, db: Session = Depends(get_db)):
    try:
        analysis = get_analysis_or_raise(db, payload.document_id)
        loopholes = safe_json_loads(analysis.loopholes_json, [])

        result = evaluate_decision_risk(
            db=db,
            document_id=payload.document_id,
            language=payload.language,
            user_decision=payload.user_decision,
        )

        return DecisionRiskResponse(
            document_id=payload.document_id,
            language=payload.language.lower(),
            loopholes=loopholes,
            user_decision=payload.user_decision,
            possible_consequences=result.get("possible_consequences", []),
            ai_risk_score=result.get("ai_risk_score", 0),
            rules_risk_score=result.get("rules_risk_score", 0),
            final_risk_score=result.get("final_risk_score", 0),
            risk_level=result.get("risk_level", "low"),
            risk_reasons=result.get("risk_reasons", []),
            recommended_next_steps=result.get("recommended_next_steps", []),
            legal_provisions=result.get("legal_provisions", []),
            clause_references=result.get("clause_references", []),
            raw_result=result,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))