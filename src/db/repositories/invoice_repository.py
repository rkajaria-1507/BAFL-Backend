"""
Invoice repository for database operations.
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, or_, and_, Integer
from src.db.models.invoice import Invoice, InvoiceItem


class InvoiceRepository:
    """Repository for Invoice database operations."""
    
    @staticmethod
    def create(db: Session, invoice: Invoice) -> Invoice:
        """Create a new invoice."""
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_by_id(db: Session, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID with items and relationships."""
        return db.scalar(
            select(Invoice)
            .options(
                joinedload(Invoice.items),
                joinedload(Invoice.school),
                joinedload(Invoice.creator)
            )
            .where(Invoice.id == invoice_id)
        )

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        sort: str = "date",
        order: str = "desc",
        search: Optional[str] = None,
        school_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        template: Optional[str] = None
    ) -> tuple[List[Invoice], int]:
        """
        Get all invoices with filtering, pagination, and sorting.
        Returns tuple of (invoices, total_count).
        """
        # Base query with relationships
        query = select(Invoice).options(
            joinedload(Invoice.items),
            joinedload(Invoice.school),
            joinedload(Invoice.creator)
        )
        
        # Apply filters
        filters = []
        
        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Invoice.invoice_no.ilike(search_pattern),
                    Invoice.billed_to_name.ilike(search_pattern)
                )
            )
        
        if school_id is not None:
            filters.append(Invoice.school_id == school_id)
        
        if start_date:
            filters.append(Invoice.date >= start_date)
        
        if end_date:
            filters.append(Invoice.date <= end_date)
        
        if template:
            filters.append(Invoice.template == template)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(Invoice)
        if filters:
            count_query = count_query.where(and_(*filters))
        total = db.scalar(count_query) or 0
        
        # Apply sorting
        sort_column = getattr(Invoice, sort, Invoice.date)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        invoices = list(db.scalars(query).unique().all())
        return invoices, total

    @staticmethod
    def update(db: Session, invoice: Invoice, update_data: dict) -> Invoice:
        """Update an invoice."""
        for key, value in update_data.items():
            if key != "items":  # Handle items separately
                setattr(invoice, key, value)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def delete(db: Session, invoice: Invoice) -> None:
        """Delete an invoice."""
        db.delete(invoice)
        db.commit()

    @staticmethod
    def get_next_invoice_number(db: Session) -> str:
        """Get the next available invoice number."""
        # Get the highest numeric invoice number
        result = db.scalar(
            select(func.max(func.cast(Invoice.invoice_no, Integer)))
        )
        if result is None:
            return "1"
        return str(result + 1)

    @staticmethod
    def get_by_invoice_no(db: Session, invoice_no: str) -> Optional[Invoice]:
        """Get invoice by invoice number."""
        return db.scalar(
            select(Invoice)
            .options(joinedload(Invoice.items))
            .where(Invoice.invoice_no == invoice_no)
        )


class InvoiceItemRepository:
    """Repository for InvoiceItem database operations."""
    
    @staticmethod
    def create(db: Session, item: InvoiceItem) -> InvoiceItem:
        """Create a new invoice item."""
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def create_bulk(db: Session, items: List[InvoiceItem]) -> List[InvoiceItem]:
        """Create multiple invoice items."""
        db.add_all(items)
        db.commit()
        for item in items:
            db.refresh(item)
        return items

    @staticmethod
    def delete_by_invoice_id(db: Session, invoice_id: int) -> None:
        """Delete all items for an invoice."""
        items = db.scalars(
            select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id)
        ).all()
        for item in items:
            db.delete(item)
        db.commit()

    @staticmethod
    def get_by_invoice_id(db: Session, invoice_id: int) -> List[InvoiceItem]:
        """Get all items for an invoice."""
        return list(
            db.scalars(
                select(InvoiceItem)
                .where(InvoiceItem.invoice_id == invoice_id)
                .order_by(InvoiceItem.sort_order)
            ).all()
        )
