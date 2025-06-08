"""
FastAPI Router für QA (Question-Answering) Endpoints
Implementiert RAG-basierte Antwortgenerierung mit LLM
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
import time
from datetime import datetime

# Local imports
from .models import QARequest, QAResponse, SearchResult, ErrorResponse
from .dependencies import get_qa_system, get_search_engine
from ..llm.lm_studio_client import LegalQASystem
from ..search.semantic_search import SemanticSearchEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["question-answering"])


@router.post("/ask", response_model=QAResponse)
async def ask_legal_question(
    request: QARequest,
    qa_system: LegalQASystem = Depends(get_qa_system),
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Beantwortet rechtliche Fragen basierend auf der Gutachten-Datenbank
    
    Verwendet RAG (Retrieval-Augmented Generation):
    1. Relevante Chunks aus der Datenbank abrufen
    2. Context für LLM zusammenstellen
    3. Antwort generieren mit Deepseek V2 Lite 16B
    """
    start_time = time.time()
    
    try:
        # Frage analysieren und relevante Chunks finden
        search_results = await search_engine.search(
            query=request.question,
            search_type="hybrid",
            limit=request.context_limit,
            similarity_threshold=0.6
        )
        
        if not search_results.results:
            # Fallback: Allgemeine rechtliche Antwort ohne spezifischen Context
            logger.warning(f"No relevant chunks found for question: {request.question}")
            response = await qa_system.generate_general_legal_response(
                question=request.question,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        else:
            # RAG-Pipeline mit gefundenen Chunks
            response = await qa_system.answer_question(
                question=request.question,
                context_chunks=search_results.results,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                include_sources=request.include_sources
            )
        
        # Sources für Response vorbereiten
        sources = search_results.results if request.include_sources else []
        
        qa_response = QAResponse(
            question=request.question,
            answer=response.text,
            confidence_score=response.confidence_score,
            sources=sources,
            generation_time_ms=(time.time() - start_time) * 1000,
            tokens_generated=response.tokens_generated,
            legal_analysis=response.metadata.get('legal_analysis', {})
        )
        
        logger.info(f"QA completed: {qa_response.tokens_generated} tokens in {qa_response.generation_time_ms:.2f}ms")
        return qa_response
        
    except Exception as e:
        logger.error(f"Error in legal QA: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Fragenbeantwortung: {str(e)}"
        )


@router.post("/explain", response_model=QAResponse)
async def explain_legal_concept(
    concept: str,
    context_limit: int = 5,
    qa_system: LegalQASystem = Depends(get_qa_system),
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Erklärt rechtliche Konzepte und Begriffe
    Spezialisiert auf Definitionen und Erläuterungen
    """
    start_time = time.time()
    
    try:
        # Query für Konzept-Erklärung formulieren
        explanation_query = f"Was ist {concept}? Definition und Erklärung"
        
        # Relevanten Context suchen
        search_results = await search_engine.search(
            query=explanation_query,
            search_type="semantic",
            limit=context_limit,
            similarity_threshold=0.5
        )
        
        # Erklärung generieren
        response = await qa_system.explain_legal_concept(
            concept=concept,
            context_chunks=search_results.results,
            max_tokens=800
        )
        
        qa_response = QAResponse(
            question=f"Erklärung: {concept}",
            answer=response.text,
            confidence_score=response.confidence_score,
            sources=search_results.results,
            generation_time_ms=(time.time() - start_time) * 1000,
            tokens_generated=response.tokens_generated,
            legal_analysis=response.metadata.get('legal_analysis', {})
        )
        
        return qa_response
        
    except Exception as e:
        logger.error(f"Error explaining legal concept: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Konzept-Erklärung: {str(e)}"
        )


@router.post("/summarize", response_model=QAResponse)
async def summarize_legal_text(
    text: str,
    summary_length: str = "medium",  # short, medium, long
    focus: str = "general",  # general, legal_norms, key_points
    qa_system: LegalQASystem = Depends(get_qa_system)
):
    """
    Erstellt Zusammenfassungen von rechtlichen Texten
    """
    start_time = time.time()
    
    try:
        # Zusammenfassung generieren
        response = await qa_system.summarize_legal_text(
            text=text,
            summary_length=summary_length,
            focus=focus
        )
        
        qa_response = QAResponse(
            question=f"Zusammenfassung ({summary_length}, {focus})",
            answer=response.text,
            confidence_score=response.confidence_score,
            sources=[],  # Keine externen Quellen bei Zusammenfassung
            generation_time_ms=(time.time() - start_time) * 1000,
            tokens_generated=response.tokens_generated,
            legal_analysis=response.metadata.get('legal_analysis', {})
        )
        
        return qa_response
        
    except Exception as e:
        logger.error(f"Error summarizing legal text: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Textzusammenfassung: {str(e)}"
        )


@router.post("/compare-cases")
async def compare_legal_cases(
    case_ids: List[str],
    comparison_aspects: List[str] = ["sachverhalt", "rechtslage", "ergebnis"],
    qa_system: LegalQASystem = Depends(get_qa_system),
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
) -> Dict[str, Any]:
    """
    Vergleicht mehrere Rechtsfälle miteinander
    """
    start_time = time.time()
    
    try:
        if len(case_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="Mindestens 2 Fälle zum Vergleich erforderlich"
            )
        
        # Cases-Daten abrufen
        cases_data = []
        for case_id in case_ids:
            case_chunks = await search_engine.get_chunks_by_gutachten_id(case_id)
            cases_data.append({
                'id': case_id,
                'chunks': case_chunks
            })
        
        # Vergleich durchführen
        comparison_result = await qa_system.compare_legal_cases(
            cases_data=cases_data,
            comparison_aspects=comparison_aspects
        )
        
        return {
            'comparison': comparison_result.text,
            'cases_compared': case_ids,
            'aspects': comparison_aspects,
            'processing_time_ms': (time.time() - start_time) * 1000,
            'confidence_score': comparison_result.confidence_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing legal cases: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Fallvergleich: {str(e)}"
        )


@router.post("/legal-advice")
async def provide_legal_advice(
    situation: str,
    legal_area: str = None,
    urgency: str = "normal",  # low, normal, high
    qa_system: LegalQASystem = Depends(get_qa_system),
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
) -> QAResponse:
    """
    Gibt rechtliche Einschätzungen zu konkreten Situationen
    HINWEIS: Ersetzt keine professionelle Rechtsberatung!
    """
    start_time = time.time()
    
    try:
        # Relevante Rechtsnormen und Fälle suchen
        legal_query = f"Rechtslage bei: {situation}"
        if legal_area:
            legal_query += f" im Bereich {legal_area}"
        
        search_results = await search_engine.search(
            query=legal_query,
            search_type="hybrid",
            limit=8,
            similarity_threshold=0.5
        )
        
        # Rechtliche Einschätzung generieren
        response = await qa_system.provide_legal_advice(
            situation=situation,
            legal_area=legal_area,
            context_chunks=search_results.results,
            urgency=urgency
        )
        
        qa_response = QAResponse(
            question=f"Rechtliche Einschätzung: {situation[:100]}...",
            answer=response.text,
            confidence_score=response.confidence_score,
            sources=search_results.results,
            generation_time_ms=(time.time() - start_time) * 1000,
            tokens_generated=response.tokens_generated,
            legal_analysis=response.metadata.get('legal_analysis', {})
        )
        
        return qa_response
        
    except Exception as e:
        logger.error(f"Error providing legal advice: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der rechtlichen Einschätzung: {str(e)}"
        )


@router.get("/history/{session_id}")
async def get_qa_history(
    session_id: str,
    limit: int = 50,
    qa_system: LegalQASystem = Depends(get_qa_system)
) -> List[Dict[str, Any]]:
    """
    Gibt die QA-Historie für eine Session zurück
    """
    try:
        history = await qa_system.get_session_history(
            session_id=session_id,
            limit=limit
        )
        return history
    except Exception as e:
        logger.error(f"Error getting QA history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der QA-Historie: {str(e)}"
        )


@router.delete("/history/{session_id}")
async def clear_qa_history(
    session_id: str,
    qa_system: LegalQASystem = Depends(get_qa_system)
) -> Dict[str, str]:
    """
    Löscht die QA-Historie für eine Session
    """
    try:
        await qa_system.clear_session_history(session_id)
        return {"message": f"Historie für Session {session_id} gelöscht"}
    except Exception as e:
        logger.error(f"Error clearing QA history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Löschen der QA-Historie: {str(e)}"
        )
