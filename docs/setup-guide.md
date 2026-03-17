# Setup Guide

This guide covers both local (non-container) and Docker-based development.

## 1) Environment Variables

Create your runtime file first:

```bash
cp .env.example .env
```

### Frontend variables
- `FRONTEND_PORT`: Nginx listen port inside frontend container (default `80`).
- `NGINX_BACKEND_HOST`: backend hostname resolvable by Nginx (default `backend` in Compose/K8s).
- `NGINX_BACKEND_PORT`: backend app port (default `8000`).

### Backend variables
- `DJANGO_ENV`: environment label (`development`, `staging`, `production`) - informational.
- `DJANGO_DEBUG`: `True`/`False` debug mode.
- `DJANGO_SECRET_KEY`: Django secret key.
- `DJANGO_ALLOWED_HOSTS`: comma-separated host allowlist (currently defined in env template; add usage in settings if enforcing this in production).
- `DJANGO_CORS_ALLOWED_ORIGINS`: template variable for future CORS handling.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated trusted origins for CSRF-protected POSTs.
- `DJANGO_DB_ENGINE`: DB engine path (`django.db.backends.mysql`).
- `DJANGO_DB_NAME`: schema name.
- `DJANGO_DB_USER`: DB username.
- `DJANGO_DB_PASSWORD`: DB password.
- `DJANGO_DB_HOST`: DB host.
- `DJANGO_DB_PORT`: DB port.
- `DJANGO_PORT`: backend container listening port.

### Database variables
- `MYSQL_ROOT_PASSWORD`: root password.
- `MYSQL_DATABASE`: initial app database.
- `MYSQL_USER`: app DB user.
- `MYSQL_PASSWORD`: app user password.
- `MYSQL_PORT`: host-exposed port.

## 2) Local Development (without Docker)

## Prerequisites
- Python 3.12+
- MySQL 8+

## Steps

```bash
cp .env.example .env
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional but recommended
python manage.py runserver
```

Frontend can be served by any static server, but for parity with production behavior use Dockerized Nginx frontend.

## 3) Docker Compose Setup

Start full stack:

```bash
docker compose up --build -d
```

Inspect status:

```bash
docker compose ps
docker compose logs -f backend frontend mysql
```

Stop stack:

```bash
docker compose down
```

## 4) Migration Steps

## Local
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

## In running backend container
```bash
docker compose exec backend python manage.py migrate
```

## Kubernetes job-style migration (recommended)
Use the same backend image and run one-shot migration command before rollout:

```bash
kubectl run migrate-$(date +%s) \
  --image=orgoveggies/backend:latest \
  --restart=Never \
  --env-from=configmap/backend-config \
  --env-from=secret/backend-secrets \
  --command -- python manage.py migrate
```

> Avoid relying only on runtime-start migrations in large clusters; explicit migration jobs are safer and auditable.

## 5) Local Verification Checklist

- `http://localhost:8080` serves frontend.
- `http://localhost:8000/api/health/` returns `{"status":"ok"}`.
- Register/Login works from UI.
- Product listing endpoint responds.
- Cart + checkout endpoint flows complete.

## 6) Troubleshooting

- **Backend cannot connect to DB**: verify `DJANGO_DB_HOST=mysql` for Compose and DB container health.
- **CSRF/auth failures**: ensure correct `DJANGO_CSRF_TRUSTED_ORIGINS` and use same origin/proxy path.
- **Frontend cannot reach backend**: check Nginx upstream vars and `/api/` proxy config.
