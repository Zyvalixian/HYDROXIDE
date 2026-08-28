#!/usr/bin/env python3

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


API_URL = "https://stella.heroinhound.cc/api/moderators"
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "moderators.json"
CHANGES_PATH = ROOT / "data" / "moderator_changes.json"


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_ids(values):
    result = set()
    for value in values or []:
        try:
            user_id = int(value)
        except (TypeError, ValueError):
            continue
        if user_id > 0:
            result.add(user_id)
    return sorted(result)


def set_output(name, value):
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"{name}={value}\n")


def add_summary(lines):
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("\n".join(lines) + "\n")


def format_ids(title, values, limit=100):
    if not values:
        return [f"### {title}", "None"]
    shown = values[:limit]
    lines = [f"### {title} ({len(values)})", "```text"]
    lines.extend(str(value) for value in shown)
    if len(values) > limit:
        lines.append(f"... and {len(values) - limit} more")
    lines.append("```")
    return lines


def finish_unchanged(reason, count):
    print(reason)
    set_output("changed", "false")
    set_output("added", 0)
    set_output("removed", 0)
    add_summary(["## Stella moderator sync", reason, f"Current count: {count}"])


def main():
    token = os.getenv("STELLA_TOKEN", "").strip()
    if not token:
        raise RuntimeError("STELLA_TOKEN secret is not configured")

    old_snapshot = load_json(SNAPSHOT_PATH)
    old_ids = normalize_ids(old_snapshot.get("moderators"))
    old_etag = str(old_snapshot.get("source_etag") or "").strip()

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "Salenware-HYDROXIDE-Moderator-Sync/1.0",
    }
    if old_etag:
        headers["If-None-Match"] = old_etag

    request = urllib.request.Request(API_URL, headers=headers, method="GET")

    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as error:
        if error.code == 304:
            finish_unchanged("Stella returned 304: moderator list is unchanged.", len(old_ids))
            return
        body = error.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"Stella returned HTTP {error.code}: {body}") from error

    with response:
        body = response.read()
        response_etag = response.headers.get("ETag")

    data = json.loads(body)
    if data.get("ok") is not True or not isinstance(data.get("moderators"), list):
        raise RuntimeError("Stella returned an invalid moderator response")

    new_ids = normalize_ids(data["moderators"])
    declared_count = data.get("count")
    if declared_count is not None and int(declared_count) != len(new_ids):
        raise RuntimeError(
            f"Stella count mismatch: declared {declared_count}, decoded {len(new_ids)}"
        )
    if len(new_ids) < 100:
        raise RuntimeError(f"Refusing suspiciously small moderator list: {len(new_ids)}")

    source_version = str(data.get("version") or "").strip()
    source_etag = response_etag or (f'"{source_version}"' if source_version else "")
    added = sorted(set(new_ids) - set(old_ids))
    removed = sorted(set(old_ids) - set(new_ids))
    metadata_changed = (
        source_version != str(old_snapshot.get("source_version") or "")
        or source_etag != old_etag
    )

    if not added and not removed and not metadata_changed:
        finish_unchanged("Stella returned 200, but the snapshot is unchanged.", len(new_ids))
        return

    updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    write_json(
        SNAPSHOT_PATH,
        {
            "schema": 1,
            "source": "stella",
            "source_version": source_version,
            "source_etag": source_etag,
            "updated_at": updated_at,
            "count": len(new_ids),
            "moderators": new_ids,
        },
    )

    if added or removed:
        write_json(
            CHANGES_PATH,
            {
                "updated_at": updated_at,
                "source_version": source_version,
                "added": added,
                "removed": removed,
            },
        )

    print(f"Updated moderator snapshot: +{len(added)} -{len(removed)}")
    set_output("changed", "true")
    set_output("added", len(added))
    set_output("removed", len(removed))
    add_summary(
        [
            "## Stella moderator sync",
            f"Snapshot count: {len(new_ids)}",
            f"Source version: `{source_version or 'unknown'}`",
            *format_ids("Added", added),
            *format_ids("Removed", removed),
        ]
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Moderator sync failed: {error}", file=sys.stderr)
        add_summary(["## Stella moderator sync failed", f"`{error}`"])
        raise
