from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class GitHubAssetRef:
    owner: str
    repository: str
    path: str
    ref: str = "main"


def build_raw_file_url(asset: GitHubAssetRef) -> str:
    return f"https://raw.githubusercontent.com/{asset.owner}/{asset.repository}/{asset.ref}/{asset.path.lstrip('/')}"


async def fetch_repository_file(asset: GitHubAssetRef, token: str = "") -> str:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(build_raw_file_url(asset), headers=headers)
        response.raise_for_status()
        return response.text
