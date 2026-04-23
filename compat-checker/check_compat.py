"""
Compatibility checker: compares the official JS lib (gokapso/whatsapp-cloud-api-js)
against the Python fork (HeiCg/whatsapp-cloud-api-py) and creates GitHub issues
when breaking changes are detected.

Runs daily on Railway as a cron job.

Optimization: Uses a cached API surface summary stored in a GitHub Gist.
- 1st run: full analysis (~90K tokens) → generates api_surface + state
- Next runs: only sends diff + cached summary (~5-10K tokens) → 90% cheaper

Required env vars:
  ANTHROPIC_API_KEY   — MiniMax API key (compatible with Anthropic SDK)
  ANTHROPIC_BASE_URL  — MiniMax base URL (default: https://api.minimax.io/anthropic)
  GITHUB_TOKEN        — GitHub PAT with repo + issues + gist permissions
  GIST_ID             — GitHub Gist ID for persisting state between runs
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import anthropic
from github import Auth, Github, InputFileContent

JS_REPO = "gokapso/whatsapp-cloud-api-js"
PY_REPO = "HeiCg/whatsapp-cloud-api-py"

# Gist filenames
STATE_FILENAME = "compat-checker-state.json"
SURFACE_FILENAME = "api-surface.json"


# ── Env / State ──────────────────────────────────────────────────────────────


def get_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: {name} env var is required")
        sys.exit(1)
    return value


def load_gist_file(gh: Github, gist_id: str, filename: str) -> dict:
    try:
        gist = gh.get_gist(gist_id)
        if filename in gist.files:
            return json.loads(gist.files[filename].content)
    except Exception:
        pass
    return {}


def save_gist_files(gh: Github, gist_id: str, files: dict[str, dict]) -> None:
    gist = gh.get_gist(gist_id)
    gist.edit(
        files={name: InputFileContent(json.dumps(data, indent=2)) for name, data in files.items()}
    )


# ── Git helpers ──────────────────────────────────────────────────────────────


def clone_repo(repo: str, dest: Path) -> None:
    url = f"https://github.com/{repo}.git"
    subprocess.run(["git", "clone", "--depth", "50", url, str(dest)], check=True)


def get_recent_commits(repo_dir: Path, since_sha: str | None) -> str:
    cmd = ["git", "-C", str(repo_dir), "log", "--oneline", "--no-decorate"]
    if since_sha:
        cmd.append(f"{since_sha}..HEAD")
    else:
        cmd.extend(["--since=7 days ago"])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_diff(repo_dir: Path, since_sha: str | None) -> str:
    cmd = ["git", "-C", str(repo_dir), "diff"]
    if since_sha:
        cmd.append(f"{since_sha}..HEAD")
    else:
        cmd.extend(["HEAD~10..HEAD"])
    cmd.append("--")
    cmd.extend(["src/", "package.json"])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_head_sha(repo_dir: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def collect_tree(repo_dir: Path, subdir: str, extensions: tuple[str, ...]) -> str:
    parts: list[str] = []
    src = repo_dir / subdir
    if not src.exists():
        return ""
    for f in sorted(src.rglob("*")):
        if f.is_file() and f.suffix in extensions:
            rel = f.relative_to(repo_dir)
            try:
                content = f.read_text(errors="replace")
            except Exception:
                continue
            parts.append(f"=== {rel} ===\n{content}")
    return "\n\n".join(parts)


# ── LLM calls ───────────────────────────────────────────────────────────────


def _llm_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimax.io/anthropic"),
    )


def _call_llm(prompt: str, max_tokens: int = 4096) -> str:
    client = _llm_client()
    response = client.messages.create(
        model="MiniMax-M2.7",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    # MiniMax-M2.7 can return ThinkingBlock + TextBlock — extract the text one
    text = ""
    for block in response.content:
        if block.type == "text":
            text = block.text.strip()
            break
    if not text:
        print(f"WARNING: No text block in response. Blocks: {[b.type for b in response.content]}")
        return ""
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def generate_api_surface(js_src: str, py_src: str) -> dict:
    """First run: full analysis of both libs → structured API surface JSON."""
    prompt = f"""Analyze these two WhatsApp Cloud API SDKs and produce a structured API surface map.

## JS/TS library source (official)
{js_src[:80000]}

## Python library source (community fork)
{py_src[:80000]}

Produce a JSON object mapping every public resource and method in both libs:

{{
  "js": {{
    "client": {{
      "constructor_params": ["accessToken", "baseUrl", "graphVersion", ...],
      "methods": ["request", "fetch"]
    }},
    "messages": {{
      "methods": ["sendText", "sendImage", "sendDocument", ...],
      "models": ["TextMessage", "ImageMessage", ...]
    }},
    "media": {{
      "methods": ["upload", "get", "download", "delete"]
    }},
    "templates": {{
      "methods": ["list", "get", "create", "delete"],
      "models": [...]
    }},
    "phone_numbers": {{
      "methods": [...]
    }},
    "flows": {{
      "methods": [...]
    }},
    "webhooks": {{
      "functions": ["verifySignature", "normalizeWebhook"],
      "event_types": [...]
    }}
  }},
  "py": {{
    // same structure but with Python names (snake_case)
  }},
  "gaps": [
    {{
      "type": "missing_in_py" | "missing_in_js" | "signature_mismatch",
      "resource": "messages",
      "detail": "JS has sendRaw(), Python does not"
    }}
  ]
}}

