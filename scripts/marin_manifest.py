#!/usr/bin/env python3
"""Edit one scalar in the standard MarinOS manifest without serializing its YAML.

This is deliberately NOT a general YAML parser. Accept single-document block
mappings with simple keys and single-line scalar values. Refuse advanced YAML
(flow collections, sequences, block/multiline scalars, aliases, anchors, tags,
merge keys, and directives) instead of guessing which text owns platform.shell.
No dependency on PyYAML/yq, and no YAML constructors are executed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import re

from assets import AssetError, require

NUMBER = r"(?:0|[1-9][0-9]*)"
IDENTIFIER = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION = re.compile(
    rf"{NUMBER}\.{NUMBER}\.{NUMBER}"
    rf"(?:-{IDENTIFIER}(?:\.{IDENTIFIER})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
KEY = r"[A-Za-z_][A-Za-z0-9_-]*"
ENTRY = re.compile(rf"(?P<spaces> *)(?P<key>{KEY}|'(?:{KEY})'|\"(?:{KEY})\"):(?P<tail>.*)")


@dataclass(frozen=True)
class Manifest:
    text: str
    bom: bytes
    version: str
    start: int
    end: int

    def updated(self, version: str) -> bytes:
        require(VERSION.fullmatch(version) is not None, "Invalid target shell version")
        return self.bom + (self.text[:self.start] + version + self.text[self.end:]).encode("utf-8")


@dataclass
class Mapping:
    indent: int
    path: tuple[str, ...]
    keys: set[str] = field(default_factory=set)


def scalar(tail: str, line: int) -> tuple[str | None, int, int]:
    """Return the scalar token and its content span within tail, without quotes."""
    require(not tail or tail[0] in " \t", f"marin.yml line {line}: expected whitespace after ':'")
    value = tail.lstrip(" \t")
    start = len(tail) - len(value)
    if not value or value.startswith("#"):
        return None, start, start
    if value[0] in "'\"":
        pattern = r"'(?:[^']|'')*'" if value[0] == "'" else r'"(?:[^"\\]|\\.)*"'
        match = re.match(pattern, value)
        require(match is not None, f"marin.yml line {line}: multiline or invalid quoted scalar")
        token = match[0]
        remainder = value[len(token):]
        require(re.fullmatch(r"[ \t]*(?:#.*)?", remainder) is not None
                and (not remainder or remainder[0] in " \t"),
                f"marin.yml line {line}: unsupported text after quoted scalar")
        if token[0] == '"':
            try:
                json.loads(token)
            except ValueError as exc:
                raise AssetError(f"marin.yml line {line}: unsupported quoted escape") from exc
        return token[1:-1], start + 1, start + len(token) - 1
    require(value[0] not in "!&*|>{}[]%@`" and not re.match(r"[-?:](?:\s|$)", value),
            f"marin.yml line {line}: advanced YAML is not supported; no files changed")
    token = re.split(r"[ \t]+#", value, maxsplit=1)[0].rstrip(" \t")
    require(re.search(r":(?:[ \t]|$)", token) is None,
            f"marin.yml line {line}: unexpected mapping inside a scalar")
    return token, start, start + len(token)


def parse_manifest(data: bytes) -> Manifest:
    """Locate exactly one direct platform.shell, preserving all other bytes."""
    require(len(data) <= 1024 * 1024, "marin.yml exceeds the 1 MiB safety limit")
    bom = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    try:
        text = data[len(bom):].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AssetError("marin.yml must be UTF-8") from exc
    require(not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x85\u2028\u2029]", text),
            "marin.yml contains unsupported control characters or line separators")
    frames = [Mapping(0, ())]
    pending: tuple[str, ...] | None = None
    values: dict[tuple[str, ...], tuple[str | None, int, int]] = {}
    offset = 0
    document_started = document_ended = content_seen = False
    for line_number, raw in enumerate(text.splitlines(keepends=True), start=1):
        line = raw.removesuffix("\n").removesuffix("\r")
        require("\r" not in line, f"marin.yml line {line_number}: unsupported line ending")
        if not line.strip() or line.lstrip().startswith("#"):
            offset += len(raw)
            continue
        require(not document_ended, "marin.yml: multiple YAML documents are not supported")
        if re.fullmatch(r"---[ \t]*(?:#.*)?", line):
            require(not document_started and not content_seen,
                    "marin.yml: multiple YAML documents are not supported")
            document_started = True
            offset += len(raw)
            continue
        if re.fullmatch(r"\.\.\.[ \t]*(?:#.*)?", line):
            require(content_seen, "marin.yml: empty YAML document")
            document_ended = True
            offset += len(raw)
            continue
        match = ENTRY.fullmatch(line)
        require(match is not None, f"marin.yml line {line_number}: expected a simple block-mapping entry")
        indent = len(match["spaces"])
        if indent > frames[-1].indent:
            require(pending is not None, f"marin.yml line {line_number}: unexpected indentation")
            frames.append(Mapping(indent, pending))
        else:
            while indent < frames[-1].indent:
                frames.pop()
            require(indent == frames[-1].indent,
                    f"marin.yml line {line_number}: inconsistent indentation")
        key = match["key"].strip("'\"")
        frame = frames[-1]
        require(key not in frame.keys,
                f"marin.yml line {line_number}: duplicate key {'.'.join(frame.path + (key,))}")
        frame.keys.add(key)
        path = frame.path + (key,)
        value, first, last = scalar(match["tail"], line_number)
        values[path] = (value, offset + match.start("tail") + first,
                        offset + match.start("tail") + last)
        pending = path if value is None else None
        offset += len(raw)
        content_seen = True
    require(("platform",) in values and values[("platform",)][0] is None,
            "marin.yml must contain one platform block mapping")
    require(("platform", "shell") in values,
            "marin.yml does not declare platform.shell. Complete the app-shell refactor first; "
            "the installer will not convert a legacy app")
    version, first, last = values[("platform", "shell")]
    require(version is not None and VERSION.fullmatch(version) is not None,
            "marin.yml platform.shell must be a single-line semantic version, such as 1.0.1")
    return Manifest(text, bom, version, first, last)
