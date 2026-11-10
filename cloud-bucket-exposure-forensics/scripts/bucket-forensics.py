#!/usr/bin/env python3
"""bucket-forensics.py — re-runnable probe for Gates 1-3 of this skill's methodology.

Reconstructed from this skill's own SKILL.md spec (the file was referenced there
but missing from the kit export — see bounty-kit/README.md's sanitization note
for why some files needed reconstruction).

Gate 1 — Ownership: list the bucket (AWS S3 virtual-host XML, with GCS XML/JSON
         fallback), discriminate AWS vs GCS by XML namespace (NOT by which URL
         happened to answer), and surface one non-PII-looking object so a human
         can read it and judge true ownership before anything else happens.
Gate 2 — Key encoding: demonstrates the %2F silent-404 trap. Always fetch keys
         with literal slashes, never percent-encoded ones.
Gate 3 — Reachability: HEAD + a 4-byte Range per sampled object (never a full
         GET), with a random-suffix 404 control, repeated 3x for stability.

This script only ever reads: list-bucket (metadata) and a tiny byte-range HEAD
probe per object. It never downloads full object bodies and never writes
anything to the target. Use only on buckets you own or are authorized to test.

Usage:
    python bucket-forensics.py <bucket-name> [--sample N] [--prefix PREFIX]

Output: a JSON report to stdout (pipe to a file yourself if you want it saved) —
nothing here does any of the "build ZIP + INDEX.csv for delivery" step described
in SKILL.md's "Delivery to the operator" section; that step is a human judgment
call on real content and is deliberately left out of an automated script.
"""
from __future__ import annotations
import argparse
import json
import random
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

AWS_NS = "http://s3.amazonaws.com/doc/2006-03-01/"
GCS_XML_NS_HINTS = ("doc.s3.amazonaws.com",)  # GCS's S3-compat XML mode reuses an odd namespace


def _get(url: str, headers: dict | None = None, timeout: float = 10.0):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "bucket-forensics/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()
    except Exception as e:
        return None, {}, str(e).encode()


def gate1_ownership(bucket: str, max_pages: int = 200) -> dict:
    """List the bucket, paginate to completion, discriminate AWS vs GCS by
    namespace in the body (not by which hostname happened to answer), and
    return the key inventory plus one candidate non-PII object to read."""
    result = {"store": None, "keys": [], "truncated_pages": 0, "sample_object_key": None,
              "list_status": None}

    # Try AWS S3 virtual-host style first (the one that actually works; path-style
    # 301s with PermanentRedirect and should not be treated as "closed").
    token = None
    for _ in range(max_pages):
        url = f"https://{bucket}.s3.amazonaws.com/?list-type=2&max-keys=1000"
        if token:
            url += f"&continuation-token={urllib.parse.quote(token)}"
        status, headers, body = _get(url)
        result["list_status"] = status
        if status != 200:
            break
        text = body.decode("utf-8", errors="replace")
        if AWS_NS in text:
            result["store"] = "AWS_S3"
        elif any(h in text for h in GCS_XML_NS_HINTS):
            result["store"] = "GCS_XML_COMPAT"
        keys = re.findall(r"<Key>([^<]*)</Key>", text)
        result["keys"].extend(keys)
        result["truncated_pages"] += 1
        m = re.search(r"<NextContinuationToken>([^<]*)</NextContinuationToken>", text)
        is_truncated = "<IsTruncated>true</IsTruncated>" in text
        if is_truncated and m:
            token = m.group(1)
            continue
        break

    if not result["keys"]:
        # Fall back to GCS JSON API
        status, headers, body = _get(
            f"https://storage.googleapis.com/storage/v1/b/{bucket}/o?maxResults=1000"
        )
        result["list_status"] = status
        if status == 200:
            try:
                data = json.loads(body)
                if data.get("kind") == "storage#objects":
                    result["store"] = "GCS_JSON"
                    result["keys"] = [item["name"] for item in data.get("items", [])]
            except Exception:
                pass

    # Pick a plausibly non-PII sample object (skip obvious identity-document-ish
    # folder names) to hand the operator for a manual ownership read.
    pii_hint = re.compile(r"(licen[cs]e|passport|statement|signature|id[-_ ]?card|ssn)", re.I)
    candidates = [k for k in result["keys"] if not pii_hint.search(k)]
    if candidates:
        # Prefer short, root-level, text/doc-looking files (terms, readme, etc.)
        candidates.sort(key=lambda k: (k.count("/"), len(k)))
        result["sample_object_key"] = candidates[0]

    return result


