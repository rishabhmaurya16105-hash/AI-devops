# DevOpsMart

DevOpsMart is a local-first, three-tier e-commerce portfolio project.
The project is being implemented incrementally. Its FastAPI product and
order APIs use PostgreSQL, and the React storefront displays products
and submits orders. Orders are currently unauthenticated; payment
processing is not implemented.

## Current implementation

- FastAPI backend with environment-based application settings.
- `GET /health` returns `{"status":"healthy"}`.
- `GET /health/db` checks database connectivity and returns a generic
  unhealthy response without exposing connection details.
- SQLAlchemy engine, declarative base, and reusable request-scoped
  database sessions.
- Central JSON logging with request IDs, HTTP method/path/status,
  processing duration, and redacted exception details.
- Automated backend health, product API, order, database rollback,
  error-handling, seed, and CORS tests; frontend React component tests.
- SQLAlchemy Product model with decimal-safe prices, stock constraints,
  optional image URL, category, stable seed slug, and sample marker.
- Alembic migration for the products table.
- `GET /api/v1/products` with Pydantic response validation and
  sanitized database error handling.
- Idempotent local sample-product seeding.
- SQLAlchemy Order and OrderItem models with decimal-safe price
  snapshots, foreign keys, and transactional inventory updates.
- `POST /api/v1/orders`, which validates product IDs and quantities,
  calculates prices on the backend, checks stock, persists the order,
  and decrements inventory atomically.
- Responsive React/Vite storefront that fetches products from the API,
  with loading, retryable error, empty, search, and category-filter
  states.
- Editable browser cart with estimated totals and a Place Order action;
  server-confirmed order number and total are shown on success.
- No sign-in or payment details are collected. Orders are not associated
  with a user account.
- CORS allows only the configured local Vite origin
  (`http://127.0.0.1:5173`).

## Backend setup

From the `backend` directory in PowerShell, create a virtual environment
and install the runtime and test dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Start the local development server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Open
`http://127.0.0.1:8000/health` to verify the health endpoint. Expected
response:

```json
{"status":"healthy"}
```

Run the backend tests from the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Backend Docker image

From the project root, build the production backend image:

```powershell
docker build --pull=false --tag devopsmart-backend:0.1.0 .\backend
```

Run it locally and check the API health endpoint:

```powershell
docker run --detach --rm --name devopsmart-backend `
    --publish 127.0.0.1:18000:8000 `
    devopsmart-backend:0.1.0
Invoke-RestMethod http://127.0.0.1:18000/health
docker logs devopsmart-backend
docker stop devopsmart-backend
```

The image listens on port `8000` as an unprivileged user. Its container
health check calls `/health`; this does not require PostgreSQL. Database
settings are supplied at runtime through `POSTGRES_HOST`,
`POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and
`POSTGRES_PASSWORD`, or through `DEVOPSMART_DATABASE_URL`. When the
backend and database share a Docker network, set `POSTGRES_HOST` to the
database service name (for example, `postgres`). Do not bake credentials
into the image. Alembic migrations are not run on startup; apply them
after the database is reachable and before using database-backed
endpoints. Without a reachable database, `/health/db` returns HTTP 503
with `{"status":"unhealthy"}`.

The backend loads PostgreSQL settings from the ignored
`database/.env` file. Start PostgreSQL first using the commands in
[Local PostgreSQL](#local-postgresql), then start FastAPI from the
`backend` directory. The settings file is resolved relative to the
project path, so it works regardless of the terminal's current
directory. Process environment variables override values from the file.

The backend uses `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`,
`POSTGRES_USER`, and `POSTGRES_PASSWORD` to build its SQLAlchemy
connection URL. Optionally, set `DEVOPSMART_DATABASE_URL` to provide a
complete `postgresql+psycopg` URL instead. Never commit that URL if it
contains credentials.

## Environment files and secrets

Create local environment files from the examples only when they do not
already exist. The commands below preserve existing local settings.
From the repository root in PowerShell:

```powershell
if (-not (Test-Path database/.env)) {
    Copy-Item database/.env.example database/.env
}
if (-not (Test-Path frontend/.env)) {
    Copy-Item frontend/.env.example frontend/.env
}
```

Set a private local value for `POSTGRES_PASSWORD` in `database/.env`.
The backend reads this same file for database settings and optional
`DEVOPSMART_APP_NAME`, `DEVOPSMART_ENVIRONMENT`,
`DEVOPSMART_DEBUG`, and `DEVOPSMART_DATABASE_URL` settings. The
`DEVOPSMART_DATABASE_URL` override uses the format
`postgresql+psycopg://<user>:<password>@<host>:<port>/<database>`;
when it is unset, the URL is assembled from the individual
`POSTGRES_*` variables. Application settings have safe defaults in
`backend/app/core/config.py`.

