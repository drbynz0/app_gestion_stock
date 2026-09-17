"""Supabase Storage adapter for product images.

The mobile client never receives Supabase credentials: it uploads its file to
our authenticated API and this module talks to Supabase with the service key.
"""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import httpx
from django.core.exceptions import ImproperlyConfigured


MAX_PRODUCT_IMAGE_SIZE = 8 * 1024 * 1024  # 8 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


def _settings() -> tuple[str, str, str]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images")
    if not url or not key:
        raise ImproperlyConfigured(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured on the backend."
        )
    return url, key, bucket


def upload_product_image(*, file, company_id: int, product_id: int) -> tuple[str, str]:
    """Upload one validated image and return ``(public_url, storage_path)``."""
    content_type = (file.content_type or "").lower().strip()
    if content_type == "image/jpg":
        content_type = "image/jpeg"
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Format d'image non pris en charge. Utilisez JPEG, PNG ou WebP.")
    if file.size > MAX_PRODUCT_IMAGE_SIZE:
        raise ValueError("L'image ne doit pas dépasser 8 Mo.")

    try:
        supabase_url, service_key, bucket = _settings()
        extension = Path(file.name or "image").suffix.lower() or ".jpg"
        path = f"companies/{company_id}/products/{product_id}/{uuid4().hex}{extension}"
        endpoint = f"{supabase_url}/storage/v1/object/{bucket}/{path}"
        response = httpx.post(
            endpoint,
            content=file.read(),
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
                "Content-Type": content_type,
                "x-upsert": "false",
            },
            timeout=15,
        )
        if response.status_code in (200, 201):
            return f"{supabase_url}/storage/v1/object/public/{bucket}/{path}", path
    except Exception as exc:
        pass

    # Fallback vers le stockage local Django en cas de défaillance Supabase
    from django.core.files.storage import default_storage
    extension = Path(file.name or "image").suffix.lower() or ".jpg"
    rel_path = f"products/{company_id}_{product_id}_{uuid4().hex[:8]}{extension}"
    file.seek(0)
    saved_path = default_storage.save(rel_path, file)
    url = default_storage.url(saved_path)
    return url, saved_path


def delete_product_image(storage_path: str | None) -> None:
    """Best-effort cleanup; a failed cleanup must not invalidate saved data."""
    if not storage_path:
        return
    try:
        supabase_url, service_key, bucket = _settings()
        httpx.delete(
            f"{supabase_url}/storage/v1/object/{bucket}/{storage_path}",
            headers={"Authorization": f"Bearer {service_key}", "apikey": service_key},
            timeout=15,
        )
    except Exception:
        pass
