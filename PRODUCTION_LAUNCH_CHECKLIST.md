# Production Launch Checklist

## 1. Server
- [ ] Supported Python/Node installed; dedicated unprivileged application user created.
## 2. Domain/DNS
- [ ] Final domain points to the production proxy; no domain is hardcoded in source.
## 3. HTTPS
- [ ] Valid certificate, renewal and HTTP→HTTPS redirect verified.
## 4. Environment
- [ ] Copy `.env.example`; set a unique secret and all required production values outside Git.
## 5. PostgreSQL
- [ ] Dedicated least-privilege role, connection test and capacity monitoring configured.
## 6. Migrations
- [ ] Take backup, run `python manage.py migrate`, then verify `showmigrations`.
## 7. Static files
- [ ] Run `collectstatic`; serve Django static and `frontend/dist` through the proxy/CDN.
## 8. Private media
- [ ] Do not expose `MEDIA_ROOT`; protect receipts, support files, stamps and signatures and back them up encrypted.
## 9. Gunicorn/application server
- [ ] Run Gunicorn under a process supervisor with restart, timeout and worker limits.
## 10. reverse proxy
- [ ] Serve SPA/static pages; proxy `/api/`, `/health/` and set trusted `X-Forwarded-Proto` only at the proxy.
## 11. firewall
- [ ] Expose only SSH (restricted), HTTP and HTTPS; PostgreSQL and Gunicorn remain private.
## 12. backups
- [ ] Daily encrypted PostgreSQL and private-media backups; 7 daily, 4 weekly and 6 monthly copies; quarterly restore test; pre-deployment snapshot.
- Restore drill: provision an isolated database, run `pg_restore --clean --if-exists --no-owner`, restore media to a private path, then run checks and smoke tests.
## 13. Search Console
- [ ] Add domain property, place the real verification mechanism at the DNS/provider or future environment-driven meta integration, and inspect index/security reports.
## 14. sitemap
- [ ] Verify `https://DOMAIN/sitemap.xml`, submit it and confirm only public canonical URLs appear.
## 15. robots
- [ ] Verify public pages are allowed and account, support, admin and API paths are excluded.
## 16. canonical domain
- [ ] Set `VITE_SITE_URL` and `PUBLIC_SITE_URL` to the exact HTTPS origin; verify every public canonical.
## 17. monitoring
- [ ] Monitor `/health/`, HTTP 5xx, latency, disk, database connections and certificate expiry without logging secrets.
## 18. first admin
- [ ] Create the first superuser securely, enable MFA at infrastructure/identity layer when available, and keep an emergency procedure.
## 19. payment configuration
- [ ] Enter verified bank details privately; perform a small end-to-end payment approval test.
## 20. post-deploy smoke test
- [ ] Landing, pricing, registration/login, trial, business workflow, invoice PDF, payment, support and platform admin tested on mobile and desktop.
