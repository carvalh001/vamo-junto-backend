from datetime import datetime
from typing import Dict, Optional
from app.services.nfce_scraper import scrape_nfce
from app.services.db_service import (
    create_note,
    create_product,
    check_note_exists,
    get_user_notes,
    get_note_by_id,
    get_note_products
)
from app.utils.encryption import hash_access_key
import logging

logger = logging.getLogger(__name__)


def process_and_save_note(user_id: int, code_or_url: str) -> Dict:
    """Process NFC-e code/URL and save to database"""
    # Scrape NFC-e data
    nfce_data = scrape_nfce(code_or_url)
    
    # Check if note already exists
    access_key_hash = hash_access_key(nfce_data["access_key"])
    if check_note_exists(access_key_hash, user_id):
        raise ValueError("This note has already been registered.")
    
    # Create note
    note = create_note(
        user_id=user_id,
        access_key=nfce_data["access_key"],
        market_name=nfce_data["market_name"],
        market_cnpj=nfce_data["market_cnpj"],
        market_address=nfce_data["market_address"],
        emission_date=nfce_data["emission_date"],
        total_value=nfce_data["total_value"],
        total_taxes=nfce_data["total_taxes"]
    )
    
    # Create products
    products = []
    for product_data in nfce_data["products"]:
        product = create_product(
            note_id=note["id"],
            barcode=product_data.get("barcode"),
            name=product_data["name"],
            quantity=product_data["quantity"],
            unit=product_data["unit"],
            unit_price=product_data["unit_price"],
            total_price=product_data["total_price"],
            category=product_data.get("category")
        )
        products.append(product)
    
    # Return complete note with products
    note["products"] = products
    return note


def get_user_notes_with_products(user_id: int, limit: int = 100, offset: int = 0, market_filter: Optional[str] = None) -> list:
    """Get user notes with their products"""
    notes = get_user_notes(user_id, limit, offset, market_filter)
    
    result = []
    for note in notes:
        products = get_note_products(note["id"])
        note["products"] = products
        result.append(note)
    
    return result


def get_note_with_products(note_id: int, user_id: int) -> Optional[Dict]:
    """Get a specific note with its products"""
    note = get_note_by_id(note_id, user_id)
    if note:
        products = get_note_products(note["id"])
        note["products"] = products
    return note

