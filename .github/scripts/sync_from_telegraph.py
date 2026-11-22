#!/usr/bin/env python3
"""Pull latest.json and signed status.json from Telegraph into this repo."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_HEX = (ROOT / "ed25519_public.hex").read_text(encoding="utf-8").strip()

STATUS_PAGE = "https://api.telegra.ph/getPage/pleer-status-11-22?return_content=true"
LATEST_PAGE = "https://api.telegra.ph/getPage/pleer-latest-11-22?return_content=true"

# The script is vendored into the public repo without the rest of pleer-bot,
# so signature verification is duplicated here in a small form.
import base64

# cryptography is installed in the workflow.
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "pleer-status-sync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_json(payload: dict) -> dict:
    if not payload.get("ok"):
        raise SystemExit(f"telegraph not ok: {payload}")
    texts: list[str] = []

    def walk(node):
        if isinstance(node, str):
            texts.append(node)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, dict):
            for child in node.get("children") or []:
                walk(child)

    walk((payload.get("result") or {}).get("content") or [])
    for text in texts:
        stripped = text.strip()
        if stripped.startswith("{"):
            return json.loads(stripped)
    raise SystemExit("no JSON object in telegraph page")


def b64url_decode(text: str) -> bytes:
    padded = text + ("=" * ((4 - len(text) % 4) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def verify_status(doc: dict) -> bool:
    try:
        if int(doc.get("v")) != 1:
            return False
        generated_at = int(doc["generated_at"])
        installs = doc.get("installs") or {}
        lines = ["PLEER-STATUS-v1", str(generated_at)]
        for digest in sorted(installs):
            entry = installs[digest]
            lines.append(f"{digest}:{entry['status']}:{int(entry['expires_at'])}")
        preimage = ("\n".join(lines) + "\n").encode("utf-8")
        sig = b64url_decode(str(doc["sig"]))
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_HEX)).verify(sig, preimage)
        return True
    except Exception as exc:
        print("status verify failed:", exc, file=sys.stderr)
        return False


def write_pretty(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    status = extract_json(fetch(STATUS_PAGE))
    if not verify_status(status):
        raise SystemExit("refusing to commit a status.json that does not verify")
    latest = extract_json(fetch(LATEST_PAGE))
    for field in ("versionName", "versionCode", "notes", "url"):
        if field not in latest:
            raise SystemExit(f"latest.json missing {field}")
    write_pretty(ROOT / "status.json", status)
    write_pretty(ROOT / "latest.json", latest)
    print(
        "synced status generated_at=",
        status.get("generated_at"),
        "installs=",
        len(status.get("installs") or {}),
        "latest=",
        latest.get("versionName"),
        latest.get("versionCode"),
    )


if __name__ == "__main__":
    main()
