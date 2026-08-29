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

Serve `backend/staticfiles/` through the reverse proxy or platform static-file service. The application currently has no user-uploaded media or invoice-logo storage.

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
