# Developer Guide

## 1) Repository Module Structure

```text
backend/
  config/           # Django settings, URL routing, WSGI/ASGI
  api/              # DRF serializers + endpoint controllers
  users/            # user profile roles, role permissions, signals
  products/         # product model + stock lock helper
  cart/             # cart item model
  orders/           # order models + transactional order service
frontend/
  templates/        # page templates
  js/app.js         # SPA-like client behavior + API calls
  css/              # UI styles
kubernetes/         # deployment/service manifests
database/           # SQL reference schema and seed scripts
```

## 2) Backend Coding Practices

- Keep endpoint-level validation in DRF serializers.
- Keep cross-model transactional workflows in service-like functions (example: `place_order_for_user`).
- Enforce authorization in **both** `permission_classes` and role decorators for explicitness.
- Prefer queryset filtering and DB-side operations over Python loops when possible.
- Preserve atomicity for checkout/order placement.

## 3) API Conventions

- Base API prefix: `/api/`.
- Endpoint style currently uses **no trailing slash** (except `/api/health/`).
- JSON request/response format only.
- Authentication:
  - Login returns JWT access/refresh tokens.
  - Protected endpoints require `Authorization: Bearer <token>`.
- Error handling:
  - Validation errors return DRF 400 payloads.
  - Missing resources return 404 with `detail` message.

## 4) Role and Permission Conventions

User roles are represented in `users.UserRole`:
- `visitor`: browse products
- `buyer`: cart + place orders
- `seller`: manage products

Custom permission classes (`users/permissions.py`) map role capabilities to action-level checks:
- `CanManageProducts`
- `CanEditCart`
- `CanCreateOrders`

When adding new APIs, define permission semantics first, then endpoint handlers.

## 5) Model and Migration Conventions

- Add/modify Django models first.
- Generate migrations with `python manage.py makemigrations`.
- Apply with `python manage.py migrate`.
- Keep migrations backward-compatible where possible to support rolling deployments.

## 6) Frontend Development Conventions

- Keep API logic centralized in `frontend/js/app.js` (`api.request` wrapper).
- Add new pages in `frontend/templates/` and wire into navigation/header.
- Reuse existing UI classes/components before introducing new style systems.
- Preserve `/api/` proxy assumption for environment portability.

## 7) Logging Conventions

Current runtime emits container stdout/stderr logs (Gunicorn/Nginx/MySQL).

Recommended backend app logging pattern for new modules:
- Use Python `logging.getLogger(__name__)` per module.
- Log structured key context (user id, product id, order id).
- Never log secrets, passwords, raw JWTs, or PII beyond minimum diagnostics.
- Use `INFO` for normal lifecycle events, `WARNING` for recoverable issues, `ERROR` for failed operations.

## 8) Testing and Quality Checks

Suggested baseline checks before merge:

```bash
cd backend
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

For integration smoke tests:
- verify health endpoint
- register/login flow
- product list and detail
- cart add/remove
- order placement
