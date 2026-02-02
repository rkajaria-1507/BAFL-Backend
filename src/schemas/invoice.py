"""
Pydantic schemas for Invoice API.
"""
from datetime import datetime
from datetime import date as date_type
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


# Invoice Item Schemas
class InvoiceItemBase(BaseModel):
    """Base schema for invoice items."""
    description: str = Field(..., max_length=500)
    sessions: int = Field(default=0, ge=0)
    rate: Decimal = Field(default=0, ge=0)
    amount: Decimal = Field(default=0, ge=0)
    sort_order: int = Field(default=0, ge=0)


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating invoice items."""
    pass


class InvoiceItemUpdate(BaseModel):
    """Schema for updating invoice items."""
    description: Optional[str] = Field(None, max_length=500)
    sessions: Optional[int] = Field(None, ge=0)
    rate: Optional[Decimal] = Field(None, ge=0)
    amount: Optional[Decimal] = Field(None, ge=0)
    sort_order: Optional[int] = Field(None, ge=0)


class InvoiceItemResponse(InvoiceItemBase):
    """Schema for invoice item responses."""
    id: int

    class Config:
        from_attributes = True


# Nested Schemas for Invoice Details
class BilledFromSchema(BaseModel):
    """Schema for billed from information."""
    name: Optional[str] = None
    address: Optional[str] = None


class BilledToSchema(BaseModel):
    """Schema for billed to information."""
    name: str
    address: Optional[str] = None


class PeriodSchema(BaseModel):
    """Schema for billing period."""
    start: Optional[date_type] = None
    end: Optional[date_type] = None


class PaymentDetailsSchema(BaseModel):
    """Schema for payment details."""
    bank_name: Optional[str] = None
    branch: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = None
    pan: Optional[str] = None


class SignatorySchema(BaseModel):
    """Schema for signatory information."""
    name: Optional[str] = None
    title: Optional[str] = None


# Invoice Schemas
class InvoiceBase(BaseModel):
    """Base schema for invoices."""
    invoice_no: str = Field(..., max_length=50)
    template: str = Field(default="archery", max_length=50)
    frequency: str = Field(default="monthly", max_length=20)
    date: date_type
    school_id: Optional[int] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""
    billed_from: Optional[BilledFromSchema] = None
    billed_to: BilledToSchema
    period: Optional[PeriodSchema] = None
    payment_details: Optional[PaymentDetailsSchema] = None
    signatory: Optional[SignatorySchema] = None
    items: list[InvoiceItemCreate] = []


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""
    invoice_no: Optional[str] = Field(None, max_length=50)
    template: Optional[str] = Field(None, max_length=50)
    frequency: Optional[str] = Field(None, max_length=20)
    date: Optional[date_type] = None
    school_id: Optional[int] = None
    billed_from: Optional[BilledFromSchema] = None
    billed_to: Optional[BilledToSchema] = None
    period: Optional[PeriodSchema] = None
    payment_details: Optional[PaymentDetailsSchema] = None
    signatory: Optional[SignatorySchema] = None
    notes: Optional[str] = None
    items: Optional[list[InvoiceItemCreate]] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice responses."""
    id: int
    billed_from_name: Optional[str] = None
    billed_from_address: Optional[str] = None
    billed_to_name: str
    billed_to_address: Optional[str] = None
    period_start: Optional[date_type] = None
    period_end: Optional[date_type] = None
    bank_name: Optional[str] = None
    branch: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = None
    pan: Optional[str] = None
    signatory_name: Optional[str] = None
    signatory_title: Optional[str] = None
    total_amount: Decimal
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: list[InvoiceItemResponse] = []

    class Config:
        from_attributes = True


class InvoiceDetailedResponse(InvoiceResponse):
    """Detailed schema with computed fields."""
    billed_from: BilledFromSchema
    billed_to: BilledToSchema
    period: PeriodSchema
    payment_details: PaymentDetailsSchema
    signatory: SignatorySchema
    created_by_name: Optional[str] = None

    @classmethod
    def from_invoice(cls, invoice):
        """Convert Invoice model to detailed response."""
        return cls(
            id=invoice.id,
            invoice_no=invoice.invoice_no,
            template=invoice.template,
            frequency=invoice.frequency,
            date=invoice.date,
            school_id=invoice.school_id,
            billed_from_name=invoice.billed_from_name,
            billed_from_address=invoice.billed_from_address,
            billed_to_name=invoice.billed_to_name,
            billed_to_address=invoice.billed_to_address,
            period_start=invoice.period_start,
            period_end=invoice.period_end,
            bank_name=invoice.bank_name,
            branch=invoice.branch,
            account_number=invoice.account_number,
            ifsc=invoice.ifsc,
            pan=invoice.pan,
            signatory_name=invoice.signatory_name,
            signatory_title=invoice.signatory_title,
            notes=invoice.notes,
            total_amount=invoice.total_amount,
            created_by=invoice.created_by,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
            items=[InvoiceItemResponse.model_validate(item) for item in invoice.items],
            billed_from=BilledFromSchema(
                name=invoice.billed_from_name,
                address=invoice.billed_from_address
            ),
            billed_to=BilledToSchema(
                name=invoice.billed_to_name,
                address=invoice.billed_to_address
            ),
            period=PeriodSchema(
                start=invoice.period_start,
                end=invoice.period_end
            ),
            payment_details=PaymentDetailsSchema(
                bank_name=invoice.bank_name,
                branch=invoice.branch,
                account_number=invoice.account_number,
                ifsc=invoice.ifsc,
                pan=invoice.pan
            ),
            signatory=SignatorySchema(
                name=invoice.signatory_name,
                title=invoice.signatory_title
            ),
            created_by_name=invoice.creator.username if invoice.creator else None
        )


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list."""
    invoices: list[InvoiceResponse]
    pagination: dict


class InvoiceCreateResponse(BaseModel):
    """Schema for invoice creation response."""
    invoice_id: int
    invoice_no: str


# Default/PreCreate Schemas
class InvoiceDefaultsResponse(BaseModel):
    """Schema for pre-populated invoice defaults."""
    billed_from: BilledFromSchema
    payment_details: PaymentDetailsSchema
    signatory: SignatorySchema
    next_invoice_no: str
