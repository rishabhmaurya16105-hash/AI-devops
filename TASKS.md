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

## Phase 4: CI/CD

- [x] Step 2A: Configure frontend ESLint and backend Ruff linting; both lint commands pass.
- [x] Step 2B: Add and validate independent GitHub Actions frontend/backend CI jobs for lint, tests, and frontend build. The owner verified both GitHub jobs are green.
- [x] Step 3: Build and verify frontend/backend Docker images in CI using full Git SHA tags, digest-pinned base images, and no registry publishing. Local image builds and smoke checks passed.
- [~] Add security and configuration validation; local checks pass, pending hosted CI verification of image scans.
- [ ] Design a safe deployment workflow for the local kind cluster.
- [ ] Verify deployment and rollback behavior.
