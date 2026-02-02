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

### 1. Get Invoice Defaults

**GET** `/api/v1/invoices/pre-create`

Get default configuration values for creating new invoices.

**Authorization:** Admin only

**Response:** `200 OK`

```json
{
  "billed_from": {
    "name": "BAFL Foundation",
    "address": "FLC/5 Siddhivinayak Vihars No 72/2E, Hadapsar,\nPune, 411028 Maharashtra, India"
  },
  "payment_details": {
    "bank_name": "HDFC Bank",
    "branch": "Wanowrie",
    "account_number": "50200088770120",
    "ifsc": "HDFC0000486",
    "pan": "AAMCB1807H"
  },
  "signatory": {
    "name": "Dawny Johnson",
    "title": "Founder & Director"
  },
  "next_invoice_no": "24"
}
```

---

### 2. Create Invoice

**POST** `/api/v1/invoices`

Create a new invoice with line items.

**Authorization:** Admin only

**Request Body:**

```json
{
  "invoice_no": "24",
  "heading": "Invoice",
  "template": "archery",
  "frequency": "monthly",
  "date": "2026-02-02",
  "school_id": 1,
  "billed_from": {
    "name": "BAFL Foundation",
    "address": "FLC/5 Siddhivinayak Vihars No 72/2E, Hadapsar,\nPune, 411028 Maharashtra, India"
  },
  "billed_to": {
    "name": "Avasara Academy",
    "address": "Lavale, Bavdhan, Pune, Maharashtra, India, 411055"
  },
  "period": {
    "start": "2026-01-01",
    "end": "2026-01-31"
  },
  "payment_details": {
    "bank_name": "HDFC Bank",
    "branch": "Wanowrie",
    "account_number": "50200088770120",
    "ifsc": "HDFC0000486",
    "pan": "AAMCB1807H"
  },
  "signatory": {
    "name": "Dawny Johnson",
    "title": "Founder & Director"
  },
  "items": [
    {
      "description": "Archery coaching - Batch A",
      "sessions": 8,
      "rate": 1200,
      "amount": 9600,
      "sort_order": 0
    },
    {
      "description": "Archery coaching - Batch B",
      "sessions": 4,
      "rate": 1200,
      "amount": 4800,
      "sort_order": 1
    }
  ]
}
```

**Response:** `201 Created`

```json
{
  "id": 24,
  "invoice_no": "24",
  "message": "Invoice created successfully"
}
```

**Validation Rules:**
- `invoice_no` is required and should be unique
- `heading` defaults to "Invoice" if not provided
- `date` is required (YYYY-MM-DD format)
- `billed_to.name` is required
- `items` array must have at least 1 item
- Each item must have `description`
- `total_amount` is auto-calculated from sum of all item amounts

---

### 3. List Invoices

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
      "heading": "Invoice",
      "template": "archery",
      "frequency": "monthly",
      "date": "2025-09-30",
      "school_id": 1,
      "billed_from_name": "BAFL Foundation",
      "billed_to_name": "Avasara Academy",
      "total_amount": 9600,
      "created_by": 1,
      "created_by_name": "admin",
      "created_at": "2025-09-30T10:00:00Z",
      "updated_at": "2025-09-30T10:00:00Z"
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

**Note:** List response returns simplified invoice data without nested objects or items for performance.

---

### 4. Get Invoice by ID

**GET** `/api/v1/invoices/{invoice_id}`

Get detailed information about a specific invoice including all line items.

**Authorization:** Authenticated users

**Path Parameters:**

