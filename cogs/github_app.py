import os
import time
import logging
from datetime import datetime, timezone

import jwt  # PyJWT
import requests
import base64

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
JWT_TTL_SECONDS = 600  # 10 minutes

# Simple in-memory cache: installation_id -> {token, expires_at (epoch)}
_token_cache = {}


def _load_private_key() -> str:
    """Load private key PEM either from path or raw env var."""
    path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
    pem = os.getenv("GITHUB_PRIVATE_KEY_PEM")
    b64 = os.getenv("GITHUB_PRIVATE_KEY_B64")
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    if pem:
        return pem
    if b64:
        # decode single-line base64-encoded PEM
        try:
            return base64.b64decode(b64).decode("utf-8")
        except Exception:
            raise RuntimeError("GITHUB_PRIVATE_KEY_B64 is not valid base64")
    raise RuntimeError("GitHub App private key not found: set GITHUB_PRIVATE_KEY_PATH or GITHUB_PRIVATE_KEY_PEM")


def _create_jwt(app_id: str, private_key_pem: str) -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + JWT_TTL_SECONDS,
        "iss": int(app_id),
    }
    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def _get_jwt(app_id: str) -> str:
    pk = _load_private_key()
    return _create_jwt(app_id, pk)


def get_installation_id_for_repo(repo_full_name: str) -> int:
    """Return installation id for a repo (owner/repo)."""
    app_id = os.getenv("GITHUB_APP_ID")
    if not app_id:
        raise RuntimeError("GITHUB_APP_ID environment variable not set")
    jwt_token = _get_jwt(app_id)
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"{GITHUB_API}/repos/{repo_full_name}/installation"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()["id"]


def _create_installation_access_token(installation_id: int) -> dict:
    app_id = os.getenv("GITHUB_APP_ID")
    if not app_id:
        raise RuntimeError("GITHUB_APP_ID environment variable not set")
    jwt_token = _get_jwt(app_id)
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"{GITHUB_API}/app/installations/{installation_id}/access_tokens"
    resp = requests.post(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_cached_installation_token(repo_full_name: str) -> str:
    """Get a valid installation token for the given repo (caches until expiry).

    Raises RuntimeError on configuration errors or requests exceptions.
    """
    # Resolve installation id (may raise)
    installation_id = None
    try:
        installation_id = get_installation_id_for_repo(repo_full_name)
    except Exception:
        logger.exception("Failed to fetch installation id for %s", repo_full_name)
        raise

    cache = _token_cache.get(installation_id)
    now = int(time.time())
    if cache and cache.get("token") and now < (cache.get("expires_at", 0) - 30):
        return cache["token"]

    data = _create_installation_access_token(installation_id)
    token = data.get("token")
    expires_at_raw = data.get("expires_at")
    if not token or not expires_at_raw:
        raise RuntimeError("Invalid token response from GitHub App API")

    # parse ISO8601 e.g. 2025-11-01T12:34:56Z
    expires_dt = datetime.strptime(expires_at_raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    expires_epoch = int(expires_dt.timestamp())
    _token_cache[installation_id] = {"token": token, "expires_at": expires_epoch}
    return token
