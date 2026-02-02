"""
Invoice service for business logic.
"""
from datetime import date
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from src.db.repositories.invoice_repository import InvoiceRepository, InvoiceItemRepository
from src.db.models.invoice import Invoice, InvoiceItem
from src.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceDefaultsResponse,
    BilledFromSchema,
    PaymentDetailsSchema,
    SignatorySchema
)


class InvoiceService:
    """Service for invoice business logic."""
    
    @staticmethod
    def create_invoice(db: Session, invoice_data: InvoiceCreate, created_by: int) -> Invoice:
        """Create a new invoice with items."""
        # Calculate total amount from items
        total_amount = sum(item.amount for item in invoice_data.items)
        
        # Create invoice model
        invoice = Invoice(
            invoice_no=invoice_data.invoice_no,
            heading=invoice_data.heading,
            template=invoice_data.template,
            frequency=invoice_data.frequency,
            date=invoice_data.date,
            school_id=invoice_data.school_id,
            billed_from_name=invoice_data.billed_from.name if invoice_data.billed_from else "BAFL Foundation",
            billed_from_address=invoice_data.billed_from.address if invoice_data.billed_from else None,
            billed_to_name=invoice_data.billed_to.name,
            billed_to_address=invoice_data.billed_to.address,
            period_start=invoice_data.period.start if invoice_data.period else None,
            period_end=invoice_data.period.end if invoice_data.period else None,
            payment_bank_name=invoice_data.payment_details.bank_name if invoice_data.payment_details else None,
            payment_branch=invoice_data.payment_details.branch if invoice_data.payment_details else None,
            payment_account_number=invoice_data.payment_details.account_number if invoice_data.payment_details else None,
            payment_ifsc=invoice_data.payment_details.ifsc if invoice_data.payment_details else None,
            payment_pan=invoice_data.payment_details.pan if invoice_data.payment_details else None,
            signatory_name=invoice_data.signatory.name if invoice_data.signatory else None,
            signatory_title=invoice_data.signatory.title if invoice_data.signatory else None,
            total_amount=total_amount,
            created_by=created_by
        )
        
        # Create invoice in database
        invoice = InvoiceRepository.create(db, invoice)
        
        # Create invoice items
        for idx, item_data in enumerate(invoice_data.items):
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=item_data.description,
                sessions=item_data.sessions,
                rate=item_data.rate,
                amount=item_data.amount,
                sort_order=item_data.sort_order or idx
            )
            InvoiceItemRepository.create(db, item)
        
        # Refresh to get items
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_invoice(db: Session, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID."""
        return InvoiceRepository.get_by_id(db, invoice_id)

    @staticmethod
    def get_all_invoices(
        db: Session,
        page: int = 1,
        limit: int = 20,
        sort: str = "date",
        order: str = "desc",
        search: Optional[str] = None,
        school_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        template: Optional[str] = None
    ) -> tuple[list[Invoice], dict]:
        """
        Get all invoices with pagination and filtering.
        Returns tuple of (invoices, pagination_info).
        """
        skip = (page - 1) * limit
        invoices, total = InvoiceRepository.get_all(
            db=db,
            skip=skip,
            limit=limit,
            sort=sort,
            order=order,
            search=search,
            school_id=school_id,
            start_date=start_date,
            end_date=end_date,
            template=template
        )
        
        total_pages = (total + limit - 1) // limit  # Ceiling division
        pagination = {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
        
        return invoices, pagination

    @staticmethod
    def update_invoice(db: Session, invoice_id: int, invoice_data: InvoiceUpdate) -> Optional[Invoice]:
        """Update an invoice."""
        invoice = InvoiceRepository.get_by_id(db, invoice_id)
        if not invoice:
            return None
        
        update_dict = {}
        
        # Update basic fields
        if invoice_data.invoice_no is not None:
            update_dict["invoice_no"] = invoice_data.invoice_no
        if invoice_data.heading is not None:
            update_dict["heading"] = invoice_data.heading
        if invoice_data.template is not None:
            update_dict["template"] = invoice_data.template
        if invoice_data.frequency is not None:
            update_dict["frequency"] = invoice_data.frequency
        if invoice_data.date is not None:
            update_dict["date"] = invoice_data.date
        if invoice_data.school_id is not None:
            update_dict["school_id"] = invoice_data.school_id
        
        # Update nested objects
        if invoice_data.billed_from:
            if invoice_data.billed_from.name is not None:
                update_dict["billed_from_name"] = invoice_data.billed_from.name
            if invoice_data.billed_from.address is not None:
                update_dict["billed_from_address"] = invoice_data.billed_from.address
        
        if invoice_data.billed_to:
            if invoice_data.billed_to.name is not None:
                update_dict["billed_to_name"] = invoice_data.billed_to.name
            if invoice_data.billed_to.address is not None:
                update_dict["billed_to_address"] = invoice_data.billed_to.address
        
        if invoice_data.period:
            if invoice_data.period.start is not None:
                update_dict["period_start"] = invoice_data.period.start
            if invoice_data.period.end is not None:
                update_dict["period_end"] = invoice_data.period.end
        
        if invoice_data.payment_details:
            if invoice_data.payment_details.bank_name is not None:
                update_dict["payment_bank_name"] = invoice_data.payment_details.bank_name
            if invoice_data.payment_details.branch is not None:
                update_dict["payment_branch"] = invoice_data.payment_details.branch
            if invoice_data.payment_details.account_number is not None:
                update_dict["payment_account_number"] = invoice_data.payment_details.account_number
            if invoice_data.payment_details.ifsc is not None:
                update_dict["payment_ifsc"] = invoice_data.payment_details.ifsc
            if invoice_data.payment_details.pan is not None:
                update_dict["payment_pan"] = invoice_data.payment_details.pan
        
        if invoice_data.signatory:
            if invoice_data.signatory.name is not None:
                update_dict["signatory_name"] = invoice_data.signatory.name
            if invoice_data.signatory.title is not None:
                update_dict["signatory_title"] = invoice_data.signatory.title
        
        # Update items if provided
        if invoice_data.items is not None:
            # Delete existing items
            InvoiceItemRepository.delete_by_invoice_id(db, invoice_id)
            
            # Create new items
            total_amount = Decimal(0)
            for idx, item_data in enumerate(invoice_data.items):
                item = InvoiceItem(
                    invoice_id=invoice_id,
                    description=item_data.description,
                    sessions=item_data.sessions,
                    rate=item_data.rate,
                    amount=item_data.amount,
                    sort_order=item_data.sort_order or idx
                )
                InvoiceItemRepository.create(db, item)
                total_amount += item_data.amount
            
            update_dict["total_amount"] = total_amount
        
        # Update invoice
        invoice = InvoiceRepository.update(db, invoice, update_dict)
        db.refresh(invoice)
        return invoice

    @staticmethod
    def delete_invoice(db: Session, invoice_id: int) -> bool:
        """Delete an invoice."""
        invoice = InvoiceRepository.get_by_id(db, invoice_id)
        if not invoice:
            return False
        InvoiceRepository.delete(db, invoice)
        return True

    @staticmethod
    def get_next_invoice_number(db: Session) -> str:
        """Get the next available invoice number."""
        return InvoiceRepository.get_next_invoice_number(db)

    @staticmethod
    def duplicate_invoice(db: Session, invoice_id: int, created_by: int) -> Optional[Invoice]:
        """Duplicate an existing invoice."""
        original = InvoiceRepository.get_by_id(db, invoice_id)
        if not original:
            return None
        
        # Get next invoice number
        next_no = InvoiceRepository.get_next_invoice_number(db)
        
        # Create new invoice
        new_invoice = Invoice(
            invoice_no=next_no,
            heading=original.heading,
            template=original.template,
            frequency=original.frequency,
            date=date.today(),
            school_id=original.school_id,
            billed_from_name=original.billed_from_name,
            billed_from_address=original.billed_from_address,
            billed_to_name=original.billed_to_name,
            billed_to_address=original.billed_to_address,
            period_start=original.period_start,
            period_end=original.period_end,
            payment_bank_name=original.payment_bank_name,
            payment_branch=original.payment_branch,
            payment_account_number=original.payment_account_number,
            payment_ifsc=original.payment_ifsc,
            payment_pan=original.payment_pan,
            signatory_name=original.signatory_name,
            signatory_title=original.signatory_title,
            total_amount=original.total_amount,
            created_by=created_by
        )
        
        new_invoice = InvoiceRepository.create(db, new_invoice)
        
        # Duplicate items
        for original_item in original.items:
            new_item = InvoiceItem(
                invoice_id=new_invoice.id,
                description=original_item.description,
                sessions=original_item.sessions,
                rate=original_item.rate,
                amount=original_item.amount,
                sort_order=original_item.sort_order
            )
            InvoiceItemRepository.create(db, new_item)
        
        db.refresh(new_invoice)
        return new_invoice

    @staticmethod
    def get_invoice_defaults(db: Session) -> InvoiceDefaultsResponse:
        """Get default values for invoice creation."""
        next_no = InvoiceRepository.get_next_invoice_number(db)
        
        return InvoiceDefaultsResponse(
            billed_from=BilledFromSchema(
                name="BAFL Foundation",
                address="FLC/5 Siddhivinayak Vihars No 72/2E, Hadapsar,\nPune, 411028 Maharashtra, India"
            ),
            payment_details=PaymentDetailsSchema(
                bank_name="HDFC Bank",
                branch="Wanowrie",
                account_number="50200088770120",
                ifsc="HDFC0000486",
                pan="AAMCB1807H"
            ),
            signatory=SignatorySchema(
                name="Dawny Johnson",
                title="Founder & Director"
            ),
            next_invoice_no=next_no
        )
