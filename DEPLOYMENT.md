# Deployment

This project expects PostgreSQL, a Django application process, and the statically built Vite frontend. A reverse proxy should serve the frontend and route `/api/` to Django on the same HTTPS origin.

## 1. Install

Install Python requirements and frontend dependencies using supported Python and Node.js releases:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm ci && npm run build && cd ..
```

The production frontend is written to `frontend/dist/`.

## 2. PostgreSQL

Create a dedicated database and role with access only to that database. Supply connection values through environment variables. Do not use the PostgreSQL superuser for the application.

## 3. Environment

Start from `backend/.env.example`. Required production values include:

- `DJANGO_SECRET_KEY`: long random value; Django refuses to start without it when `DEBUG=False`
- `DEBUG=False`
- `ALLOWED_HOSTS`: comma-separated public hostnames
- `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`
- `CSRF_TRUSTED_ORIGINS`: comma-separated HTTPS origins
- HTTPS cookie/security settings shown in the example
- `USE_X_FORWARDED_PROTO=True` only when a trusted reverse proxy sets `X-Forwarded-Proto`

Set `VITE_API_BASE_URL` in the frontend build environment before `npm run build` when the reverse proxy exposes Django under a path other than `/api`. Same-origin deployment is required by the current configuration; cross-origin CORS support is intentionally not included.

Set a nonzero `SECURE_HSTS_SECONDS` only after HTTPS is confirmed for the domain and subdomains. Increase it gradually before enabling preload.

## 4. Database and static files

```bash
cd backend
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Serve `backend/staticfiles/` through the reverse proxy or platform static-file service. Keep `backend/media/` private: receipts, support attachments, seller stamps and signatures must only be delivered by their authenticated API endpoints. For scale-out deployments, use private object storage or a shared encrypted volume without changing authorization checks.

## 5. Processes

Example Django process on Linux:

```bash
cd backend
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

Serve `frontend/dist/` as an SPA: unknown non-API routes must fall back to `index.html`. Serve `/sw.js` from the origin root without a path rewrite so its scope remains `/`.

## 6. HTTPS and PWA

HTTPS is required for service workers and installation outside localhost. The service worker must never be changed to cache `/api/` responses. Verify the manifest, 192px/512px icons, and `/sw.js` after deployment.

## 7. Backups

Schedule encrypted PostgreSQL backups and periodically test restoration. A basic logical backup is:

```bash
pg_dump --format=custom --file=field_sales.dump field_sales
```

Keep backups outside the application host and protect them with the same care as production credentials.

Back up private media together with PostgreSQL so database references and files represent the same recovery point. Retain at least 7 daily, 4 weekly and 6 monthly encrypted copies, and test an isolated restore quarterly.

## 8. Subscription bootstrap

Migration `subscriptions.0002_seed_plans` creates editable development plans: a 30-day monthly plan at 990,000 Rial and a 365-day yearly plan at 9,900,000 Rial. Review and update these values in Django admin before production launch; the frontend always reads current active plans from the API.

Existing users are not silently granted an unlimited production subscription. For a finite local-development activation, run:

```bash
cd backend
python manage.py activate_subscription user@example.com --plan monthly-development
```

Superusers bypass customer subscription checks for platform administration. Customer business APIs require an effective active subscription; authentication and subscription renewal endpoints remain available after expiration.

## 9. Manual subscription payments

Configure the public transfer destination through the `MANUAL_PAYMENT_*` environment variables shown in `.env.example`; never commit real bank details. A customer creates a subscription order, submits a tracking code or receipt image, and waits for a platform administrator to approve the payment. Approval reuses the transactional subscription-order activation path.

Receipt uploads accept validated JPG, PNG, or WebP content up to `MAX_RECEIPT_UPLOAD_BYTES` (5 MB by default). Files are stored below `MEDIA_ROOT/subscription-receipts/` with generated names and are delivered through authenticated API endpoints only. Do not expose `MEDIA_ROOT` as a public directory in production. Use private object storage or protected reverse-proxy delivery, retain encrypted backups, and apply an appropriate financial-record retention policy.