The frontend reads only `VITE_API_BASE_URL` from `frontend/.env`.
Values prefixed with `VITE_` are included in browser code and must
never contain passwords, API keys, or other secrets. The future AI
Incident Assistant is not implemented yet, so no unused AI API-key
variable is included in current environment examples.

The root `.gitignore` ignores `.env` and local environment variants
while explicitly allowing `.env.example` templates. It also excludes
Python/Node dependencies and caches, build/coverage output, local IDE
and operating-system files, logs/database artifacts, and Terraform
state and local variable files. Keep real credentials only in ignored
local files or environment variables; never commit them.

### Docker image and runtime secrets

Compose supplies database credentials at runtime from the ignored
`database/.env`; they are not Docker build arguments. The frontend image
does not receive secret build variables. Vite embeds `VITE_` variables
into browser assets, so use them only for public configuration.

Anyone with access to the Docker daemon can inspect container
environment variables, including runtime database credentials. A local
`.env` file is not a secrets manager. For shared or production
deployments, use Docker secrets or another protected secret mechanism
and configure the application to read mounted secret files where
supported.

The 2026-11-18 image audit checked both application image configurations,
build histories, all image layers, and frontend production assets. It
found no included `.env` files, matches for the local secret values,
high-confidence private-key/token patterns, or sensitive `VITE_`
variable names. This is a point-in-time check, not a substitute for
keeping credentials out of build contexts and source code.

Verify the API and database separately:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/db
```

Both return `{"status":"healthy"}` when the API and database are
available. The database health endpoint returns HTTP 503 with
`{"status":"unhealthy"}` if its query fails; internal connection
details are not returned.

## Application logging

The backend configures Python's standard-library logging once when the
FastAPI application is loaded. Log records are emitted as JSON to
stderr with a UTC timestamp, level, service name, message, and request
ID. Uvicorn logs use the same formatter; SQLAlchemy engine query
logging stays at WARNING to avoid logging SQL values.

HTTP middleware accepts a bounded, validated `X-Request-ID` or
generates a UUID, places it in request context, and returns it in the
response header. Start/completion records include method, path, status,
and duration in milliseconds. Query strings and request bodies are not
logged. Unexpected exceptions are logged with redacted exception
details and frame locations; clients receive only a generic HTTP 500
response. Known secret patterns, bearer tokens, and database URL
credentials are redacted from emitted log text.

To see the JSON logs, run the backend server in a terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Each request's response includes `X-Request-ID`, which can be used to
correlate its start, completion, and error records.

## Frontend setup

From the `frontend` directory in PowerShell, install the npm
dependencies:

```powershell
npm install
```

Start the Vite development server:

```powershell
npm run dev
```

Open `http://127.0.0.1:5173` in a browser. Create a production build
with:

```powershell
npm run build
```

The storefront reads its catalog from FastAPI. Cart contents stay in
browser memory until the user places an order; the server validates and
persists that order.

## Frontend Docker image

The frontend has a multi-stage `frontend/Dockerfile`:

- **Build stage:** `node:24-alpine` runs `npm ci` against
  `package-lock.json`, then `npm run build`.
- **Runtime stage:** `nginxinc/nginx-unprivileged:1.29-alpine` serves
  `dist/` as the non-root `nginx` user (UID 101) on port **8080**.

`frontend/nginx.conf` provides:

- SPA fallback: unknown paths return `index.html`.
- Long-term caching for hashed `/assets/*` files; `index.html` is sent
  with `Cache-Control: no-cache`.
- gzip and basic security headers.
- A `/healthz` endpoint used by the image `HEALTHCHECK`.
- A same-origin `/api/` reverse proxy to `backend:8000`.

