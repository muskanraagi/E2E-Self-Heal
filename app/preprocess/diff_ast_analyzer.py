"""Diff-JSX AST Analyzer: turn a git diff into before/after DOM node trees.

v0.1 uses a lightweight regex heuristic over changed JSX/TSX hunks to stay
dependency-free. Upgrade path: parse with tree-sitter (tree-sitter-typescript) for
robust element/attribute extraction — track as a v0.2 refinement.
"""

import re

import structlog

from app.schemas import DomDiff

logger = structlog.get_logger(__name__)

_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_JSX_TAG_RE = re.compile(
    r"<([A-Za-z][\w.]*)((?:\s+[\w-]+=(?:\"[^\"]*\"|'[^']*'|\{[^}]*\}))*)\s*/?>"
)
_ATTR_RE = re.compile(r"([\w-]+)=(?:\"([^\"]*)\"|'([^']*)'|\{([^}]*)\})")
_JSX_SUFFIXES = (".tsx", ".jsx")


def _parse_element(line: str) -> dict | None:
    """Parse the first JSX element on a line into ``{"tag", "attributes"}``."""
    tag_match = _JSX_TAG_RE.search(line)
    if not tag_match:
        return None
    attrs: dict[str, str] = {}
    for attr_match in _ATTR_RE.finditer(tag_match.group(2)):
        name = attr_match.group(1)
        value = attr_match.group(2) or attr_match.group(3) or attr_match.group(4) or ""
        attrs[name] = value
    return {"tag": tag_match.group(1), "attributes": attrs}


def analyze_diff(git_diff: str | None) -> list[DomDiff]:
    """Parse the JSX/TSX regions of a git diff into lightweight DOM diffs.

    Pairs removed (``-``) and added (``+``) element lines within each file by order —
    a best-effort mapping sufficient for the Diagnoser to correlate a broken selector
    with the attribute that changed. Each added element carries its 1-based new-file line
    (tracked from ``@@`` hunk headers) so review mode can anchor an inline PR comment.
    """
    if not git_diff:
        return []

    diffs: list[DomDiff] = []
    current_file = ""
    new_line = 0
    removed: list[dict] = []
    added: list[tuple[dict, int]] = []

    def flush(file: str) -> None:
        for previous, (current, line) in zip(removed, added):
            diffs.append(DomDiff(file=file, line=line, previous=previous, current=current))
        removed.clear()
        added.clear()

    for line in git_diff.splitlines():
        file_match = _FILE_RE.match(line)
        if file_match:
            flush(current_file)
            current_file = file_match.group(1)
            continue
        if not current_file.endswith(_JSX_SUFFIXES):
            continue
        hunk_match = _HUNK_RE.match(line)
        if hunk_match:
            new_line = int(hunk_match.group(1))
            continue
        if line.startswith("-") and not line.startswith("---"):
            element = _parse_element(line[1:])
            if element:
                removed.append(element)
            continue  # removed lines exist only in the old file — new-file line unchanged
        if line.startswith("+") and not line.startswith("+++"):
            element = _parse_element(line[1:])
            if element:
                added.append((element, new_line))
            new_line += 1
            continue
        new_line += 1  # unchanged context line advances the new-file counter
    flush(current_file)

    logger.debug("diff_analyzed", dom_changes=len(diffs))
    return diffs
