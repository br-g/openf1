"""Replays archived sessions through two versions of the processing code and compares
the documents they produce.

By default, the base is the commit of origin/main that the head is built on, so the
comparison only shows the head's own changes. Both versions run on the same raw
data, through the same code path as `ingest_session`, without writing to the
database. This shows which documents a change alters, and confirms that nothing
else changed.

Usage, from the root of the repository:

    python tools/replay.py compare                  # changes in the working tree
    python tools/replay.py compare --head my-branch # changes in a branch
    python tools/replay.py compare --session 2026/1298/11399 --collection laps
    python tools/replay.py compare --season 2025 --jobs 3

Raw data is downloaded once (F1_TOKEN is needed for that) and cached in
`.cache/replay`. The output of a commit is cached too, so `--base` is only
processed once per session.

The exit code is 0 when both versions produce the same documents, and 1 otherwise.
"""

import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import typer

WORKTREE = "WORKTREE"
DEFAULT_SESSIONS_FILE = Path(__file__).parent / "replay_sessions.txt"
OUTPUT_FORMAT = 2  # bump when the saved output changes, to ignore older caches

cli = typer.Typer(pretty_exceptions_show_locals=False, add_completion=False)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _read_sessions_file(sessions_file: Path) -> list[tuple]:
    """Returns (year, meeting_key, session_key, label) for each listed session"""
    res = []
    for line in sessions_file.read_text().splitlines():
        content, _, label = line.partition("#")
        if content.strip():
            res.append((*map(int, content.split()), label.strip()))
    return res


def _cache_requests(cache_dir: Path) -> list[str]:
    """Serves F1 downloads from the cache, and caches new ones.

    A topic missing from F1's archive is served as an empty file, as if no message
    had been received. Returns the list of missing topics, filled as they're found.
    """
    import requests

    real_get = requests.get
    missing_topics = []

    def empty_response(url: str):
        missing_topics.append(url.rsplit("/", 1)[1][: -len(".jsonStream")])
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response._content = b""
        return response

    def cached_get(url: str, *args, **kwargs):
        path = cache_dir / "raw" / url.split("://", 1)[1]
        missing_marker = path.with_name(path.name + ".missing")
        if missing_marker.exists():
            return empty_response(url)
        # The index of a season grows as sessions are added
        is_season_index = re.search(r"/static/\d{4}/Index\.json$", url) is not None
        is_fresh = path.exists() and not (
            is_season_index and time.time() - path.stat().st_mtime > 86400
        )
        if is_fresh:
            response = requests.Response()
            response.status_code = 200
            response.url = url
            response._content = path.read_bytes()
            return response

        if not os.environ.get("F1_TOKEN"):
            sys.exit(f"F1_TOKEN is needed to download {url}")
        response = real_get(url, *args, **kwargs)
        # F1 answers 403 for a topic that isn't in a session's archive
        if response.status_code in (403, 404) and url.endswith(".jsonStream"):
            missing_marker.parent.mkdir(parents=True, exist_ok=True)
            missing_marker.touch()
            return empty_response(url)
        if response.status_code == 200:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
            tmp_path.write_bytes(response.content)
            tmp_path.replace(path)
        return response

    requests.get = cached_get
    return missing_topics


def _check_import(src: Path, module):
    # An installed copy of the package would silently replace the one being tested
    if src.resolve() not in Path(module.__file__).resolve().parents:
        sys.exit(f"openf1 was imported from {module.__file__}, not from {src}")


