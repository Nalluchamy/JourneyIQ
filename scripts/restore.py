#!/usr/bin/env python3
"""
JourneyIQ Restore Script
=========================
Restores a backup archive created by backup.py.

Steps:
  1. Verify archive-level SHA-256 checksum
  2. Extract the archive
  3. Verify individual file checksums from manifest.json
  4. Restore ML model checkpoints to backend/models/
  5. Optionally restore database dump via psql
  6. Optionally restore configuration files

Usage:
    python scripts/restore.py backups/journeyiq_backup_20260711_120000.zip
    python scripts/restore.py backups/journeyiq_backup_20260711_120000.zip --restore-db --restore-configs
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
MODELS_DIR = os.path.join(BACKEND_DIR, "models")


def sha256_file(filepath: str) -> str:
    """Calculate SHA-256 checksum for a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_archive_checksum(zip_path: str) -> bool:
    """Verify the ZIP archive against its companion .sha256 file."""
    sha_path = zip_path.replace(".zip", ".sha256")
    if not os.path.exists(sha_path):
        print("  [WARN] No .sha256 checksum file found. Skipping archive verification.")
        return True

    with open(sha_path, "r") as f:
        expected_line = f.read().strip()

    # Format: "<hash>  <filename>"
    expected_hash = expected_line.split()[0]
    actual_hash = sha256_file(zip_path)

    if actual_hash == expected_hash:
        print(f"  [OK] Archive checksum verified: {actual_hash[:16]}...")
        return True
    else:
        print(f"  [FAIL] Archive checksum mismatch!")
        print(f"    Expected: {expected_hash}")
        print(f"    Actual:   {actual_hash}")
        return False


def verify_file_checksums(extract_dir: str, manifest: dict) -> tuple[int, int]:
    """Verify individual file checksums from the manifest."""
    checksums = manifest.get("checksums", {})
    passed = 0
    failed = 0

    for rel_path, expected_hash in checksums.items():
        filepath = os.path.join(extract_dir, rel_path)
        if not os.path.exists(filepath):
            print(f"  [FAIL] Missing file: {rel_path}")
            failed += 1
            continue

        actual_hash = sha256_file(filepath)
        if actual_hash == expected_hash:
            passed += 1
        else:
            print(f"  [FAIL] Checksum mismatch: {rel_path}")
            failed += 1

    return passed, failed


