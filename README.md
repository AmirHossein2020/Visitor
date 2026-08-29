# Field Sales Web App

A Persian, RTL, mobile-first application for field sales operations. It covers visitor authentication, products, customers, sales orders, purchases, seller profiles, snapshot-based invoices and PDF files, invoice revisions, sales returns, inventory movements, dashboards, reports, and an installable PWA shell.

## Stack

- Django 5.2, Django REST Framework, Simple JWT
- PostgreSQL and Psycopg
- React 19, Vite 7, Tailwind CSS 4
- ReportLab with bundled DejaVu fonts for Persian invoice PDFs

## Local setup

Requirements: Python 3.11+, Node.js 20+, npm, and PostgreSQL.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Set local PostgreSQL values and `DEBUG=True` in `backend/.env`, then run:

```powershell
cd backend
python manage.py migrate
python manage.py runserver
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to Django during development. The local `.env` file is ignored by Git.

## Verification

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.accounts apps.products apps.customers apps.orders apps.purchases apps.companies apps.invoices

cd ..\frontend
npm run build
```

No frontend lint/test script is currently configured.

## Production

See [DEPLOYMENT.md](DEPLOYMENT.md). Production secrets must be supplied through environment variables; never commit `backend/.env` or a frontend `.env` containing deployment-specific values.

## Important behavior

- Every business object is scoped to its authenticated owner.
- Prices, quantities, totals, and stock movements use decimal database fields.
- Issued invoices and their item snapshots are immutable; corrections create revisions.
- Inventory is derived from traceable movements, not a mutable product counter.
- The service worker caches static shell assets only. API data and writes are always network-driven; offline synchronization is intentionally not implemented.
