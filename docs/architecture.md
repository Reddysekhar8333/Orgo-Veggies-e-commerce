# Architecture

## 1) High-Level System Design

Orgo Veggies follows a **layered clean architecture style** inside a modular Django monolith, deployed as separate runtime services:

- **Frontend service (Nginx static site + reverse proxy)**
  - Serves static web UI assets.
  - Proxies `/api/*` requests to backend.
- **Backend service (Django + DRF + Gunicorn)**
  - Handles auth, catalog, cart, and order workflows.
- **Database service (MySQL 8)**
  - Stores users, profiles/roles, products, cart items, and orders.

Even though business features live in one backend codebase, bounded modules (`users`, `products`, `cart`, `orders`, `api`) create clear service boundaries for ownership and future extraction.

## 2) Clean Architecture Mapping

### Domain / Data model layer
- Entities modeled in app-local `models.py`:
  - `users.UserProfile` + `UserRole`
  - `products.Product`
  - `cart.CartItem`
  - `orders.Order`, `orders.OrderItem`

### Application / Use-case layer
- Orchestration logic in API views and domain services:
  - API endpoints in `api/views.py`
  - Transactional order placement in `orders/views.py::place_order_for_user`
  - Product locking helper in `products/views.py::lock_products_for_checkout`

### Interface / Delivery layer
- REST API exposed through `config/urls.py` and `api/urls.py`.
- Frontend JS client (`frontend/js/app.js`) calls `/api/*` endpoints.
- Nginx in frontend container routes `/api/` to backend upstream.

### Infrastructure layer
- MySQL via Django ORM.
- Runtime packaging via Dockerfiles.
- Service orchestration via Docker Compose and Kubernetes manifests.

## 3) Service Boundaries

## Frontend boundary

**Responsibilities**
- Rendering page templates (`frontend/templates/*`).
- Calling backend APIs for auth, products, cart, checkout.
- Persisting fallback cart/token in browser local storage.

**Non-responsibilities**
- Authorization and role enforcement.
- Transactional data integrity.

## Backend boundary

**Responsibilities**
- AuthN/AuthZ and role-based permissions.
- Product CRUD/read and stock validation.
- Cart updates.
- Atomic order placement with stock decrement.

**Non-responsibilities**
- Browser rendering logic.
- Static asset hosting at scale (recommended to offload to S3/CloudFront in production).

## Database boundary

**Responsibilities**
- Durable persistence and relational integrity.
- Row-level locking support for checkout consistency.

## 4) Request Flow

## A) Product listing
1. Browser requests `/templates/products.html` from frontend service.
2. Page JS calls `GET /api/products?...`.
3. Nginx proxies to backend.
4. Backend `ProductListCreateAPIView.get` applies filters (`q`, `min_price`, `max_price`, `in_stock`) and returns serialized products.

## B) Add to cart
1. Browser calls `POST /api/cart/add`.
2. Backend authenticates with JWT, checks buyer role + `cart:edit` permission.
3. Serializer validates product existence and stock.
4. Backend creates/updates `CartItem` with quantity checks.

## C) Place order
1. Browser calls `POST /api/order/place`.
2. Backend verifies buyer role + `orders:create` permission.
3. `place_order_for_user` runs in `transaction.atomic()`:
   - Locks cart rows.
   - Locks product rows (`select_for_update`).
   - Validates stock.
   - Creates `Order` + `OrderItem` rows.
   - Decrements stock.
   - Clears cart.
4. API returns order id and total.

## 5) Security and Access

- JWT auth via `rest_framework_simplejwt`.
- CSRF endpoints (`/api/auth/csrf`) and CSRF protection decorators on state-changing auth/cart/order APIs.
- Role model:
  - Buyer: cart + ordering
  - Seller: product management
  - Visitor: read-only product browsing

## 6) Data Consistency Strategy

- Use database transactions for checkout.
- Use `select_for_update` for both cart items and products during order placement.
- Enforce cart uniqueness per `(buyer, product)` in model meta constraint.

## 7) Scalability Strategy (Architecture Level)

- **Horizontal scale backend/frontend** with additional replicas (already represented in Kubernetes manifests for backend/frontend).
- Keep backend stateless (JWT + DB state) so pods can scale behind a service.
- Scale MySQL vertically first; later migrate to managed relational service (RDS/Aurora) with read replica strategy if reporting traffic increases.
- Optionally externalize sessions/cache/rate-limiting to Redis if needed.

## 8) Observability Boundaries

- Health endpoint: `/api/health/` for liveness/readiness checks.
- Container logs available via Docker/Kubernetes log streams.
- Production recommendation: centralize logs/metrics/traces in CloudWatch (detailed setup in `docs/deployment-guide.md`).
