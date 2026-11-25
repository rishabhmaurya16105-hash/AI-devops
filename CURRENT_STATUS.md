# Current Status

## Phase 3: Kubernetes

- PostgreSQL StatefulSet `postgres` is deployed with one replica.
- PVC `postgres-data` is Bound.
- Headless and client-facing PostgreSQL Services are configured.
- The StatefulSet references `postgres-secret` securely through the `POSTGRES_PASSWORD` key.
- The PostgreSQL pod is Running and Ready, and `pg_isready` succeeds.
- Alembic migrations completed through Kubernetes Job `alembic-migrations`; current revision is `0002_orders`.
- The `products`, `orders`, `order_items`, and `alembic_version` tables are present.
- Six sample products were seeded through Kubernetes Job `products-seed`; all expected slugs are present with no duplicates.
- Backend Deployment and ClusterIP Service are configured; the backend pod is Ready.
- Backend `/health/db` confirms PostgreSQL connectivity, and `/api/v1/products` returns all six seeded products.
- Frontend Deployment and ClusterIP Service use image `devopsmart-db-frontend:k8s` on port 8080.
- Frontend readiness and liveness probes use `/healthz`; rollout completed with one Ready pod and a ready Service endpoint on port 8080.
- Frontend `/` and `/healthz` returned HTTP 200; `/api/v1/products` through the Nginx proxy returned all six seeded products.
- Local access to the frontend was verified using temporary loopback-only port-forwarding; the forward was stopped after testing. The application Services remain ClusterIP.
- F5 NGINX Ingress Controller v5.8.1 is installed in `nginx-ingress`; its Deployment is 1/1 Ready and its Service has a ready endpoint.
- Ingress `devopsmart` uses class `nginx` and host `devopsmart.local`. `/api` routes to `backend:8000` without a rewrite, and `/` routes to `frontend:8080`. PostgreSQL has no Ingress route and remains an internal ClusterIP Service.
- Through the loopback-only Ingress port-forward on `127.0.0.1:8080`, `/` returned HTTP 200 and `/api/v1/products` returned HTTP 200 with all six products. Backend `/health` and `/health/db` both returned healthy over a separate loopback-only backend port-forward. Both forwards were stopped after verification.
- No NodePort, Windows hosts-file change, or TLS configuration was used; local hostname routing was verified with the `devopsmart.local` Host header.
- Browser-based end-to-end testing used temporary product ID `7` (`e2e-temporary-test-product`), inserted temporarily with approval because the application has no supported product-creation API or UI. The cart showed quantity 1 and total `$1.00`; one order succeeded with database ID `1` and order number `ORD-5E4E16C989B3440EAD3E7031DC80EC62`. Its single item referenced product `7`, quantity 1, unit price/subtotal `$1.00`; the temporary product stock changed from 1 to 0.
- Cleanup removed only the inspected test order item, order, and temporary product by exact IDs. Final database counts are 6 products, 0 orders, and 0 order items; all six seeded product stock quantities match the recorded baseline.
- After cleanup, frontend `/` and `/healthz` returned HTTP 200, and the frontend Nginx proxy returned HTTP 200 with all six products. Backend `/health` and `/health/db` are healthy, and PostgreSQL accepts connections.
- Pod self-recovery tests completed by deleting only the verified application pods. Frontend `frontend-7c57868c6b-ffk8z` was automatically replaced by `frontend-7c57868c6b-vhjb9` in about 17.6 seconds; backend `backend-bcd7f87c9-pzq77` was automatically replaced by `backend-bcd7f87c9-m656s` in about 34.5 seconds. Both Deployments remained 1/1 Ready with 0 container restarts.
- StatefulSet pod `postgres-0` was gracefully deleted and automatically recreated with a new pod UID in about 9.1 seconds; it returned Ready with 0 container restarts. StatefulSet `postgres` remained 1/1 Ready.
- PVC `postgres-data` and PV `pvc-8d07a4a4-850a-4cff-9bc7-cde0db60200a` remained Bound before and after PostgreSQL pod recreation. The recreated pod mounted the same claim at `/var/lib/postgresql/data`.
- Read-only persistence checks after recovery confirmed the baseline product count, all six slugs and stock quantities, and unchanged counts of 0 orders and 0 order items. Backend `/health`, `/health/db`, and the six-product API response remained healthy; the frontend proxy returned HTTP 200 with all six products.
- Recovery timings measure pod deletion through readiness; zero downtime was not measured. `kubectl get endpoints` emitted a Kubernetes deprecation notice for the legacy Endpoints API; ready Service endpoints were present.
- Sample product cards currently show image placeholders because the seeded products do not have image URLs.

PostgreSQL and backend pods recorded transient startup probe warnings while initializing. They are currently Ready; backend and frontend have zero restarts, and the frontend had no warning events. Backend logs contained no credential-like values, and frontend logs had no errors or credential-like values.

## Phase 4: CI/CD

- Step 2A (frontend and backend linting setup) is complete.
- Frontend linting uses ESLint 10.15.0 with JavaScript/JSX, React Hooks, and Vite Fast Refresh rules. `npm run lint` passes.
- Backend linting uses Ruff 0.17.6 targeting Python 3.14. From `backend`, `.\.venv\Scripts\python.exe -m ruff check .` passes.
- Frontend dependency lockfile was updated for the lint tools. Ruff is pinned in `backend/requirements-dev.txt`; the production `requirements.lock` remains unchanged.
- Existing validation passed: frontend tests (8), backend tests (23), and the frontend production build. Backend tests emitted one Starlette `TestClient` deprecation warning.
- Backend edits were limited to lint findings: import ordering, a type-check-only model import, an unused exception binding, and an intentional Alembic model-registration import suppression. No API or application behavior changes were made.
- Step 2B (GitHub Actions CI workflow) is complete and locally validated in `.github/workflows/ci.yml`. Pull requests targeting `main` and pushes to `main` run independent frontend and backend jobs.
- The frontend job uses Node.js 24, `npm ci` with lockfile-based npm caching, then runs `npm run lint`, `npm test`, and `npm run build`.
- The backend job uses Python 3.14, installs pinned runtime dependencies from `requirements.lock` followed by development/test tools from `requirements-dev.txt`, then runs Ruff and pytest. The tests use in-memory SQLite and dependency overrides; no PostgreSQL service is required.
- Workflow validation passed with actionlint. Local verification passed: frontend `npm ci`, lint, 8 tests, and production build; backend dependency-install dry-runs, Ruff, and 23 tests. Backend pytest retains one Starlette `TestClient` deprecation warning.
- CI has read-only `contents: read` permissions, no secrets or deployment steps, checkout credentials are not persisted, both jobs have 15-minute timeouts, and concurrency cancels superseded runs. A hosted GitHub Actions run has not been observed.
- Existing backend development requirements leave `httpx` and `pytest` unpinned; runtime dependencies remain pinned by `requirements.lock`. Local kind deployment remains outside hosted-runner workflows.
- The next pending Phase 4 task is image build and tagging. No Docker, Kubernetes, application, or README files were changed.