`VITE_API_BASE_URL` is deliberately not set in the image, so the
browser calls its own origin and Nginx forwards `/api/` to the backend.
`.env` files and tests are excluded by `frontend/.dockerignore`; no
secrets or localhost URLs are baked into the bundle.

Build and run from the `frontend` directory in PowerShell:

```powershell
docker build -t devopsmart-frontend:0.1.0 .
docker run -d --name devopsmart-frontend -p 8080:8080 devopsmart-frontend:0.1.0
```

Open `http://127.0.0.1:8080`. Check health and logs, then clean up:

```powershell
curl.exe -s http://127.0.0.1:8080/healthz
docker inspect devopsmart-frontend --format "{{.State.Health.Status}}"
docker logs devopsmart-frontend
docker rm -f devopsmart-frontend
```

When run standalone, the storefront shell loads, but `/api/` requests
return **502**: the hostname `backend` only resolves on a shared Docker
network. Run the application with the Docker Compose setup below for
the complete product catalog and order flow. The Vite dev server remains
available for frontend development.

## Local PostgreSQL

The database runs separately from FastAPI in a lightweight PostgreSQL
17 Alpine container. It binds only to `127.0.0.1`, uses a persistent
named Docker volume, and has a 512 MiB memory limit. This database-only
Compose file does not build or connect the application services. The
container uses the `unless-stopped` restart policy.

Run the following commands from the repository root in PowerShell. On
first setup, create the ignored local environment file and set a private
development password in it. Do not overwrite an existing
`database/.env`; it contains the local database credentials.

```powershell
if (-not (Test-Path database/.env)) {
    Copy-Item database/.env.example database/.env
}
notepad database/.env
```

`database/.env.example` contains only placeholders. The local
`database/.env` is ignored by Git.

Start PostgreSQL:

```powershell
docker compose --env-file database/.env -f database/compose.yaml -p devopsmart-db up -d
docker compose --env-file database/.env -f database/compose.yaml -p devopsmart-db ps
```

Check that PostgreSQL accepts connections and run a test query (replace
the default database and role names if you changed them in `.env`):

```powershell
docker compose --env-file database/.env -f database/compose.yaml -p devopsmart-db exec -T postgres pg_isready -h 127.0.0.1 -p 5432
docker compose --env-file database/.env -f database/compose.yaml -p devopsmart-db exec -T postgres psql -U devopsmart -d devopsmart -c "SELECT current_database(), current_user;"
```

The default host connection settings are `127.0.0.1:5432`, database
`devopsmart`, and role `devopsmart`. The database, role, password, and
host port can be changed through `database/.env`; FastAPI reads these
settings when it creates its SQLAlchemy connection.

The named volume is `devopsmart-db_postgres_data` when the documented
Compose project name is used. It stores PostgreSQL's data independently
of the container. The PostgreSQL image uses `POSTGRES_DB`,
`POSTGRES_USER`, and `POSTGRES_PASSWORD` when initializing an empty
volume; changing those environment values does not overwrite or
reconfigure an already initialized database.

Stop and restart the database without removing its data:

```powershell
docker compose --env-file database/.env -f database/compose.yaml -p devopsmart-db stop
docker compose --env-file database/.env -f database/compose.yaml -p devopsmart-db up -d
```

Stopping a container keeps both the container and its volume. Removing
a stopped container, or running `docker compose ... down`, removes the
container (and, for `down`, its network) but keeps this named volume.
Deleting the named volume permanently deletes the database files.
Never use `docker compose ... down -v`, `docker volume rm`, or volume
pruning for this development database; no existing database volume
should be deleted.

When FastAPI runs in a container on the same Docker network, set
`POSTGRES_HOST=postgres` in that backend container's runtime environment.
`localhost` inside the backend container refers to the backend itself.
The host-development default remains `127.0.0.1`. The backend accepts
these settings through environment variables or the optional
`DEVOPSMART_DATABASE_URL`; credentials are not stored in either image.

The database health check uses `pg_isready`. Alembic migrations are not
run automatically; back up and review existing data before any planned
migration.

## Full application with Docker Compose

The root `compose.yaml` starts the frontend, backend, and PostgreSQL on
the same Compose network. It uses the existing ignored
`database/.env` for database credentials and runtime settings; do not
overwrite an existing file. If creating it for the first time, copy the
safe example and replace the placeholder password with a private local
value:

