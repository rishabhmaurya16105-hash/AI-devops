# DevOpsMart Tasks

## Phase 3: Kubernetes

- [x] Deploy PostgreSQL Kubernetes infrastructure: ConfigMap, 1Gi PVC, Services, and StatefulSet.
- [x] Verify the PVC is Bound, the PostgreSQL pod is Ready, and `pg_isready` succeeds.
- [x] Run Alembic migrations in Kubernetes through a temporary Job; verify revision `0002_orders` and application tables.
- [x] Seed six sample products in Kubernetes PostgreSQL and verify their slugs with no duplicates.
- [x] Deploy the backend to Kubernetes and verify readiness, PostgreSQL connectivity, and product listing.
- [x] Deploy the frontend to Kubernetes and verify the storefront and proxied product API.
- [x] Complete a controlled browser end-to-end order test with a temporary product; verify persistence and remove only test records without changing seeded product stock.
- [x] Verify frontend, backend, and PostgreSQL pod self-recovery and confirm database persistence on the existing PVC.
- [x] Install F5 NGINX Ingress Controller v5.8.1 and verify local `/` frontend and unchanged `/api` backend routing, database health, and loopback-only access; keep PostgreSQL internal.