Include ALL methods and models. Be exhaustive. Return ONLY valid JSON."""

    text = _call_llm(prompt, max_tokens=8192)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"WARNING: Failed to parse API surface JSON:\n{text[:500]}")
        return {}


def analyze_diff_against_surface(
    api_surface: dict,
    js_diff: str,
    js_commits: str,
) -> dict | None:
    """Incremental run: analyze diff against cached API surface (~5-10K tokens)."""
    surface_str = json.dumps(api_surface, indent=2)

    prompt = f"""You are a compatibility analyzer for two WhatsApp Cloud API SDKs.

## Cached API surface (both libs)
{surface_str}

## Recent JS library changes

### Commits
{js_commits}

### Diff (src/ and package.json only)
{js_diff[:30000]}

## Your task

Based on the diff, determine if the JS library introduced changes that break compatibility
with the Python library. Use the cached API surface to understand what Python currently has.

Focus on:
1. **New API methods** added to JS that Python doesn't have
2. **Changed method signatures** (new required params, renamed params, removed params)
3. **New message types** or resources added in JS
4. **Changed response types** or error handling
5. **Removed or deprecated features**
6. **New optional fields on response types** — even if additive/non-breaking for the
   JS consumer, they often signal new server behavior the Python port must consume.
   Example: a new `downloadUrl` field on `MediaMetadataResponse` that the JS client
   now prefers over `url`. Flag these at **medium** severity with `suggested_fix`
   spelling out what Python needs to read/use.
7. **New internal switches over response data** — when JS starts routing requests
   through a different field/URL/path based on response content (e.g. preferring
   `downloadUrl` over `url`, or branching on a new enum value). These are not
   "signature changes" but carry real behavioral divergence — flag at **medium**.

**Ignore:**
- Internal implementation details (HTTP client plumbing, bundling, etc.) — but
  do NOT treat #6/#7 above as "internal"; those are observable protocol changes.
- Kapso-proxy-only features (conversations, contacts, calls)
- Code style / test-only changes

Respond with a JSON object:
{{
  "has_breaking_changes": true/false,
  "changes": [
    {{
      "type": "new_feature" | "breaking_change" | "signature_change" | "deprecation",
      "severity": "high" | "medium" | "low",
      "js_location": "file:method or description",
      "description": "what changed",
      "python_impact": "what needs to change in the Python lib",
      "suggested_fix": "brief description of the fix needed"
    }}
  ],
  "surface_updates": [
    {{
      "lib": "js",
      "resource": "messages",
      "action": "add_method" | "remove_method" | "rename_method",
      "detail": "added sendCarousel()"
    }}
  ],
  "summary": "one paragraph summary"
}}

If NO compatibility issues, return:
{{
  "has_breaking_changes": false,
  "changes": [],
  "surface_updates": [...],
  "summary": "No compatibility issues found."
}}

Return ONLY valid JSON."""

    text = _call_llm(prompt)
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        print(f"WARNING: LLM returned invalid JSON:\n{text[:500]}")
        return None

    return result


def apply_surface_updates(api_surface: dict, updates: list[dict]) -> dict:
    """Patch the cached API surface with incremental changes from analysis."""
    for update in updates:
        lib = update.get("lib", "js")
        resource = update.get("resource", "")
        action = update.get("action", "")
        detail = update.get("detail", "")

        if lib not in api_surface:
            api_surface[lib] = {}
        if resource not in api_surface[lib]:
            api_surface[lib][resource] = {"methods": [], "models": []}

        res = api_surface[lib][resource]

        if action == "add_method" and "methods" in res:
            method_name = detail.replace("added ", "").split("(")[0].strip()
            if method_name and method_name not in res["methods"]:
                res["methods"].append(method_name)
        elif action == "remove_method" and "methods" in res:
            method_name = detail.replace("removed ", "").split("(")[0].strip()
            res["methods"] = [m for m in res["methods"] if m != method_name]

    return api_surface


# ── GitHub Issue creation ────────────────────────────────────────────────────


def create_issue(gh: Github, analysis: dict) -> None:
    repo = gh.get_repo(PY_REPO)

    # Skip if open compat issue already exists
    title_prefix = "[Compat] "
    existing = repo.get_issues(state="open", labels=["compatibility"])
    for issue in existing:
        if issue.title.startswith(title_prefix):
            print(f"Existing compat issue found: #{issue.number} — skipping")
            return

    changes_md = ""
    for c in analysis["changes"]:
        severity_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}[c["severity"]]
        changes_md += f"""### {severity_badge} {c['type']}: {c['description']}