```powershell
if (-not (Test-Path database/.env)) {
    Copy-Item database/.env.example database/.env
}
notepad database/.env
```

From the repository root, validate and start the services:

```powershell
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db config --quiet
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db up -d --build --no-recreate
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db ps
```

To explicitly rebuild the frontend and backend images, then recreate only
those two application containers from the rebuilt images:

```powershell
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db build frontend backend
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db up -d --no-deps --force-recreate backend frontend
```

The second command excludes PostgreSQL and its persistent volume. Run
the application tests from their respective directories:

```powershell
Push-Location backend
.\.venv\Scripts\python.exe -m pytest -q
Pop-Location

Push-Location frontend
npm test
Pop-Location
```

Inspect the Compose image tags and Docker-reported sizes:

```powershell
docker image ls --format "table {{.Repository}}`t{{.Tag}}`t{{.Size}}"
```

The `devopsmart-db` project name reuses
`devopsmart-db_postgres_data` and the existing database container. The
`--no-recreate` option avoids replacing an existing database container;
if Compose reports a conflict or a required database change, inspect it
and obtain approval rather than removing or recreating the container.
No second database volume is needed.

### Compose network and service communication

Compose connects `frontend`, `backend`, and `postgres` to the project
bridge network `devopsmart-db_default`. Docker DNS resolves the service
names `backend` and `postgres` on this private network. The backend
connects to PostgreSQL at `postgres:5432`; the Nginx frontend proxies
same-origin `/api/` requests to `backend:8000`. Neither application
container should use `localhost` to reach a different service:
`localhost` always refers to that same container. The browser uses the
published loopback frontend URL and does not resolve Docker service
names.

Startup ordering uses `depends_on` with health conditions: PostgreSQL's
`pg_isready` check gates the backend, and the backend's `/health/db`
check gates the frontend. This is startup ordering, not a runtime
dependency supervisor. The API's database health check and SQLAlchemy
connection pool pre-ping detect database connectivity problems; no
automatic database restart, migration, or destructive recovery is
performed. If a dependency is unavailable, check Compose health and
logs, then allow the service to recover or start it again only after
the dependency is healthy. Do not stop PostgreSQL to simulate an outage
against the existing development database.

Open the storefront at `http://127.0.0.1:8080`. Nginx serves the app
and proxies same-origin `/api/` requests to `backend:8000`; Docker
service names stay inside the Docker network and are not exposed to
browser JavaScript. For local API access, the backend is also published
only on loopback at `http://127.0.0.1:8000`. PostgreSQL remains on
`127.0.0.1:5432`. The backend connects to the `postgres` service using
`POSTGRES_HOST=postgres` and the `POSTGRES_*` settings. Its optional
full URL setting is named `DEVOPSMART_DATABASE_URL`, not `DATABASE_URL`;
Compose uses the existing individual settings so credentials are
handled safely by SQLAlchemy.

PostgreSQL's `pg_isready` health check gates backend startup. The
backend's Compose health check uses `/health/db`, and frontend startup
waits for the backend to become healthy. A temporary database outage
can make database-backed requests return their existing sanitized
unhealthy responses; the backend does not migrate or reset data on
startup and can become healthy again when PostgreSQL recovers.

Check service health and the proxied API:

```powershell
Invoke-WebRequest http://127.0.0.1:8080/ -UseBasicParsing
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/db
Invoke-RestMethod http://127.0.0.1:8080/api/v1/products
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db logs --tail 100 postgres backend frontend
```

The current database is already at Alembic revision `0002_orders`, so
no migration is required. Migrations never run automatically. Only
after reviewing the migration and backing up the database, run a
necessary upgrade as a separate, deliberate operation:

```powershell
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db run --rm backend alembic upgrade head
```

Stop and resume the services without removing their containers or
database data:

```powershell
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db stop
docker compose --env-file database/.env -f compose.yaml -p devopsmart-db start
```

`docker compose ... down` removes the containers and project network
but keeps the named database volume. Removing the PostgreSQL container
is not necessary for normal shutdown. Never use `down -v`, `docker
volume rm`, or volume pruning for this development database; deleting
the named volume permanently deletes the stored data.

