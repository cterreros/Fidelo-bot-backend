# 📡 API Documentation - FideloBot

---

## Overview

FideloBot provides a RESTful API for managing loyalty programs, customers, purchases, and points. This document describes all available endpoints, request/response formats, and usage examples.

**Base URL:** `http://127.0.0.1:8080/api/` (Development)

---

## Authentication

Currently, the API uses Django's built-in session authentication for web forms and direct database access for the Telegram bot. Future versions will implement token-based authentication.

---

## API Endpoints

### 1. Businesses

#### **GET /api/businesses/**
Retrieve list of active businesses.

**Parameters:**
- `is_active` (optional): Filter by active status (default: true)

**Response:**
```json
[
  {
    "business_id": "uuid",
    "name": "Good Taste Coffee Shop",
    "email": "coffee@example.com",
    "timezone": "America/Mexico_City",
    "points_per_currency": "0.100",
    "birthday_bonus_points": 100,
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

#### **GET /api/businesses/{business_id}/**
Retrieve specific business details.

**Response:**
```json
{
  "business_id": "uuid",
  "name": "Good Taste Coffee Shop",
  "email": "coffee@example.com",
  "timezone": "America/Mexico_City",
  "points_per_currency": "0.100",
  "birthday_bonus_points": 100,
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

---

### 2. Clients

#### **GET /api/clients/**
Retrieve clients with optional filtering.

**Parameters:**
- `business_id` (optional): Filter by business UUID
- `phone` (optional): Filter by phone number
- `email` (optional): Filter by email address

**Example:** `GET /api/clients/?business_id=uuid&phone=+529511577551`

**Response:**
```json
[
  {
    "client_id": "uuid",
    "business": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+529511577551",
    "birthday": "1990-05-15",
    "joined_at": "2023-01-01",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

#### **POST /api/clients/**
Create a new client.

**Request:**
```json
{
  "business": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+529511577551",
  "birthday": "1990-05-15"
}
```

**Response:**
```json
{
  "client_id": "uuid",
  "business": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+529511577551",
  "birthday": "1990-05-15",
  "joined_at": "2023-01-01",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### **GET /api/clients/{client_id}/points_balance/**
Get client's current points balance.

**Response:**
```json
{
  "points_balance": 150
}
```

#### **POST /api/clients/{client_id}/award_birthday_bonus/**
Award birthday bonus to client.

**Response:**
```json
{
  "message": "Birthday bonus awarded",
  "bonus_points": 50,
  "new_balance": 200
}
```

---

### 3. Purchases

#### **GET /api/purchases/**
Retrieve purchases with optional filtering.

**Parameters:**
- `business_id` (optional): Filter by business UUID
- `client_id` (optional): Filter by client UUID

**Response:**
```json
[
  {
    "purchase_id": "uuid",
    "business": "uuid",
    "client": "uuid",
    "amount": "100.00",
    "currency": "MXN",
    "purchased_at": "2023-01-01T12:00:00Z",
    "created_at": "2023-01-01T12:00:00Z"
  }
]
```

#### **POST /api/purchases/**
Create a new purchase (simple version).

**Request:**
```json
{
  "business": "uuid",
  "client": "uuid",
  "amount": "100.00",
  "currency": "MXN"
}
```

**Response:**
```json
{
  "purchase_id": "uuid",
  "business": "uuid",
  "client": "uuid",
  "amount": "100.00",
  "currency": "MXN",
  "purchased_at": "2023-01-01T12:00:00Z",
  "created_at": "2023-01-01T12:00:00Z"
}
```

---

### 4. Advanced Purchase Creation

#### **POST /api/purchase-with-client-data/**
Create purchase with automatic client management (main endpoint for web form).

**Request:**
```json
{
  "business_id": "uuid",
  "amount": "100.00",
  "currency": "MXN",
  "client_name": "John Doe",
  "client_email": "john@example.com",
  "client_phone": "+529511577551",
  "client_birthday": "1990-05-15",
  "send_telegram_notification": true,
  "send_sms_notification": false
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Purchase created successfully",
  "purchase_id": "uuid",
  "client_id": "uuid",
  "created_new_client": false,
  "points_earned": 10,
  "client_points_balance": 160,
  "telegram_notification_sent": true,
  "sms_notification_sent": false
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Error creating purchase: Business not found"
}
```

**Response (Validation Error):**
```json
{
  "success": false,
  "errors": {
    "client_phone": ["This field is required."],
    "amount": ["Ensure this value is greater than 0."]
  }
}
```

---

### 5. Point Events

#### **GET /api/point-events/**
Retrieve point events (transaction history).

**Parameters:**
- `business_id` (optional): Filter by business UUID
- `client_id` (optional): Filter by client UUID
- `source` (optional): Filter by source (purchase, birthday, adjustment)

**Response:**
```json
[
  {
    "event_id": "uuid",
    "business": "uuid",
    "client": "uuid",
    "source": "purchase",
    "points": 10,
    "related_purchase": "uuid",
    "note": "",
    "occurred_at": "2023-01-01T12:00:00Z",
    "created_at": "2023-01-01T12:00:00Z"
  },
  {
    "event_id": "uuid",
    "business": "uuid",
    "client": "uuid",
    "source": "birthday",
    "points": 50,
    "related_purchase": null,
    "note": "Birthday bonus",
    "occurred_at": "2023-05-15T09:00:00Z",
    "created_at": "2023-05-15T09:00:00Z"
  }
]
```

---

### 6. Loyalty Accounts

#### **GET /api/loyalty-accounts/**
Retrieve loyalty account information.

**Parameters:**
- `business_id` (optional): Filter by business UUID

**Response:**
```json
[
  {
    "account_id": "uuid",
    "business": "uuid",
    "client": "uuid",
    "points_balance": 160,
    "updated_at": "2023-01-01T12:05:00Z"
  }
]
```

---

## Web Template Endpoints

### 1. Purchase Form

#### **GET /purchase-form/**
Display the purchase registration form for businesses.

**Response:** HTML page with business authentication and purchase form.

#### **POST /purchase-form/**
Handle business authentication (login/logout).

**Login Request:**
```json
{
  "action": "login",
  "business_id": "uuid"
}
```

**Login Response:**
```json
{
  "success": true,
  "business_name": "Good Taste Coffee Shop",
  "business_id": "uuid"
}
```

**Logout Request:**
```json
{
  "action": "logout"
}
```

**Logout Response:**
```json
{
  "success": true
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "success": false,
  "error": "Error message description",
  "errors": {
    "field_name": ["Field-specific error messages"]
  }
}
```

### Common Error Scenarios

#### **Client Creation Errors**
```json
{
  "success": false,
  "errors": {
    "phone": ["Client with this phone already exists for this business."],
    "email": ["Enter a valid email address."]
  }
}
```

#### **Business Not Found**
```json
{
  "success": false,
  "error": "Business not found or inactive"
}
```

#### **Invalid Amount**
```json
{
  "success": false,
  "errors": {
    "amount": ["Ensure this value is greater than 0."]
  }
}
```

---

## Usage Examples

### Example 1: Register a Purchase for Existing Customer

```bash
curl -X POST http://127.0.0.1:8080/api/purchase-with-client-data/ \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "your-business-uuid",
    "amount": "50.00",
    "currency": "MXN",
    "client_name": "John Doe",
    "client_email": "john@example.com",
    "client_phone": "+529511577551",
    "send_telegram_notification": true
  }'
```

### Example 2: Check Customer Points

```bash
curl "http://127.0.0.1:8080/api/clients/?business_id=your-business-uuid&phone=+529511577551"
```

### Example 3: View Purchase History

```bash
curl "http://127.0.0.1:8080/api/point-events/?client_id=your-client-uuid"
```

---

## Rate Limiting

Currently not implemented. Future versions will include:
- 100 requests per minute for web interface
- 50 requests per minute for bot operations
- Higher limits for authenticated business accounts

---

## Versioning

Current API version: **v1**

Future versions will be accessible via URL path:
- `/api/v1/` - Current version
- `/api/v2/` - Future version

---

## SDK and Libraries

### Python Example

```python
import requests

class FideloBotAPI:
    def __init__(self, base_url="http://127.0.0.1:8080/api/"):
        self.base_url = base_url

    def create_purchase(self, business_id, amount, client_data):
        data = {
            "business_id": business_id,
            "amount": str(amount),
            "currency": "MXN",
            **client_data
        }
        response = requests.post(
            f"{self.base_url}purchase-with-client-data/",
            json=data
        )
        return response.json()

    def get_client_points(self, business_id, phone):
        params = {"business_id": business_id, "phone": phone}
        response = requests.get(f"{self.base_url}clients/", params=params)
        return response.json()

# Usage
api = FideloBotAPI()
result = api.create_purchase(
    business_id="your-uuid",
    amount=100.00,
    client_data={
        "client_name": "John Doe",
        "client_phone": "+529511577551",
        "client_email": "john@example.com"
    }
)
```

### JavaScript Example

```javascript
class FideloBotAPI {
    constructor(baseURL = 'http://127.0.0.1:8080/api/') {
        this.baseURL = baseURL;
    }

    async createPurchase(businessId, amount, clientData) {
        const data = {
            business_id: businessId,
            amount: amount.toString(),
            currency: 'MXN',
            ...clientData
        };

        const response = await fetch(`${this.baseURL}purchase-with-client-data/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        return await response.json();
    }

    async getClientPoints(businessId, phone) {
        const params = new URLSearchParams({
            business_id: businessId,
            phone: phone
        });

        const response = await fetch(`${this.baseURL}clients/?${params}`);
        return await response.json();
    }
}

// Usage
const api = new FideloBotAPI();
const result = await api.createPurchase('your-uuid', 100.00, {
    client_name: 'John Doe',
    client_phone: '+529511577551',
    client_email: 'john@example.com'
});
```

---

## Webhook Support (Future)

Planned webhook events for external integrations:

- `purchase.created` - New purchase registered
- `client.registered` - New client created
- `points.awarded` - Points added to account
- `birthday.bonus` - Birthday bonus awarded

---

This API documentation reflects the current MVP implementation and will be updated as new features are added.