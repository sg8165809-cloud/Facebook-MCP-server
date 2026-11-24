"""Facebook Page MCP server (FastMCP + SSE).

Tools:
  - get_page_posts(limit)  : পেজের সাম্প্রতিক পোস্ট পড়া
  - publish_post(message, link) : পেজে নতুন পোস্ট করা
"""
import os

import httpx
from mcp.server.fastmcp import FastMCP

GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v21.0")
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

PAGE_ID = os.environ["FB_PAGE_ID"]
PAGE_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]
# URL-এর ভেতরে গোপন কোড, যাতে অন্য কেউ আপনার সার্ভার ব্যবহার করতে না পারে
SECRET = os.environ.get("MCP_SECRET", "").strip("/")
PREFIX = f"/{SECRET}" if SECRET else ""

mcp = FastMCP(
    "facebook-page",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
    sse_path=f"{PREFIX}/sse",
    message_path=f"{PREFIX}/messages/",
)


def _check(resp: httpx.Response) -> dict:
    data = resp.json()
    if resp.status_code >= 400 or "error" in data:
        err = data.get("error", data)
        raise RuntimeError(f"Facebook API error: {err}")
    return data


@mcp.tool()
async def get_page_posts(limit: int = 10) -> dict:
    """Facebook পেজের সাম্প্রতিক পোস্টগুলো পড়ে (সর্বোচ্চ ২৫টি)।"""
    limit = max(1, min(limit, 25))
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{GRAPH_URL}/{PAGE_ID}/posts",
            params={
                "fields": "id,message,created_time,permalink_url",
                "limit": limit,
                "access_token": PAGE_TOKEN,
            },
        )
    return _check(r)


@mcp.tool()
async def publish_post(message: str, link: str | None = None) -> dict:
    """Facebook পেজে নতুন টেক্সট পোস্ট (ঐচ্ছিক লিংকসহ) প্রকাশ করে।"""
    payload = {"message": message, "access_token": PAGE_TOKEN}
    if link:
        payload["link"] = link
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{GRAPH_URL}/{PAGE_ID}/feed", data=payload)
    return _check(r)


if __name__ == "__main__":
    mcp.run(transport="sse")
