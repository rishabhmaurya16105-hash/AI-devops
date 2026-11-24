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
- Local access was verified at `http://127.0.0.1:8080` using a temporary port-forward, which has been stopped. The ClusterIP Service has no Ingress or NodePort.
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
