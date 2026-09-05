"""Evidence-bounded OpenAI labels for Herald Decoder knowledge-graph communities."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Callable

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None


PROMPT_VERSION = "community-label-v2-global"
INSTRUCTIONS = """You name communities in a quantum-error-correction research knowledge graph.

Return one concise, human-readable scholarly category name for each supplied community.
Use only the supplied evidence. The name must be a 2–5 word English noun phrase in Title Case, such as “Error-Correction Decoders” or “Symmetry-Enriched Topological Order”. Prefer the shared subject across members, not a repository slug, one paper title, author name, date, or a generic term such as “Research”, “Methods”, or “Quantum Physics”. Every label in the response must be distinct from the other labels. Do not add explanations; return only the requested JSON."""

SCHEMA = {
    "type": "json_schema",
    "name": "community_labels",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "labels": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "community_id": {"type": "integer"},
                        "label": {"type": "string", "minLength": 2, "maxLength": 64},
                    },
                    "required": ["community_id", "label"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["labels"],
        "additionalProperties": False,
    },
}

WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9+./'’–-]*")
GENERIC = frozenset({"methods", "physics", "project", "quantum physics", "research", "science"})
LOWERCASE_WORDS = frozenset({"and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "via", "with"})
ACRONYMS = frozenset({"AI", "BP", "ML", "MWPM", "QEC", "SU(2)", "U(1)"})


def _title_case(label: str) -> str:
    words = re.sub(r"\s+", " ", label).strip().split(" ")
    rendered = []
    for index, word in enumerate(words):
        if word.upper() in ACRONYMS:
            rendered.append(word.upper())
        elif index and word.casefold() in LOWERCASE_WORDS:
            rendered.append(word.casefold())
        else:
            rendered.append(word[:1].upper() + word[1:])
    return " ".join(rendered)


def normalize_community_label(label: str) -> str:
    """Apply the same display convention to local and model-generated labels."""
    return _title_case(label)


def _valid_label(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    label = _title_case(value.strip().strip(".\"'"))
    words = WORD.findall(label)
    if not 1 <= len(words) <= 6 or len(label) > 64 or "\n" in label:
        return None
    if label.casefold() in GENERIC:
        return None
    return label


def _shorten(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value if len(value) <= limit else f"{value[:limit - 1].rsplit(' ', 1)[0]}…"


def community_evidence(graph: dict[str, Any], pages: list[dict[str, Any]], community: dict[str, Any]) -> str:
    """Build a bounded, injection-resistant evidence packet from compiled Wiki records."""
    page_by_id = {page["id"]: page for page in pages}
    members = [node for node in graph["nodes"] if node["community"] == community["id"] and node["id"] in page_by_id]
    member_pages = [page_by_id[node["id"]] for node in members]
    topics = Counter(topic for page in member_pages for topic in page.get("topics", []))
    ranked = sorted(members, key=lambda node: (-node.get("weighted_degree", 0), node["label"].casefold()))
    lines = [
        f"<community id=\"{community['id']}\" member_count=\"{len(members)}\">",
        "Topics: " + ("; ".join(f"{topic} ({count})" for topic, count in topics.most_common()) or "none"),
        "Members:",
    ]
    for node in ranked[:16]:
        page = page_by_id[node["id"]]
        lines.append(
            f"- type={page.get('page_type', 'reference')}; title={_shorten(page.get('title', node['label']), 140)}; "
            f"summary={_shorten(page.get('preview', ''), 300) or 'none'}"
        )
    lines.append("</community>")
    return "\n".join(lines)[:14000]


def _load_cache(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {"version": 1, "entries": {}}
    return payload if isinstance(payload, dict) and isinstance(payload.get("entries"), dict) else {"version": 1, "entries": {}}


def _save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp") as handle:
        json.dump(cache, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _cache_key(model: str, evidence: str) -> str:
    return hashlib.sha256(f"{PROMPT_VERSION}\n{model}\n{evidence}".encode("utf-8")).hexdigest()


def _graph_evidence(graph: dict[str, Any], pages: list[dict[str, Any]]) -> str:
    """Give the model every community at once so labels are comparatively named."""
    communities = sorted(graph["communities"], key=lambda community: community["id"])
    return "\n\n".join(community_evidence(graph, pages, community) for community in communities)


def enrich_community_labels(
    graph: dict[str, Any], pages: list[dict[str, Any]], *, cache_path: Path,
    api_key: str, model: str, timeout_seconds: float = 20,
    client_factory: Callable[..., Any] | None = None,
) -> dict[str, int]:
    """Name the complete community set together; failure never disables the graph."""
    if not api_key:
        return {"cached": 0, "generated": 0, "fallback": len(graph["communities"])}
    cache = _load_cache(cache_path)
    evidence = _graph_evidence(graph, pages)
    key = _cache_key(model, evidence)
    expected = {community["id"]: community for community in graph["communities"]}
    cached_labels = cache["entries"].get(key, {}).get("labels", {})
    if isinstance(cached_labels, dict):
        validated = {community_id: _valid_label(cached_labels.get(str(community_id))) for community_id in expected}
        values = [label for label in validated.values() if label]
        if len(values) == len(expected) and len({label.casefold() for label in values}) == len(values):
            for community_id, label in validated.items():
                expected[community_id]["label"] = label
                expected[community_id]["label_source"] = "openai-cache"
            return {"cached": len(expected), "generated": 0, "fallback": 0}

    if client_factory is None:
        if OpenAI is None:
            return {"cached": 0, "generated": 0, "fallback": len(expected)}
        client_factory = OpenAI

    response = client_factory(api_key=api_key, timeout=timeout_seconds, max_retries=2).responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=evidence,
        text={"format": SCHEMA},
        max_output_tokens=max(600, len(expected) * 120),
        store=False,
    )
    payload = json.loads(response.output_text)
    labels: dict[int, str] = {}
    for item in payload.get("labels", []):
        if not isinstance(item, dict) or item.get("community_id") not in expected:
            continue
        label = _valid_label(item.get("label"))
        if not label or label.casefold() in {value.casefold() for value in labels.values()}:
            continue
        labels[item["community_id"]] = label
    for community_id, label in labels.items():
        expected[community_id]["label"] = label
        expected[community_id]["label_source"] = "openai"
    if len(labels) == len(expected):
        cache["entries"][key] = {
            "labels": {str(community_id): label for community_id, label in labels.items()},
            "model": model,
            "prompt_version": PROMPT_VERSION,
        }
        _save_cache(cache_path, cache)
    return {"cached": 0, "generated": len(labels), "fallback": len(expected) - len(labels)}
