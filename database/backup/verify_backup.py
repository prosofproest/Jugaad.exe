"""
Backup and Restore Verification Utility.
Validates backup manifests, checksums, and simulates integrity checks.
"""

import hashlib
import json
import os
import sys
from typing import Dict, List, Optional, Tuple


def calculate_sha256(filepath: str) -> str:
    """Computes SHA-256 hash of a file in streaming chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_backup_manifest(manifest_path: str, base_dir: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Validates that all files in a backup manifest exist and match their SHA-256 checksums."""
    errors = []
    if not os.path.exists(manifest_path):
        return False, [f"Manifest file not found: {manifest_path}"]

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        return False, [f"Failed to parse manifest JSON: {e}"]

    required_keys = ["backup_id", "timestamp_utc", "rpo_target_minutes", "files"]
    for k in required_keys:
        if k not in manifest:
            errors.append(f"Missing required manifest field: {k}")

    if errors:
        return False, errors

    root_dir = base_dir or os.path.dirname(manifest_path)

    for item in manifest.get("files", []):
        filename = item.get("path")
        expected_hash = item.get("sha256")
        if not filename or not expected_hash:
            errors.append(f"Invalid file item in manifest: {item}")
            continue

        target_file = os.path.join(root_dir, filename)
        if not os.path.exists(target_file):
            errors.append(f"Backup artefact missing on disk: {target_file}")
            continue

        actual_hash = calculate_sha256(target_file)
        if actual_hash.lower() != expected_hash.lower():
            errors.append(
                f"Checksum mismatch for {filename}: expected {expected_hash}, calculated {actual_hash}"
            )

    return len(errors) == 0, errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 database/backup/verify_backup.py <path_to_manifest.json>")
        sys.exit(1)

    manifest_file = sys.argv[1]
    ok, errs = verify_backup_manifest(manifest_file)
    if ok:
        print(f"[+] Backup manifest {manifest_file} verified successfully!")
        sys.exit(0)
    else:
        print(f"[!] Backup verification failed with {len(errs)} error(s):")
        for err in errs:
            print(f"    - {err}")
        sys.exit(1)
