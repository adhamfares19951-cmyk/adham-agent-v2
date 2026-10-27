"""GitHub Engine for adham-agent.
Allows the bot to:
1. Accept any GitHub URL (or owner/repo).
2. Clone, extract, inspect, and read its contents, architecture, and code.
3. Search code, read files, and extract useful scripts/libraries into workspace projects.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger("github_engine")

REPOS_CACHE_DIR = Path(__file__).resolve().parent.parent / "repos_cache"
REPOS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _normalize_github_url(repo_url: str) -> tuple[str, str, str]:
    """Extracts owner, repo, and clean clone URL."""
    url = repo_url.strip()
    # match patterns:
    # https://github.com/owner/repo(.git)?
    # github.com/owner/repo
    # owner/repo
    m = re.search(r"(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)", url)
    if m:
        owner = m.group(1)
        repo = m.group(2).removesuffix(".git")
    else:
        parts = url.split("/")
        if len(parts) == 2 and not url.startswith("http"):
            owner, repo = parts[0], parts[1].removesuffix(".git")
        else:
            raise ValueError(f"رابط غير صحيح لمستودع جيت هب: {repo_url}")

    clone_url = f"https://github.com/{owner}/{repo}.git"
    return owner, repo, clone_url


async def clone_or_update_repo(repo_url: str, depth: int = 1) -> dict[str, Any]:
    """Clones a GitHub repository to local cache or updates it."""
    try:
        owner, repo, clone_url = _normalize_github_url(repo_url)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    target_dir = REPOS_CACHE_DIR / f"{owner}__{repo}"

    try:
        if target_dir.exists() and (target_dir / ".git").exists():
            # Update existing
            proc = await asyncio.create_subprocess_exec(
                "git", "pull", "--ff-only",
                cwd=str(target_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            action = "updated"
        else:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)

            cmd = ["git", "clone", f"--depth={depth}", clone_url, str(target_dir)]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                err_text = stderr.decode(errors="replace")
                return {"success": False, "error": f"فشل في استنساخ المستودع عبر git: {err_text}"}
            action = "cloned"

        # Analyze structure
        structure = _analyze_repo(target_dir)
        return {
            "success": True,
            "action": action,
            "owner": owner,
            "repo": repo,
            "path": str(target_dir),
            "structure": structure,
        }
    except Exception as e:
        log.exception("Failed to clone/update repo: %s", repo_url)
        return {"success": False, "error": f"خطأ أثناء معالجة المستودع: {e}"}


def _analyze_repo(repo_dir: Path) -> dict[str, Any]:
    """Analyzes directory tree, key files, and package manifests."""
    tree: list[str] = []
    key_files: list[str] = []
    readme_snippet = ""
    tech_stack = []

    readme_files = [f for f in repo_dir.glob("README*") if f.is_file()]
    if readme_files:
        try:
            readme_text = readme_files[0].read_text(encoding="utf-8", errors="replace")
            # First 1500 chars
            readme_snippet = readme_text[:1500].strip()
        except Exception:
            pass

    # Check for tech stack indicators
    manifests = {
        "composer.json": "PHP / Laravel",
        "package.json": "Node.js / JavaScript / TypeScript",
        "pubspec.yaml": "Flutter / Dart",
        "requirements.txt": "Python",
        "pyproject.toml": "Python (Poetry/Modern)",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "Dockerfile": "Docker Container",
        "docker-compose.yml": "Docker Compose",
    }

    for fname, tech in manifests.items():
        if (repo_dir / fname).exists():
            tech_stack.append(f"{tech} ({fname})")
            key_files.append(fname)

    # Collect files up to 3 levels deep
    for root, dirs, files in os.walk(repo_dir):
        # Exclude .git and huge vendor dirs
        dirs[:] = [d for d in dirs if d not in (".git", "vendor", "node_modules", ".dart_tool", "dist", "build", "__pycache__")]
        rel_root = Path(root).relative_to(repo_dir)
        depth = len(rel_root.parts)
        if depth > 3:
            continue

        for f in files:
            rel_file = str(rel_root / f) if str(rel_root) != "." else f
            if len(tree) < 50:
                tree.append(rel_file)

    return {
        "tech_stack": tech_stack,
        "key_files": key_files,
        "readme_snippet": readme_snippet,
        "sample_tree": tree,
        "total_sample_files": len(tree),
    }


def read_repo_file(repo_name: str, relative_path: str, max_chars: int = 6000) -> dict[str, Any]:
    """Reads a specific file from a cached cloned repo."""
    # Find matching directory in REPOS_CACHE_DIR
    matched_dir = None
    r_clean = repo_name.lower().strip()
    for d in REPOS_CACHE_DIR.iterdir():
        if d.is_dir() and (r_clean in d.name.lower() or d.name.lower().endswith(f"__{r_clean}")):
            matched_dir = d
            break

    if not matched_dir:
        return {"error": f"المستودع '{repo_name}' غير موجود في الذاكرة المحلية. قم باستنساخه أولاً عبر inspect_github_repo."}

    target_file = matched_dir / relative_path.lstrip("/\\")
    if not target_file.exists() or not target_file.is_file():
        return {"error": f"الملف '{relative_path}' غير موجود داخل المستودع."}

    try:
        content = target_file.read_text(encoding="utf-8", errors="replace")
        truncated = False
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... (تم الاقتطاع لطول الملف)"
            truncated = True

        return {
            "success": True,
            "file": relative_path,
            "content": content,
            "truncated": truncated,
            "size_bytes": target_file.stat().st_size,
        }
    except Exception as e:
        return {"error": f"فشل في قراءة الملف: {e}"}


def search_repo_code(repo_name: str, pattern: str, limit: int = 15) -> list[dict[str, Any]]:
    """Searches code within a cached cloned repo."""
    matched_dir = None
    r_clean = repo_name.lower().strip()
    for d in REPOS_CACHE_DIR.iterdir():
        if d.is_dir() and (r_clean in d.name.lower() or d.name.lower().endswith(f"__{r_clean}")):
            matched_dir = d
            break

    if not matched_dir:
        return []

    results = []
    p_lower = pattern.lower()

    for root, dirs, files in os.walk(matched_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "vendor", "node_modules", ".dart_tool", "dist", "build", "__pycache__")]
        for f in files:
            # Skip binary
            if f.endswith((".png", ".jpg", ".jpeg", ".ico", ".exe", ".dll", ".so", ".zip", ".tar", ".gz", ".apk", ".bin")):
                continue
            fpath = Path(root) / f
            try:
                rel = fpath.relative_to(matched_dir)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as file_obj:
                    for i, line in enumerate(file_obj, 1):
                        if p_lower in line.lower():
                            results.append({
                                "file": str(rel),
                                "line_num": i,
                                "line": line.strip()[:150],
                            })
                            if len(results) >= limit:
                                return results
            except Exception:
                continue

    return results


async def search_github_worldwide(query: str, language: str = "", sort: str = "stars", limit: int = 6) -> dict[str, Any]:
    """Search all public GitHub repositories worldwide using GitHub Search API."""
    q = query.strip()
    if language:
        q += f" language:{language}"

    headers = {
        "User-Agent": "adham-agent-bot/2.0",
        "Accept": "application/vnd.github.v3+json",
    }
    gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": q, "sort": sort, "order": "desc", "per_page": limit},
                headers=headers
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                repos = []
                for item in items:
                    repos.append({
                        "name": item.get("full_name"),
                        "url": item.get("html_url"),
                        "clone_url": item.get("clone_url"),
                        "stars": item.get("stargazers_count", 0),
                        "description": item.get("description", "") or "لا يوجد وصف",
                        "language": item.get("language") or "غير محدد",
                        "updated_at": item.get("updated_at", "")[:10],
                    })
                return {"success": True, "total_count": data.get("total_count", 0), "repos": repos}
            else:
                return {"success": False, "error": f"GitHub API error: {resp.status_code} - {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _tool_search_github_worldwide(args: dict) -> str:
    query = str(args.get("query", "")).strip()
    language = str(args.get("language", "")).strip()
    if not query:
        return "يرجى تحديد كلمات البحث عن المستودعات."

    res = await search_github_worldwide(query, language=language)
    if not res.get("success"):
        return f"❌ تعذر البحث في GitHub: {res.get('error')}"

    repos = res.get("repos", [])
    if not repos:
        return f"لم يتم العثور على أي مستودعات تطابق: '{query}'."

    lines = [f"🌍 **أفضل مستودعات GitHub العالمية المطابقة لـ ({query})** [إجمالي: {res.get('total_count')}]:\n"]
    for r in repos:
        lines.append(
            f"⭐ **[{r['name']}]({r['url']})** (`{r['stars']} ⭐` • {r['language']})\n"
            f"   📝 {r['description']}\n"
            f"   📥 أمر التنزيل: `/repo {r['url']}`\n"
        )
    lines.append("💡 *اضغط على أمر التنزيل لفكفكة أي مستودع واستخراج أكواده.*")
    return "\n".join(lines)


# Tool definitions

async def _tool_inspect_github_repo(args: dict) -> str:
    repo_url = str(args.get("repo_url", ""))
    if not repo_url:
        return "يرجى تزويدي برابط مستودع GitHub."

    res = await clone_or_update_repo(repo_url)
    if not res.get("success"):
        return f"❌ خطأ أثناء تحميل المستودع: {res.get('error')}"

    st = res["structure"]
    tech = ", ".join(st["tech_stack"]) if st["tech_stack"] else "غير محدد تلقائياً"
    files_sample = "\n".join(f"  • {f}" for f in st["sample_tree"][:15])

    readme_snippet = st.get("readme_snippet", "")
    if readme_snippet:
        readme_display = f"\n📖 **نبذة من README:**\n> {readme_snippet[:400]}..."
    else:
        readme_display = ""

    return (
        f"✅ **تم تنزيل وفك مستودع GitHub بنجاح!**\n"
        f"📦 **المستودع:** `{res['owner']}/{res['repo']}`\n"
        f"🛠️ **التقنيات المكتشفة:** {tech}\n"
        f"📁 **المسار المحلي:** `{res['path']}`\n"
        f"{readme_display}\n\n"
        f"📂 **عينة من الملفات:**\n{files_sample}\n\n"
        f"💡 يمكنك الآن قراءة أي ملف برمجياً عبر `read_repo_file` أو البحث داخل الكود عبر `search_repo_code`."
    )


async def _tool_read_repo_file(args: dict) -> str:
    repo_name = str(args.get("repo_name", ""))
    file_path = str(args.get("file_path", ""))
    if not repo_name or not file_path:
        return "يرجى تحديد اسم المستودع ومسار الملف داخل المستودع."

    res = read_repo_file(repo_name, file_path)
    if "error" in res:
        return f"❌ {res['error']}"

    return (
        f"📄 **الملف: `{file_path}` من `{repo_name}`** ({res['size_bytes']} بايت):\n\n"
        f"```\n{res['content']}\n```"
    )


async def _tool_search_repo_code(args: dict) -> str:
    repo_name = str(args.get("repo_name", ""))
    pattern = str(args.get("pattern", ""))
    if not repo_name or not pattern:
        return "يرجى تحديد اسم المستودع وكلمة/دالة البحث."

    matches = search_repo_code(repo_name, pattern)
    if not matches:
        return f"لم أجد أي تطابق لـ '{pattern}' في كود `{repo_name}`."

    out = [f"🔎 نتائج البحث عن `{pattern}` في `{repo_name}` ({len(matches)} نتيجة):"]
    for m in matches:
        out.append(f"• `{m['file']}:{m['line_num']}` ➔ `{m['line']}`")
    return "\n".join(out)


TOOLS = [
    {
        "name": "inspect_github_repo",
        "description": (
            "قم بتنزيل واستنساخ وفك وفحص أي مستودع GitHub من الرابط مباشرة، "
            "وقراءة معماريته وملفاته وتقنياته لتوظيفه وفهم ما بداخله."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "رابط مستودع GitHub مثل https://github.com/owner/repo أو owner/repo",
                },
            },
            "required": ["repo_url"],
        },
        "handler": _tool_inspect_github_repo,
    },
    {
        "name": "read_repo_file",
        "description": "اقرأ محتوى أي ملف أو كود مصدري داخل مستودع GitHub الذي تم تنزيله مسبقاً.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "اسم المستودع مثل my-repo أو owner__my-repo",
                },
                "file_path": {
                    "type": "string",
                    "description": "مسار الملف داخل المستودع مثل README.md أو src/index.ts أو app/Services/Scraper.php",
                },
            },
            "required": ["repo_name", "file_path"],
        },
        "handler": _tool_read_repo_file,
    },
    {
        "name": "search_repo_code",
        "description": "ابحث عن الدوال أو الكلاسات أو الكلمات داخل كود مستودع GitHub المحمّل.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "اسم المستودع",
                },
                "pattern": {
                    "type": "string",
                    "description": "الدالة أو الكلمة أو التعبير المراد البحث عنه في الكود",
                },
            },
            "required": ["repo_name", "pattern"],
        },
        "handler": _tool_search_repo_code,
    },
    {
        "name": "search_github_worldwide",
        "description": "ابحث في ملايين مستودعات GitHub في العالم عن أي مكتبة، مشروع، روبوت، أو كود مفتوح المصدر بالنجوم واللغات والوصف.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "كلمات البحث أو الموضوع (مثال: 'laravel pos' أو 'trading bot python' أو 'telegram automation')",
                },
                "language": {
                    "type": "string",
                    "description": "لغة البرمجة المفضلة (اختياري، مثل python أو php أو typescript)",
                },
            },
            "required": ["query"],
        },
        "handler": _tool_search_github_worldwide,
    },
]
