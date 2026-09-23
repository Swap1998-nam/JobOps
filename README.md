# JobOps: a DevOps and DevSecOps practice application

A job application tracker with FastAPI, PostgreSQL, a browser UI, health checks, and Prometheus metrics. Designed as a real project you can extend rather than a collection of disconnected demos.

## Start

Install Docker with Compose, then run:

```bash
docker compose up --build -d
```

Open http://localhost:8000. API docs: http://localhost:8000/docs. Check `docker compose ps`; stop with `docker compose down` (add `-v` only when you intend to erase local data).

## Practice path

1. **Application and Git:** add one feature (notes or follow-up date), create a branch and PR; add a migration before changing the database schema.
2. **CI:** push to GitHub to run tests, Bandit, pip-audit, and a container build. Fix findings rather than suppressing them without investigation.
3. **Security:** add Trivy image and IaC scans, Gitleaks, dependency updates, pinned action commit SHAs, SBOM generation, and artifact signing. Review findings and document exceptions.
4. **Registry and CD:** publish tagged images to ECR with GitHub OIDC; deploy a versioned image through Helm and require approval for production. Avoid long-lived AWS keys.
5. **Kubernetes:** use `k8s/app.yaml` after supplying a real PostgreSQL service and a `jobops-db` Secret containing `database-url`. For a local kind cluster, load the image with `kind load docker-image jobops:local`; apply the manifest and port forward `svc/jobops 8000:80`. The sample secret is deliberately not committed.
6. **Infrastructure:** run `terraform fmt`/`validate`, then provision the example private, encrypted S3 artifact bucket with a globally unique `bucket_name`. Expand to VPC, ECR, RDS and EKS in a separate AWS account with a budget; plan before apply and clean up costly resources afterward. Do not place database credentials in Terraform state.
7. **Observability and reliability:** scrape `/metrics`; chart `jobops_applications_created_total`, add alerts, load test, backup and restore PostgreSQL, simulate DB failure and confirm readiness fails while liveness succeeds.

## Local tests

Start just the database with `docker compose up -d db`. Create a Python 3.12 virtual environment; run `pip install -r requirements-dev.txt`, then `pytest -q`. `DATABASE_URL` defaults to the Compose database exposed on localhost:5432. Keep production credentials out of source control.

## API

`POST /api/applications` accepts `company`, `role`, optional `status`. `GET /api/applications` lists entries. `PATCH /api/applications/{id}?status=interview` changes status. `/health/live`, `/health/ready`, and `/metrics` support operations.

The Compose password is intentionally local demo data. Set distinct secrets for remote environments. The Terraform example creates only S3; full AWS deployment is an exercise and may incur charges.