@cli.command(hidden=True)
def process(
    src: Path,
    year: int,
    meeting_key: int,
    session_key: int,
    out: Path,
    cache_dir: Path,
    collection: list[str] = typer.Option([]),
):
    """Processes a session with the code in `src`, and saves the documents to `out`"""
    import traceback

    from openf1.services.ingestor_livetiming.core import objects
    from openf1.services.ingestor_livetiming.historical.main import (
        _get_processed_documents,
    )
    from openf1.util.misc import json_serializer

    _check_import(src, objects)
    missing_topics = _cache_requests(cache_dir)
    os.environ.setdefault("F1_TOKEN", "")

    # Processing prints and skips a message that raises an exception: count them
    errors = Counter()

    def count_error(*args, **kwargs):
        exception = sys.exc_info()[1]
        errors[f"{type(exception).__name__}: {exception}"[:150]] += 1

    traceback.print_exc = count_error

    collection_names = collection or sorted(
        c.__class__.name for c in objects.get_collections(meeting_key, session_key)
    )
    docs_by_collection = _get_processed_documents(
        year=year,
        meeting_key=meeting_key,
        session_key=session_key,
        collection_names=collection_names,
        verbose=False,
    )

    documents = {}
    for name, docs in docs_by_collection.items():
        documents[name] = {}
        for doc in docs:
            mongo_doc = doc.to_mongo_doc_sync()
            mongo_doc.pop("_id")  # generated from the current time
            documents[name][mongo_doc.pop("_key")] = mongo_doc

    res = {
        "missing_topics": sorted(set(missing_topics)),
        "processing_errors": dict(errors),
        "documents": documents,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt") as f:
        json.dump(res, f, default=json_serializer, sort_keys=True)


@cli.command(hidden=True)
def list_sessions(src: Path, year: int, out: Path, cache_dir: Path):
    """Lists the sessions of a season, as the code in `src` sees them"""
    from openf1.util import schedule

    _check_import(src, schedule)
    _cache_requests(cache_dir)
    os.environ.setdefault("F1_TOKEN", "")

    sessions = []
    for meeting in schedule.get_schedule(year)["Meetings"]:
        for session in meeting["Sessions"]:
            if session["Key"] == -1 or "Path" not in session:
                continue
            # e.g. 2025/2025-03-16_Australian_Grand_Prix/2025-03-14_Practice_1/
            parts = session["Path"].strip("/").split("/")[1:]
            label = " ".join(p.split("_", 1)[1].replace("_", " ") for p in parts)
            sessions.append((year, meeting["Key"], session["Key"], label))
    out.write_text(json.dumps(sessions))


class _Version:
    """A version of the processing code: a git ref, or the working tree"""

    def __init__(self, repo: Path, ref: str, name: str, tmp_dir: Path):
        self.ref = ref
        if ref == WORKTREE:
            self.src = repo / "src"
            self.tree = None  # uncommitted changes can't be cached
            dirty = _git(repo, "status", "--porcelain", "src")
            self.name = f"working tree ({_git(repo, 'rev-parse', '--short', 'HEAD')}"
            self.name += " + uncommitted changes)" if dirty else ")"
        else:
            self.src = tmp_dir / ref.replace("/", "_") / "src"
            self.tree = _git(repo, "rev-parse", f"{ref}:src")
            self.name = f"{name} ({_git(repo, 'rev-parse', '--short', ref)})"
            archive = subprocess.run(
                ["git", "-C", str(repo), "archive", ref, "src"],
                check=True,
                capture_output=True,
            ).stdout
            self.src.parent.mkdir(parents=True)
            subprocess.run(
                ["tar", "-x", "-C", str(self.src.parent)], input=archive, check=True
            )

    def _run(self, *args: str):
        cmd = [sys.executable, __file__, *args]
        env = {
            **os.environ,
            "PYTHONPATH": str(self.src),
            "_TYPER_STANDARD_TRACEBACK": "1",
        }
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            last_lines = result.stderr.strip().splitlines()[-1:]
            raise RuntimeError(
                last_lines[0] if last_lines else f"exit {result.returncode}"
            )

    def list_sessions(self, year: int, cache_dir: Path) -> list[tuple]:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sessions.json"
            self._run(
                "list-sessions", str(self.src), str(year), str(out), str(cache_dir)
            )
            return [tuple(s) for s in json.loads(out.read_text())]

    def get_documents(self, session: tuple, collections: list[str], cache_dir: Path):
        year, meeting_key, session_key, _ = session
        filters = hashlib.sha1(",".join(sorted(collections)).encode()).hexdigest()[:8]
        filename = (
            f"{year}_{meeting_key}_{session_key}_{filters}_v{OUTPUT_FORMAT}.json.gz"
        )
        out = cache_dir / "documents" / (self.tree or WORKTREE) / filename

        if self.tree is None or not out.exists():
            args = ["process", str(self.src), str(year), str(meeting_key)]
            args += [str(session_key), str(out), str(cache_dir)]
            for c in collections:
                args += ["--collection", c]
            self._run(*args)

        with gzip.open(out, "rt") as f:
            return json.load(f)


def _short(value, max_length: int = 80) -> str:
    text = json.dumps(value)
    return text if len(text) <= max_length else text[: max_length - 3] + "..."


def _compare(base: dict, head: dict, n_examples: int) -> tuple[list[str], list[str]]:
    """Returns the names of the identical collections, and a description of the
    differences"""
    identical, lines = [], []
    for name in sorted(set(base) | set(head)):
        if name not in base or name not in head:
            missing_from = "base" if name not in base else "head"
            lines.append(f"  {name}: missing from {missing_from}")
            continue

        docs_base, docs_head = base[name], head[name]
        removed = sorted(docs_base.keys() - docs_head.keys())
        added = sorted(docs_head.keys() - docs_base.keys())
        changed = sorted(
            k
            for k in docs_base.keys() & docs_head.keys()
            if docs_base[k] != docs_head[k]
        )
        if not (removed or added or changed):
            identical.append(f"{name} ({len(docs_base)})")
            continue

        lines.append(
            f"  {name}: {len(docs_base)} -> {len(docs_head)} documents, "
            f"{len(removed)} removed, {len(added)} added, {len(changed)} changed"
        )
        for label, keys, docs in (
            ("removed", removed, docs_base),
            ("added", added, docs_head),
        ):
            for key in keys[:n_examples]:
                lines.append(f"    {label} {key}: {_short(docs[key], 120)}")
            if len(keys) > n_examples:
                lines.append(f"    ... {len(keys) - n_examples} more {label}")

        changed_fields = Counter()
        examples = []
        for key in changed:
            doc_base, doc_head = docs_base[key], docs_head[key]
            for field in sorted(doc_base.keys() | doc_head.keys()):
                if doc_base.get(field) != doc_head.get(field):
                    changed_fields[field] += 1
                    examples.append(
                        f"    changed {key} {field}: "
                        f"{_short(doc_base.get(field))} -> {_short(doc_head.get(field))}"
                    )
        if changed_fields:
            counts = ", ".join(f"{f} ({n})" for f, n in changed_fields.most_common())
            lines.append(f"    fields changed: {counts}")
            lines += examples[:n_examples]
            if len(examples) > n_examples:
                lines.append(f"    ... {len(examples) - n_examples} more changes")

    return identical, lines


def _compare_errors(base: dict, head: dict) -> list[str]:
    """Describes the change in exceptions raised (and skipped) while processing"""
    if base == head:
        return []
    lines = [f"  processing errors: {sum(base.values())} -> {sum(head.values())}"]
    for error in sorted(base.keys() | head.keys()):
        if base.get(error, 0) != head.get(error, 0):
            lines.append(f"    {base.get(error, 0)} -> {head.get(error, 0)}  {error}")
    return lines


@cli.command()
def compare(
    base: str = typer.Option(
        None,
        help="Git ref of the reference version. Default: where head forked from origin/main.",
    ),
    head: str = typer.Option(
        WORKTREE, help="Git ref, or WORKTREE for the files on disk."
    ),
    session: list[str] = typer.Option(
        [], help="Session as YEAR/MEETING_KEY/SESSION_KEY (repeatable)."
    ),
    season: list[int] = typer.Option(
        [], help="Replay every past session of a season (repeatable)."
    ),
    sessions_file: Path = typer.Option(
        DEFAULT_SESSIONS_FILE, help="Sessions replayed when no session is given."
    ),
    collection: list[str] = typer.Option(
        [], help="Collection to compare (repeatable). All by default."
    ),
    jobs: int = typer.Option(1, help="Sessions processed in parallel."),
    cache_dir: Path = typer.Option(Path(".cache/replay"), help="Where downloads go."),
    examples: int = typer.Option(3, help="Examples shown per kind of difference."),
):
    """Compares the documents produced by two versions of the processing code"""
    repo = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel"))
    cache_dir = cache_dir.resolve()

    head_commit = _git(repo, "rev-parse", "HEAD" if head == WORKTREE else head)
    base_name = base
    if base is None:
        base = _git(repo, "merge-base", "origin/main", head_commit)
        base_name = "origin/main where head forked"
    elif subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", base, head_commit]
    ).returncode:
        print(
            f"Warning: head isn't built on {base}, so the differences include changes "
            f"made to {base} since head forked from it.\n"
        )

    with tempfile.TemporaryDirectory() as tmp:
        versions = [
            _Version(repo, ref, name, Path(tmp) / str(i))
            for i, (ref, name) in enumerate(((base, base_name), (head, head)))
        ]
        print(f"Base: {versions[0].name}")
        print(f"Head: {versions[1].name}\n")

        listed = _read_sessions_file(sessions_file)
        labels = {s[:3]: s[3] for s in listed}
        sessions = [
            (*k, labels.get(k, ""))
            for k in (tuple(map(int, s.split("/"))) for s in session)
        ]
        for year in season:
            sessions += versions[1].list_sessions(year, cache_dir)
        sessions = sessions or listed

        def replay(s: tuple) -> tuple[str, list[str]]:
            """Returns the status of a session, and the lines describing it"""
            year, meeting_key, session_key, label = s
            lines = [f"{year}/{meeting_key}/{session_key}  {label}"]
            try:
                res_base, res_head = (
                    v.get_documents(s, collection, cache_dir) for v in versions
                )
            except RuntimeError as e:
                return "failed", lines + [f"  failed: {e}", ""]

            identical, differences = _compare(
                res_base["documents"], res_head["documents"], examples
            )
            differences += _compare_errors(
                res_base["processing_errors"], res_head["processing_errors"]
            )
            if res_head["missing_topics"]:
                missing = ", ".join(res_head["missing_topics"])
                lines.append(f"  not in F1's archive: {missing}")
            lines += differences
            if identical:
                lines.append(f"  identical: {', '.join(identical)}")
            return ("different" if differences else "identical"), lines + [""]

        statuses = Counter()
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            for status, lines in executor.map(replay, sessions):
                statuses[status] += 1
                print("\n".join(lines), flush=True)

    print(
        f"{statuses['identical']} of {len(sessions)} sessions identical, "
        f"{statuses['different']} different, {statuses['failed']} failed"
    )
    raise typer.Exit(0 if statuses["identical"] == len(sessions) else 1)


if __name__ == "__main__":
    cli()