## Configuration

The backend reads optional application settings from environment
variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DEVOPSMART_APP_NAME` | `DevOpsMart API` | FastAPI application title |
| `DEVOPSMART_ENVIRONMENT` | `development` | Application environment name |
| `DEVOPSMART_DEBUG` | `false` | FastAPI debug mode |

Database settings are read from the ignored `database/.env` file or
matching process environment variables. `DEVOPSMART_DATABASE_URL` is an
optional full-URL override. Never commit real credentials.

The frontend reads `VITE_API_BASE_URL` from `frontend/.env`. Copy
`frontend/.env.example` to `frontend/.env` if it does not exist. Vite
exposes `VITE_` variables to browser code, so they must contain public
configuration only, never secrets. The local `.env` file is ignored by
Git.

## Product listing

The backend exposes `GET http://127.0.0.1:8000/api/v1/products`. It
returns a JSON array, including an empty array when the catalog has no
rows. Prices use SQL `NUMERIC(10, 2)` and are serialized as decimal
strings. Database failures return HTTP 503 with a generic message; the
response does not include internal database details.

Each product response includes `id`, `slug`, `name`, `description`,
`price`, `image_url`, `category`, `stock_quantity`, `is_sample`,
`created_at`, and `updated_at`.

From the `backend` directory, apply the schema migration and seed the
local catalog:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.db.seed_products
```

The seed command inserts six clearly marked sample products. It uses
stable unique slugs and skips existing rows when run again. Sample
products have no external image URLs; the UI displays an image
placeholder until a product has an `image_url`.

With PostgreSQL and FastAPI running, check the endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/products
```

The browser storefront uses the same endpoint through
`frontend/src/api/products.js`. Its search and category filters operate
on the returned API data. Product image URLs are optional.

## Order creation

The backend exposes `POST http://127.0.0.1:8000/api/v1/orders`. The
frontend sends only product IDs and quantities; the server reads current
prices and stock from PostgreSQL, calculates line subtotals and the
order total, and saves the order/items while decrementing stock in one
transaction.

Example request:

```json
{
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 2, "quantity": 1 }
  ]
}
```

The response includes the order number, `placed` status, authoritative
total, timestamps, and order items with their price snapshots. Expected
errors are HTTP 422 for invalid or empty quantities/items, 404 for an
unknown product, and 409 when stock is insufficient. Database failures
return a generic HTTP 503 response. Failed requests do not create an
order or change inventory.

Orders do not require authentication in this initial local version and
are not linked to a user. Payment processing or payment-card data is
not implemented or stored. The cart total is only an estimate; the
server response is authoritative. Duplicate product IDs in one request
are combined into one order line.

## Backend layout

```text
backend/
├── app/
│   ├── api/
│   │   ├── router.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── health_db.py
│   │       ├── products.py
│   │       └── orders.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── middleware.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── seed_products.py
│   ├── models/
│   │   ├── product.py
│   │   └── order.py
│   ├── repositories/
│   │   ├── product.py
│   │   └── order.py
│   ├── schemas/
│   │   ├── product.py
│   │   └── order.py
│   ├── services/
│   │   ├── product.py
│   │   └── order.py
│   └── main.py
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_create_products.py
│       └── 0002_create_orders.py
├── tests/
│   ├── test_health.py
│   ├── test_database_health.py
│   ├── test_products.py
│   ├── test_orders.py
│   └── test_logging.py
├── alembic.ini
├── requirements.txt
└── requirements-dev.txt
```

The API route delegates database reads through a service and repository.
Alembic loads its database URL from the existing environment-based
backend configuration.

## Frontend layout

```text
frontend/
├── .env.example
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
└── src/
    ├── api/
    │   ├── client.js
    │   ├── products.js
    │   └── orders.js
    ├── app/
    │   ├── App.jsx
    │   └── App.test.jsx
    ├── components/
    │   ├── layout/
    │   └── ui/
    ├── features/
    │   ├── cart/
    │   ├── orders/
    │   │   └── OrderConfirmation.jsx
    │   └── products/
    │       └── ProductCard.jsx
    ├── utils/
    │   └── currency.js
    ├── test/
    │   └── setup.js
    └── styles/
```

## Automated testing and verification

