from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from app.schemas.note import NoteScanRequest, NoteResponse, NotesListResponse
from app.services.note_service import process_and_save_note, get_user_notes_with_products, get_note_with_products
from app.api.deps import get_current_user
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/scan", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def scan_note(
    request: Request,
    scan_data: NoteScanRequest,
    current_user: dict = Depends(get_current_user)
):
    """Scan and save NFC-e note"""
    try:
        note = process_and_save_note(current_user["id"], scan_data.code_or_url)
        return NoteResponse(**note)
    except ValueError as e:
        # User-friendly errors (e.g., note already exists, invalid code)
        error_msg = str(e)
        
        # Special handling for duplicate notes - this is not really an error
        if "já foi escaneada" in error_msg.lower() or "already been registered" in error_msg.lower():
            logger.info(f"User attempted to scan duplicate note: {current_user['id']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta nota fiscal já foi escaneada anteriormente."
            )
        
        # Other validation errors
        logger.warning(f"Validation error scanning note: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error scanning note: {error_message}", exc_info=True)
        
        # Provide more specific error messages based on error type
        if "not found" in error_message.lower() or "invalid" in error_message.lower():
            detail = "NFC-e não encontrada ou código inválido. Verifique o código e tente novamente."
            status_code = status.HTTP_400_BAD_REQUEST
        elif "parse" in error_message.lower() or "format" in error_message.lower():
            detail = "Não foi possível processar os dados da NFC-e. O formato pode ter mudado. Tente novamente mais tarde."
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif "fetch" in error_message.lower() or "network" in error_message.lower():
            detail = "Erro ao buscar dados da NFC-e. Verifique sua conexão e tente novamente."
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            detail = "Erro ao processar nota fiscal. Por favor, tente novamente."
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail=detail
        )


@router.get("", response_model=NotesListResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_notes(
    request: Request,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    market: Optional[str] = Query(None)
):
    """Get user's notes"""
    try:
        notes = get_user_notes_with_products(
            current_user["id"],
            limit=limit,
            offset=offset,
            market_filter=market
        )
        
        # Convert to response format
        note_responses = [NoteResponse(**note) for note in notes]
        
        return NotesListResponse(
            notes=note_responses,
            total=len(note_responses)
        )
    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notes. Please try again."
        )


@router.get("/{note_id}", response_model=NoteResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_note(
    request: Request,
    note_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific note by ID"""
    note = get_note_with_products(note_id, current_user["id"])
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    return NoteResponse(**note)