def restore_models(extract_dir: str) -> int:
    """Restore ML model checkpoints to backend/models/."""
    models_src = os.path.join(extract_dir, "models")
    if not os.path.exists(models_src):
        print("  [WARN] No models directory in backup. Skipping.")
        return 0

    os.makedirs(MODELS_DIR, exist_ok=True)
    count = 0
    for filename in os.listdir(models_src):
        src = os.path.join(models_src, filename)
        dst = os.path.join(MODELS_DIR, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            count += 1
            print(f"  [OK] Restored model: {filename}")

    return count


def restore_database(extract_dir: str) -> bool:
    """Restore database from pg_dump SQL file if available."""
    dump_path = os.path.join(extract_dir, "database", "journeyiq_dump.sql")
    if not os.path.exists(dump_path):
        print("  [WARN] No SQL dump file found in backup. Skipping database restore.")
        return False

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("  [WARN] DATABASE_URL not set. Cannot restore database.")
        return False

    pg_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    if not shutil.which("psql"):
        print("  [WARN] psql not found. Cannot restore database.")
        return False

    try:
        result = subprocess.run(
            ["psql", pg_url, "-f", dump_path],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("  [OK] Database restored successfully.")
            return True
        else:
            print(f"  [FAIL] psql error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  [FAIL] Database restore error: {e}")
        return False


def restore_configs(extract_dir: str) -> int:
    """Restore configuration files to their original locations."""
    configs_src = os.path.join(extract_dir, "configs")
    if not os.path.exists(configs_src):
        print("  [WARN] No configs directory in backup. Skipping.")
        return 0

    count = 0
    for filename in os.listdir(configs_src):
        src = os.path.join(configs_src, filename)
        if not os.path.isfile(src):
            continue

        # Parse prefix to determine destination
        if filename.startswith("backend_"):
            dest_name = filename.replace("backend_", "", 1)
            dest = os.path.join(BACKEND_DIR, dest_name)
        elif filename.startswith("root_"):
            dest_name = filename.replace("root_", "", 1)
            dest = os.path.join(PROJECT_ROOT, dest_name)
        else:
            continue

        shutil.copy2(src, dest)
        count += 1
        print(f"  [OK] Restored config: {dest}")

    return count


def main():
    parser = argparse.ArgumentParser(description="JourneyIQ Restore Tool")
    parser.add_argument("archive", help="Path to the backup ZIP archive")
    parser.add_argument(
        "--restore-db",
        action="store_true",
        help="Restore database from SQL dump",
    )
    parser.add_argument(
        "--restore-configs",
        action="store_true",
        help="Restore configuration files",
    )
    parser.add_argument(
        "--skip-checksum",
        action="store_true",
        help="Skip checksum verification",
    )
    args = parser.parse_args()

    zip_path = os.path.abspath(args.archive)
    if not os.path.exists(zip_path):
        print(f"[FAIL] Archive not found: {zip_path}")
        return 1

    print("=== JourneyIQ Restore v1.0 ===")
    print(f"Archive: {zip_path}")
    print()

    # 1. Verify archive checksum
    if not args.skip_checksum:
        print("[1/5] Verifying archive checksum...")
        if not verify_archive_checksum(zip_path):
            print("[ABORT] Archive integrity check failed. Use --skip-checksum to bypass.")
            return 1
    else:
        print("[1/5] Skipping archive checksum (--skip-checksum)")

    # 2. Extract
    print("[2/5] Extracting archive...")
    extract_base = os.path.join(os.path.dirname(zip_path), "_restore_temp")
    if os.path.exists(extract_base):
        shutil.rmtree(extract_base)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_base)

    # Find the actual backup directory inside extract
    subdirs = [
        d
        for d in os.listdir(extract_base)
        if os.path.isdir(os.path.join(extract_base, d))
    ]
    if subdirs:
        extract_dir = os.path.join(extract_base, subdirs[0])
    else:
        extract_dir = extract_base

    print(f"  [OK] Extracted to: {extract_dir}")

    # 3. Verify file checksums
    manifest_path = os.path.join(extract_dir, "manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

    if not args.skip_checksum and manifest.get("checksums"):
        print("[3/5] Verifying file checksums...")
        passed, failed = verify_file_checksums(extract_dir, manifest)
        print(f"  Passed: {passed}, Failed: {failed}")
        if failed > 0:
            print("[ABORT] File integrity check failed.")
            shutil.rmtree(extract_base)
            return 1
    else:
        print("[3/5] Skipping file checksum verification")

    # 4. Restore models (always)
    print("[4/5] Restoring ML models...")
    models_count = restore_models(extract_dir)
    print(f"  Restored {models_count} model files.")

    # 5. Optional restores
    print("[5/5] Optional restores...")
    if args.restore_db:
        restore_database(extract_dir)
    else:
        print("  [SKIP] Database restore (use --restore-db to enable)")

    if args.restore_configs:
        configs_count = restore_configs(extract_dir)
        print(f"  Restored {configs_count} config files.")
    else:
        print("  [SKIP] Config restore (use --restore-configs to enable)")

    # Cleanup
    shutil.rmtree(extract_base)

    print()
    print("=== Restore Complete ===")
    print(f"Models restored: {models_count}")
    print(f"Backup name: {manifest.get('backup_name', 'unknown')}")
    print(f"Backup created: {manifest.get('created_at', 'unknown')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
