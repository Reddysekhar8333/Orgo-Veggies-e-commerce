# Deployment Guide

This document covers EC2 and EKS deployment patterns, static file strategy with S3, logging setup, monitoring/alerting, scaling, and rollback.

## 1) Deployment Artifacts

- Docker images:
  - `orgoveggies/backend:latest`
  - `orgoveggies/frontend:latest`
- Kubernetes manifests under `kubernetes/` for backend/frontend/mysql services and deployments.

## 2) EC2 Deployment (Docker Compose)

Use this for simple environments or low/medium traffic.

## Steps
1. Provision EC2 (Amazon Linux 2023 or Ubuntu), attach security groups (80/443/22 and optional 3306 internal only).
2. Install Docker + Compose plugin.
3. Clone repository and create `.env`.
4. Start stack:
   ```bash
   docker compose up --build -d
   ```
5. Configure TLS/ingress (Nginx reverse proxy or ALB in front).
6. Persist MySQL volume with EBS-backed storage.

## Migration procedure (EC2)
Run explicitly during release:

```bash
docker compose exec backend python manage.py migrate
```

## Scaling on EC2
- Scale frontend/backend containers with Compose replicas only for non-stateful services.
- Keep MySQL single-writer unless managed externally.
- For serious scale, move DB to RDS and app to EKS.

## 3) EKS Deployment (Kubernetes)

Use this for production-grade orchestration.

## Baseline flow
1. Build/push images to ECR.
2. Create/update ConfigMaps and Secrets:
   - `backend-config`, `backend-secrets`
   - `frontend-config`
   - `mysql-config`, `mysql-secrets`
3. Apply manifests:
   ```bash
   kubectl apply -f kubernetes/mysql-deployment.yaml
   kubectl apply -f kubernetes/backend-deployment.yaml
   kubectl apply -f kubernetes/frontend-deployment.yaml
   ```
4. Run migration job using backend image before rolling out app changes.
5. Expose frontend via Ingress + ALB controller.

## Recommended production adjustments
- Replace in-cluster MySQL with RDS/Aurora MySQL.
- Use separate namespaces per environment.
- Pin image tags (avoid `latest` in production).
- Add HPA for backend/frontend based on CPU and request rate.

## 4) S3 Static File Strategy

Current frontend is served from Nginx container. For production CDN performance:

1. Build frontend artifact (`index.html`, `templates/`, `js/`, `css/`, `static/`).
2. Upload to S3 bucket configured for private origin.
3. Serve through CloudFront.
4. Route API requests to backend ALB domain.

Benefits:
- lower latency global delivery
- reduced compute cost for static assets
- simpler frontend rollbacks (versioned objects)

## 5) Logging Setup (CloudWatch Integration)

## Container logs
- **EC2**: use CloudWatch Agent or Fluent Bit on host to ship Docker logs.
- **EKS**: deploy `aws-for-fluent-bit` DaemonSet and send logs to per-service log groups:
  - `/orgo-veggies/frontend`
  - `/orgo-veggies/backend`
  - `/orgo-veggies/mysql`

## Application logs
- Emit backend logs to stdout in JSON-like structured format where possible.
- Include request metadata and correlation ids (if added at ingress layer).

## 6) Monitoring Dashboards and Alarms

Create CloudWatch dashboards for:

- **Infrastructure**: CPU, memory, disk, network per node/pod/instance.
- **Backend**: request count, p95 latency, 4xx/5xx rate, restart count.
- **Database**: CPU, free storage, connections, slow queries, replica lag (if RDS).

Recommended alarms:

- Backend 5xx error rate > 2% for 5 min.
- Backend p95 latency > 1.5s for 10 min.
- Pod restart count spike.
- MySQL/RDS free storage < 20%.
- DB CPU > 80% sustained for 15 min.
- ALB target unhealthy hosts > 0.

Integrate alarm actions with SNS -> Slack/PagerDuty/email.

## 7) Scaling Strategy

## Stateless tiers
- Scale frontend and backend horizontally.
- Use rolling updates with readiness/liveness probes.
- Add HPA and cluster autoscaler in EKS.

## Stateful tier
- Prefer managed DB scaling (RDS instance class, storage autoscaling, read replicas).
- Keep write operations transactional to preserve consistency under load.

## 8) Rollback Procedure

## EC2 rollback
1. Keep prior image tags available.
2. Update Compose image tags back to last known good release.
3. Restart affected services:
   ```bash
   docker compose up -d backend frontend
   ```
4. If schema migration is backward-incompatible, execute pre-written down migration or restore DB snapshot.

## EKS rollback
1. Roll back deployments:
   ```bash
   kubectl rollout undo deployment/backend
   kubectl rollout undo deployment/frontend
   ```
2. Verify rollout health:
   ```bash
   kubectl rollout status deployment/backend
   kubectl rollout status deployment/frontend
   ```
3. If DB changes caused failure, restore from snapshot or run corrective migration job.

## 9) Release Checklist

- [ ] Images built and tagged with immutable version.
- [ ] Migrations reviewed and applied safely.
- [ ] ConfigMaps/Secrets updated.
- [ ] Health checks pass after deploy.
- [ ] CloudWatch dashboards show normal latency/error trends.
- [ ] Rollback plan and DB snapshot confirmed.

