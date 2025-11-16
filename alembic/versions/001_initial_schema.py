"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            cpf VARCHAR(14) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index on email
    op.execute("CREATE INDEX idx_users_email ON users(email)")
    
    # Create index on cpf
    op.execute("CREATE INDEX idx_users_cpf ON users(cpf)")
    
    # Create notes table
    op.execute("""
        CREATE TABLE notes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            access_key_hash VARCHAR(64) NOT NULL,
            market_name VARCHAR(255) NOT NULL,
            market_cnpj VARCHAR(18),
            market_address TEXT,
            emission_date TIMESTAMP NOT NULL,
            total_value DECIMAL(10, 2) NOT NULL,
            total_taxes DECIMAL(10, 2),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, access_key_hash)
        )
    """)
    
    # Create indexes on notes
    op.execute("CREATE INDEX idx_notes_user_id ON notes(user_id)")
    op.execute("CREATE INDEX idx_notes_access_key_hash ON notes(access_key_hash)")
    op.execute("CREATE INDEX idx_notes_emission_date ON notes(emission_date)")
    op.execute("CREATE INDEX idx_notes_market_name ON notes(market_name)")
    
    # Create products table
    op.execute("""
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            barcode VARCHAR(50),
            name VARCHAR(255) NOT NULL,
            quantity DECIMAL(10, 3) NOT NULL,
            unit VARCHAR(10) NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            total_price DECIMAL(10, 2) NOT NULL,
            category VARCHAR(100),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes on products
    op.execute("CREATE INDEX idx_products_note_id ON products(note_id)")
    op.execute("CREATE INDEX idx_products_barcode ON products(barcode)")
    op.execute("CREATE INDEX idx_products_category ON products(category)")
    op.execute("CREATE INDEX idx_products_name ON products(name)")


def downgrade() -> None:
    # Drop tables in reverse order
    op.execute("DROP TABLE IF EXISTS products")
    op.execute("DROP TABLE IF EXISTS notes")
    op.execute("DROP TABLE IF EXISTS users")

