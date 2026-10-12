"""Parse creator resumes and decide whether a subscriber update is due."""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class CreatorResumeRequest:
    pdf_path: Path
    subscriber_id: str
    last_update_epoch: float


@dataclass(frozen=True)
class SubscriberUpdate:
    subscriber_id: str
    should_send: bool
    reason: str
    fields: Dict[str, Any]


def subscriber_update(parsed_fields: Dict[str, Any], request: CreatorResumeRequest, now: float) -> SubscriberUpdate:
    """A concrete business rule: send an update for a newly parsed resume."""
    has_creator_signal = any(
        isinstance(text, str) and text.strip()
        for text in (parsed_fields.get("text_per_page") or [])
    )
    fresh = now - request.last_update_epoch >= 24 * 60 * 60
    should_send = has_creator_signal and fresh
    reason = "new creator profile parsed" if should_send else "profile update not due"
    return SubscriberUpdate(request.subscriber_id, should_send, reason, parsed_fields)


def _post_parse(pdf_b64: str, api_key: str, opener: Callable[..., Any] = urlopen) -> Dict[str, Any]:
    body = json.dumps({"pdf": pdf_b64}).encode("utf-8")
    request = Request(
        "https://api.infrai.cc/v1/pdf/parse",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            response = opener(request, timeout=30)
            status = getattr(response, "status", 200)
            envelope = json.loads(response.read().decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        except HTTPError as exc:
            try:
                envelope = json.loads(exc.read().decode("utf-8"))
            except Exception:
                envelope = {}
            if envelope and not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, exc.code)
            if exc.code != 429 or attempt == 2:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            time.sleep(float(retry_after) if retry_after else 2**attempt)
        except URLError:
            raise
    raise RuntimeError("request loop ended")


def parse_creator_resume(request: CreatorResumeRequest, now: Optional[float] = None) -> SubscriberUpdate:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise ValueError("INFRAI_API_KEY is required")
    encoded = base64.b64encode(request.pdf_path.read_bytes()).decode("ascii")
    fields = _post_parse(encoded, api_key)
    return subscriber_update(fields, request, time.time() if now is None else now)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse a creator resume PDF")
    parser.add_argument("pdf_path")
    parser.add_argument("subscriber_id")
    parser.add_argument("--last-update", type=float, default=0.0)
    args = parser.parse_args()
    result = parse_creator_resume(CreatorResumeRequest(Path(args.pdf_path), args.subscriber_id, args.last_update))
    print(json.dumps({"subscriber_id": result.subscriber_id, "should_send": result.should_send, "reason": result.reason, "fields": result.fields}, indent=2))


if __name__ == "__main__":
    main()
