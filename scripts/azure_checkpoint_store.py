"""Small, immutable Azure Blob checkpoint snapshots for national Älgdata.

This first iteration is deliberately isolated from the portal runner. It is used
by a manual synthetic smoke workflow before any production checkpoint is moved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT", "stskogkolldata")
CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER", "national-algdata")
PREFIX_ROOT = "national-algdata"


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _clients():
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:
        raise RuntimeError(
            "Azure SDK is missing; install azure-identity and azure-storage-blob"
        ) from exc
    credential = DefaultAzureCredential()
    service = BlobServiceClient(
        account_url=f"https://{ACCOUNT}.blob.core.windows.net",
        credential=credential,
    )
    return credential, service


def _safe_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe relative path: {value!r}")
    return path.as_posix()


def _upload_immutable(container, blob_name: str, source: Path, digest: str, size: int) -> None:
    from azure.core.exceptions import ResourceExistsError

    blob = container.get_blob_client(blob_name)
    metadata = {"sha256": digest, "byte_count": str(size)}
    try:
        with source.open("rb") as stream:
            blob.upload_blob(stream, overwrite=False, metadata=metadata)
    except ResourceExistsError:
        existing = blob.get_blob_properties().metadata or {}
        if existing.get("sha256") != digest or existing.get("byte_count") != str(size):
            raise RuntimeError(f"Immutable Azure object conflicts with local file: {blob_name}")
    props = blob.get_blob_properties()
    actual_metadata = props.metadata or {}
    if props.size != size or actual_metadata.get("sha256") != digest:
        raise RuntimeError(f"Azure object metadata/size verification failed: {blob_name}")


def publish_snapshot(source_dir: Path, collection_id: str, snapshot_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", collection_id):
        raise ValueError("collection_id contains unsupported characters")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", snapshot_id):
        raise ValueError("snapshot_id contains unsupported characters")
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise FileNotFoundError(source_dir)
    files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    if not files:
        raise ValueError("Refusing to publish an empty checkpoint snapshot")

    manifest_files = []
    for path in files:
        relative = _safe_relative_path(path.relative_to(source_dir).as_posix())
        digest, size = sha256_file(path)
        manifest_files.append({"path": relative, "sha256": digest, "bytes": size})

    prefix = f"{PREFIX_ROOT}/snapshots/{collection_id}/{snapshot_id}"
    credential, service = _clients()
    try:
        container = service.get_container_client(CONTAINER)
        try:
            container.create_container()
        except Exception as exc:
            # Do not suppress arbitrary authorization/network failures.
            from azure.core.exceptions import ResourceExistsError
            if not isinstance(exc, ResourceExistsError):
                raise

        for item in manifest_files:
            blob_name = f"{prefix}/files/{item['path']}"
            _upload_immutable(container, blob_name, source_dir / item["path"], item["sha256"], item["bytes"])

        manifest = {
            "schema_version": 1,
            "kind": "national_algdata_checkpoint_snapshot",
            "storage_account": ACCOUNT,
            "container": CONTAINER,
            "collection_id": collection_id,
            "snapshot_id": snapshot_id,
            "production_write": False,
            "files": manifest_files,
        }
        manifest_path = Path(tempfile.gettempdir()) / f"algdata-manifest-{snapshot_id}.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        digest, size = sha256_file(manifest_path)
        _upload_immutable(container, f"{prefix}/checkpoint-manifest.json", manifest_path, digest, size)
        return {
            "status": "uploaded",
            "container": CONTAINER,
            "prefix": prefix,
            "file_count": len(manifest_files),
            "manifest_sha256": digest,
        }
    finally:
        service.close()
        credential.close()


def restore_snapshot(collection_id: str, snapshot_id: str, output_dir: Path) -> dict[str, Any]:
    prefix = f"{PREFIX_ROOT}/snapshots/{collection_id}/{snapshot_id}"
    credential, service = _clients()
    try:
        container = service.get_container_client(CONTAINER)
        manifest_blob = container.get_blob_client(f"{prefix}/checkpoint-manifest.json")
        manifest = json.loads(manifest_blob.download_blob().readall())
        if (
            manifest.get("schema_version") != 1
            or manifest.get("kind") != "national_algdata_checkpoint_snapshot"
            or manifest.get("production_write") is not False
            or manifest.get("collection_id") != collection_id
            or manifest.get("snapshot_id") != snapshot_id
        ):
            raise RuntimeError("Azure checkpoint manifest provenance/schema validation failed")
        files = manifest.get("files")
        if not isinstance(files, list) or not files:
            raise RuntimeError("Azure checkpoint manifest has no files")
        output_dir = output_dir.resolve()
        if output_dir.exists() and any(output_dir.iterdir()):
            raise RuntimeError(f"Refusing to overwrite non-empty restore directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        restored = []
        for item in files:
            relative = _safe_relative_path(str(item["path"]))
            target = output_dir.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            blob = container.get_blob_client(f"{prefix}/files/{relative}")
            with target.open("wb") as stream:
                downloader = blob.download_blob()
                for chunk in downloader.chunks():
                    stream.write(chunk)
            digest, size = sha256_file(target)
            if digest != item.get("sha256") or size != int(item.get("bytes", -1)):
                raise RuntimeError(f"Restored file failed SHA-256/size verification: {relative}")
            restored.append({"path": relative, "sha256": digest, "bytes": size})
        return {
            "status": "restored_and_verified",
            "container": CONTAINER,
            "prefix": prefix,
            "file_count": len(restored),
            "files": restored,
            "production_write": False,
        }
    finally:
        service.close()
        credential.close()


def create_synthetic_fixture(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "checkpoint.json").write_text(
        json.dumps({
            "schema_version": 1,
            "kind": "synthetic_national_algdata_checkpoint",
            "production_write": False,
            "note": "Synthetic test data only; no portal data.",
            "areas": [{"area_portal_id": "SYNTHETIC-001", "status": "success"}],
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (path / "areas" / "SYNTHETIC-001").mkdir(parents=True, exist_ok=True)
    (path / "areas" / "SYNTHETIC-001" / "export.csv").write_text(
        "area_portal_id,year,harvest_count\nSYNTHETIC-001,2026,7\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("smoke-write")
    write.add_argument("--collection-id", required=True)
    write.add_argument("--snapshot-id", required=True)
    restore = sub.add_parser("smoke-restore")
    restore.add_argument("--collection-id", required=True)
    restore.add_argument("--snapshot-id", required=True)
    restore.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "smoke-write":
        with tempfile.TemporaryDirectory(prefix="algdata-synthetic-") as temp:
            fixture = Path(temp) / "fixture"
            create_synthetic_fixture(fixture)
            result = publish_snapshot(fixture, args.collection_id, args.snapshot_id)
    else:
        result = restore_snapshot(args.collection_id, args.snapshot_id, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
