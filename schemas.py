from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_id: int
    filename: str
    language: str
    extracted_text_preview: str


class AnalyzeRequest(BaseModel):
    document_id: int
    language: str = Field(..., description="english, kannada, tamil, hindi, malayalam")


class LegalProvision(BaseModel):
    law_name: str
    section_or_clause: str
    explanation: str


class LoopholeItem(BaseModel):
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    explanation: str
    suggestion: str


class ClauseReference(BaseModel):
    clause_name: str
    clause_reference: str
    explanation: str


class AnalysisResponse(BaseModel):
    document_id: int
    language: str
    document_type: str
    summary: str
    keywords: List[str]
    loopholes: List[LoopholeItem]
    legal_provisions: List[LegalProvision]
    clause_references: List[ClauseReference]
    parties: List[str]
    obligations: List[str]
    raw_analysis: Dict[str, Any]


class ChatStartRequest(BaseModel):
    document_id: int
    language: str


class ChatStartResponse(BaseModel):
    session_id: int
    document_id: int
    language: str


class ChatRequest(BaseModel):
    session_id: int
    question: str
    language: str


class ChatResponse(BaseModel):
    session_id: int
    language: str
    answer: str
    legal_provisions: List[LegalProvision]
    clause_references: List[ClauseReference]
    follow_up_suggestions: List[str]


class DecisionRiskRequest(BaseModel):
    document_id: int
    language: str
    user_decision: str


class DecisionRiskResponse(BaseModel):
    document_id: int
    language: str
    loopholes: List[LoopholeItem]
    user_decision: str
    possible_consequences: List[str]
    ai_risk_score: int
    rules_risk_score: int
    final_risk_score: int
    risk_level: str
    risk_reasons: List[str]
    recommended_next_steps: List[str]
    legal_provisions: List[LegalProvision]
    clause_references: List[ClauseReference]
    raw_result: Dict[str, Any]