- `invoice_id` (integer, required): Invoice ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "invoice_no": "03",
  "heading": "Invoice",
  "template": "archery",
  "frequency": "monthly",
  "date": "2025-09-30",
  "school_id": 1,
  "billed_from": {
    "name": "BAFL Foundation",
    "address": "FLC/5 Siddhivinayak Vihars No 72/2E, Hadapsar,\nPune, 411028 Maharashtra, India"
  },
  "billed_to": {
    "name": "Avasara Academy",
    "address": "Lavale, Bavdhan, Pune, Maharashtra, India, 411055"
  },
  "period": {
    "start": "2025-09-01",
    "end": "2025-09-30"
  },
  "payment_details": {
    "bank_name": "HDFC Bank",
    "branch": "Wanowrie",
    "account_number": "50200088770120",
    "ifsc": "HDFC0000486",
    "pan": "AAMCB1807H"
  },
  "signatory": {
    "name": "Dawny Johnson",
    "title": "Founder & Director"
  },
  "items": [
    {
      "id": 1,
      "description": "Archery coaching - Batch A",
      "sessions": 8,
      "rate": 1200,
      "amount": 9600,
      "sort_order": 0
    }
  ],
  "total_amount": 9600,
  "created_by": 1,
  "created_at": "2025-09-30T10:00:00Z",
  "updated_at": "2025-09-30T10:00:00Z"
}
```

**Error Responses:**

- `404 Not Found` - Invoice not found

---

### 5. Update Invoice

**PUT** `/api/v1/invoices/{invoice_id}`

Update an existing invoice. All fields are optional - only include what needs to be updated.

**Authorization:** Admin only

**Path Parameters:**

- `invoice_id` (integer, required): Invoice ID

**Request Body:**

Same structure as POST, all fields optional.
**Example Update:**

```json
{
  "invoice_no": "04",
  "heading": "Tax Invoice",
  "date": "2025-10-01",
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

Returns the updated invoice (same format as GET by ID).

**Error Responses:**

- `404 Not Found` - Invoice not found
- `403 Forbidden` - Not authorized (not admin)

---

### 6. Delete Invoice

**DELETE** `/api/v1/invoices/{invoice_id}`

Delete an invoice and all its line items (cascade delete).

**Authorization:** Admin only

**Path Parameters:**

- `invoice_id` (integer, required): Invoice ID

**Response:** `204 No Content`

**Error Responses:**

- `404 Not Found` - Invoice not found
- `403 Forbidden` - Not authorized (not admin)

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
  "id": 5,
  "invoice_no": "5",
  "message": "Invoice created successfully"
}
```

**Error Responses:**

- `404 Not Found` - Invoice not found

---

## Data Models

### Invoice Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `invoice_no` | string | Yes | Invoice number (e.g., "24") |
| `heading` | string | No | Invoice heading (default: "Invoice") |
| `template` | string | No | Template type (default: "archery") |
| `frequency` | string | No | Billing frequency (default: "monthly") |
| `date` | date | Yes | Invoice date (YYYY-MM-DD) |
| `school_id` | integer | No | Reference to school |
| `billed_from` | object | No | Biller information |
| `billed_to` | object | Yes | Client information |
| `period` | object | No | Billing period |
| `payment_details` | object | No | Bank details |
| `signatory` | object | No | Signatory information |
| `items` | array | Yes | Invoice line items (min 1) |
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
  "id": 5,
  "invoice_no": "5",
  "message": "Invoice created successfully"
}
```

**Error Responses:**

- `404 Not Found` - Invoice not found

---

## Data Models

### Invoice Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `invoice_no` | string | Yes | Invoice number (e.g., "24") |
| `heading` | string | No | Invoice heading (default: "Invoice") |
| `template` | string | No | Template type (default: "archery") |
| `frequency` | string | No | Billing frequency (default: "monthly") |
| `date` | date | Yes | Invoice date (YYYY-MM-DD) |
| `school_id` | integer | No | Reference to school |
| `billed_from` | object | No | Biller information |
| `billed_to` | object | Yes | Client information |
| `period` | object | No | Billing period |
| `payment_details` | object | No | Bank details |
| `signatory` | object | No | Signatory information |
| `items` | array | Yes | Invoice line items (min 1) |