Run backend tests from `backend` in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The backend tests use isolated in-memory SQLite engines through FastAPI
dependency overrides. They do not connect to, delete, truncate, or
modify the local development PostgreSQL database. Coverage includes
health endpoints, product listing and empty results, sample-seed
idempotency, successful and multi-product orders, invalid/missing
products, client-supplied price tampering, stock validation,
authoritative totals, persistence, rollback, error sanitization, and
CORS.

Run frontend component tests from `frontend`:

```powershell
npm test
```

Vitest runs React Testing Library tests in jsdom. API calls are mocked,
so frontend tests do not depend on a running backend or database. They
cover the loading, product display, empty and API-error/retry states,
cart additions, quantity changes/removal, successful and failed orders,
and cart clearing only after success.

Build the frontend for production from `frontend`:

```powershell
npm run build
```

Latest verification: backend **23 passed** with one upstream Starlette
`TestClient` deprecation warning; frontend **7 passed**; Vite production
build passed. These test runs did not use the development PostgreSQL
database.

The logging tests verify JSON fields, generated and accepted/rejected
request IDs, response headers, status/duration fields, unexpected
exception records, generic client errors, and sensitive-value
redaction. `pip check` reported no broken requirements.

### Local end-to-end verification

The local PostgreSQL container and the documented FastAPI and Vite
development servers were already running, so they were reused rather
than restarted. The browser loaded six API-backed products, added two
products to the bag, raised the notebook quantity to two, removed the
bottle, and placed an order. The UI showed a confirmed total of `$36.00`
and cleared the bag. PostgreSQL then showed the persisted order and line
item (product 1, quantity 2, unit price `18.00`, subtotal `36.00`); the
notebook stock changed from 16 to 14.

Live API checks returned HTTP 422 for zero quantity, 404 for an
unknown product, and 409 for insufficient stock. After these rejected
requests, PostgreSQL still had three total orders (the two pre-existing
orders plus the one successful checkout) and product 1 stock remained
14.

The browser's backend-unavailable state was tested by aborting its
product API request; it displayed a retryable error instead of
crashing. The browser order-error state was tested with a simulated
HTTP 409 and retained the bag. Database-unavailable handling is covered
by the isolated backend tests; the running PostgreSQL service was not
stopped for this verification.

A temporary local Uvicorn smoke server on port 8001 emitted a JSON
`HTTP request completed` record for `GET /health`; its request ID
matched the `X-Request-ID` response header and the record included
status 200 and request duration. The temporary server and its log files
were removed after the check.

Alembic applied migration `0002_orders`; `alembic check` reported no
new upgrade operations. The seed command inserted six products on its
first run and zero on its second. The database query confirmed six
products and six unique slugs. Live `GET /api/v1/products` returned
those six PostgreSQL products with decimal-string prices; both health
endpoints returned HTTP 200.

Live PostgreSQL verification created a multi-product order with a
server-calculated total of `68.00`, persisted two order items, and
decremented the corresponding stock. A second order placed from the
browser was also confirmed in PostgreSQL. Nonexistent products returned
404, zero/negative quantities returned 422, and insufficient stock
returned 409 without changing stock. A forced database failure returned
503; automated tests verified the order and inventory were rolled back.

PostgreSQL 17 Alpine started and reported healthy. `pg_isready` reported
that it was accepting connections, the host mapping on
`127.0.0.1:5432` was reachable, and a SQL query returned
`devopsmart|devopsmart`. Stop/start verification succeeded and the
database remained healthy afterward.

The frontend production build passed with Vite 8.3.5. Browser
verification confirmed all six API-backed products appeared, search
and category filters worked, cart quantity controls worked, and a
successful order displayed its server order number and total while
clearing the cart. A simulated stock-conflict response showed an error
and preserved the cart. At 390px the page had no horizontal overflow.

Suggested screenshots (not captured yet):

- `screenshots/frontend/order-flow-desktop.png`
- `screenshots/frontend/order-confirmation-mobile.png`
- `screenshots/backend/orders-api-swagger.png`

## Project constraints

- Develop and deploy locally; do not provision paid cloud
  infrastructure without approval.
- Use kind for the planned local Kubernetes phase.
- Keep secrets out of Git and use lightweight, incremental steps suited
  to a Windows PC with 8 GB RAM.
