"""Utilities for collecting repository data from the GitHub API."""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Tuple

import httpx

GITHUB_API_BASE = "https://api.github.com"


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an unexpected response."""


def extract_owner_repo(repo_url: str) -> Tuple[str, str]:
    """Extract the ``owner`` and ``repository`` slug from a GitHub URL."""

    if "github.com" not in repo_url:
        raise ValueError("The provided URL does not appear to be a GitHub repository")

    cleaned = repo_url.strip().rstrip("/")
    parts = cleaned.split("github.com/")[-1].split("/")
    if len(parts) < 2:
        raise ValueError("Please include both the owner and repository name in the URL")

    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


async def fetch_repository_snapshot(owner: str, repo: str) -> Dict[str, Any]:
    """Collect useful metadata, language stats, and a README excerpt for a repository."""

    async with httpx.AsyncClient(timeout=20.0, headers={"Accept": "application/vnd.github+json"}) as client:
        repo_resp = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
        if repo_resp.status_code != 200:
            raise GitHubAPIError(
                f"Unable to retrieve repository: {repo_resp.status_code} {repo_resp.text}"
            )
        repo_data = repo_resp.json()

        languages_resp = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/languages")
        languages_data = languages_resp.json() if languages_resp.status_code == 200 else {}

        readme_text = ""
        readme_resp = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme")
        if readme_resp.status_code == 200:
            readme_payload = readme_resp.json()
            encoding = readme_payload.get("encoding", "base64")
            if encoding == "base64" and "content" in readme_payload:
                raw_bytes = base64.b64decode(readme_payload["content"].encode())
                readme_text = raw_bytes.decode("utf-8", errors="ignore")
        else:
            readme_text = ""

        commits_resp = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
            params={"per_page": 5},
        )
        commits: List[Dict[str, Any]] = []
        if commits_resp.status_code == 200:
            for item in commits_resp.json():
                commit = item.get("commit", {})
                commits.append(
                    {
                        "message": commit.get("message", ""),
                        "date": (commit.get("author") or {}).get("date"),
                    }
                )

    topics = repo_data.get("topics", [])

    return {
        "name": repo_data.get("name"),
        "full_name": repo_data.get("full_name"),
        "description": repo_data.get("description"),
        "html_url": repo_data.get("html_url"),
        "default_branch": repo_data.get("default_branch"),
        "license": (repo_data.get("license") or {}).get("name"),
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "open_issues": repo_data.get("open_issues_count", 0),
        "watchers": repo_data.get("subscribers_count", 0),
        "language": repo_data.get("language"),
        "topics": topics,
        "languages": languages_data,
        "recent_commits": commits,
        "readme_excerpt": readme_text[:4000],
    }
