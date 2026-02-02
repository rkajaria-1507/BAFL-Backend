"""
Invoice and InvoiceItem models for billing management.
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from src.db.database import Base


class Invoice(Base):
    """
    Main invoice record tracking billing information.
    """
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_no = Column(String(50), nullable=False, index=True)
    template = Column(String(50), default="archery", nullable=False)
    frequency = Column(String(20), default="monthly", nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    # Billed From
    billed_from_name = Column(String(255), nullable=True)
    billed_from_address = Column(Text, nullable=True)
    
    # Billed To (with optional FK to schools)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    billed_to_name = Column(String(255), nullable=False)
    billed_to_address = Column(Text, nullable=True)
    
    # Billing Period
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    
    # Payment Details
    bank_name = Column(String(255), nullable=True)
    branch = Column(String(255), nullable=True)
    account_number = Column(String(100), nullable=True)
    ifsc = Column(String(50), nullable=True)
    pan = Column(String(50), nullable=True)
    
    # Signatory
    signatory_name = Column(String(255), nullable=True)
    signatory_title = Column(String(255), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    total_amount = Column(Numeric(12, 2), default=0, nullable=False)
    
    # Audit Fields
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    school = relationship("School", foreign_keys=[school_id])
    creator = relationship("User", foreign_keys=[created_by])


class InvoiceItem(Base):
    """
    Individual line items in an invoice.
    """
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    sessions = Column(Integer, default=0, nullable=False)
    rate = Column(Numeric(10, 2), default=0, nullable=False)
    amount = Column(Numeric(12, 2), default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")
