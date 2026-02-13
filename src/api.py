"""
BF6 (Battlefield 6) API client for GameTools.Network.

Base URL: https://api.gametools.network
No API key required. Uses rate limiting and retries.
"""

import time

import requests

BASE_URL = "https://api.gametools.network"
DEFAULT_RATE_LIMIT_SEC = 1.0
MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 1.0


class BF6APIError(Exception):
    """Raised when the API returns an error or invalid response."""


class BF6APIClient:
    def __init__(
        self,
        base_url: str = BASE_URL,
        rate_limit_sec: float = DEFAULT_RATE_LIMIT_SEC,
        max_retries: int = MAX_RETRIES,
    ):
        self.base_url = base_url.rstrip("/")
        self.rate_limit_sec = rate_limit_sec
        self.max_retries = max_retries
        self._last_request_time: float = 0.0

    def _wait_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - elapsed)
        self._last_request_time = time.monotonic()

    def _sleep_or_raise(self, attempt: int, message: str) -> None:
        """On last attempt raise BF6APIError; otherwise sleep and continue."""
        if attempt == self.max_retries - 1:
            raise BF6APIError(message)
        time.sleep(RETRY_BACKOFF_SEC * (attempt + 1))

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict | list:
        url = f"{self.base_url}{path}"
        for attempt in range(self.max_retries):
            self._wait_rate_limit()
            try:
                if method.upper() == "GET":
                    r = requests.get(url, params=params, timeout=30)
                else:
                    r = requests.post(url, params=params, json=json, timeout=30)
            except requests.RequestException as e:
                self._sleep_or_raise(attempt, f"Request failed: {e}")
                continue

            if r.status_code >= 500:
                self._sleep_or_raise(
                    attempt,
                    f"Server error {r.status_code}: {r.text[:200]}",
                )
                continue

            if r.status_code >= 400:
                try:
                    err = r.json()
                    errors = err.get("errors", [r.text[:200]])
                except Exception:
                    errors = [r.text[:200]]
                raise BF6APIError(f"API error {r.status_code}: {errors}")

            try:
                return r.json()
            except Exception as e:
                raise BF6APIError(f"Invalid JSON response: {e}") from e

        raise BF6APIError("Max retries exceeded")

    def get_player_id(self, name: str, platform: str = "pc") -> dict:
        """
        Resolve player ID from name and platform.
        Returns dict with at least 'id' and optionally 'userName'.
        """
        path = "/bf6/player/"
        params = {"name": name, "platform": platform}
        data = self._request("GET", path, params=params)
        if isinstance(data, dict) and "id" in data:
            return data
        if isinstance(data, list) and data:
            return data[0] if isinstance(data[0], dict) else {"id": data[0]}
        raise BF6APIError(f"Could not resolve player: {name} on {platform}")

    def get_stats(
        self,
        name: str | None = None,
        player_id: str | int | None = None,
        platform: str = "pc",
    ) -> dict:
        """
        Get full stats for one player. Provide either name or player_id.
        """
        path = "/bf6/stats/"
        params: dict = {"platform": platform}
        if player_id is not None:
            params["playerid"] = str(player_id)
        elif name:
            params["name"] = name
        else:
            raise ValueError("Provide either name or player_id")
        return self._request("GET", path, params=params)  # type: ignore[return-value]

    def get_stats_batch(
        self, player_ids: list[str | int], platform: str = "pc"
    ) -> list[dict]:
        """
        Get stats for up to 128 players in one request.
        player_ids: list of numeric player IDs (as int or string).
        """
        if not player_ids:
            return []
        if len(player_ids) > 128:
            raise ValueError("Maximum 128 players per batch")
        path = "/bf6/multiple/"
        body = {
            "playerIds": [str(pid) for pid in player_ids],
            "platform": platform,
        }
        data = self._request("POST", path, json=body)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return [data] if isinstance(data, dict) else []
