# MockLMS

MockLMS is an independent enterprise-grade mock Loan Management System (LMS) built for demonstration and integration testing with EDDP connectors.

## Sprint 1 Scope

- Django project bootstrap
- Modular app structure
- Django REST Framework configuration
- drf-spectacular Swagger setup
- Health endpoint

## Sprint 2 Scope

- Branch management CRUD API
- Customer onboarding CRUD API
- Loan application CRUD API
- Loan account CRUD API
- Relational model wiring across branch -> customer -> application -> loan

## Tech Stack

- Python 3.13
- Django 5
- Django REST Framework
- SQLite
- drf-spectacular
- django-filter

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Apply migrations:

   ```bash
   python manage.py migrate
   ```

4. Start the server:

   ```bash
   python manage.py runserver 8001
   ```

## API Endpoints (Sprint 1)

- `GET /api/health`
- `GET /api/schema/`
- `GET /api/docs/`

## API Endpoints (Sprint 2)

- `GET/POST /api/branches/`
- `GET/PUT/PATCH/DELETE /api/branches/{id}/`
- `GET/POST /api/customers/`
- `GET/PUT/PATCH/DELETE /api/customers/{id}/`
- `GET/POST /api/applications/`
- `GET/PUT/PATCH/DELETE /api/applications/{id}/`
- `GET/POST /api/loans/`
- `GET/PUT/PATCH/DELETE /api/loans/{id}/`

## CMD Verification (Sprint 2)

Run these in Command Prompt after starting server on port `8001`.

```bat
curl -s http://127.0.0.1:8001/api/health
curl -s http://127.0.0.1:8001/api/branches/
```

Create a branch:

```bat
curl -X POST http://127.0.0.1:8001/api/branches/ ^
   -H "Content-Type: application/json" ^
   -d "{\"branch_code\":\"BR-001\",\"name\":\"Prime Main\",\"city\":\"Chennai\",\"state\":\"TN\",\"is_active\":true}"
```

Create a customer (replace `branch_id` with a real branch id):

```bat
curl -X POST http://127.0.0.1:8001/api/customers/ ^
   -H "Content-Type: application/json" ^
   -d "{\"customer_number\":\"CUST-0001\",\"first_name\":\"Ravi\",\"last_name\":\"Kumar\",\"phone\":\"+919999000111\",\"email\":\"ravi.kumar@example.com\",\"branch_id\":1,\"is_active\":true}"
```

Create a loan application (branch must match customer's branch):

```bat
curl -X POST http://127.0.0.1:8001/api/applications/ ^
   -H "Content-Type: application/json" ^
   -d "{\"application_number\":\"APP-0001\",\"customer_id\":1,\"branch_id\":1,\"loan_type\":\"HOME\",\"requested_amount\":2500000,\"tenure_months\":180,\"interest_rate\":9.25,\"status\":\"SUBMITTED\"}"
```

Create a loan account:

```bat
curl -X POST http://127.0.0.1:8001/api/loans/ ^
   -H "Content-Type: application/json" ^
   -d "{\"loan_account_number\":\"LN-0001\",\"application_id\":1,\"sanctioned_amount\":2400000,\"disbursed_amount\":500000,\"outstanding_principal\":2400000,\"emi_amount\":24500,\"status\":\"ACTIVE\"}"
```
