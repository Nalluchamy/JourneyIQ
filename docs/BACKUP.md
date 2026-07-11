# JourneyIQ — Backup & Disaster Recovery Guide

> **Version:** 1.0.0 | **Last Updated:** 2026-07-11

This guide covers backup procedures, integrity verification, restore operations, and disaster recovery planning for all JourneyIQ production data.

---

## Table of Contents

- [Backup Overview](#backup-overview)
- [Database Backup](#database-backup)
  - [Using scripts/backup.py](#using-scriptsbackuppy)
  - [Manual pg_dump](#manual-pg_dump)
  - [SQLAlchemy Fallback](#sqlalchemy-fallback)
- [Model Checkpoint Backup](#model-checkpoint-backup)
- [Configuration Backup](#configuration-backup)
- [SHA-256 Checksum Verification](#sha-256-checksum-verification)
- [Restore Procedure](#restore-procedure)
  - [Using scripts/restore.py](#using-scriptsrestorepy)
  - [Manual Database Restore](#manual-database-restore)
  - [Manual Model Restore](#manual-model-restore)
- [Backup Verification](#backup-verification)
- [Recommended Backup Schedule](#recommended-backup-schedule)
- [Disaster Recovery Playbook](#disaster-recovery-playbook)

---

## Backup Overview

JourneyIQ has three categories of critical data that require regular backups:

| Category | Contents | Location | RPO Target |
|---|---|---|---|
| **Database** | User accounts, orders, products, reviews, recommendations, events | PostgreSQL (Supabase) | 24 hours |
| **Model Checkpoints** | Trained PyTorch NCF weights, metadata, evaluation metrics | `backend/models/` | 7 days |
| **Configuration** | Environment variables, secrets, deployment settings | `.env`, `.env.production` | On change |

```
Backup Archive Structure:
backups/
├── db/
│   ├── journeyiq_db_2026-07-11_030000.sql.gz
│   ├── journeyiq_db_2026-07-11_030000.sql.gz.sha256
│   ├── journeyiq_db_2026-07-10_030000.sql.gz
│   └── journeyiq_db_2026-07-10_030000.sql.gz.sha256
├── models/
│   ├── journeyiq_models_2026-07-11_030000.tar.gz
│   ├── journeyiq_models_2026-07-11_030000.tar.gz.sha256
│   └── ...
└── config/
    ├── journeyiq_config_2026-07-11_030000.tar.gz
    ├── journeyiq_config_2026-07-11_030000.tar.gz.sha256
    └── ...
```

---

## Database Backup

### Using scripts/backup.py

The primary backup mechanism uses `scripts/backup.py`, which attempts `pg_dump` first and falls back to SQLAlchemy export if `pg_dump` is unavailable.

```bash
# Run database backup
python scripts/backup.py --type database --output backups/db/

# Full backup (database + models + config)
python scripts/backup.py --type full --output backups/

# With compression
python scripts/backup.py --type database --output backups/db/ --compress
```

#### How It Works

```
scripts/backup.py
    │
    ├── Try: pg_dump (preferred)
    │   ├── Connects using DATABASE_URL from .env
    │   ├── Dumps all tables with CREATE + INSERT statements
    │   ├── Compresses output with gzip
    │   └── Generates SHA-256 checksum file
    │
    └── Fallback: SQLAlchemy export
        ├── Connects via async SQLAlchemy session
        ├── Iterates all ORM models and exports as JSON
        ├── Packages into compressed archive
        └── Generates SHA-256 checksum file
```

### Manual pg_dump

For direct database backup without the Python script:

```bash
# From host (if PostgreSQL is accessible)
pg_dump -h localhost -U postgres -d journeyiq \
  --format=custom \
  --file=backups/db/journeyiq_$(date +%Y-%m-%d_%H%M%S).dump

# From Docker container
docker exec journeyiq_db_prod pg_dump \
  -U ${POSTGRES_USER:-postgres} \
  -d ${POSTGRES_DB:-postgres} \
  --format=custom \
  --file=/tmp/backup.dump

# Copy backup from container to host
docker cp journeyiq_db_prod:/tmp/backup.dump ./backups/db/

# Compressed SQL dump
docker exec journeyiq_db_prod pg_dump \
  -U postgres -d postgres \
  | gzip > backups/db/journeyiq_$(date +%Y-%m-%d_%H%M%S).sql.gz
```

> [!IMPORTANT]
> Always use `--format=custom` for `pg_dump` when possible. Custom format supports parallel restore, selective table restoration, and built-in compression.

### SQLAlchemy Fallback

When `pg_dump` is not available (e.g., managed database without shell access), the backup script falls back to SQLAlchemy-based export:

```python
# Conceptual flow of the SQLAlchemy fallback
from sqlalchemy import inspect
from app.db.session import engine

async def export_via_sqlalchemy(output_path):
    async with engine.connect() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()

        for table in tables:
            rows = await conn.execute(text(f"SELECT * FROM {table}"))
            data = [dict(row._mapping) for row in rows]
            # Serialize to JSON and write to archive
```

> [!NOTE]
> The SQLAlchemy fallback exports data as JSON, not SQL. This means schema (table definitions, indexes, constraints) must be recreated separately via Alembic migrations during restore.

---

## Model Checkpoint Backup

Model backups capture the entire `backend/models/` directory:

```bash
# Backup all model files
tar -czf backups/models/journeyiq_models_$(date +%Y-%m-%d_%H%M%S).tar.gz \
  -C backend models/

# From Docker container
docker exec journeyiq_backend_prod tar -czf /tmp/models_backup.tar.gz -C /app models/
docker cp journeyiq_backend_prod:/tmp/models_backup.tar.gz ./backups/models/

# Using the backup script
python scripts/backup.py --type models --output backups/models/
```

### What Gets Backed Up

| File | Size (Typical) | Critical |
|---|---|---|
| `latest.pt` | 2–10 MB | ✅ Active model weights |
| `ncf_model_v*.pt` | 2–10 MB each | ✅ Version history for rollback |
| `model_metadata.json` | < 5 KB | ✅ Training metadata and history |
| `evaluation_metrics.json` | < 1 KB | ✅ Current evaluation scores |

> [!TIP]
> For large deployments with many checkpoints, consider backing up only `latest.pt`, `model_metadata.json`, and the 3 most recent versioned checkpoints to reduce archive size.

---

## Configuration Backup

Environment files contain secrets and deployment configuration that must be backed up separately:

```bash
# Backup environment files
tar -czf backups/config/journeyiq_config_$(date +%Y-%m-%d_%H%M%S).tar.gz \
  .env .env.production .env.staging 2>/dev/null

# Using the backup script
python scripts/backup.py --type config --output backups/config/
```

### Files Included

| File | Contents |
|---|---|
| `.env` | Primary environment configuration |
| `.env.production` | Production-specific overrides |
| `.env.staging` | Staging-specific overrides (if exists) |

> [!CAUTION]
> Configuration backups contain **plaintext secrets** (DATABASE_URL with passwords, SECRET_KEY, JWT_SECRET). Always:
> - Encrypt backup archives before transferring off-server
> - Store in access-controlled locations (e.g., AWS S3 with SSE, Azure Blob with encryption)
> - Never commit backup archives to version control

```bash
# Encrypt config backup with GPG
gpg --symmetric --cipher-algo AES256 \
  backups/config/journeyiq_config_2026-07-11_030000.tar.gz
```

---

## SHA-256 Checksum Verification

Every backup archive is accompanied by a `.sha256` checksum file for integrity verification.

### Generating Checksums

```bash
# Generate checksum for a backup file
sha256sum backups/db/journeyiq_db_2026-07-11_030000.sql.gz \
  > backups/db/journeyiq_db_2026-07-11_030000.sql.gz.sha256

# Generate checksums for all backup files
find backups/ -name "*.tar.gz" -o -name "*.sql.gz" | while read f; do
  sha256sum "$f" > "${f}.sha256"
done
```

### Verifying Checksums

```bash
# Verify a single file
sha256sum -c backups/db/journeyiq_db_2026-07-11_030000.sql.gz.sha256

# Verify all checksums
find backups/ -name "*.sha256" -exec sha256sum -c {} \;
```

Expected output:
```
backups/db/journeyiq_db_2026-07-11_030000.sql.gz: OK
backups/models/journeyiq_models_2026-07-11_030000.tar.gz: OK
backups/config/journeyiq_config_2026-07-11_030000.tar.gz: OK
```

> [!WARNING]
> If verification fails (`FAILED`), the backup file is corrupted. Do **not** use it for restoration. Re-run the backup immediately.

### Windows (PowerShell)

```powershell
# Generate checksum
Get-FileHash .\backups\db\journeyiq_db_2026-07-11_030000.sql.gz -Algorithm SHA256 |
  Format-List | Out-File .\backups\db\journeyiq_db_2026-07-11_030000.sql.gz.sha256

# Verify checksum
$expected = (Get-Content .\backups\db\journeyiq_db_2026-07-11_030000.sql.gz.sha256 |
  Select-String "Hash").ToString().Split(":")[1].Trim()
$actual = (Get-FileHash .\backups\db\journeyiq_db_2026-07-11_030000.sql.gz -Algorithm SHA256).Hash
if ($expected -eq $actual) { Write-Host "OK" } else { Write-Host "FAILED" }
```

---

## Restore Procedure

### Using scripts/restore.py

```bash
# Restore database from backup
python scripts/restore.py --type database \
  --input backups/db/journeyiq_db_2026-07-11_030000.sql.gz

# Restore models from backup
python scripts/restore.py --type models \
  --input backups/models/journeyiq_models_2026-07-11_030000.tar.gz

# Restore configuration
python scripts/restore.py --type config \
  --input backups/config/journeyiq_config_2026-07-11_030000.tar.gz

# Full restore (all components)
python scripts/restore.py --type full --input backups/
```

#### Restore Flow

```
scripts/restore.py
    │
    ├── 1. Verify SHA-256 checksum
    │      └── Abort if checksum mismatch
    │
    ├── 2. Decompress archive
    │
    ├── 3. For database:
    │      ├── Stop backend containers
    │      ├── Drop and recreate database
    │      ├── pg_restore or psql < dump.sql
    │      ├── Run alembic upgrade head (schema sync)
    │      └── Restart backend containers
    │
    ├── 4. For models:
    │      ├── Extract to backend/models/
    │      ├── Verify latest.pt exists
    │      └── Restart backend for model reload
    │
    └── 5. For config:
           ├── Extract .env files to project root
           ├── Verify critical vars are set
           └── Restart all services
```

### Manual Database Restore

```bash
# From custom format dump
docker exec -i journeyiq_db_prod pg_restore \
  --clean --if-exists \
  -U postgres -d postgres \
  < backups/db/journeyiq_db_2026-07-11_030000.dump

# From compressed SQL dump
gunzip -c backups/db/journeyiq_db_2026-07-11_030000.sql.gz \
  | docker exec -i journeyiq_db_prod psql -U postgres -d postgres

# Run migrations after restore to ensure schema is current
docker exec journeyiq_backend_prod alembic upgrade head
```

> [!IMPORTANT]
> Always run `alembic upgrade head` after a database restore to ensure the schema matches the current codebase. Backups from older versions may have missing columns or tables.

### Manual Model Restore

```bash
# Extract model backup
tar -xzf backups/models/journeyiq_models_2026-07-11_030000.tar.gz \
  -C backend/

# Verify files exist
ls -la backend/models/latest.pt
ls -la backend/models/model_metadata.json
ls -la backend/models/evaluation_metrics.json

# Restart backend to load restored model
docker restart journeyiq_backend_prod
```

---

## Backup Verification

After creating a backup, run through this verification checklist:

### Automated Verification

```bash
#!/bin/bash
# verify_backup.sh — Run after each backup

BACKUP_DIR="${1:?Usage: verify_backup.sh <backup_dir>}"

echo "=== JourneyIQ Backup Verification ==="

# 1. Check files exist
echo -n "Checking backup files exist... "
DB_FILE=$(ls -t ${BACKUP_DIR}/db/*.sql.gz 2>/dev/null | head -1)
MODEL_FILE=$(ls -t ${BACKUP_DIR}/models/*.tar.gz 2>/dev/null | head -1)

[ -f "$DB_FILE" ] && echo -n "DB:✅ " || echo -n "DB:❌ "
[ -f "$MODEL_FILE" ] && echo -n "Models:✅ " || echo -n "Models:❌ "
echo ""

# 2. Verify checksums
echo -n "Verifying checksums... "
if [ -f "${DB_FILE}.sha256" ]; then
  sha256sum -c "${DB_FILE}.sha256" --quiet 2>/dev/null && echo -n "DB:✅ " || echo -n "DB:❌ "
fi
if [ -f "${MODEL_FILE}.sha256" ]; then
  sha256sum -c "${MODEL_FILE}.sha256" --quiet 2>/dev/null && echo -n "Models:✅ " || echo -n "Models:❌ "
fi
echo ""

# 3. Check file sizes (non-zero)
echo -n "Checking file sizes... "
DB_SIZE=$(stat -f%z "$DB_FILE" 2>/dev/null || stat -c%s "$DB_FILE" 2>/dev/null)
MODEL_SIZE=$(stat -f%z "$MODEL_FILE" 2>/dev/null || stat -c%s "$MODEL_FILE" 2>/dev/null)

[ "$DB_SIZE" -gt 1000 ] && echo -n "DB:✅ (${DB_SIZE}B) " || echo -n "DB:❌ (${DB_SIZE}B) "
[ "$MODEL_SIZE" -gt 1000 ] && echo -n "Models:✅ (${MODEL_SIZE}B) " || echo -n "Models:❌ (${MODEL_SIZE}B) "
echo ""

# 4. Test decompression
echo -n "Testing decompression... "
gunzip -t "$DB_FILE" 2>/dev/null && echo -n "DB:✅ " || echo -n "DB:❌ "
tar -tzf "$MODEL_FILE" >/dev/null 2>&1 && echo -n "Models:✅ " || echo -n "Models:❌ "
echo ""

echo "=== Verification Complete ==="
```

### Manual Verification Checklist

- [ ] Backup archive files are present in the expected directory
- [ ] SHA-256 checksum files exist alongside each archive
- [ ] Checksum verification passes for all archives
- [ ] Archive file sizes are non-zero and reasonable
- [ ] Archives can be decompressed without errors
- [ ] Database dump contains expected tables (`\dt` after test restore)
- [ ] Model backup contains `latest.pt` and `model_metadata.json`
- [ ] Config backup contains `.env` with expected variables

---

## Recommended Backup Schedule

| Backup Type | Frequency | Retention | Time Window |
|---|---|---|---|
| **Database** | Daily | 30 days | 03:00 UTC (off-peak) |
| **Model Checkpoints** | Weekly | 12 weeks | Sunday 04:00 UTC |
| **Configuration** | On every change | Indefinite | Immediate |
| **Full Backup** | Weekly | 4 weeks | Sunday 03:00 UTC |

### Cron Schedule

```bash
# Daily database backup at 3:00 AM UTC
0 3 * * * cd /opt/journeyiq && python scripts/backup.py --type database --output backups/db/ 2>&1 | tee -a backups/backup.log

# Weekly full backup on Sunday at 3:00 AM UTC
0 3 * * 0 cd /opt/journeyiq && python scripts/backup.py --type full --output backups/ 2>&1 | tee -a backups/backup.log

# Daily cleanup: remove backups older than 30 days
0 5 * * * find /opt/journeyiq/backups/db/ -name "*.sql.gz" -mtime +30 -delete

# Weekly cleanup: remove model backups older than 12 weeks
0 5 * * 0 find /opt/journeyiq/backups/models/ -name "*.tar.gz" -mtime +84 -delete
```

### Off-Site Backup Sync

```bash
# Sync to AWS S3
aws s3 sync backups/ s3://journeyiq-backups/$(date +%Y-%m) \
  --storage-class STANDARD_IA \
  --server-side-encryption AES256

# Sync to Azure Blob Storage
az storage blob upload-batch \
  --destination backups \
  --account-name journeyiqstorage \
  --source backups/ \
  --pattern "*.gz"
```

---

## Disaster Recovery Playbook

### Scenario 1 — Database Corruption

```
1. Stop backend services
   docker compose -f docker-compose.prod.yml stop backend ml-service

2. Identify latest valid backup
   ls -lt backups/db/

3. Verify backup integrity
   sha256sum -c backups/db/journeyiq_db_LATEST.sql.gz.sha256

4. Restore database
   gunzip -c backups/db/journeyiq_db_LATEST.sql.gz | \
     docker exec -i journeyiq_db_prod psql -U postgres -d postgres

5. Run migrations
   docker exec journeyiq_backend_prod alembic upgrade head

6. Restart services
   docker compose -f docker-compose.prod.yml up -d backend ml-service

7. Verify health
   curl -s http://localhost/api/v1/health
```

### Scenario 2 — Complete Server Loss

```
1. Provision new server (same specs as original)
2. Install Docker and Docker Compose
3. Clone repository from GitHub
4. Restore configuration backup (.env files)
5. Start infrastructure (DB + Redis only)
   docker compose -f docker-compose.prod.yml up -d db redis
6. Wait for database health check to pass
7. Restore database from off-site backup
8. Restore model checkpoints from off-site backup
9. Start remaining services
   docker compose -f docker-compose.prod.yml up -d
10. Verify all endpoints respond
11. Update DNS records if IP changed
12. Verify SSL certificates
```

### Scenario 3 — Model Degradation

```
1. Check evaluation metrics
   curl -s http://localhost:8000/api/v1/system/models | jq '.data.active_model.evaluation_metrics'

2. Compare with previous version's metrics
   (Check model_metadata.json history or monitoring dashboards)

3. Rollback to last known good model
   curl -X POST http://localhost:8000/api/v1/system/models/rollback/{good_version_id}

4. Restart backend to force model reload
   docker restart journeyiq_backend_prod

5. Verify inference is working
   curl -s http://localhost:8000/api/v1/system/models | jq '.data.inference_statistics'

6. Investigate root cause (data drift, training bug, etc.)
```

> [!TIP]
> Run quarterly disaster recovery drills to validate that backup and restore procedures work end-to-end. Restore to a staging environment and verify all system endpoints.

---

*For production monitoring and troubleshooting, see [RUNBOOK.md](RUNBOOK.md). For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).*
