from app.database import get_db_cursor
from app.utils.encryption import hash_access_key
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


def create_user(name: str, email: str, cpf: str, password_hash: str) -> Dict:
    """Create a new user"""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (name, email, cpf, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, email, cpf, created_at, updated_at
            """,
            (name, email, cpf, password_hash, datetime.utcnow(), datetime.utcnow())
        )
        result = cursor.fetchone()
        return dict(result)


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, name, email, cpf, password_hash, created_at, updated_at FROM users WHERE email = %s",
            (email,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, name, email, cpf, password_hash, created_at, updated_at FROM users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def get_user_by_cpf(cpf: str) -> Optional[Dict]:
    """Get user by CPF"""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, name, email, cpf, password_hash, created_at, updated_at FROM users WHERE cpf = %s",
            (cpf,)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def create_note(
    user_id: int,
    access_key: str,
    market_name: str,
    market_cnpj: Optional[str],
    market_address: Optional[str],
    emission_date: datetime,
    total_value: float,
    total_taxes: Optional[float]
) -> Dict:
    """Create a new note"""
    access_key_hash = hash_access_key(access_key)
    
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO notes (
                user_id, access_key_hash, market_name, market_cnpj, market_address,
                emission_date, total_value, total_taxes, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, access_key_hash, market_name, market_cnpj, market_address,
                     emission_date, total_value, total_taxes, created_at
            """,
            (
                user_id, access_key_hash, market_name, market_cnpj, market_address,
                emission_date, total_value, total_taxes, datetime.utcnow()
            )
        )
        result = cursor.fetchone()
        return dict(result)


def check_note_exists(access_key_hash: str, user_id: int) -> bool:
    """Check if note with same access key hash already exists for user"""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as count FROM notes WHERE access_key_hash = %s AND user_id = %s",
            (access_key_hash, user_id)
        )
        result = cursor.fetchone()
        return result["count"] > 0


def create_product(
    note_id: int,
    barcode: Optional[str],
    name: str,
    quantity: float,
    unit: str,
    unit_price: float,
    total_price: float,
    category: Optional[str]
) -> Dict:
    """Create a new product"""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO products (
                note_id, barcode, name, quantity, unit, unit_price, total_price, category, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, note_id, barcode, name, quantity, unit, unit_price, total_price, category, created_at
            """,
            (note_id, barcode, name, quantity, unit, unit_price, total_price, category, datetime.utcnow())
        )
        result = cursor.fetchone()
        return dict(result)


def get_user_notes(user_id: int, limit: int = 100, offset: int = 0, market_filter: Optional[str] = None) -> List[Dict]:
    """Get notes for a user"""
    with get_db_cursor() as cursor:
        query = """
            SELECT id, user_id, access_key_hash, market_name, market_cnpj, market_address,
                   emission_date, total_value, total_taxes, created_at
            FROM notes
            WHERE user_id = %s
        """
        params = [user_id]
        
        if market_filter:
            query += " AND market_name = %s"
            params.append(market_filter)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        return [dict(row) for row in results]


def get_note_by_id(note_id: int, user_id: int) -> Optional[Dict]:
    """Get note by ID (only if belongs to user)"""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, user_id, access_key_hash, market_name, market_cnpj, market_address,
                   emission_date, total_value, total_taxes, created_at
            FROM notes
            WHERE id = %s AND user_id = %s
            """,
            (note_id, user_id)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def get_note_products(note_id: int) -> List[Dict]:
    """Get products for a note"""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, note_id, barcode, name, quantity, unit, unit_price, total_price, category, created_at
            FROM products
            WHERE note_id = %s
            ORDER BY id
            """,
            (note_id,)
        )
        results = cursor.fetchall()
        return [dict(row) for row in results]


def delete_note(note_id: int, user_id: int) -> bool:
    """Delete a note and all its products (only if belongs to user)"""
    with get_db_cursor() as cursor:
        # First check if note belongs to user
        cursor.execute(
            "SELECT id FROM notes WHERE id = %s AND user_id = %s",
            (note_id, user_id)
        )
        result = cursor.fetchone()
        
        if not result:
            return False
        
        # Delete products first (due to foreign key constraint)
        cursor.execute(
            "DELETE FROM products WHERE note_id = %s",
            (note_id,)
        )
        
        # Then delete the note
        cursor.execute(
            "DELETE FROM notes WHERE id = %s AND user_id = %s",
            (note_id, user_id)
        )
        
        return True


def get_user_stats(user_id: int) -> Dict:
    """Get statistics for a user"""
    with get_db_cursor() as cursor:
        # Total spent
        cursor.execute(
            "SELECT COALESCE(SUM(total_value), 0) as total_spent FROM notes WHERE user_id = %s",
            (user_id,)
        )
        total_spent = cursor.fetchone()["total_spent"]
        
        # Number of notes
        cursor.execute(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = %s",
            (user_id,)
        )
        notes_count = cursor.fetchone()["count"]
        
        # Number of products
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM products p
            INNER JOIN notes n ON p.note_id = n.id
            WHERE n.user_id = %s
            """,
            (user_id,)
        )
        products_count = cursor.fetchone()["count"]
        
        # Spending by category
        cursor.execute(
            """
            SELECT 
                COALESCE(p.category, 'Uncategorized') as category,
                SUM(p.total_price) as total
            FROM products p
            INNER JOIN notes n ON p.note_id = n.id
            WHERE n.user_id = %s
            GROUP BY p.category
            ORDER BY total DESC
            """,
            (user_id,)
        )
        category_spending = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_spent": float(total_spent),
            "notes_count": notes_count,
            "products_count": products_count,
            "category_spending": category_spending
        }

