"""Local research control surface for the Herald Decoder project."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import mimetypes
import os
import re
import shlex
import tarfile
import sys
import tarfile
import logging
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import networkx as nx
import yaml
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(path, override=False):
        """Load simple .env assignments when python-dotenv is unavailable.

        The dashboard only needs ordinary environment variables.  Keeping this
        small fallback lets it use the validated Numba runtime without making
        the optional dotenv package part of the decoder runtime contract.
        """
        candidate = Path(path)
        if not candidate.is_file():
            return False
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            key, separator, value = line.partition("=")
            key = key.strip()
            if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                continue
            value = value.strip()
            if value[:1] in {"'", '"'}:
                try:
                    value = shlex.split(value, comments=True)[0]
                except (ValueError, IndexError):
                    continue
            else:
                value = value.split("#", 1)[0].rstrip()
            if override or key not in os.environ:
                os.environ[key] = value
        return True

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:  # Support both ``python dashboard/server.py`` and package-based tests.
    from dashboard.backend.community_naming import enrich_community_labels, normalize_community_label
    from dashboard.backend.search import UnifiedSearch, local_search, search_document
except ModuleNotFoundError:
    from backend.community_naming import enrich_community_labels, normalize_community_label
    from backend.search import UnifiedSearch, local_search, search_document

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
DASHBOARD = ROOT / "dashboard"
FRONTEND = DASHBOARD / "frontend"
LABS = ROOT / "labs"
REFERENCES = ROOT / "references"
WIKI = ROOT / "wiki"
DISCUSSION = ROOT / "discussion"
ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,100}$")
LAB_STAGES = ("active", "blocked", "complete")
WIKI_LINK = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")
OBSIDIAN_WIKI_LINK = re.compile(r"(?<!\\)\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
REFERENCE_LINK = re.compile(r"references/([^/]+)/paper\.pdf")
REFERENCE_ROUTE_LINK = re.compile(r"/reference\?id=([a-z0-9][a-z0-9-]{1,100})")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9+._-]*|[\u3400-\u9fff]+")
GRAPH_COLORS = ("#147d70", "#d27a35", "#536fb5", "#a3538f", "#6a8b3d", "#bd4a4a")
# A Lab artifact is edited independently of the dashboard process.  Retain a
# module only while its source file has the same version, otherwise a running
# dashboard can keep validating requests against a superseded control schema.
LAB_MODULES: dict[str, tuple[int, object]] = {}
COMMUNITY_LABEL_CACHE = ROOT / ".tmp" / "community-labels.json"
LOGGER = logging.getLogger(__name__)
UNIFIED_SEARCH = UnifiedSearch(ROOT)


def run_lab_function(lab_id: str, relative_module: str, function_name: str, payload: dict):
    """Load and call a Lab-owned function without placing research code here."""
    lab_folder = (LABS / valid_id(lab_id)).resolve()
    module_path = (lab_folder / relative_module).resolve()
    if not module_path.is_relative_to(lab_folder) or module_path.suffix != ".py" or not module_path.is_file():
        raise FileNotFoundError("Lab runtime module not found")
    cache_key = str(module_path)
    module_version = module_path.stat().st_mtime_ns
    cached = LAB_MODULES.get(cache_key)
    if cached is None or cached[0] != module_version:
        spec = importlib.util.spec_from_file_location(f"lab_runtime_{valid_id(lab_id).replace('-', '_')}", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load Lab runtime module")
        module = importlib.util.module_from_spec(spec)
        module_directory = str(module_path.parent)
        sys.path.insert(0, module_directory)
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(module_directory)
        LAB_MODULES[cache_key] = (module_version, module)
    function = getattr(LAB_MODULES[cache_key][1], function_name, None)
    if not callable(function):
        raise RuntimeError("Lab runtime function not found")
    return function(payload)


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_discussion_text(value: object) -> str:
    """Turn paste-escaped line breaks into actual Markdown line breaks."""
    return str(value).replace("\\r\\n", "\n").replace("\\n", "\n").strip()


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def valid_id(value: str) -> str:
    if not ID.fullmatch(value):
        raise ValueError("Invalid identifier")
    return value


def markdown_document(path: Path) -> dict:
    return {"path": str(path.relative_to(ROOT)), "content": path.read_text(encoding="utf-8") if path.exists() else ""}


def report_lint_errors(lab_id: str) -> list[str]:
    lint_path = ROOT / "skills" / "organize-lab" / "scripts" / "lab_report_lint.py"
    spec = importlib.util.spec_from_file_location("lab_report_lint", lint_path)
    if spec is None or spec.loader is None:
        raise ValueError("Lab report lint is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lint(LABS / lab_id)


def lab_catalog() -> list[dict]:
    """Return the lab index enriched from each lab's own metadata file.

    ``labs/labs.json`` is only the discoverable index.  Mutable lab state is
    canonical in ``<lab>/lab.json`` so reopening a lab cannot leave the
    homepage and the lab page disagreeing.
    """
    index = read_json(LABS / "labs.json", {"labs": []}).get("labs", [])
    catalog = []
    state_keys = ("stage", "current_focus", "next_action", "summary", "created", "updated", "parents")
    for entry in index:
        item = dict(entry)
        detail = read_json(LABS / str(item.get("id", "")) / "lab.json", {})
        for key in state_keys:
            if key in detail:
                item[key] = detail[key]
        # ``parents`` is the sole source of Lab lineage.  Roots deliberately
        # omit it from their metadata; clients receive an empty list instead.
        item.setdefault("parents", [])
        catalog.append(item)
    return catalog


def discussion_payload() -> dict:
    data = read_json(DISCUSSION / "threads.json", {"threads": []})
    threads = data.get("threads", [])
    threads.sort(key=lambda item: (item.get("status") != "open", item.get("updated", "")))
    return {"threads": threads}


def lab_payload(lab_id: str) -> dict:
    valid_id(lab_id)
    catalog = next((item for item in lab_catalog() if item["id"] == lab_id), None)
    if not catalog:
        raise FileNotFoundError("Lab not found")
    folder = LABS / lab_id
    detail = read_json(folder / "lab.json", {})
    evidence = [item for subdir in ("results", "figures") for item in (folder / subdir).rglob("*") if item.is_file() and item.name != "README.md"]
    outputs = []
    for item in detail.get("results", []):
        output_id = str(item.get("id", ""))
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,100}", output_id):
            continue
        # The Lab Results panel is a research-facing synthesis, not a file
        # browser.  Keep only renderable page results and explicitly promoted
        # summarized data; raw runs, selection manifests, and audits remain
        # provenance evidence under the Lab folder.
        presentation = str(item.get("presentation", "page"))
        if presentation not in {"page", "result"}:
            continue
        wiki_page = str(item.get("wiki_page", ""))
        if wiki_page:
            if not re.fullmatch(r"[a-z0-9][a-z0-9/-]{1,180}", wiki_page) or not (WIKI / f"{wiki_page}.md").is_file():
                continue
            outputs.append({
                "id": output_id, "kind": "wiki", "format": "wiki",
                "title": str(item.get("title", wiki_page.rsplit("/", 1)[-1])),
                "summary": str(item.get("summary", "")), "presentation": presentation,
                "wiki_page": wiki_page, "href": f"/wiki?page={wiki_page}",
            })
            continue
        relative = Path(str(item.get("path", "")))
        candidate = (folder / relative).resolve()
        if not candidate.is_relative_to(folder.resolve()) or not candidate.is_file():
            continue
        outputs.append({
            "id": output_id,
            "kind": str(item.get("kind", "artifact")),
            "format": str(item.get("format", "file")),
            "title": str(item.get("title", candidate.stem)),
            "summary": str(item.get("summary", "")),
            "presentation": presentation,
            "language": str(item.get("language", "")),
            "path": str(candidate.relative_to(ROOT)),
            "asset_path": str(candidate.relative_to(folder)),
            "size": candidate.stat().st_size,
        })
    threads = [thread for thread in discussion_payload()["threads"] if lab_id in thread.get("related_labs", [])]
    local_wiki = markdown_document(folder / "wiki" / "index.md") if (folder / "wiki" / "index.md").is_file() else None
    if local_wiki:
        outputs.insert(0, {"id": "local-wiki", "kind": "wiki", "format": "wiki", "title": "Local Wiki", "summary": "Navigable methods, evidence boundaries, and detailed research records for this Lab.", "presentation": "page", "href": f"/lab-wiki?lab={quote(lab_id)}"})
    return {"lab": catalog, "detail": detail, "plan": markdown_document(folder / "PLAN.md"), "report": markdown_document(folder / "REPORT.md"), "local_wiki": local_wiki, "evidence": [{"path": str(item.relative_to(ROOT)), "size": item.stat().st_size} for item in evidence], "outputs": outputs, "threads": threads}


def local_wiki_payload(lab_id: str, page_id: str = "index") -> dict:
    folder = LABS / valid_id(lab_id) / "wiki"
    if not re.fullmatch(r"[a-z0-9][a-z0-9/-]{0,180}", page_id):
        raise ValueError("Invalid Local Wiki page")
    pages = sorted(path.relative_to(folder).with_suffix("").as_posix() for path in folder.rglob("*.md"))
    candidate = (folder / f"{page_id}.md").resolve()
    if not candidate.is_relative_to(folder.resolve()) or not candidate.is_file():
        raise FileNotFoundError("Local Wiki page not found")
    text = candidate.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    metadata = yaml.safe_load(match.group(1)) if match else {}
    metadata = {key: str(value) for key, value in (metadata or {}).items()}
    return {"lab": lab_id, "pages": pages, "page": page_id, "metadata": metadata, **markdown_document(candidate)}


def reference_payload(reference_id: str) -> dict:
    valid_id(reference_id)
    records = read_json(REFERENCES / "references.json", {"references": []})["references"]
    record = next((item for item in records if item["id"] == reference_id), None)
    if not record:
        raise FileNotFoundError("Reference not found")
    folder = REFERENCES / reference_id
    related_wiki = []
    for page in wiki_pages():
        page_path = ROOT / page["path"]
        if reference_id in page_path.read_text(encoding="utf-8"):
            related_wiki.append(page)
    return {"reference": record, "provenance": read_json(folder / "provenance.json", {}), "has_pdf": (folder / "paper.pdf").is_file(), "has_source": any((folder / name).is_file() for name in ("source.tar", "source.tar.gz", "source.tgz")), "related_wiki": related_wiki}


def reference_archive(reference_id: str) -> Path:
    folder = REFERENCES / valid_id(reference_id)
    archive = next((folder / name for name in ("source.tar", "source.tar.gz", "source.tgz") if (folder / name).is_file()), None)
    if archive is None:
        raise FileNotFoundError("Local source archive not available")
    return archive


TEXT_EXTENSIONS = {".py", ".cc", ".cpp", ".c", ".h", ".hpp", ".js", ".ts", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".txt", ".md", ".rst", ".cmake", ".bazel", ".bzl", ".sh", ".gitignore", ".clang-format", ".flake8"}
CODE_EXTENSIONS = {".py", ".cc", ".cpp", ".c", ".h", ".hpp", ".js", ".ts", ".sh", ".cmake", ".bazel", ".bzl"}
PROJECT_DOCUMENT_EXTENSIONS = TEXT_EXTENSIONS | {".csv"}
PROJECT_DOCUMENT_ROOTS = {"labs", "wiki", "models"}


def project_document_path(raw_path: str) -> Path:
    """Resolve one safe, viewable project document without exposing ROOT."""
    relative = Path(unquote(raw_path))
    if not raw_path or relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Invalid project document path")
    if relative.parts[0] not in PROJECT_DOCUMENT_ROOTS or relative.suffix.lower() not in PROJECT_DOCUMENT_EXTENSIONS:
        raise FileNotFoundError("Project document is not available for viewing")
    candidate = (ROOT / relative).resolve()
    if not candidate.is_relative_to(ROOT.resolve()) or not candidate.is_file():
        raise FileNotFoundError("Project document not found")
    if candidate.stat().st_size > 2_000_000:
        raise ValueError("Project document is too large to preview")
    return candidate


def project_document_payload(raw_path: str) -> dict:
    candidate = project_document_path(raw_path)
    relative = candidate.relative_to(ROOT).as_posix()
    kind = "markdown" if candidate.suffix.lower() == ".md" else "code" if candidate.suffix.lower() in CODE_EXTENSIONS else "text"
    return {
        "path": relative,
        "kind": kind,
        "size": candidate.stat().st_size,
        "content": candidate.read_text(encoding="utf-8", errors="replace"),
    }


def project_document_href(relative_path: str, fragment: str = "") -> str:
    """Choose the human-facing viewer for a resolved project document path."""
    normalized = project_document_path(relative_path).relative_to(ROOT).as_posix()
    suffix = fragment if fragment.startswith("#") else ""
    if normalized.startswith("wiki/") and normalized.endswith(".md"):
        page_id = normalized.removeprefix("wiki/").removesuffix(".md")
        return f"/wiki?page={quote(page_id, safe='')}{suffix}"
    return f"/document?path={quote(normalized, safe='')}{suffix}"

def archive_kind(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf": return "pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}: return "image"
    if suffix in {".md", ".rst"}: return "markdown"
    if suffix in CODE_EXTENSIONS: return "code"
    if suffix in TEXT_EXTENSIONS or Path(path).name.startswith("."): return "text"
    return "binary"

def archive_members(reference_id: str) -> dict[str, tarfile.TarInfo]:
    with tarfile.open(reference_archive(reference_id), "r:*") as bundle:
        members = [item for item in bundle.getmembers() if item.isfile() and not Path(item.name).is_absolute() and ".." not in Path(item.name).parts]
        roots = {Path(item.name).parts[0] for item in members if Path(item.name).parts}
        prefix = next(iter(roots)) if len(roots) == 1 else ""
        return {str(Path(*Path(item.name).parts[1:]) if prefix else Path(item.name)): item for item in members if not prefix or len(Path(item.name).parts) > 1}

def archive_files(reference_id: str) -> list[dict]:
    return [{"path": path, "size": item.size, "kind": archive_kind(path)} for path, item in sorted(archive_members(reference_id).items())]


def archive_file_payload(reference_id: str, path: str, raw: bool = False):
    if not path or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("Invalid archive path")
    member = archive_members(reference_id).get(path)
    if member is None:
        raise FileNotFoundError("Source file unavailable for viewing")
    kind = archive_kind(path)
    with tarfile.open(reference_archive(reference_id), "r:*") as bundle:
        handle = bundle.extractfile(member)
        if handle is None:
            raise FileNotFoundError("Source file unavailable for viewing")
        body = handle.read()
    if raw: return path, body
    content = body.decode("utf-8", errors="replace") if kind in {"text", "code", "markdown"} and member.size <= 1_000_000 else ""
    return {"path": path, "size": member.size, "kind": kind, "content": content, "previewable": bool(content) or kind in {"pdf", "image"}}


def parse_frontmatter(content: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return {}
    metadata = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            continue
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            metadata[key.strip()] = [item.strip() for item in value[1:-1].split(",") if item.strip()]
        else:
            metadata[key.strip()] = value
    return metadata


def wiki_page_type(page_id: str) -> str:
    if page_id == "thesis":
        return "project"
    if page_id == "index":
        return "index"
    prefix = page_id.split("/", 1)[0]
    return {"concepts": "concept", "methods": "method", "models": "model", "implementations": "implementation", "papers": "reference", "references": "reference", "labs": "evidence"}.get(prefix, "note")


def wiki_pages() -> list[dict]:
    pages = []
    for file in sorted(WIKI.rglob("*.md")):
        if file.name in {"README.md", "SCHEMA.md", "log.md"}:
            continue
        content = file.read_text(encoding="utf-8")
        metadata = parse_frontmatter(content)
        page_id = str(file.relative_to(WIKI).with_suffix(""))
        title = next((line[2:].strip() for line in content.splitlines() if line.startswith("# ")), file.stem.replace("-", " ").title())
        body = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)
        blocks = [
            " ".join(line.strip() for line in block.splitlines()).strip()
            for block in re.split(r"\n\s*\n", body)
        ]
        preview = next(
            (block for block in blocks if block and not block.lstrip().startswith("#")),
            title,
        )
        links = []
        for target in WIKI_LINK.findall(content):
            candidate = (file.parent / target).resolve()
            if candidate.suffix != ".md":
                candidate = candidate.with_suffix(".md")
            if candidate.is_relative_to(WIKI.resolve()) and candidate.suffix == ".md":
                links.append(str(candidate.relative_to(WIKI).with_suffix("")))
        for target in OBSIDIAN_WIKI_LINK.findall(content):
            candidate = (WIKI / target).resolve().with_suffix(".md")
            if candidate.is_relative_to(WIKI.resolve()) and candidate.is_file():
                links.append(str(candidate.relative_to(WIKI).with_suffix("")))
        pages.append({
            "id": page_id,
            "title": title,
            "path": str(file.relative_to(ROOT)),
            "preview": preview,
            "page_type": wiki_page_type(page_id),
            "topics": metadata.get("topics", []),
            "status": metadata.get("status", "active"),
            "updated": str(metadata.get("updated", "")),
            "links": sorted(set(links)),
            # Wiki pages cite local PDFs as well as dashboard reference routes.
            # Both forms describe the same provenance relationship and must feed
            # the graph; otherwise implementation records such as PyMatching,
            # Union-Find, and Belief Matching appear as isolated nodes.
            "source_refs": sorted(set(REFERENCE_LINK.findall(content)) | set(REFERENCE_ROUTE_LINK.findall(content))),
        })
    by_id = {page["id"]: page for page in pages}
    for page in pages:
        page["links"] = [target for target in page["links"] if target in by_id]
        page["backlinks"] = [
            {"id": other["id"], "title": other["title"]}
            for other in pages if page["id"] in other["links"]
        ]
    return pages


def unified_search_documents() -> list[dict]:
    """Compile the three user-facing catalogs into one canonical search index."""
    documents = []
    for reference in read_json(REFERENCES / "references.json", {"references": []})["references"]:
        reference_id = str(reference["id"])
        documents.append(search_document(
            entity_type="reference",
            entity_id=reference_id,
            title=str(reference.get("title", reference_id)),
            stage=str(reference.get("status", "fetched")),
            target={"kind": "reference", "id": reference_id, "href": f"/reference?id={reference_id}"},
            fields=[
                ("Kind", reference.get("kind"), 100),
                ("Authors", reference.get("authors"), 800),
                ("Year", reference.get("year"), 50),
                ("arXiv", reference.get("arxiv"), 100),
                ("Canonical URL", reference.get("url"), 500),
                ("Summary", reference.get("summary"), 2600),
                ("Project relevance", reference.get("project_relevance"), 2200),
                ("Topics", reference.get("topics"), 1200),
            ],
        ))
    for lab in lab_catalog():
        lab_id = str(lab["id"])
        folder = LABS / lab_id
        detail = read_json(folder / "lab.json", {})
        plan = (folder / "PLAN.md").read_text(encoding="utf-8") if (folder / "PLAN.md").is_file() else ""
        report = (folder / "REPORT.md").read_text(encoding="utf-8") if (folder / "REPORT.md").is_file() else ""
        documents.append(search_document(
            entity_type="lab",
            entity_id=lab_id,
            title=str(lab.get("title", lab_id)),
            stage=str(lab.get("stage", "planned")),
            target={"kind": "lab", "id": lab_id, "href": f"/lab?id={lab_id}"},
            fields=[
                ("Summary", lab.get("summary"), 2200),
                ("Current focus", lab.get("current_focus"), 1800),
                ("Next action", lab.get("next_action"), 1800),
                ("Updated", lab.get("updated"), 100),
                ("Research question", detail.get("question"), 1800),
                ("Motivation", detail.get("motivation"), 1800),
                ("Plan", plan, 3200),
                ("Report", report, 4200),
            ],
        ))
    for page in wiki_pages():
        page_id = str(page["id"])
        content = (ROOT / page["path"]).read_text(encoding="utf-8")
        documents.append(search_document(
            entity_type="wiki",
            entity_id=page_id,
            title=str(page.get("title", page_id)),
            stage=str(page.get("status", "active")),
            target={"kind": "wiki", "id": page_id, "href": f"/wiki?page={page_id}"},
            fields=[
                ("Page type", page.get("page_type"), 100),
                ("Topics", page.get("topics"), 1200),
                ("Summary", page.get("preview"), 2200),
                ("Source references", page.get("source_refs"), 1200),
                ("Content", content, 7000),
            ],
        ))
    return documents


def unified_search_payload(query: str, scope: str, limit: int, refine: bool) -> dict:
    documents = unified_search_documents()
    enabled = os.getenv("OPENAI_CATALOG_SEARCH_ENABLED", "").strip().casefold() in {"1", "true", "yes"}
    if enabled and os.getenv("OPENAI_API_KEY", "").strip():
        try:
            return UNIFIED_SEARCH.search(query, scope=scope, documents=documents, limit=limit, refine=refine)
        except Exception as error:
            LOGGER.warning("Unified semantic search fell back to local ranking: %s", error)
    return local_search(query, scope=scope, documents=documents, limit=limit)


def wiki_lint_status() -> dict:
    """Run the deterministic Wiki check on demand and retain a timestamped health record."""
    cache = ROOT / ".tmp" / "wiki-lint-status.json"
    try:
        cached = read_json(cache, {})
        checked = datetime.fromisoformat(str(cached.get("checked_at", "")).replace("Z", "+00:00"))
        if (datetime.now(UTC) - checked).total_seconds() < 300:
            return cached
    except (TypeError, ValueError):
        pass
    command = [sys.executable, str(ROOT / "skills/wiki-lint/scripts/lint_wiki.py"), str(ROOT)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        output = (completed.stdout + "\n" + completed.stderr).strip()
        match = re.search(r"Wiki lint: (\d+) error\(s\), (\d+) warning\(s\)", output)
        record = {"checked_at": now(), "errors": int(match.group(1)) if match else None, "warnings": int(match.group(2)) if match else None, "state": "healthy" if match and completed.returncode == 0 else "needs-attention"}
    except (OSError, subprocess.TimeoutExpired):
        record = {"checked_at": now(), "errors": None, "warnings": None, "state": "unavailable"}
    write_json(cache, record)
    return record


def wiki_index_payload() -> dict:
    """Return the live control-plane data used by the Wiki Index landing page."""
    pages = [page for page in wiki_pages() if page["id"] != "index"]
    by_type = Counter(page["page_type"] for page in pages)
    by_status = Counter(page["status"] for page in pages)
    topics = Counter(topic for page in pages for topic in page.get("topics", []))
    sections = {
        "research_program": [page for page in pages if page["page_type"] == "project"],
        "foundations": [page for page in pages if page["page_type"] == "concept"],
        "decoding_methods": [page for page in pages if page["page_type"] == "method"],
        "models_and_implementations": [page for page in pages if page["page_type"] in {"model", "implementation"}],
        "references": [page for page in pages if page["page_type"] == "reference"],
    }
    for collection in sections.values():
        collection.sort(key=lambda page: page["title"].casefold())
    sources = yaml.safe_load((WIKI / "sources.yml").read_text(encoding="utf-8")) or {}
    records = sources.get("sources", []) if isinstance(sources, dict) else []
    source_kinds = Counter(str(item.get("kind", "other")) for item in records if isinstance(item, dict))
    log_headings = re.findall(r"^## \[(\d{4}-\d{2}-\d{2})\] ([^\n]+)\n+([^#]+)", (WIKI / "log.md").read_text(encoding="utf-8"), re.MULTILINE)
    recent_log = [{"date": date, "title": title, "summary": " ".join(body.split())} for date, title, body in log_headings[-3:]][::-1]
    recent_pages = sorted((page for page in pages if page.get("updated")), key=lambda page: (page["updated"], page["title"].casefold()), reverse=True)[:5]
    return {"statistics": {"pages": len(pages), "by_type": dict(by_type), "by_status": dict(by_status), "topics": dict(topics)}, "sources": {"total": len(records), "by_kind": dict(source_kinds)}, "sections": sections, "recent_pages": recent_pages, "recent_log": recent_log, "lint": wiki_lint_status()}


def _graph_tokens(page: dict) -> set[str]:
    text = " ".join([page["title"], *page.get("topics", [])])
    stopwords = {
        "and", "for", "from", "into", "the", "with", "without", "quantum",
        "decoder", "decoding", "code", "codes", "paper", "study", "using",
    }
    return {
        token.casefold() for token in TOKEN.findall(text)
        if len(token) > 2 and token.casefold() not in stopwords
    }


def _graph_pair(source: str, target: str) -> tuple[str, str]:
    return tuple(sorted((source, target)))


def _local_community_label(records: dict[str, dict], members: list[str]) -> str:
    """Name common decoder subgraphs distinctly when the LLM is unavailable."""
    titles = " ".join(str(records[node].get("title", "")).casefold() for node in members)
    if sum(term in titles for term in (
        "non-abelian", "nonabelian", "intrinsic heralding", "anyonic decoding",
        "anyons is fault tolerant",
    )) >= 2:
        return "Non-Abelian Fault-Tolerant Decoding"
    if sum(term in titles for term in (
        "program-level scientific roadmap", "topological quantum memory",
        "mixed-state topological order", "symmetry enforced entanglement",
    )) >= 2:
        return "Topological Memory Research"
    if sum(term in titles for term in (
        "belief matching", "belief propagation", "pymatching", "union-find", "relay-bp",
    )) >= 2:
        return "Decoder Architectures"
    if sum(term in titles for term in (
        "side-information", "charge-informed", "soft information", "erasure channel",
    )) >= 2:
        return "Side-Information Decoding"
    topic_counts = Counter(topic for node in members for topic in records[node].get("topics", []))
    return normalize_community_label(topic_counts.most_common(1)[0][0] if topic_counts else records[members[0]]["title"])


def _max_normalized(values: dict[str, float]) -> dict[str, float]:
    maximum = max(values.values(), default=0.0)
    return {key: (value / maximum if maximum else 0.0) for key, value in values.items()}


def _weighted_pagerank(graph: nx.Graph, iterations: int = 80, damping: float = 0.85) -> dict[str, float]:
    """Small deterministic PageRank implementation; avoids an optional SciPy runtime."""
    nodes = list(graph.nodes())
    if not nodes:
        return {}
    rank = {node: 1.0 / len(nodes) for node in nodes}
    strengths = {node: sum(data.get("weight", 1.0) for _, _, data in graph.edges(node, data=True)) for node in nodes}
    for _ in range(iterations):
        dangling = sum(rank[node] for node in nodes if strengths[node] == 0)
        next_rank = {node: (1.0 - damping) / len(nodes) + damping * dangling / len(nodes) for node in nodes}
        for source in nodes:
            if strengths[source] == 0:
                continue
            for target, data in graph[source].items():
                next_rank[target] += damping * rank[source] * data.get("weight", 1.0) / strengths[source]
        if max(abs(next_rank[node] - rank[node]) for node in nodes) < 1e-9:
            rank = next_rank
            break
        rank = next_rank
    return rank


def _graph_importance(graph: nx.Graph, direct_degree: Counter) -> dict[str, float]:
    weighted_degree = {node: graph.degree(node, weight="weight") for node in graph.nodes()}
    pagerank = _weighted_pagerank(graph)
    if graph.number_of_edges():
        distance_graph = graph.copy()
        for _, _, data in distance_graph.edges(data=True):
            data["distance"] = 1.0 / max(data.get("weight", 1.0), 0.001)
        betweenness = nx.betweenness_centrality(distance_graph, weight="distance", normalized=True)
    else:
        betweenness = {node: 0.0 for node in graph.nodes()}
    normalized = [
        _max_normalized(weighted_degree),
        _max_normalized(pagerank),
        _max_normalized(betweenness),
        _max_normalized({node: float(direct_degree[node]) for node in graph.nodes()}),
    ]
    return {
        node: round(
            0.45 * normalized[0][node]
            + 0.25 * normalized[1][node]
            + 0.20 * normalized[2][node]
            + 0.10 * normalized[3][node],
            4,
        )
        for node in graph.nodes()
    }


def knowledge_graph(pages: list[dict]) -> dict:
    semantic = [page for page in pages if page["page_type"] != "index"]
    for reference in read_json(REFERENCES / "references.json", {"references": []})["references"]:
        semantic.append({
            "id": f"reference/{reference['id']}",
            "title": reference["title"],
            "preview": reference.get("summary", ""),
            "page_type": "reference",
            "topics": reference.get("topics", []),
            "links": [],
            "source_refs": [reference["id"]],
            "href": f"/reference?id={reference['id']}",
        })
    records = {page["id"]: page for page in semantic}
    ids = sorted(records)

    # Candidate generation mirrors the proven Mercor graph model: authored links,
    # bounded shared-source groups, and local two-hop topology. Generic keyword
    # overlap is deliberately not allowed to manufacture relationships.
    authored_pairs = {
        _graph_pair(source, target)
        for source, page in records.items()
        for target in page.get("links", [])
        if target in records and source != target
    }
    authored_neighbors = {page_id: set() for page_id in ids}
    for source, target in authored_pairs:
        authored_neighbors[source].add(target)
        authored_neighbors[target].add(source)

    candidates = set(authored_pairs)
    source_owners = defaultdict(list)
    for page_id, page in records.items():
        for source_ref in page.get("source_refs", []):
            source_owners[source_ref].append(page_id)
    for owners in source_owners.values():
        if len(owners) > 8:
            continue
        for index, source in enumerate(sorted(set(owners))):
            for target in sorted(set(owners))[index + 1:]:
                candidates.add(_graph_pair(source, target))
    for center, neighbors in authored_neighbors.items():
        del center
        if len(neighbors) > 14:
            continue
        ordered = sorted(neighbors)
        for index, source in enumerate(ordered):
            for target in ordered[index + 1:]:
                candidates.add(_graph_pair(source, target))

    edges = []
    for source, target in sorted(candidates):
        left, right = records[source], records[target]
        direct = (source, target) in authored_pairs
        left_sources, right_sources = set(left.get("source_refs", [])), set(right.get("source_refs", []))
        shared_sources = left_sources & right_sources
        source_union = left_sources | right_sources
        source_overlap = len(shared_sources) / len(source_union) if source_union else 0.0
        citation = (
            (source.startswith("reference/") and source.removeprefix("reference/") in right_sources)
            or (target.startswith("reference/") and target.removeprefix("reference/") in left_sources)
        )
        common_neighbors = authored_neighbors[source] & authored_neighbors[target]
        adamic_adar = sum(
            1.0 / math.log(max(2, len(authored_neighbors[neighbor])))
            for neighbor in common_neighbors
        )
        type_affinity = 1.0 if left["page_type"] == right["page_type"] else 0.0
        weight = 8.0 * direct + 4.0 * citation + 2.0 * source_overlap + 1.5 * adamic_adar + 0.25 * type_affinity
        if weight < 1.5:
            continue
        if direct:
            display_role = "authored"
        elif citation or source_overlap:
            display_role = "grounded"
        elif adamic_adar:
            display_role = "predicted"
        else:
            continue
        reasons = []
        if direct:
            reasons.append("authored Wiki link")
        if shared_sources:
            reasons.append(f"shared source: {', '.join(sorted(shared_sources)[:2])}")
        if citation:
            reasons.append("explicit citation provenance")
        if common_neighbors:
            reasons.append(f"{len(common_neighbors)} shared authored neighbor{'s' if len(common_neighbors) != 1 else ''}")
        edges.append({
            "source": source,
            "target": target,
            "weight": round(weight, 4),
            "signals": {
                "direct": 1 if direct else 0,
                "citation": 1 if citation else 0,
                "source_overlap": round(source_overlap, 4),
                "adamic_adar": round(adamic_adar, 4),
                "type_affinity": type_affinity,
            },
            "reasons": reasons,
            "display_role": display_role,
        })

    # Predictions never organize the graph. Only authored and source-grounded
    # evidence contributes to communities, centrality, degrees, and hover scope.
    confirmed_edges = [edge for edge in edges if edge["display_role"] != "predicted"]
    adjacency = {page_id: set() for page_id in ids}
    weighted_degree = Counter()
    direct_degree = Counter()
    for edge in confirmed_edges:
        adjacency[edge["source"]].add(edge["target"])
        adjacency[edge["target"]].add(edge["source"])
        weighted_degree[edge["source"]] += edge["weight"]
        weighted_degree[edge["target"]] += edge["weight"]
        if edge["display_role"] == "authored":
            direct_degree[edge["source"]] += 1
            direct_degree[edge["target"]] += 1

    graph_model = nx.Graph()
    graph_model.add_nodes_from(ids)
    graph_model.add_weighted_edges_from((edge["source"], edge["target"], edge["weight"]) for edge in confirmed_edges)
    detected = nx.community.louvain_communities(graph_model, weight="weight", resolution=1.05, seed=42) if confirmed_edges else [{page_id} for page_id in ids]
    detected = sorted(detected, key=lambda group: (-len(group), min(group)))

    # Display every authored relation, a bounded amount of source-grounded
    # context, and only a handful of high-confidence predictions.
    display_edges = sorted(
        (edge for edge in edges if edge["display_role"] == "authored"),
        key=lambda edge: (edge["source"], edge["target"]),
    )
    display_edges.extend(sorted(
        (edge for edge in edges if edge["display_role"] == "grounded" and edge["signals"]["citation"]),
        key=lambda edge: (edge["source"], edge["target"]),
    ))
    grounded_degree = Counter(
        node
        for edge in display_edges if edge["display_role"] == "grounded"
        for node in (edge["source"], edge["target"])
    )
    grounded_candidates = sorted(
        (edge for edge in edges if edge["display_role"] == "grounded" and not edge["signals"]["citation"]),
        key=lambda edge: (-edge["weight"], edge["source"], edge["target"]),
    )
    for edge in grounded_candidates:
        if grounded_degree[edge["source"]] >= 3 or grounded_degree[edge["target"]] >= 3:
            continue
        display_edges.append(edge)
        grounded_degree[edge["source"]] += 1
        grounded_degree[edge["target"]] += 1
    predicted_edges = sorted(
        (edge for edge in edges if edge["display_role"] == "predicted"),
        key=lambda edge: (-edge["signals"]["adamic_adar"], -edge["weight"], edge["source"], edge["target"]),
    )[:4]
    display_edges.extend(predicted_edges)
    communities = []
    community_by_node = {}
    for members_set in detected:
        members = sorted(members_set)
        label = _local_community_label(records, members)
        community_id = len(communities)
        for node in members:
            community_by_node[node] = community_id
        possible = len(members) * (len(members) - 1) / 2
        internal = sum(1 for edge in confirmed_edges if edge["source"] in members and edge["target"] in members)
        communities.append({
            "id": community_id,
            "label": label,
            "color": GRAPH_COLORS[community_id % len(GRAPH_COLORS)],
            "node_count": len(members),
            "cohesion": round(internal / possible, 2) if possible else 1.0,
        })

    importance = _graph_importance(graph_model, direct_degree)
    nodes = [{
        "id": page_id,
        "label": records[page_id]["title"],
        "type": records[page_id]["page_type"],
        "summary": records[page_id]["preview"],
        "community": community_by_node[page_id],
        "href": records[page_id].get("href", f"/wiki?page={page_id}"),
        "degree": len(adjacency[page_id]),
        "weighted_degree": weighted_degree[page_id],
        "importance_score": importance[page_id],
        "size": round(7.5 + 8.5 * math.sqrt(importance[page_id]), 2),
    } for page_id in ids]

    predicted = [{
        "title": f"Review predicted link: {records[edge['source']]['title']} ↔ {records[edge['target']]['title']}",
        "description": (" · ".join(edge["reasons"]) + " · no authored or shared-source relation"),
        "node_ids": [edge["source"], edge["target"]],
    } for edge in predicted_edges]
    anomalies = [{
        "title": "Unconnected knowledge page",
        "description": node["label"],
        "node_ids": [node["id"]],
    } for node in nodes if node["degree"] == 0]
    fingerprint = hashlib.sha256(json.dumps([ids, edges], sort_keys=True).encode()).hexdigest()[:16]
    result = {
        "nodes": nodes,
        "edges": edges,
        "display_edges": display_edges,
        "communities": communities,
        "insights": {"predicted_connections": predicted, "graph_anomalies": anomalies},
        "model": {
            "edge_roles": ["authored", "grounded", "predicted"],
            "prediction_limit": 4,
            "predictions_affect_layout": False,
        },
        "fingerprint": fingerprint,
    }
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_COMMUNITY_NAMING_MODEL", "gpt-5.6").strip() or "gpt-5.6"
    try:
        timeout = max(1.0, min(float(os.getenv("OPENAI_API_TIMEOUT_SECONDS", "20")), 120.0))
    except ValueError:
        timeout = 20.0
    try:
        stats = enrich_community_labels(
            result, semantic, cache_path=COMMUNITY_LABEL_CACHE, api_key=api_key,
            model=model, timeout_seconds=timeout,
        )
        result["model"]["community_naming"] = {
            "mode": "openai" if api_key else "local", "model": model if api_key else None, **stats,
        }
    except Exception as error:  # The optional service must never prevent graph rendering.
        LOGGER.warning("Community naming fell back to local labels: %s", error)
        result["model"]["community_naming"] = {"mode": "local-fallback", "fallback": len(communities)}

    # An optional model may fail or return a broad duplicate label. Preserve a
    # useful, deterministic legend by restoring the evidence-based local name
    # for any repeated display label.
    used_labels = set()
    for community in result["communities"]:
        normalized = str(community["label"]).casefold()
        if normalized in used_labels:
            members = sorted(node_id for node_id, group_id in community_by_node.items() if group_id == community["id"])
            community["label"] = _local_community_label(records, members)
            community["label_source"] = "local-disambiguation"
            normalized = community["label"].casefold()
            suffix = 2
            while normalized in used_labels:
                community["label"] = f"{community['label']} {suffix}"
                normalized = community["label"].casefold()
                suffix += 1
        used_labels.add(normalized)
    return result


def project_payload() -> dict:
    project = read_json(ROOT / "project.json", {})
    labs, threads = lab_catalog(), discussion_payload()["threads"]
    active_labs = [lab for lab in labs if lab.get("stage") == "active"]
    return {
        "project": project,
        "counts": {
            "references": len(read_json(REFERENCES / "references.json", {"references": []})["references"]),
            "labs": len(labs),
            "wiki_pages": len(wiki_pages()),
            "open_threads": sum(item.get("status") == "open" for item in threads),
        },
        "active_labs": active_labs,
        "attention": [thread for thread in threads if thread.get("status") == "open" and thread.get("priority") in {"blocking", "high"}],
    }


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("dashboard | " + fmt % args)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def send_json(self, payload, status=HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if urlparse(self.path).path == "/api/labs/lab-006-sun-bp-theory/artifact":
            # The Lab artifact is also useful as a directly opened local HTML
            # file.  Permit only this local, read-only computation endpoint to
            # answer that file-origin request.
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def error_json(self, status, message: str) -> None:
        self.send_json({"detail": message}, status)

    def request_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 120_000:
            raise ValueError("Request is too large")
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path.startswith("/lab-assets/"):
                return self.serve_lab_asset(parsed.path)
            if parsed.path.startswith("/api/"):
                return self.api_get(parsed)
            direct_path = unquote(parsed.path.lstrip("/"))
            try:
                project_document_path(direct_path)
            except (FileNotFoundError, ValueError):
                pass
            else:
                location = project_document_href(direct_path, parsed.fragment)
                self.send_response(HTTPStatus.FOUND)
                self.send_header("Location", location)
                self.end_headers()
                return
            if parsed.path in {"/", "/references", "/reference", "/labs", "/lab", "/lab-result", "/lab-wiki", "/wiki", "/discussion", "/document"}:
                self.path = "/index.html"
            return super().do_GET()
        except (FileNotFoundError, ValueError) as error:
            self.error_json(HTTPStatus.NOT_FOUND, str(error))

    def do_HEAD(self):  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path.startswith("/lab-assets/"):
                return self.serve_lab_asset(parsed.path, send_body=False)
            direct_path = unquote(parsed.path.lstrip("/"))
            try:
                project_document_path(direct_path)
            except (FileNotFoundError, ValueError):
                pass
            else:
                self.send_response(HTTPStatus.FOUND)
                self.send_header("Location", project_document_href(direct_path, parsed.fragment))
                self.end_headers()
                return
            return super().do_HEAD()
        except (FileNotFoundError, ValueError) as error:
            self.send_error(HTTPStatus.NOT_FOUND, str(error))

    def serve_lab_asset(self, request_path: str, send_body: bool = True) -> None:
        """Serve a manifest-declared resource from a lab folder."""
        parts = [unquote(part) for part in request_path.split("/") if part]
        if len(parts) < 3 or parts[0] != "lab-assets":
            raise FileNotFoundError("Lab artifact not found")
        lab_id = valid_id(parts[1])
        folder = LABS / lab_id
        candidate = (folder / Path(*parts[2:])).resolve()
        relative_path = candidate.relative_to(folder).as_posix() if candidate.is_relative_to(folder.resolve()) else ""
        # Reports and plans may embed reproducible figures before each one is
        # promoted to the Lab's result manifest.  Keep that content scoped to
        # the two evidence directories rather than exposing arbitrary files.
        is_evidence_asset = relative_path.startswith("figures/") or relative_path.startswith("results/")
        if not candidate.is_relative_to(folder.resolve()) or not candidate.is_file() or not is_evidence_asset:
            raise FileNotFoundError("Lab artifact not found")
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if candidate.suffix == ".html":
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        self.api_mutate("POST")

    def do_OPTIONS(self):  # noqa: N802
        if urlparse(self.path).path == "/api/labs/lab-006-sun-bp-theory/artifact":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_PATCH(self):  # noqa: N802
        self.api_mutate("PATCH")

    def api_get(self, parsed):
        query, path = parse_qs(parsed.query), parsed.path.rstrip("/")
        if path == "/api/project":
            return self.send_json(project_payload())
        if path == "/api/search":
            needle = " ".join(query.get("q", [""])[0].split())
            scope = query.get("scope", ["all"])[0]
            refine = query.get("refine", ["false"])[0].casefold() == "true"
            try:
                limit = int(query.get("limit", ["50"])[0])
            except ValueError as error:
                raise ValueError("Search limit must be an integer") from error
            if not needle or len(needle) > 500:
                raise ValueError("Search query must contain 1–500 characters")
            if scope not in {"references", "labs", "wiki", "all"}:
                raise ValueError("Unsupported search scope")
            if limit < 1 or limit > 100:
                raise ValueError("Search limit must be between 1 and 100")
            return self.send_json(unified_search_payload(needle, scope, limit, refine))
        if path == "/api/references":
            return self.send_json({"references": read_json(REFERENCES / "references.json", {"references": []})["references"]})
        if path.startswith("/api/references/"):
            parts, reference_id = path.split("/"), path.split("/")[3]
            if len(parts) == 5 and parts[4] == "pdf":
                pdf = REFERENCES / valid_id(reference_id) / "paper.pdf"
                if not pdf.exists():
                    raise FileNotFoundError("Local PDF not available")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(pdf.stat().st_size))
                self.end_headers()
                self.wfile.write(pdf.read_bytes())
                return
            if len(parts) == 5 and parts[4] == "files":
                return self.send_json({"files": archive_files(reference_id)})
            if len(parts) == 5 and parts[4] == "file":
                if query.get("raw", [""])[0] == "1":
                    filename, body = archive_file_payload(reference_id, query.get("path", [""])[0], raw=True)
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "application/octet-stream")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers(); self.wfile.write(body); return
                return self.send_json(archive_file_payload(reference_id, query.get("path", [""])[0]))
            return self.send_json(reference_payload(reference_id))
        if path == "/api/labs":
            return self.send_json({"labs": lab_catalog()})
        if path.startswith("/api/labs/") and path.endswith("/wiki"):
            return self.send_json(local_wiki_payload(path.split("/")[3], query.get("page", ["index"])[0]))
        if path.startswith("/api/labs/"):
            return self.send_json(lab_payload(path.split("/")[3]))
        if path == "/api/documents/file":
            return self.send_json(project_document_payload(query.get("path", [""])[0]))
        if path == "/api/wiki":
            pages = wiki_pages()
            return self.send_json({"pages": pages, "graph": knowledge_graph(pages)})
        if path == "/api/wiki/index":
            return self.send_json(wiki_index_payload())
        if path == "/api/wiki/search":
            needle = query.get("q", [""])[0].lower().strip()
            if not needle or len(needle) > 500:
                raise ValueError("Search query must contain 1–500 characters")
            refine = query.get("refine", ["false"])[0].casefold() == "true"
            payload = unified_search_payload(needle, "wiki", 50, refine)
            by_id = {page["id"]: page for page in wiki_pages()}
            pages = []
            for result in payload["results"]:
                page = by_id.get(result["entity_id"])
                if page:
                    pages.append({**page, "search_result": True, "score": result["score"], "match_type": result["match_type"], "reason": result["reason"]})
            return self.send_json({**payload, "pages": pages})
        if path.startswith("/api/wiki/page/"):
            page_id = unquote(path.removeprefix("/api/wiki/page/"))
            candidate = (WIKI / (page_id + ".md")).resolve()
            if not candidate.is_relative_to(WIKI.resolve()) or not candidate.is_file():
                raise FileNotFoundError("Wiki page not found")
            metadata = next((page for page in wiki_pages() if page["id"] == page_id), {})
            return self.send_json({**markdown_document(candidate), "page": metadata})
        if path == "/api/discussion":
            return self.send_json(discussion_payload())
        return self.error_json(HTTPStatus.NOT_FOUND, "Unknown API endpoint")

    def api_mutate(self, method: str):
        path = urlparse(self.path).path.rstrip("/")
        try:
            body = self.request_body()
            if method == "PATCH" and path.startswith("/api/labs/"):
                return self.patch_lab(path.split("/")[3], body)
            if method == "POST" and path == "/api/labs/lab-001-string-herald-visualization/predecode":
                result = run_lab_function(
                    "lab-001-string-herald-visualization",
                    "scripts/local_decoder.py",
                    "predecode_payload",
                    body,
                )
                return self.send_json(result)
            if method == "POST" and path == "/api/labs/lab-001-string-herald-visualization/mwpm":
                result = run_lab_function(
                    "lab-001-string-herald-visualization",
                    "scripts/mwpm_decoder.py",
                    "mwpm_decode",
                    body,
                )
                return self.send_json(result)
            if method == "POST" and path == "/api/labs/lab-002-herald-belief-matching/artifact":
                result = run_lab_function(
                    "lab-002-herald-belief-matching",
                    "scripts/artifact_backend.py",
                    "artifact_payload",
                    body,
                )
                return self.send_json(result)
            if method == "POST" and path == "/api/labs/lab-006-sun-bp-theory/artifact":
                # Compatibility boundary for a pre-A3 browser tab.  The
                # current Lab 006 observation is exactly (m, R), but an old
                # iframe may continue posting its removed eta control until
                # the tab is refreshed.  Never pass that stale field into a
                # Lab runtime, including a runtime cached before the schema
                # correction.
                body.pop("eta", None)
                result = run_lab_function(
                    "lab-006-sun-bp-theory",
                    "scripts/artifact_backend.py",
                    "artifact_payload",
                    body,
                )
                return self.send_json(result)
            if method == "POST" and path == "/api/discussion/threads":
                return self.create_thread(body)
            match = re.fullmatch(r"/api/discussion/threads/([a-z0-9-]+)/messages", path)
            if method == "POST" and match:
                return self.reply_thread(match.group(1), body)
            match = re.fullmatch(r"/api/discussion/threads/([a-z0-9-]+)/messages/([a-z0-9-]+)", path)
            if method == "PATCH" and match:
                return self.edit_thread_message(match.group(1), match.group(2), body)
            match = re.fullmatch(r"/api/discussion/threads/([a-z0-9-]+)", path)
            if method == "PATCH" and match:
                return self.transition_thread(match.group(1), body)
            return self.error_json(HTTPStatus.NOT_FOUND, "Unknown write endpoint")
        except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
            self.error_json(HTTPStatus.BAD_REQUEST, str(error))

    def patch_lab(self, lab_id: str, body: dict):
        valid_id(lab_id)
        catalog = read_json(LABS / "labs.json", {"labs": []})
        record = next((item for item in catalog["labs"] if item["id"] == lab_id), None)
        if not record:
            raise FileNotFoundError("Lab not found")
        for key in ("stage", "current_focus", "next_action", "summary"):
            if key in body:
                value = str(body[key]).strip()
                if not value or len(value) > 2000:
                    raise ValueError(f"Invalid {key}")
                if key == "stage" and value not in LAB_STAGES:
                    raise ValueError(f"Invalid stage; choose one of: {', '.join(LAB_STAGES)}")
                if key == "stage" and value == "complete" and record.get("stage") != "complete":
                    errors = report_lint_errors(lab_id)
                    if errors:
                        raise ValueError("Lab cannot be completed: " + "; ".join(errors))
                record[key] = value
        record["updated"] = datetime.now().date().isoformat()
        write_json(LABS / "labs.json", catalog)
        detail_path, detail = LABS / lab_id / "lab.json", read_json(LABS / lab_id / "lab.json", {})
        # Persist mutable catalog fields in the Lab-owned metadata as the
        # canonical source.  The index write above remains for compatibility
        # with older tooling and discovery views.
        for key in ("stage", "current_focus", "next_action", "summary"):
            if key in body:
                detail[key] = record[key]
        detail["updated"] = record["updated"]
        for key in ("question", "motivation", "frontier", "blockers", "resolved"):
            if key in body:
                detail[key] = body[key]
        write_json(detail_path, detail)
        self.send_json(lab_payload(lab_id))

    def create_thread(self, body: dict):
        title, message = str(body.get("title", "")).strip(), normalize_discussion_text(body.get("message", ""))
        if not title or len(title) > 160 or not message or len(message) > 12000:
            raise ValueError("Thread title and opening message are required")
        data, sequence = discussion_payload(), 1
        existing = {item["id"] for item in data["threads"]}
        while f"thread-{sequence:03d}" in existing:
            sequence += 1
        timestamp = now()
        thread = {"id": f"thread-{sequence:03d}", "title": title, "category": body.get("category", "scientific"), "priority": body.get("priority", "normal"), "status": "open", "related_labs": [valid_id(item) for item in body.get("related_labs", [])], "created": timestamp, "updated": timestamp, "messages": [{"id": "msg-001", "author": "user", "type": "request", "created": timestamp, "content": message}]}
        data["threads"].append(thread)
        write_json(DISCUSSION / "threads.json", data)
        self.send_json({"thread": thread, "discussion": discussion_payload()}, HTTPStatus.CREATED)

    def reply_thread(self, thread_id: str, body: dict):
        valid_id(thread_id)
        message = normalize_discussion_text(body.get("message", ""))
        if not message or len(message) > 12000:
            raise ValueError("Reply is required")
        data = discussion_payload()
        thread = next((item for item in data["threads"] if item["id"] == thread_id), None)
        if not thread or thread.get("status") != "open":
            raise ValueError("Open thread not found")
        timestamp = now()
        thread["messages"].append({"id": f"msg-{len(thread['messages']) + 1:03d}", "author": "user", "type": "reply", "created": timestamp, "content": message})
        thread["updated"] = timestamp
        write_json(DISCUSSION / "threads.json", data)
        self.send_json({"thread": thread, "discussion": discussion_payload()})

    def edit_thread_message(self, thread_id: str, message_id: str, body: dict):
        valid_id(thread_id)
        if not re.fullmatch(r"msg-[0-9]{3}", message_id):
            raise ValueError("Invalid message ID")
        data = discussion_payload()
        thread = next((item for item in data["threads"] if item["id"] == thread_id), None)
        if not thread:
            raise FileNotFoundError("Thread not found")
        message = next((item for item in thread.get("messages", []) if item.get("id") == message_id), None)
        if not message or message.get("author") != "user":
            raise ValueError("Only your own posts can be edited")
        timestamp = now()
        if body.get("withdraw") is True:
            message["content"], message["withdrawn"], message["withdrawn_at"] = "", True, timestamp
        else:
            content = normalize_discussion_text(body.get("message", ""))
            if not content or len(content) > 12000:
                raise ValueError("Message content is required")
            message["content"], message["edited"] = content, timestamp
        thread["updated"] = timestamp
        write_json(DISCUSSION / "threads.json", data)
        self.send_json({"thread": thread, "discussion": discussion_payload()})

    def transition_thread(self, thread_id: str, body: dict):
        valid_id(thread_id)
        status = str(body.get("status", ""))
        if status not in {"open", "closed"}:
            raise ValueError("Status must be open or closed")
        data = discussion_payload()
        thread = next((item for item in data["threads"] if item["id"] == thread_id), None)
        if not thread:
            raise FileNotFoundError("Thread not found")
        thread["status"], thread["updated"] = status, now()
        write_json(DISCUSSION / "threads.json", data)
        self.send_json({"thread": thread, "discussion": discussion_payload()})

    def translate_path(self, path: str) -> str:
        target = (FRONTEND / urlparse(path).path.lstrip("/")).resolve()
        return str(target if target.is_relative_to(FRONTEND.resolve()) else FRONTEND / "index.html")


if __name__ == "__main__":
    if os.environ.get("HERALD_SERVER_LAUNCHED") != "1":
        raise SystemExit("Start this service through ./run_server.sh")
    port = 8010
    # Move Lab 006's Numba specialization cost to server startup.  Its BP
    # kernels specialize by dtype/rank, so this tiny graph covers every L and
    # every group in the interactive artifact.
    try:
        run_lab_function(
            "lab-006-sun-bp-theory", "scripts/artifact_backend.py",
            "warm_numba_kernels", {},
        )
    except Exception:
        LOGGER.exception("Lab 006 Numba warm-up failed; artifact will compile lazily")
    print(f"Herald Decoder server: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
