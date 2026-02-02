"""
Migration script to create invoice tables.

Run this after installing the backend to create the invoice tables.
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import engine, Base
from src.db.models.invoice import Invoice, InvoiceItem
from src.core.logging import db_logger


def create_invoice_tables():
    """Create invoice and invoice_items tables."""
    try:
        db_logger.info("Creating invoice tables...")
        
        # Create tables
        Invoice.__table__.create(bind=engine, checkfirst=True)
        InvoiceItem.__table__.create(bind=engine, checkfirst=True)
        
        db_logger.info("Invoice tables created successfully!")
        print("✓ Invoice tables created successfully!")
        
    except Exception as e:
        db_logger.error(f"Failed to create invoice tables: {str(e)}")
        print(f"✗ Failed to create invoice tables: {str(e)}")
        raise


if __name__ == "__main__":
    create_invoice_tables()
