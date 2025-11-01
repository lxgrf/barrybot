"""GitHub App integration helpers."""

from __future__ import annotations

import base64
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional, Sequence

import requests

logger = logging.getLogger(__name__)

_GITHUB_API_DEFAULT = "https://api.github.com"


class GitHubAppError(RuntimeError):
    """Raised when GitHub App configuration or API calls fail."""


@dataclass
class GitHubAppConfig:
    """Configuration options for authenticating as a GitHub App."""

    app_id: int
    private_key: str
    api_base: str = _GITHUB_API_DEFAULT


class GitHubAppClient:
    """Small helper client for working with the GitHub App REST API."""

    _token_cache: Dict[int, Dict[str, object]]

    def __init__(self, config: GitHubAppConfig, session: Optional[requests.Session] = None) -> None:
        self.config = config
        self._session = session or requests.Session()
        self._token_cache = {}

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------
    def _create_jwt(self) -> str:
        import jwt  # imported lazily to keep module-level imports lightweight

        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": int(self.config.app_id),
        }
        token = jwt.encode(payload, self.config.private_key, algorithm="RS256")
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        return token

    def _request_as_app(self, method: str, path: str, **kwargs):
        jwt_token = self._create_jwt()
        headers = kwargs.pop("headers", {})
        headers.update(
            {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            }
        )
        url = f"{self.config.api_base}{path}"
        response = self._session.request(method, url, headers=headers, timeout=kwargs.pop("timeout", 10), **kwargs)
        if not response.ok:
            raise GitHubAppError(f"GitHub API responded with {response.status_code}: {response.text}")
        return response

    def get_installation_id(self, repo_full_name: str) -> int:
        """Return the installation id for the configured app on the repository."""

        response = self._request_as_app("GET", f"/repos/{repo_full_name}/installation")
        data = response.json()
        installation_id = data.get("id")
        if installation_id is None:
            raise GitHubAppError("Installation ID missing from GitHub response")
        return int(installation_id)

    def _create_installation_access_token(self, installation_id: int) -> Dict[str, object]:
        response = self._request_as_app("POST", f"/app/installations/{installation_id}/access_tokens")
        data = response.json()
        token = data.get("token")
        expires_at = data.get("expires_at")
        if not token or not expires_at:
            raise GitHubAppError("GitHub failed to return installation token")
        return {"token": token, "expires_at": expires_at}

    def get_installation_token(self, repo_full_name: str) -> str:
        """Return a cached installation token for the repository."""

        installation_id = self.get_installation_id(repo_full_name)
        cached = self._token_cache.get(installation_id)
        now = int(time.time())
        if cached and now < int(cached.get("expires_epoch", 0)) - 30:
            return str(cached["token"])

        token_data = self._create_installation_access_token(installation_id)
        expires_at_str = str(token_data["expires_at"])
        expires_dt = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        expires_epoch = int(expires_dt.timestamp())
        self._token_cache[installation_id] = {
            "token": token_data["token"],
            "expires_epoch": expires_epoch,
        }
        return str(token_data["token"])

    # ------------------------------------------------------------------
    # Convenience wrappers for issue creation
    # ------------------------------------------------------------------
    def _request_as_installation(self, method: str, repo_full_name: str, path: str, **kwargs):
        access_token = self.get_installation_token(repo_full_name)
        headers = kwargs.pop("headers", {})
        headers.update(
            {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github+json",
            }
        )
        url = f"{self.config.api_base}{path}"
        response = self._session.request(method, url, headers=headers, timeout=kwargs.pop("timeout", 10), **kwargs)
        if not response.ok:
            raise GitHubAppError(f"GitHub API responded with {response.status_code}: {response.text}")
        return response

    def list_labels(self, repo_full_name: str) -> Sequence[str]:
        response = self._request_as_installation("GET", repo_full_name, f"/repos/{repo_full_name}/labels")
        return [label["name"] for label in response.json()]

    def list_assignees(self, repo_full_name: str) -> Sequence[str]:
        response = self._request_as_installation("GET", repo_full_name, f"/repos/{repo_full_name}/assignees")
        return [user["login"] for user in response.json()]

    def create_issue(
        self,
        repo_full_name: str,
        title: str,
        body: str,
        labels: Optional[Iterable[str]] = None,
        assignees: Optional[Iterable[str]] = None,
    ) -> Dict[str, object]:
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = list(labels)
        if assignees:
            payload["assignees"] = list(assignees)

        response = self._request_as_installation(
            "POST",
            repo_full_name,
            f"/repos/{repo_full_name}/issues",
            json=payload,
        )
        return response.json()


# ----------------------------------------------------------------------
# Configuration helpers
# ----------------------------------------------------------------------

def load_private_key_from_env() -> str:
    path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
    pem = os.getenv("GITHUB_PRIVATE_KEY_PEM")
    b64 = os.getenv("GITHUB_PRIVATE_KEY_B64")

    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    if pem:
        return pem
    if b64:
        try:
            return base64.b64decode(b64).decode("utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            raise GitHubAppError("GITHUB_PRIVATE_KEY_B64 is not valid base64") from exc

    raise GitHubAppError(
        "GitHub App private key not found. Set one of GITHUB_PRIVATE_KEY_PATH, "
        "GITHUB_PRIVATE_KEY_PEM, or GITHUB_PRIVATE_KEY_B64."
    )


def build_github_app_client_from_env(api_base: Optional[str] = None) -> GitHubAppClient:
    app_id_raw = os.getenv("GITHUB_APP_ID")
    if not app_id_raw:
        raise GitHubAppError("GITHUB_APP_ID environment variable not set")

    try:
        app_id = int(app_id_raw)
    except ValueError as exc:
        raise GitHubAppError("GITHUB_APP_ID must be an integer") from exc

    private_key = load_private_key_from_env()
    config = GitHubAppConfig(app_id=app_id, private_key=private_key, api_base=api_base or _GITHUB_API_DEFAULT)
    return GitHubAppClient(config)