- **JS location:** `{c['js_location']}`
- **Python impact:** {c['python_impact']}
- **Suggested fix:** {c['suggested_fix']}

"""

    body = f"""## Compatibility Report

{analysis['summary']}

## Changes Detected

{changes_md}

---
*Automatically created by the compatibility checker.*
*Source: [`{JS_REPO}`](https://github.com/{JS_REPO})*
"""

    try:
        repo.get_label("compatibility")
    except Exception:
        repo.create_label("compatibility", "d93f0b", "Upstream JS compatibility issues")

    high_changes = [c for c in analysis["changes"] if c["severity"] == "high"]
    change_count = len(analysis["changes"])
    title = f"{title_prefix}{change_count} change(s) detected"
    if high_changes:
        title += f" ({len(high_changes)} high severity)"

    issue = repo.create_issue(title=title, body=body, labels=["compatibility"])
    print(f"Created issue: #{issue.number} — {issue.title}")


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    get_env("ANTHROPIC_API_KEY")
    github_token = get_env("GITHUB_TOKEN")
    gist_id = get_env("GIST_ID")

    gh = Github(auth=Auth.Token(github_token))
    state = load_gist_file(gh, gist_id, STATE_FILENAME)
    api_surface = load_gist_file(gh, gist_id, SURFACE_FILENAME)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        js_dir = tmp / "js"
        py_dir = tmp / "py"

        print(f"Cloning {JS_REPO}...")
        clone_repo(JS_REPO, js_dir)

        print(f"Cloning {PY_REPO}...")
        clone_repo(PY_REPO, py_dir)

        current_js_sha = get_head_sha(js_dir)
        current_py_sha = get_head_sha(py_dir)
        last_js_sha = state.get("last_js_sha")

        # ── First run: generate full API surface ─────────────────────────
        if not api_surface:
            print("First run — generating full API surface (this is the expensive one)...")
            js_src = collect_tree(js_dir, "src", (".ts", ".js", ".mts", ".mjs"))
            py_src = collect_tree(py_dir, "src", (".py",))

            api_surface = generate_api_surface(js_src, py_src)
            if not api_surface:
                print("ERROR: Failed to generate API surface. Will retry next run.")
                return

            print(f"API surface generated: {len(json.dumps(api_surface))} bytes")

            # Check for pre-existing gaps
            gaps = api_surface.get("gaps", [])
            if gaps:
                print(f"Found {len(gaps)} pre-existing gap(s) between JS and PY libs")

            save_gist_files(gh, gist_id, {
                STATE_FILENAME: {
                    "last_js_sha": current_js_sha,
                    "last_py_sha": current_py_sha,
                },
                SURFACE_FILENAME: api_surface,
            })
            print("API surface cached. Next runs will be incremental (~90% cheaper).")
            return

        # ── Incremental run: diff-only analysis ─────────────────────────
        if current_js_sha == last_js_sha:
            print("No new commits in JS repo. Nothing to do.")
            return

        print(f"JS repo: {last_js_sha or '(first run)'} → {current_js_sha}")

        js_commits = get_recent_commits(js_dir, last_js_sha)
        if not js_commits:
            print("No new commits found in range. Updating state.")
            save_gist_files(gh, gist_id, {
                STATE_FILENAME: {"last_js_sha": current_js_sha, "last_py_sha": current_py_sha},
            })
            return

        print(f"Found commits:\n{js_commits}\n")

        js_diff = get_diff(js_dir, last_js_sha)
        if not js_diff:
            print("No source changes in diff. Updating state.")
            save_gist_files(gh, gist_id, {
                STATE_FILENAME: {"last_js_sha": current_js_sha, "last_py_sha": current_py_sha},
            })
            return

        # Incremental analysis: diff + cached surface only (~5-10K tokens)
        print("Analyzing diff against cached API surface...")
        analysis = analyze_diff_against_surface(api_surface, js_diff, js_commits)

        if analysis is None:
            print("Analysis failed. Will retry next run.")
            return

        # Update cached surface with any structural changes
        surface_updates = analysis.get("surface_updates", [])
        if surface_updates:
            print(f"Applying {len(surface_updates)} surface update(s) to cache...")
            api_surface = apply_surface_updates(api_surface, surface_updates)

        if analysis.get("has_breaking_changes"):
            print(f"Breaking changes found! {len(analysis['changes'])} issue(s)")
            print(f"Summary: {analysis['summary']}")
            create_issue(gh, analysis)
        else:
            print("No breaking changes detected.")

        # Persist updated state + surface
        save_gist_files(gh, gist_id, {
            STATE_FILENAME: {"last_js_sha": current_js_sha, "last_py_sha": current_py_sha},
            SURFACE_FILENAME: api_surface,
        })
        print("Done.")


if __name__ == "__main__":
    main()