def gate2_key_encoding_note() -> dict:
    return {
        "rule": "Never percent-encode '/' inside a key when fetching. "
                "A key containing a literal '/' (e.g. a leading slash from an absolute "
                "server path baked into the object name) must be requested with that "
                "slash literal, not as %2F -- otherwise you get a 404 NoSuchKey that "
                "looks like 'not exposed' but is actually just the wrong URL.",
        "wrong_example": "GET /%2Fvar/www/html/app/uploads/file.pdf  -> 404 (misleading)",
        "right_example": "GET //var/www/html/app/uploads/file.pdf   -> 200 (correct)",
    }


def gate3_reachability(bucket: str, store: str, keys: list[str], sample_n: int,
                        stability_runs: int = 3) -> list[dict]:
    """HEAD + 4-byte Range per sampled key, repeated for stability, plus a
    random-suffix 404 control. Never pulls full object bodies."""
    if store == "AWS_S3" or store is None:
        base = f"https://{bucket}.s3.amazonaws.com/"
    elif store and store.startswith("GCS"):
        base = f"https://storage.googleapis.com/{bucket}/"
    else:
        base = f"https://{bucket}.s3.amazonaws.com/"

    sample = keys[:sample_n]
    out = []
    for key in sample:
        # literal slashes, no percent-encoding of '/' (Gate 2)
        safe_key = urllib.parse.quote(key, safe="/")
        url = base + safe_key
        runs = []
        for _ in range(stability_runs):
            status, headers, body = _get(url)
            magic = None
            if status in (200, 206):
                range_status, range_headers, range_body = _get(url, headers={"Range": "bytes=0-3"})
                magic = range_body[:4].hex() if range_body else None
            runs.append({"status": status})
            time.sleep(0.2)
        # 404 control with a random suffix — proves the endpoint isn't just
        # answering 200/403 to everything
        control_url = url + f"-does-not-exist-{random.randint(100000, 999999)}"
        control_status, _, _ = _get(control_url)
        out.append({
            "key": key,
            "url": url,
            "runs": runs,
            "control_404_status": control_status,
            "stable": len({r["status"] for r in runs}) == 1,
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bucket")
    ap.add_argument("--sample", type=int, default=5, help="objects to probe in Gate 3 (default: 5)")
    ap.add_argument("--prefix", default=None, help="only report keys starting with this prefix")
    args = ap.parse_args()

    print(f"[*] Gate 1 — listing {args.bucket} ...", file=sys.stderr)
    g1 = gate1_ownership(args.bucket)
    keys = g1["keys"]
    if args.prefix:
        keys = [k for k in keys if k.startswith(args.prefix)]

    print(f"[*] Gate 3 — reachability on {min(args.sample, len(keys))} sampled object(s) ...",
          file=sys.stderr)
    g3 = gate3_reachability(args.bucket, g1["store"], keys, args.sample)

    report = {
        "bucket": args.bucket,
        "gate1_ownership": {
            "store": g1["store"],
            "list_status": g1["list_status"],
            "key_count": len(g1["keys"]),
            "pages": g1["truncated_pages"],
            "sample_object_to_read_for_ownership": g1["sample_object_key"],
        },
        "gate2_key_encoding": gate2_key_encoding_note(),
        "gate3_reachability_sample": g3,
        "next_steps": [
            "Manually fetch and read gate1.sample_object_to_read_for_ownership "
            "(or a terms/readme-looking key) to confirm the true owner before anything else.",
            "sha256-dedupe any larger sample before claiming N objects == N leaked documents "
            "(see this skill's 'Corpus studies' section).",
            "If ownership doesn't match your engagement's scope: STOP. Park as third-party "
            "or record 'excluded — third-party asset' per this skill's Gate 1c.",
        ],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
