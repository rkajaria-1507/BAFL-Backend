"""
Invoice API endpoints.
"""
from datetime import date as date_type
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from src.api.v1.dependencies.auth import get_current_user
from src.core.logging import api_logger
from src.db.database import get_db
from src.db.models.user import User, UserRole
from src.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceDetailedResponse,
    InvoiceListResponse,
    InvoiceCreateResponse,
    InvoiceDefaultsResponse
)
from src.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"], redirect_slashes=False)


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin privileges."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


@router.post("/", response_model=InvoiceCreateResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> InvoiceCreateResponse:
    """Create a new invoice (Admin only)."""
    api_logger.info(
        f"Creating invoice '{payload.invoice_no}' by user {current_user.username} (ID: {current_user.id})"
    )
    try:
        invoice = InvoiceService.create_invoice(db, payload, current_user.id)
        api_logger.info(f"Successfully created invoice '{invoice.invoice_no}' (ID: {invoice.id})")
        return InvoiceCreateResponse(id=invoice.id, invoice_no=invoice.invoice_no)
    except Exception as e:
        api_logger.error(f"Failed to create invoice '{payload.invoice_no}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")


@router.get("/", response_model=InvoiceListResponse)
def get_invoices(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("date", description="Sort field: date, invoice_no, created_at, total_amount"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    search: Optional[str] = Query(None, description="Search in invoice number and client name"),
    school_id: Optional[int] = Query(None, description="Filter by school ID"),
    start_date: Optional[date_type] = Query(None, description="Filter invoices from this date"),
    end_date: Optional[date_type] = Query(None, description="Filter invoices until this date"),
    template: Optional[str] = Query(None, description="Filter by template type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> InvoiceListResponse:
    """Get all invoices with pagination and filtering."""
    api_logger.info(
        f"Fetching invoices. User: {current_user.username}, Page: {page}, Limit: {limit}"
    )
    try:
        invoices, pagination = InvoiceService.get_all_invoices(
            db=db,
            page=page,
            limit=limit,
            sort=sort,
            order=order,
            search=search,
            school_id=school_id,
            start_date=start_date,
            end_date=end_date,
            template=template
        )
        
        # Convert invoices to response models with created_by_name
        invoice_responses = []
        for inv in invoices:
            inv_dict = {
                "id": inv.id,
                "invoice_no": inv.invoice_no,
                "heading": inv.heading,
                "template": inv.template,
                "frequency": inv.frequency,
                "date": inv.date,
                "school_id": inv.school_id,
                "billed_from_name": inv.billed_from_name,
                "billed_to_name": inv.billed_to_name,
                "total_amount": inv.total_amount,
                "created_by": inv.created_by,
                "created_by_name": inv.creator.name if inv.creator else None,
                "created_at": inv.created_at,
                "updated_at": inv.updated_at
            }
            invoice_responses.append(InvoiceResponse(**inv_dict))
        
        return InvoiceListResponse(
            invoices=invoice_responses,
            pagination=pagination
        )
    except Exception as e:
        api_logger.error(f"Failed to fetch invoices: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch invoices: {str(e)}")


@router.get("/pre-create", response_model=InvoiceDefaultsResponse)
def get_invoice_defaults(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> InvoiceDefaultsResponse:
    """Get default values for invoice creation (Admin only)."""
    api_logger.info(f"Fetching invoice defaults for user {current_user.username}")
    try:
        return InvoiceService.get_invoice_defaults(db)
    except Exception as e:
        api_logger.error(f"Failed to fetch invoice defaults: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch defaults: {str(e)}")


@router.get("/next-number", response_model=dict)
def get_next_invoice_number(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> dict:
    """Get the next available invoice number (Admin only)."""
    api_logger.info(f"Fetching next invoice number for user {current_user.username}")
    try:
        next_no = InvoiceService.get_next_invoice_number(db)
        return {"next_invoice_no": next_no}
    except Exception as e:
        api_logger.error(f"Failed to fetch next invoice number: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch next number: {str(e)}")


@router.get("/{invoice_id}", response_model=InvoiceDetailedResponse)
def get_invoice(
    invoice_id: int = Path(..., description="Invoice ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> InvoiceDetailedResponse:
    """Get a specific invoice by ID."""
    api_logger.info(f"Fetching invoice {invoice_id} for user {current_user.username}")
    try:
        invoice = InvoiceService.get_invoice(db, invoice_id)
        if not invoice:
            api_logger.warning(f"Invoice not found. Invoice ID: {invoice_id}")
            raise HTTPException(status_code=404, detail="Invoice not found")
        return InvoiceDetailedResponse.from_invoice(invoice)
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to fetch invoice {invoice_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch invoice: {str(e)}")


@router.put("/{invoice_id}", response_model=InvoiceDetailedResponse)
def update_invoice(
    payload: InvoiceUpdate,
    invoice_id: int = Path(..., description="Invoice ID"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> InvoiceDetailedResponse:
    """Update an existing invoice (Admin only)."""
    api_logger.info(f"Updating invoice {invoice_id} by user {current_user.username}")
    try:
        invoice = InvoiceService.update_invoice(db, invoice_id, payload)
        if not invoice:
            api_logger.warning(f"Invoice not found for update. Invoice ID: {invoice_id}")
            raise HTTPException(status_code=404, detail="Invoice not found")
        api_logger.info(f"Successfully updated invoice {invoice_id}")
        return InvoiceDetailedResponse.from_invoice(invoice)
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to update invoice {invoice_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update invoice: {str(e)}")


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int = Path(..., description="Invoice ID"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete an invoice (Admin only)."""
    api_logger.info(f"Deleting invoice {invoice_id} by user {current_user.username}")
    try:
        success = InvoiceService.delete_invoice(db, invoice_id)
        if not success:
            api_logger.warning(f"Invoice not found for deletion. Invoice ID: {invoice_id}")
            raise HTTPException(status_code=404, detail="Invoice not found")
        api_logger.info(f"Successfully deleted invoice {invoice_id}")
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to delete invoice {invoice_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete invoice: {str(e)}")
    return None


@router.post("/{invoice_id}/duplicate", response_model=InvoiceCreateResponse, status_code=status.HTTP_201_CREATED)
def duplicate_invoice(
    invoice_id: int = Path(..., description="Invoice ID to duplicate"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> InvoiceCreateResponse:
    """Duplicate an existing invoice (Admin only)."""
    api_logger.info(f"Duplicating invoice {invoice_id} by user {current_user.username}")
    try:
        new_invoice = InvoiceService.duplicate_invoice(db, invoice_id, current_user.id)
        if not new_invoice:
            api_logger.warning(f"Invoice not found for duplication. Invoice ID: {invoice_id}")
            raise HTTPException(status_code=404, detail="Invoice not found")
        api_logger.info(f"Successfully duplicated invoice {invoice_id} to {new_invoice.id}")
        return InvoiceCreateResponse(id=new_invoice.id, invoice_no=new_invoice.invoice_no)
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to duplicate invoice {invoice_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to duplicate invoice: {str(e)}")
