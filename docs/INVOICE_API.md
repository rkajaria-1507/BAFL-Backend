# Invoice API Documentation

## Overview

The Invoice API provides endpoints for managing billing invoices for schools and clients. It supports creating, reading, updating, and deleting invoices with line items.

## Authentication

All endpoints require authentication. Most endpoints require **Admin privileges**.

## Base URL

```
/api/v1/invoices
```

---

## Endpoints

### 1. Create Invoice

**POST** `/api/v1/invoices`

Create a new invoice with line items.

**Authorization:** Admin only

**Request Body:**

```json
{
  "invoice_no": "03",
  "template": "archery",
  "frequency": "monthly",
  "date": "2025-09-30",
  "school_id": 1,
  "billed_from": {
    "name": "BAFL Foundation",
    "address": "123 Main St\nCity, State\nPIN: 123456"
  },
  "billed_to": {
    "name": "Avasara Academy",
    "address": "456 School Rd\nCity, State\nPIN: 654321"
  },
  "period": {
    "start": "2025-09-01",
    "end": "2025-09-30"
  },
  "payment_details": {
    "bank_name": "HDFC Bank",
    "branch": "Main Branch",
    "account_number": "1234567890",
    "ifsc": "HDFC0001234",
    "pan": "ABCDE1234F"
  },
  "signatory": {
    "name": "Dawny Johnson",
    "title": "Founder & Director"
  },
  "notes": "Thank you for your business",
  "items": [
    {
      "description": "Archery coaching - Batch A",
      "sessions": 8,
      "rate": 1200,
      "amount": 9600,
      "sort_order": 0
    }
  ]
}
```

**Response:** `201 Created`

```json
{
  "invoice_id": 1,
  "invoice_no": "03"
}
```

---

### 2. List Invoices

**GET** `/api/v1/invoices`

Get paginated list of invoices with filtering and sorting.

**Authorization:** Authenticated users

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page (max 100) |
| `sort` | string | "date" | Sort field: `date`, `invoice_no`, `created_at`, `total_amount` |
| `order` | string | "desc" | Sort order: `asc` or `desc` |
| `search` | string | - | Search in invoice number and client name |
| `school_id` | integer | - | Filter by school ID |
| `start_date` | date | - | Filter invoices from this date (YYYY-MM-DD) |
| `end_date` | date | - | Filter invoices until this date (YYYY-MM-DD) |
| `template` | string | - | Filter by template type |

**Example Request:**

```
GET /api/v1/invoices?page=1&limit=10&sort=date&order=desc&school_id=1
```

**Response:** `200 OK`

```json
{
  "invoices": [
    {
      "id": 1,
      "invoice_no": "03",
      "template": "archery",
      "frequency": "monthly",
      "date": "2025-09-30",
      "school_id": 1,
      "billed_from_name": "BAFL Foundation",
      "billed_to_name": "Avasara Academy",
      "total_amount": 9600,
      "created_at": "2025-09-30T10:00:00Z",
      "items": [...]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 45,
    "total_pages": 5
  }
}
```

---

### 3. Get Invoice by ID

**GET** `/api/v1/invoices/{invoice_id}`

Get detailed information about a specific invoice.

**Authorization:** Authenticated users

**Path Parameters:**