### Invoice Item Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Item description |
| `sessions` | integer | Yes | Number of sessions |
| `rate` | decimal | Yes | Rate per session |
| `amount` | decimal | Yes | Total amount (sessions × rate) |
| `sort_order` | integer | No | Display order (default: 0) |

### Nested Objects

**billed_from:**
```json
{
  "name": "string",
  "address": "string"
}
```

**billed_to:**
```json
{
  "name": "string",
  "address": "string"
}
```

**period:**
```json
{
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD"
}
```

**payment_details:**
```json
{
  "payment_bank_name": "string",
  "payment_branch": "string",
  "payment_account_number": "string",
  "payment_ifsc": "string",
  "payment_pan": "string"
}
```

**signatory:**
```json
{
  "name": "string",
  "title": "string"
}
```

---

## Database Schema

### invoices table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `invoice_no` | VARCHAR(50) | NOT NULL, UNIQUE | Invoice number |
| `heading` | VARCHAR(100) | DEFAULT 'Invoice' | Invoice heading |
| `template` | VARCHAR(50) | DEFAULT 'archery' | Template type |
| `frequency` | VARCHAR(50) | DEFAULT 'monthly' | Billing frequency |
| `date` | DATE | NOT NULL | Invoice date |
| `school_id` | INTEGER | FK → schools.id | Reference to school |
| `billed_from_name` | VARCHAR(255) | NOT NULL | Biller name |
| `billed_from_address` | TEXT | | Biller address |
| `billed_to_name` | VARCHAR(255) | NOT NULL | Client name |
| `billed_to_address` | TEXT | | Client address |
| `period_start_date` | DATE | | Period start |
| `period_end_date` | DATE | | Period end |
| `payment_bank_name` | VARCHAR(255) | | Bank name |
| `payment_branch` | VARCHAR(255) | | Bank branch |
| `payment_account_number` | VARCHAR(50) | | Account number |
| `payment_ifsc` | VARCHAR(20) | | IFSC code |
| `payment_pan` | VARCHAR(20) | | PAN number |
| `signatory_name` | VARCHAR(255) | | Signatory name |
| `signatory_title` | VARCHAR(100) | | Signatory title |
| `total_amount` | NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Total invoice amount |
| `created_by` | INTEGER | FK → users.id | Creator user ID |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `idx_invoice_no` on `invoice_no`
- `idx_school_id` on `school_id`
- `idx_created_by` on `created_by`
- `idx_date` on `date`

### invoice_items table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `invoice_id` | INTEGER | NOT NULL, FK → invoices.id ON DELETE CASCADE | Invoice reference |
| `description` | TEXT | NOT NULL | Item description |
| `sessions` | INTEGER | NOT NULL | Number of sessions |
| `rate` | NUMERIC(10,2) | NOT NULL | Rate per session |
| `amount` | NUMERIC(10,2) | NOT NULL | Total amount |
| `sort_order` | INTEGER | DEFAULT 0 | Display order |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- `idx_invoice_id` on `invoice_id`
- `idx_sort_order` on `sort_order`

---

## Example Workflows

### Create Invoice Workflow

1. **Get defaults:**
   ```
   GET /api/v1/invoices/pre-create
   ```
   Response provides default values for billed_from, payment_details, signatory, and next invoice number.

2. **Create invoice:**
   ```
   POST /api/v1/invoices
   ```
   Use defaults and user input to create invoice.

3. **View created invoice:**
   ```
   GET /api/v1/invoices/{id}
   ```

### Update Invoice Workflow

1. **Get existing invoice:**
   ```
   GET /api/v1/invoices/{id}
   ```

2. **Update fields:**
   ```
   PUT /api/v1/invoices/{id}
   ```
   Include only fields you want to update.

### Duplicate Invoice Workflow

1. **Duplicate existing invoice:**
   ```
   POST /api/v1/invoices/{id}/duplicate
   ```
   Creates new invoice with new number and today's date.

---

## Error Handling

All endpoints follow standard HTTP status codes:

