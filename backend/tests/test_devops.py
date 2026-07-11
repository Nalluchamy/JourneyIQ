"""
DevOps & Production Deployment Test Suite
==========================================
Verifies system endpoints, environment config, backup/restore scripts,
MLOps registry, and Prometheus metrics.
"""

import json
import os
import tempfile
import zipfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.cache import ApplicationCache
from app.core.config import Settings
from app.main import app
from app.services.deep_learning.registry import NCFModelRegistry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture()
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        from app.models import Base

        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture()
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# 1. Environment Config
# ---------------------------------------------------------------------------


class TestEnvironmentConfig:
    """Validates dynamic configuration loading."""

    def test_default_environment(self):
        s = Settings()
        assert s.ENVIRONMENT in (
            "development",
            "testing",
            "staging",
            "production",
        )

    def test_project_name(self):
        s = Settings()
        assert s.PROJECT_NAME == "JourneyIQ"

    def test_api_prefix(self):
        s = Settings()
        assert s.API_V1_STR == "/api/v1"


# ---------------------------------------------------------------------------
# 2. System Endpoints
# ---------------------------------------------------------------------------


class TestSystemEndpoints:
    """Verifies all /api/v1/system/* routes return valid responses."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "status" in data["data"]

    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_version_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/version")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["project"] == "JourneyIQ"

    @pytest.mark.asyncio
    async def test_deployment_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/deployment")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "environment" in data
        assert data["secret_key_masked"] == "********"

    @pytest.mark.asyncio
    async def test_runtime_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/runtime")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "cpu_count" in data
        assert "memory_usage_mb" in data
        assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/metrics")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "memory_usage_mb" in data
        assert "cpu_usage_pct" in data

    @pytest.mark.asyncio
    async def test_cache_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/cache")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "type" in data
        assert "stats" in data

    @pytest.mark.asyncio
    async def test_database_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/database")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "pool_size" in data

    @pytest.mark.asyncio
    async def test_logs_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/logs")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "lines_count" in data

    @pytest.mark.asyncio
    async def test_models_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/models")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "active_model" in data
        assert "inference_statistics" in data
        assert "checkpoints_registry" in data

    @pytest.mark.asyncio
    async def test_prometheus_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/system/prometheus")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        text = resp.text
        assert "journeyiq_system_cpu_usage_ratio" in text
        assert "journeyiq_cache_hits_total" in text
        assert "journeyiq_ml_inferences_total" in text


# ---------------------------------------------------------------------------
# 3. Cache Statistics
# ---------------------------------------------------------------------------


class TestCacheStatistics:
    """Validates cache hit/miss tracking."""

    def test_cache_stats_initial(self):
        c = ApplicationCache()
        stats = c.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_cache_hit_miss_tracking(self):
        c = ApplicationCache()
        c.set("test_key", "test_value", ttl_seconds=60)
        c.get("test_key")
        c.get("nonexistent_key")
        stats = c.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1


# ---------------------------------------------------------------------------
# 4. MLOps Model Registry
# ---------------------------------------------------------------------------


class TestModelRegistry:
    """Validates NCFModelRegistry operations."""

    def test_inference_telemetry(self):
        NCFModelRegistry.track_inference(0.015)
        NCFModelRegistry.track_inference(0.025)
        stats = NCFModelRegistry.get_inference_telemetry()
        assert stats["total_inference_calls"] >= 2

    def test_list_checkpoints(self):
        """Checkpoints list should work even if models dir is empty or missing."""
        checkpoints = NCFModelRegistry.list_checkpoints()
        assert isinstance(checkpoints, list)

    def test_get_active_model(self):
        model = NCFModelRegistry.get_active_model()
        assert "framework" in model
        assert model["framework"] == "pytorch"

    def test_rollback_nonexistent_version(self):
        result = NCFModelRegistry.rollback_to_version("v0000000000")
        assert result is False


# ---------------------------------------------------------------------------
# 5. Backup/Restore Scripts
# ---------------------------------------------------------------------------


class TestBackupRestore:
    """Validates backup archive creation and checksum verification."""

    @staticmethod
    def _project_root() -> str:
        """Returns the JourneyIQ project root (two levels above tests/)."""
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    def test_backup_creates_archive(self):
        """Run backup.py and verify it produces a ZIP with manifest."""
        import subprocess
        import sys

        project_root = self._project_root()
        backup_script = os.path.join(project_root, "scripts", "backup.py")

        if not os.path.exists(backup_script):
            pytest.skip("backup.py not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    backup_script,
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=project_root,
            )
            assert result.returncode == 0, f"Backup failed: {result.stderr}"

            # Verify ZIP was created
            zips = [f for f in os.listdir(tmpdir) if f.endswith(".zip")]
            assert len(zips) == 1, f"Expected 1 ZIP, found: {zips}"

            # Verify SHA-256 file was created
            sha_files = [
                f for f in os.listdir(tmpdir) if f.endswith(".sha256")
            ]
            assert len(sha_files) == 1

            # Verify manifest inside ZIP
            zip_path = os.path.join(tmpdir, zips[0])
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                manifest_files = [
                    n for n in names if n.endswith("manifest.json")
                ]
                assert len(manifest_files) == 1

                # Read and validate manifest
                with zf.open(manifest_files[0]) as mf:
                    manifest = json.loads(mf.read())
                    assert "checksums" in manifest
                    assert "backup_name" in manifest

    def test_checksum_verification(self):
        """Verify SHA-256 hashing works correctly."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("test content for checksum")
            f.flush()
            path = f.name

        try:
            import hashlib

            expected = hashlib.sha256(b"test content for checksum").hexdigest()
            # Import and use the backup module's sha256 function
            import importlib.util

            project_root = self._project_root()
            spec = importlib.util.spec_from_file_location(
                "backup",
                os.path.join(project_root, "scripts", "backup.py"),
            )
            backup_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(backup_mod)
            actual = backup_mod.sha256_file(path)
            assert actual == expected
        finally:
            os.unlink(path)