- `invoice_id` (integer, required): Invoice ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "invoice_no": "03",
  "template": "archery",
  "frequency": "monthly",
  "date": "2025-09-30",
  "school_id": 1,
  "billed_from": {
    "name": "BAFL Foundation",
    "address": "123 Main St\nCity, State"
  },
  "billed_to": {
    "name": "Avasara Academy",
    "address": "456 School Rd\nCity, State"
  },
  "period": {
    "start": "2025-09-01",
    "end": "2025-09-30"
  },
  "payment_details": {
    "bank_name": "HDFC Bank",
    "branch": "Main Branch",
    "account_number": "1234567890",
    "ifsc": "HDFC0001234",
    "pan": "ABCDE1234F"
  },
  "signatory": {
    "name": "Dawny Johnson",
    "title": "Founder & Director"
  },
  "notes": "Thank you for your business",
  "total_amount": 9600,
  "created_by": 1,
  "created_by_name": "admin",
  "created_at": "2025-09-30T10:00:00Z",
  "updated_at": "2025-09-30T10:00:00Z",
  "items": [
    {
      "id": 1,
      "description": "Archery coaching - Batch A",
      "sessions": 8,
      "rate": 1200,
      "amount": 9600,
      "sort_order": 0
    }
  ]
}
```

**Error Responses:**

- `404 Not Found` - Invoice not found

---

### 4. Update Invoice

**PUT** `/api/v1/invoices/{invoice_id}`

Update an existing invoice.

**Authorization:** Admin only

**Path Parameters:**

- `invoice_id` (integer, required): Invoice ID

**Request Body:**

All fields are optional. Only include fields you want to update.

```json
{
  "invoice_no": "04",
  "date": "2025-10-01",
  "notes": "Updated notes",
  "items": [
    {
      "description": "Updated description",
      "sessions": 10,
      "rate": 1500,
      "amount": 15000,
      "sort_order": 0
    }
  ]
}
```

**Response:** `200 OK`

Returns the updated invoice (same format as Get Invoice by ID).

**Error Responses:**

- `404 Not Found` - Invoice not found
- `403 Forbidden` - Not authorized (not admin)

---

### 5. Delete Invoice

**DELETE** `/api/v1/invoices/{invoice_id}`

Delete an invoice and all its items.

**Authorization:** Admin only

**Path Parameters:**

- `invoice_id` (integer, required): Invoice ID

**Response:** `204 No Content`

**Error Responses:**

- `404 Not Found` - Invoice not found
- `403 Forbidden` - Not authorized (not admin)

---

### 6. Get Invoice Defaults

**GET** `/api/v1/invoices/pre-create`

Get default values for creating a new invoice (billed from, payment details, signatory, next invoice number).

**Authorization:** Admin only

**Response:** `200 OK`

```json
{
  "billed_from": {
    "name": "BAFL Foundation",
    "address": "Your address here"
  },
  "payment_details": {
    "bank_name": "Your Bank Name",
    "branch": "Your Branch",
    "account_number": "XXXX-XXXX-XXXX",
    "ifsc": "XXXXXX",
    "pan": "XXXXXXXXXX"
  },
  "signatory": {
    "name": "Dawny Johnson",
    "title": "Founder & Director"
  },
  "next_invoice_no": "4"
}
```

---

### 7. Get Next Invoice Number

**GET** `/api/v1/invoices/next-number`

Get the next available invoice number.

**Authorization:** Admin only

**Response:** `200 OK`

```json
{
  "next_invoice_no": "4"
}
```

---

### 8. Duplicate Invoice

**POST** `/api/v1/invoices/{invoice_id}/duplicate`

Create a copy of an existing invoice with a new invoice number and today's date.

**Authorization:** Admin only

**Path Parameters:**

- `invoice_id` (integer, required): Invoice ID to duplicate

**Response:** `201 Created`

```json
{
  "invoice_id": 5,
  "invoice_no": "5"
}
```

**Error Responses:**

- `404 Not Found` - Invoice not found

---

## Data Models

### Invoice Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `invoice_no` | string | Yes | Invoice number (e.g., "03") |
| `template` | string | No | Template type (default: "archery") |
| `frequency` | string | No | Billing frequency (default: "monthly") |
| `date` | date | Yes | Invoice date (YYYY-MM-DD) |
| `school_id` | integer | No | Reference to school |
| `billed_from` | object | No | Biller information |
| `billed_to` | object | Yes | Client information |
| `period` | object | No | Billing period |
| `payment_details` | object | No | Bank details |
| `signatory` | object | No | Signatory information |
| `notes` | string | No | Additional notes |
| `items` | array | Yes | Invoice line items |

### Invoice Item Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Item description |
| `sessions` | integer | No | Number of sessions (default: 0) |
| `rate` | decimal | No | Rate per session (default: 0) |
| `amount` | decimal | No | Total amount (default: 0) |
| `sort_order` | integer | No | Display order (default: 0) |

---

## Error Handling

All endpoints return standard error responses:

**400 Bad Request** - Invalid request data
```json
{
  "detail": "Validation error message"
}
```

**401 Unauthorized** - Not authenticated
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden** - Not authorized (insufficient privileges)
```json
{
  "detail": "Admin privileges required"
}
```

**404 Not Found** - Resource not found
```json
{
  "detail": "Invoice not found"
}
```

**500 Internal Server Error** - Server error
```json
{
  "detail": "Error message"
}
```

---

## Example Usage

### Python (requests)

```python
import requests

# API base URL
BASE_URL = "http://localhost:8000/api/v1"
headers = {"Authorization": f"Bearer {access_token}"}

# Create invoice
invoice_data = {
    "invoice_no": "03",
    "date": "2025-09-30",
    "billed_to": {"name": "Avasara Academy"},
    "items": [
        {
            "description": "Archery coaching",
            "sessions": 8,
            "rate": 1200,
            "amount": 9600
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/invoices",
    json=invoice_data,
    headers=headers
)
print(response.json())

# List invoices
response = requests.get(
    f"{BASE_URL}/invoices?page=1&limit=10",
    headers=headers
)
print(response.json())

# Get invoice
response = requests.get(
    f"{BASE_URL}/invoices/1",
    headers=headers
)
print(response.json())
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
};

// Create invoice
const invoiceData = {
  invoice_no: '03',
  date: '2025-09-30',
  billed_to: { name: 'Avasara Academy' },
  items: [
    {
      description: 'Archery coaching',
      sessions: 8,
      rate: 1200,
      amount: 9600
    }
  ]
};

const response = await fetch(`${BASE_URL}/invoices`, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(invoiceData)
});

const result = await response.json();
console.log(result);
```

---

## Migration

To add invoice tables to your existing database, run:

```bash
python scripts/create_invoice_tables.py
```

Or use Alembic for proper migrations:

```bash
alembic revision --autogenerate -m "Add invoice tables"
alembic upgrade head
```

---

## Notes

- All invoice operations require authentication
- Only admins can create, update, delete, and duplicate invoices
- All users can view invoices they have access to
- Invoice numbers should be unique but are not enforced at database level
- Total amount is calculated automatically from line items
- Deleting an invoice cascades to delete all its items
- The `school_id` field creates an optional foreign key to the schools table
