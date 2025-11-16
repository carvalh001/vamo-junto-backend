from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ProductCreate(BaseModel):
    barcode: Optional[str] = None
    name: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    category: Optional[str] = None


class NoteScanRequest(BaseModel):
    code_or_url: str


class NoteCreate(BaseModel):
    access_key_hash: str
    market_name: str
    market_cnpj: Optional[str] = None
    market_address: Optional[str] = None
    emission_date: datetime
    total_value: float
    total_taxes: Optional[float] = None
    products: List[ProductCreate]


class ProductResponse(BaseModel):
    id: int
    note_id: int
    barcode: Optional[str]
    name: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    category: Optional[str]
    created_at: datetime


class NoteResponse(BaseModel):
    id: int
    user_id: int
    access_key_hash: str
    market_name: str
    market_cnpj: Optional[str]
    market_address: Optional[str]
    emission_date: datetime
    total_value: float
    total_taxes: Optional[float]
    created_at: datetime
    products: List[ProductResponse]


class NotesListResponse(BaseModel):
    notes: List[NoteResponse]
    total: int