- `200 OK` - Successful GET/PUT request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Validation error (see response body for details)
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized (not admin)
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include a `detail` field with error information:

```json
{
  "detail": "Error message here"
}
```

---

## Notes

- All monetary amounts use 2 decimal places
- Dates use ISO 8601 format (YYYY-MM-DD)
- Invoice numbers are strings to allow custom formats (e.g., "INV-001", "24")
- Total amount is automatically calculated from items
- Deleting an invoice cascades to delete all associated items
- The `heading` field defaults to "Invoice" if not provided
- Payment field names use `payment_` prefix (payment_bank_name, payment_branch, etc.)
- Response format varies by endpoint: lists return simple format, detail view returns full nested structure

---

## Example Usage

### Python (requests)

```python
import requests

# API base URL
BASE_URL = "http://localhost:8000/api/v1"
headers = {"Authorization": f"Bearer {access_token}"}

# Get defaults before creating invoice
response = requests.get(
    f"{BASE_URL}/invoices/pre-create",
    headers=headers
)
defaults = response.json()
print(f"Next invoice number: {defaults['next_invoice_no']}")

# Create invoice
invoice_data = {
    "invoice_no": "24",
    "heading": "Tax Invoice",
    "date": "2025-09-30",
    "billed_from": defaults["billed_from"],
    "billed_to": {
        "name": "Avasara Academy",
        "address": "School address here"
    },
    "period": {
        "start_date": "2025-09-01",
        "end_date": "2025-09-30"
    },
    "payment_details": defaults["payment_details"],
    "signatory": defaults["signatory"],
    "items": [
        {
            "description": "Archery coaching - Beginner Level",
            "sessions": 8,
            "rate": 1200,
            "amount": 9600,
            "sort_order": 0
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/invoices",
    json=invoice_data,
    headers=headers
)
result = response.json()
print(f"Invoice created with ID: {result['id']}, Number: {result['invoice_no']}")

# List invoices
response = requests.get(
    f"{BASE_URL}/invoices?page=1&limit=10",
    headers=headers
)
invoices = response.json()
print(f"Found {invoices['total']} invoices")

# Get detailed invoice
response = requests.get(
    f"{BASE_URL}/invoices/1",
    headers=headers
)
invoice = response.json()
print(f"Invoice {invoice['invoice_no']} - Total: {invoice['total_amount']}")

# Update invoice
update_data = {
    "heading": "Revised Invoice",
    "date": "2025-10-01"
}
response = requests.put(
    f"{BASE_URL}/invoices/1",
    json=update_data,
    headers=headers
)

# Duplicate invoice
response = requests.post(
    f"{BASE_URL}/invoices/1/duplicate",
    headers=headers
)
new_invoice = response.json()
print(f"Duplicated as invoice {new_invoice['invoice_no']}")

# Delete invoice
response = requests.delete(
    f"{BASE_URL}/invoices/1",
    headers=headers
)
print(f"Deleted: {response.status_code == 204}")
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
};

// Get defaults
const defaultsResponse = await fetch(`${BASE_URL}/invoices/pre-create`, { headers });
const defaults = await defaultsResponse.json();

// Create invoice
const invoiceData = {
  invoice_no: '24',
  heading: 'Tax Invoice',
  date: '2025-09-30',
  billed_from: defaults.billed_from,
  billed_to: {
    name: 'Avasara Academy',
    address: 'School address here'
  },
  period: {
    start_date: '2025-09-01',
    end_date: '2025-09-30'
  },
  payment_details: defaults.payment_details,
  signatory: defaults.signatory,
  items: [
    {
      description: 'Archery coaching - Beginner Level',
      sessions: 8,
      rate: 1200,
      amount: 9600,
      sort_order: 0
    }
  ]
};

const response = await fetch(`${BASE_URL}/invoices`, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(invoiceData)
});

const result = await response.json();
console.log(`Invoice created: ${result.invoice_no}`);
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
