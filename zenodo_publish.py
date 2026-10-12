#!/usr/bin/env python3
"""Publish a Markdown paper and PDF to Zenodo."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path


RECORD_MARKER = "<!-- zenodo-record:"
FREE_TO_READ_LICENSE = "zenodo-freetoread-1.0"


def parse_paper(
    path: Path,
    orcid: str,
    copyright_holder: str,
    publication_type: str,
) -> dict:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    author_match = re.search(r"^\*\*(.+)\*\*$", text, re.MULTILINE)
    abstract_match = re.search(
        r"^## Abstract\s*\n+(.+?)\n+\*\*Keywords:\*\*\s*(.+?)\s*\n",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if text.startswith("---\n"):
        header = text.split("\n---", 1)[0]
        def field(name):
            match = re.search(r"^" + name + r":\s*(.+)$", header, re.MULTILINE)
            if not match:
                raise ValueError("missing frontmatter field: " + name)
            value = match.group(1).strip()
            return json.loads(value) if value.startswith('"') else value.strip("'")
        title = field("title")
        author = field("author")
        block = re.search(r"^abstract: \|\n((?:[ \t].*\n|\n)+)", header + "\n", re.MULTILINE)
        if not block:
            raise ValueError("missing abstract block")
        content = "\n".join(line[2:] if line.startswith("  ") else line for line in block.group(1).splitlines())
        abstract_match = re.search(r"(.+?)\n+\*\*Keywords:\*\*\s*(.+)", content, re.DOTALL)
    else:
        if not (title_match and author_match):
            raise ValueError("source must contain title and author")
        title = title_match.group(1).strip()
        author = author_match.group(1).strip()
    if not abstract_match:
        raise ValueError("source must contain an abstract and Keywords line")
    if not re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", orcid):
        raise ValueError("ORCID must use the 0000-0000-0000-0000 form")

    abstract = " ".join(
        line.strip() for line in abstract_match.group(1).splitlines() if line.strip()
    )
    keywords = [
        item.strip() for item in abstract_match.group(2).split(",") if item.strip()
    ]
    if not abstract or not keywords:
        raise ValueError("abstract and keywords must not be empty")

    family, separator, given = author.rpartition(" ")
    creator_name = f"{given}, {family}" if separator else author
    year = date.today().year
    return {
        "upload_type": "publication",
        "publication_type": publication_type,
        "title": title,
        "creators": [{"name": creator_name, "orcid": orcid}],
        "description": (
            f"<p>{abstract}</p>"
            f"<p>Copyright © {year} {copyright_holder}. All rights reserved.</p>"
        ),
        "keywords": keywords,
        "access_right": "open",
        "license": FREE_TO_READ_LICENSE,
        "prereserve_doi": True,
    }


def request_json(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Zenodo API returned HTTP {error.code}: {detail}") from error


def upload_file(bucket_url: str, file_path: Path, token: str) -> None:
    request = urllib.request.Request(
        f"{bucket_url}/{urllib.parse.quote(file_path.name)}",
        data=file_path.read_bytes(),
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            if response.status not in (200, 201):
                raise RuntimeError(f"file upload returned HTTP {response.status}")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"file upload returned HTTP {error.code}: {detail}") from error


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--orcid", required=True)
    parser.add_argument("--copyright-holder", required=True)
    parser.add_argument("--publication-type", default="preprint")
    parser.add_argument("--release-body", default="")
    parser.add_argument("--api-root", default="https://zenodo.org/api")
    args = parser.parse_args()

    if RECORD_MARKER in args.release_body:
        raise RuntimeError("this GitHub release already has a Zenodo record marker")
    if not args.pdf.is_file():
        raise FileNotFoundError(args.pdf)
    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        raise RuntimeError("ZENODO_TOKEN is not configured")

    metadata = parse_paper(
        args.source, args.orcid, args.copyright_holder, args.publication_type
    )
    api_root = args.api_root.rstrip("/")
    deposit = request_json("POST", f"{api_root}/deposit/depositions", token, {})
    deposit_id = str(deposit["id"])
    deposit = request_json(
        "PUT",
        f"{api_root}/deposit/depositions/{deposit_id}",
        token,
        {"metadata": metadata},
    )
    upload_file(deposit["links"]["bucket"], args.pdf, token)
    published = request_json(
        "POST",
        f"{api_root}/deposit/depositions/{deposit_id}/actions/publish",
        token,
    )

    write_output("deposit_id", deposit_id)
    write_output("doi", published.get("doi", ""))
    write_output(
        "record_url",
        published.get("record_url")
        or published.get("links", {}).get("record_html", "")
        or f"https://zenodo.org/records/{deposit_id}",
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
