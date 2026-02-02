# Invoice API Quick Reference

## Base URL
```
http://localhost:8000/api/v1/invoices
```

## Authentication
All endpoints require Bearer token:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## Quick Examples

### 1. Get Invoice Defaults (Admin)
```bash
curl -X GET "http://localhost:8000/api/v1/invoices/pre-create" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Create Invoice (Admin)
```bash
curl -X POST "http://localhost:8000/api/v1/invoices" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_no": "1",
    "date": "2025-01-31",
    "template": "archery",
    "frequency": "monthly",
    "billed_to": {
      "name": "Avasara Academy",
      "address": "123 School St"
    },
    "items": [
      {
        "description": "Archery coaching",
        "sessions": 8,
        "rate": 1200,
        "amount": 9600,
        "sort_order": 0
      }
    ]
  }'
```

### 3. List All Invoices
```bash
curl -X GET "http://localhost:8000/api/v1/invoices?page=1&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Get Invoice by ID
```bash
curl -X GET "http://localhost:8000/api/v1/invoices/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Update Invoice (Admin)
```bash
curl -X PUT "http://localhost:8000/api/v1/invoices/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Updated notes"
  }'
```

### 6. Delete Invoice (Admin)
```bash
curl -X DELETE "http://localhost:8000/api/v1/invoices/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. Duplicate Invoice (Admin)
```bash
curl -X POST "http://localhost:8000/api/v1/invoices/1/duplicate" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## JavaScript/React Example

```javascript
// API client setup
const BASE_URL = 'http://localhost:8000/api/v1';
const token = localStorage.getItem('access_token');

const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Create invoice
async function createInvoice(invoiceData) {
  const response = await fetch(`${BASE_URL}/invoices`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(invoiceData)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }
  
  return await response.json();
}

// List invoices with pagination
async function listInvoices(page = 1, limit = 20, filters = {}) {
  const params = new URLSearchParams({
    page,
    limit,
    ...filters
  });
  
  const response = await fetch(`${BASE_URL}/invoices?${params}`, {
    headers: headers
  });
  
  return await response.json();
}

// Get invoice by ID
async function getInvoice(id) {
  const response = await fetch(`${BASE_URL}/invoices/${id}`, {
    headers: headers
  });
  
  return await response.json();
}

// Update invoice
async function updateInvoice(id, updates) {
  const response = await fetch(`${BASE_URL}/invoices/${id}`, {
    method: 'PUT',
    headers: headers,
    body: JSON.stringify(updates)
  });
  
  return await response.json();
}

// Delete invoice
async function deleteInvoice(id) {
  const response = await fetch(`${BASE_URL}/invoices/${id}`, {
    method: 'DELETE',
    headers: headers
  });
  
  return response.status === 204;
}

// Usage examples
const invoice = await createInvoice({
  invoice_no: "1",
  date: "2025-01-31",
  billed_to: { name: "Avasara Academy" },
  items: [
    {
      description: "Archery coaching",
      sessions: 8,
      rate: 1200,
      amount: 9600,
      sort_order: 0
    }
  ]
});

const { invoices, pagination } = await listInvoices(1, 10, {
  search: "Avasara",
  start_date: "2025-01-01"
});
```

---

## Query Parameters for List Endpoint

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `page` | int | `1` | Page number (default: 1) |
| `limit` | int | `20` | Items per page (default: 20, max: 100) |
| `sort` | string | `date` | Sort field: date, invoice_no, created_at, total_amount |
| `order` | string | `desc` | Sort order: asc or desc |
| `search` | string | `Avasara` | Search invoice number or client name |
| `school_id` | int | `1` | Filter by school ID |
| `start_date` | date | `2025-01-01` | Filter from date (YYYY-MM-DD) |
| `end_date` | date | `2025-12-31` | Filter to date (YYYY-MM-DD) |
| `template` | string | `archery` | Filter by template |

**Example:**
```
GET /api/v1/invoices?page=1&limit=10&sort=date&order=desc&school_id=1&start_date=2025-01-01
```

---

## Response Structure

### Invoice List Response
```json
{
  "invoices": [
    {
      "id": 1,
      "invoice_no": "1",
      "date": "2025-01-31",
      "total_amount": 9600,
      ...
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

### Single Invoice Response
```json
{
  "id": 1,
  "invoice_no": "1",
  "template": "archery",
  "frequency": "monthly",
  "date": "2025-01-31",
  "billed_from": {
    "name": "BAFL Foundation",
    "address": "..."
  },
  "billed_to": {
    "name": "Avasara Academy",
    "address": "..."
  },
  "period": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "payment_details": {
    "bank_name": "...",
    "account_number": "...",
    ...
  },
  "signatory": {
    "name": "...",
    "title": "..."
  },
  "items": [
    {
      "id": 1,
      "description": "...",
      "sessions": 8,
      "rate": 1200,
      "amount": 9600,
      "sort_order": 0
    }
  ],
  "total_amount": 9600,
  "created_at": "2025-01-31T10:00:00Z",
  ...
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success (GET, PUT) |
| `201` | Created (POST) |
| `204` | No Content (DELETE) |
| `400` | Bad Request (validation error) |
| `401` | Unauthorized (not authenticated) |
| `403` | Forbidden (not admin) |
| `404` | Not Found |
| `500` | Internal Server Error |

---

## Setup Steps

1. **Create tables:**
   ```bash
   python scripts/create_invoice_tables.py
   ```

2. **Restart server:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Check Swagger docs:**
   ```
   http://localhost:8000/docs
   ```

---

## Need Help?

- Full docs: `docs/INVOICE_API.md`
- Implementation summary: `docs/INVOICE_IMPLEMENTATION_SUMMARY.md`
- Swagger UI: `http://localhost:8000/docs`
